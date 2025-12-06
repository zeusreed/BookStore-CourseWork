import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from database import get_db_connection


class AdminWindow(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("Кітап Дүкені - ӘКІМШІ (ADMIN)")
        self.geometry("1200x700")

        # Переменные для сортировки
        self.sort_col = None
        self.sort_reverse = False

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Вкладка 1: Книги
        self.tab_books = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_books, text="Кітаптарды басқару")
        self.init_books_ui()

        # Вкладка 2: Отчеты
        self.tab_reports = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reports, text="Есептер (Сатылымдар)")
        self.init_reports_ui()

    # --- КӨМЕКШІ ФУНКЦИЯ (ID іздеу немесе жасау) ---
    def get_or_create_id(self, cursor, table, id_col, name_col, value):
        """Автор/Жанр/Баспа атын іздейді. Егер жоқ болса - жаңасын жасайды."""
        value = value.strip()
        # 1. Іздеу
        cursor.execute(f"SELECT {id_col} FROM {table} WHERE {name_col}=?", (value,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            # 2. Жаңасын қосу
            cursor.execute(f"INSERT INTO {table} ({name_col}) OUTPUT INSERTED.{id_col} VALUES (?)", (value,))
            return cursor.fetchone()[0]

    # ================= ВКЛАДКА 1: КІТАПТАР =================
    def init_books_ui(self):
        # 1. Фильтр (Іздеу)
        filter_frame = ttk.LabelFrame(self.tab_books, text="Іздеу")
        filter_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(filter_frame, text="Атауы бойынша:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_books())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=30).pack(side='left', padx=5)

        ttk.Button(filter_frame, text="Жаңарту", command=self.load_books).pack(side='left', padx=10)

        # 2. Кесте (Table)
        self.columns = {
            'ID': 'ID',
            'Title': 'Атауы',
            'Author': 'Автор',
            'Genre': 'Жанр',
            'Publisher': 'Баспа',
            'Price': 'Бағасы',
            'Stock': 'Қоймада (дана)'
        }
        col_keys = list(self.columns.keys())

        self.tree = ttk.Treeview(self.tab_books, columns=col_keys, show='headings')

        # Бағандарды баптау (Сұрыптау қосылған)
        for col in col_keys:
            self.tree.heading(col, text=self.columns[col], command=lambda c=col: self.sort_tree(c, False))
            self.tree.column(col, width=120)
        self.tree.column('ID', width=40, anchor='center')

        # Скроллбар
        sb = ttk.Scrollbar(self.tab_books, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side='top', fill='both', expand=True, padx=5)
        sb.pack(side='right', fill='y')

        # 3. Батырмалар (CRUD)
        btn_frame = ttk.Frame(self.tab_books)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="➕ Жаңа кітап қосу", command=self.add_book_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="✏️ Өзгерту (Толық)", command=self.edit_book_dialog).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Жою", command=self.delete_book).pack(side='left', padx=5)

        self.load_books()

    def load_books(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        search = self.search_var.get()
        conn = get_db_connection()
        if conn:
            # JOIN арқылы ID орнына атауларын аламыз
            sql = """
                  SELECT B.BookID, B.Title, A.FullName, G.GenreName, P.PublisherName, B.Price, B.StockQuantity
                  FROM Books B
                           JOIN Authors A ON B.AuthorID = A.AuthorID
                           JOIN Genres G ON B.GenreID = G.GenreID
                           JOIN Publishers P ON B.PublisherID = P.PublisherID
                  WHERE B.Title LIKE ? \
                  """
            cursor = conn.cursor()
            cursor.execute(sql, [f"%{search}%"])
            for row in cursor:
                # Бағаны әдемілеу (4500.0000 -> 4500)
                price = f"{row[5]:.0f}"
                self.tree.insert('', 'end', values=(
                    row[0], row[1], row[2], row[3], row[4], int(price), row[6]
                ))
            conn.close()

    def sort_tree(self, col, reverse):
        # Деректерді алу және сұрыптау
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            # Сан ретінде сұрыптауға тырысамыз
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except:
            # Болмаса мәтін ретінде
            l.sort(reverse=reverse)

        # Кестені қайта құру
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Заголовоктарды жаңарту (Стрелка қосу)
        for c in self.columns:
            self.tree.heading(c, text=self.columns[c])  # Тазалау

        arrow = " ▼" if reverse else " ▲"
        self.tree.heading(col, text=self.columns[col] + arrow, command=lambda: self.sort_tree(col, not reverse))

    # --- ҚОСУ ФУНКЦИЯСЫ ---
    def add_book_dialog(self):
        win = tk.Toplevel(self)
        win.title("Кітап қосу")
        win.geometry("400x450")

        labels = ["Кітап атауы", "Автор (Аты-жөні)", "Жанр атауы", "Баспа атауы", "Бағасы", "Қалдық саны"]
        entries = {}

        for lbl in labels:
            ttk.Label(win, text=lbl).pack(pady=2)
            e = ttk.Entry(win, width=40)
            e.pack(pady=2)
            entries[lbl] = e

        def save():
            try:
                conn = get_db_connection()
                cur = conn.cursor()

                # ID-ларды автоматты түрде табамыз немесе жасаймыз
                a_id = self.get_or_create_id(cur, "Authors", "AuthorID", "FullName", entries["Автор (Аты-жөні)"].get())
                g_id = self.get_or_create_id(cur, "Genres", "GenreID", "GenreName", entries["Жанр атауы"].get())
                p_id = self.get_or_create_id(cur, "Publishers", "PublisherID", "PublisherName",
                                             entries["Баспа атауы"].get())

                cur.execute("""
                            INSERT INTO Books (Title, AuthorID, GenreID, PublisherID, Price, StockQuantity)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (entries["Кітап атауы"].get(), a_id, g_id, p_id, entries["Бағасы"].get(),
                                  entries["Қалдық саны"].get()))

                conn.commit()
                conn.close()
                messagebox.showinfo("Сәтті", "Кітап қосылды!")
                win.destroy()
                self.load_books()
            except Exception as e:
                messagebox.showerror("Қате", str(e))

        ttk.Button(win, text="Сақтау", command=save).pack(pady=15)

    # --- ӨЗГЕРТУ ФУНКЦИЯСЫ ---
    def edit_book_dialog(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("!", "Өзгертетін кітапты таңдаңыз")
            return

        item = self.tree.item(sel[0])
        vals = item['values']
        # vals: [0-ID, 1-Title, 2-Author, 3-Genre, 4-Pub, 5-Price, 6-Stock]

        win = tk.Toplevel(self)
        win.title("Кітапты өзгерту")
        win.geometry("400x450")

        labels_map = {
            "Кітап атауы": vals[1],
            "Автор (Аты-жөні)": vals[2],
            "Жанр атауы": vals[3],
            "Баспа атауы": vals[4],
            "Бағасы": vals[5],
            "Қалдық саны": vals[6]
        }
        entries = {}

        for lbl, val in labels_map.items():
            ttk.Label(win, text=lbl).pack(pady=2)
            e = ttk.Entry(win, width=40)
            e.insert(0, str(val))
            e.pack(pady=2)
            entries[lbl] = e

        def update():
            try:
                conn = get_db_connection()
                cur = conn.cursor()

                a_id = self.get_or_create_id(cur, "Authors", "AuthorID", "FullName", entries["Автор (Аты-жөні)"].get())
                g_id = self.get_or_create_id(cur, "Genres", "GenreID", "GenreName", entries["Жанр атауы"].get())
                p_id = self.get_or_create_id(cur, "Publishers", "PublisherID", "PublisherName",
                                             entries["Баспа атауы"].get())

                cur.execute("""
                            UPDATE Books
                            SET Title=?,
                                AuthorID=?,
                                GenreID=?,
                                PublisherID=?,
                                Price=?,
                                StockQuantity=?
                            WHERE BookID = ?
                            """, (entries["Кітап атауы"].get(), a_id, g_id, p_id,
                                  entries["Бағасы"].get(), entries["Қалдық саны"].get(), vals[0]))

                conn.commit()
                conn.close()
                messagebox.showinfo("Сәтті", "Деректер жаңартылды!")
                win.destroy()
                self.load_books()
            except Exception as e:
                messagebox.showerror("Қате", str(e))

        ttk.Button(win, text="Сақтау", command=update).pack(pady=15)

    def delete_book(self):
        sel = self.tree.selection()
        if not sel: return
        bid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Жою", "Бұл кітапты өшіресіз бе?"):
            conn = get_db_connection()
            try:
                conn.cursor().execute("DELETE FROM Books WHERE BookID=?", (bid,)).commit()
                self.load_books()
            except Exception as e:
                messagebox.showerror("Қате", "Бұл кітапты жою мүмкін емес (Сатылым тарихы бар)")
            finally:
                conn.close()

    # ================= ВКЛАДКА 2: ЕСЕПТЕР =================
    def init_reports_ui(self):
        btn_frame = ttk.Frame(self.tab_reports)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="🔄 Жаңарту", command=self.load_report).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📊 Диаграмма (Жанрлар)", command=self.show_chart).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📥 Excel-ге жүктеу", command=self.export_excel).pack(side='left', padx=5)

        self.rep_cols = {'Date': 'Уақыты', 'Client': 'Клиент', 'Book': 'Кітап', 'Qty': 'Саны', 'Total': 'Сомасы'}
        self.tree_rep = ttk.Treeview(self.tab_reports, columns=list(self.rep_cols.keys()), show='headings')

        for col in self.rep_cols:
            self.tree_rep.heading(col, text=self.rep_cols[col])

        self.tree_rep.column('Date', width=120)
        self.tree_rep.column('Qty', width=50, anchor='center')

        self.tree_rep.pack(fill='both', expand=True, padx=5)
        self.load_report()

    def load_report(self):
        for i in self.tree_rep.get_children(): self.tree_rep.delete(i)
        conn = get_db_connection()
        if conn:
            # ТЕПЕРЬ ЗАПРОС КОРОТКИЙ И ПОНЯТНЫЙ:
            sql = """
            SELECT FORMAT(SaleDate, 'dd.MM.yyyy HH:mm'), 
                   ClientName, 
                   BookTitle, 
                   Quantity, 
                   TotalAmount 
            FROM vw_SalesSummary
            ORDER BY SaleDate DESC
            """
            cursor = conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                self.tree_rep.insert('', 'end', values=(row[0], row[1], row[2], row[3], int(row[4])))
            conn.close()

    def show_chart(self):
        conn = get_db_connection()
        if conn:
            try:
                # Жанрлар бойынша статистика
                sql = """
                      SELECT G.GenreName, SUM(SD.Quantity)
                      FROM SaleDetails SD
                               JOIN Books B ON SD.BookID = B.BookID
                               JOIN Genres G ON B.GenreID = G.GenreID
                      GROUP BY G.GenreName \
                      """
                cursor = conn.cursor()
                cursor.execute(sql)
                data = cursor.fetchall()

                if not data:
                    messagebox.showinfo("Инфо", "Сатылымдар әлі жоқ")
                    return

                genres = [row[0] for row in data]
                counts = [row[1] for row in data]

                # График салу
                plt.figure(figsize=(8, 6))
                plt.pie(counts, labels=genres, autopct='%1.1f%%', startangle=140)
                plt.title("Сатылымдар бойынша статистика (Жанрлар)")
                plt.show()

            except Exception as e:
                messagebox.showerror("Қате", str(e))
            finally:
                conn.close()

    def export_excel(self):
        conn = get_db_connection()
        if conn:
            try:
                warnings.simplefilter(action='ignore', category=UserWarning)

                # ТЕПЕРЬ ЗАПРОС КОРОТКИЙ (берем всё из представления):
                sql = """
                      SELECT SaleID AS 'Чек №', FORMAT(SaleDate, 'dd.MM.yyyy HH:mm') AS 'Уақыты', ClientName AS 'Клиент', BookTitle AS 'Кітап', Quantity AS 'Саны', Price AS 'Дана бағасы', TotalAmount AS 'Жалпы сома'
                      FROM vw_SalesSummary
                      ORDER BY SaleDate DESC \
                      """

                df = pd.read_sql(sql, conn)

                filename = "sales_report_full.xlsx"
                df.to_excel(filename, index=False)

                messagebox.showinfo("Сәтті", f"Есеп '{filename}' файлына сақталды!")

            except Exception as e:
                messagebox.showerror("Қате", str(e))
            finally:
                conn.close()