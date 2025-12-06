import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import get_db_connection
import matplotlib.pyplot as plt


class ClientWindow(tk.Tk):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.title("Кітап Дүкені - Сатып алушы")
        self.geometry("1000x600")

        self.sort_col = None
        self.sort_reverse = False

        # Фильтр
        filter_frame = ttk.LabelFrame(self, text="Іздеу")
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text="Атауы:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.load_books())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=30).pack(side='left', padx=5)

        ttk.Label(filter_frame, text="Баға (мин-макс):").pack(side='left', padx=5)
        self.price_min = ttk.Entry(filter_frame, width=8)
        self.price_min.pack(side='left')
        self.price_max = ttk.Entry(filter_frame, width=8)
        self.price_max.pack(side='left', padx=2)

        ttk.Button(filter_frame, text="Іздеу", command=self.load_books).pack(side='left', padx=10)

        # Таблица
        self.columns = {
            'ID': 'ID',
            'Title': 'Кітап атауы',
            'Author': 'Автор',
            'Genre': 'Жанр',
            'Price': 'Бағасы (тг)',
            'Stock': 'Қоймада (дана)'
        }
        col_keys = list(self.columns.keys())

        self.tree = ttk.Treeview(self, columns=col_keys, show='headings')

        # Сортировка со стрелочками
        for col in col_keys:
            self.tree.heading(col, text=self.columns[col], command=lambda c=col: self.sort_tree(c, False))

        self.tree.column('ID', width=40, anchor='center')
        self.tree.column('Price', width=80, anchor='e')
        self.tree.column('Stock', width=100, anchor='center')

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Кнопка покупки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=10)

        tk.Button(btn_frame, text="САТЫП АЛУ", bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold"), command=self.buy_book).pack(side='right', ipadx=20)

        self.load_books()

    def load_books(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        search = self.search_var.get()
        p_min = self.price_min.get()
        p_max = self.price_max.get()

        conn = get_db_connection()
        if not conn: return

        sql = """
              SELECT B.BookID, B.Title, A.FullName, G.GenreName, B.Price, B.StockQuantity
              FROM Books B
                       JOIN Authors A ON B.AuthorID = A.AuthorID
                       JOIN Genres G ON B.GenreID = G.GenreID
              WHERE B.Title LIKE ? \
              """
        params = [f"%{search}%"]

        if p_min and p_min.isdigit():
            sql += " AND B.Price >= ?"
            params.append(p_min)
        if p_max and p_max.isdigit():
            sql += " AND B.Price <= ?"
            params.append(p_max)

        cursor = conn.cursor()
        cursor.execute(sql, params)
        for row in cursor:
            price = f"{row[4]:.0f}"
            self.tree.insert('', 'end', values=(row[0], row[1], row[2], row[3], int(price), row[5]))
        conn.close()

    def sort_tree(self, col, reverse):
        # 1. Сортировка
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0].replace(' ', '')), reverse=reverse)
        except:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # 2. Визуализация стрелочек
        for c in self.columns:
            self.tree.heading(c, text=self.columns[c])

        arrow = " ▼" if reverse else " ▲"
        self.tree.heading(col, text=self.columns[col] + arrow, command=lambda: self.sort_tree(col, not reverse))

    def buy_book(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Назар аударыңыз", "Сатып алатын кітапты таңдаңыз!")
            return

        item = self.tree.item(selected[0])
        book_id = item['values'][0]
        title = item['values'][1]
        price = float(item['values'][4])
        stock = int(item['values'][5])

        qty_str = simpledialog.askstring("Сатып алу", f"'{title}' кітабынан қанша дана аласыз?", parent=self)
        if not qty_str: return

        try:
            qty = int(qty_str)
            if qty <= 0: raise ValueError
        except:
            messagebox.showerror("Қате", "Дұрыс сан енгізіңіз!")
            return

        if stock < qty:
            messagebox.showerror("Қате", f"Қоймада жеткіліксіз! Бар болғаны: {stock} дана")
            return

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                total = price * qty
                user_val = self.user_id if self.user_id else 1

                cursor.execute("INSERT INTO Sales (CustomerID, TotalAmount) OUTPUT INSERTED.SaleID VALUES (?, ?)",
                               (user_val, total))
                sale_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO SaleDetails (SaleID, BookID, Quantity, Price) VALUES (?, ?, ?, ?)",
                               (sale_id, book_id, qty, price))
                # cursor.execute("UPDATE Books SET StockQuantity = StockQuantity - ? WHERE BookID = ?", (qty, book_id))

                conn.commit()
                messagebox.showinfo("Сәтті", f"Сатылым жасалды!\nЧек №{sale_id}\nЖалпы сома: {total} тг")
                self.load_books()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Қате", str(e))
            finally:
                conn.close()

    def show_chart(self):
        conn = get_db_connection()
        if conn:
            # Запрос: Название жанра и сумма продаж по нему
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
            conn.close()

            if not data:
                messagebox.showinfo("Инфо", "Сатылымдар жоқ")
                return

            genres = [row[0] for row in data]
            counts = [row[1] for row in data]

            # Рисуем круг
            plt.figure(figsize=(6, 6))
            plt.pie(counts, labels=genres, autopct='%1.1f%%')
            plt.title("Жанрлар бойынша сатылым")
            plt.show()