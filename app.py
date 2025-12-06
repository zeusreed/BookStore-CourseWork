import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import pandas as pd

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ (ВСТАВЬ ТОТ ВАРИАНТ, КОТОРЫЙ У ТЕБЯ ЗАРАБОТАЛ) ---
CONN_STR = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=ALESSANDRO\SQLEXPRESS01;'  # <-- ПРОВЕРЬ ИМЯ СЕРВЕРА
    r'DATABASE=BookStoreDB;'
    r'Trusted_Connection=yes;'
)


# --- КЛАСС ОКНА ВХОДА (LOGIN) ---
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Авторизация")
        self.geometry("300x250")
        self.resizable(False, False)

        # Центрирование окна
        self.eval('tk::PlaceWindow . center')

        ttk.Label(self, text="Кітап Дүкеніне қош келдіңіз!", font=("Arial", 10, "bold")).pack(pady=10)

        # Логин
        ttk.Label(self, text="Логин:").pack(pady=5)
        self.entry_login = ttk.Entry(self)
        self.entry_login.pack()

        # Пароль
        ttk.Label(self, text="Құпия сөз (Пароль):").pack(pady=5)
        self.entry_pass = ttk.Entry(self, show="*")
        self.entry_pass.pack()

        # Кнопка входа
        ttk.Button(self, text="Кіру (Login)", command=self.check_login).pack(pady=10)

        # Кнопка для покупателя (без пароля)
        ttk.Button(self, text="Сатып алушы ретінде кіру", command=self.login_as_guest).pack(pady=5)

    def get_db_connection(self):
        try:
            return pyodbc.connect(CONN_STR)
        except Exception as e:
            messagebox.showerror("Қате", f"Серверге қосылу қатесі:\n{e}")
            return None

    def check_login(self):
        login = self.entry_login.get()
        password = self.entry_pass.get()

        conn = self.get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Проверяем пользователя в БД
            cursor.execute("SELECT Role FROM Users WHERE Username=? AND Password=?", (login, password))
            row = cursor.fetchone()
            conn.close()

            if row:
                role = row[0]  # 'Admin' или 'Client'
                messagebox.showinfo("Сәтті", f"Қош келдіңіз, {role}!")
                self.destroy()  # Закрываем окно входа
                app = BookStoreApp(user_role=role)  # Открываем главное окно
                app.mainloop()
            else:
                messagebox.showerror("Қате", "Логин немесе құпия сөз қате!")

    def login_as_guest(self):
        self.destroy()
        app = BookStoreApp(user_role='Client')
        app.mainloop()


# --- ГЛАВНОЕ ПРИЛОЖЕНИЕ ---
class BookStoreApp(tk.Tk):
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role  # Сохраняем роль (Admin или Client)
        self.title(f"Кітап Дүкені ({self.user_role} режимі)")
        self.geometry("900x600")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 1. Вкладка "Книги"
        self.tab_books = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_books, text="Кітаптар каталогы")
        self.init_books_tab()

        # 2. Вкладка "Магазин" (Доступна всем)
        self.tab_shop = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_shop, text="Сату (Касса)")
        self.init_shop_tab()

        # 3. Вкладка "Отчеты" (ТОЛЬКО ДЛЯ АДМИНА)
        if self.user_role == 'Admin':
            self.tab_reports = ttk.Frame(self.notebook)
            self.notebook.add(self.tab_reports, text="Есептер (Admin)")
            self.init_reports_tab()

    def get_db_connection(self):
        try:
            return pyodbc.connect(CONN_STR)
        except Exception as e:
            messagebox.showerror("Қате", str(e))
            return None

    # --- Вкладка 1: КНИГИ ---
    def init_books_tab(self):
        # Панель управления ТОЛЬКО ДЛЯ АДМИНА
        if self.user_role == 'Admin':
            control_frame = ttk.LabelFrame(self.tab_books, text="Әкімші панелі")
            control_frame.pack(fill='x', padx=5, pady=5)

            ttk.Label(control_frame, text="Атауы:").grid(row=0, column=0)
            self.entry_title = ttk.Entry(control_frame)
            self.entry_title.grid(row=0, column=1)

            ttk.Label(control_frame, text="Бағасы:").grid(row=0, column=2)
            self.entry_price = ttk.Entry(control_frame)
            self.entry_price.grid(row=0, column=3)

            ttk.Label(control_frame, text="Қалдық:").grid(row=0, column=4)
            self.entry_stock = ttk.Entry(control_frame)
            self.entry_stock.grid(row=0, column=5)

            # ID для внешних ключей
            ttk.Label(control_frame, text="Автор ID:").grid(row=1, column=0)
            self.entry_author_id = ttk.Entry(control_frame)
            self.entry_author_id.grid(row=1, column=1)

            ttk.Label(control_frame, text="Жанр ID:").grid(row=1, column=2)
            self.entry_genre_id = ttk.Entry(control_frame)
            self.entry_genre_id.grid(row=1, column=3)

            ttk.Label(control_frame, text="Баспа ID:").grid(row=1, column=4)
            self.entry_pub_id = ttk.Entry(control_frame)
            self.entry_pub_id.grid(row=1, column=5)

            btn_frame = ttk.Frame(control_frame)
            btn_frame.grid(row=2, column=0, columnspan=6, pady=10)

            ttk.Button(btn_frame, text="Қосу", command=self.add_book).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Өзгерту (Баға)", command=self.update_book).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Жою", command=self.delete_book).pack(side='left', padx=5)

        # Кнопка обновления доступна всем
        top_frame = ttk.Frame(self.tab_books)
        top_frame.pack(fill='x', padx=5)
        ttk.Button(top_frame, text="Тізімді жаңарту", command=self.load_books).pack(side='right', pady=5)

        # Таблица
        columns = ('ID', 'Title', 'Price', 'Stock', 'Author')
        self.tree_books = ttk.Treeview(self.tab_books, columns=columns, show='headings')

        self.tree_books.heading('ID', text='ID')
        self.tree_books.heading('Title', text='Кітап атауы')
        self.tree_books.heading('Price', text='Бағасы')
        self.tree_books.heading('Stock', text='Қоймада')
        self.tree_books.heading('Author', text='Автор ID')
        self.tree_books.column('ID', width=30)

        self.tree_books.pack(fill='both', expand=True, padx=5, pady=5)
        self.load_books()

    def load_books(self):
        for i in self.tree_books.get_children():
            self.tree_books.delete(i)
        conn = self.get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT BookID, Title, Price, StockQuantity, AuthorID FROM Books")
            for row in cursor:
                self.tree_books.insert('', 'end', values=(row[0], row[1], int(row[2]), row[3], row[4]))
            conn.close()

    def add_book(self):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Books (Title, AuthorID, GenreID, PublisherID, Price, StockQuantity) VALUES (?, ?, ?, ?, ?, ?)",
                (self.entry_title.get(), self.entry_author_id.get(), self.entry_genre_id.get(),
                 self.entry_pub_id.get(), self.entry_price.get(), self.entry_stock.get())
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Сәтті", "Кітап қосылды!")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Қате", str(e))

    def delete_book(self):
        selected = self.tree_books.selection()
        if not selected: return
        book_id = self.tree_books.item(selected[0])['values'][0]
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Books WHERE BookID = ?", (book_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Сәтті", "Кітап жойылды!")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Қате", str(e))

    def update_book(self):
        selected = self.tree_books.selection()
        if not selected: return
        book_id = self.tree_books.item(selected[0])['values'][0]
        new_price = self.entry_price.get()
        if not new_price: return
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Books SET Price = ? WHERE BookID = ?", (new_price, book_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Сәтті", "Баға жаңартылды!")
            self.load_books()
        except Exception as e:
            messagebox.showerror("Қате", str(e))

    # --- Вкладка 2: МАГАЗИН ---
    def init_shop_tab(self):
        frame = ttk.Frame(self.tab_shop)
        frame.pack(padx=20, pady=20)

        ttk.Label(frame, text="Кітап ID:").grid(row=0, column=0, pady=5)
        self.shop_book_id = ttk.Entry(frame)
        self.shop_book_id.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Клиент ID:").grid(row=1, column=0, pady=5)
        self.shop_client_id = ttk.Entry(frame)
        self.shop_client_id.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Саны:").grid(row=2, column=0, pady=5)
        self.shop_qty = ttk.Entry(frame)
        self.shop_qty.grid(row=2, column=1, pady=5)

        ttk.Button(frame, text="САТЫП АЛУ", command=self.make_sale).grid(row=3, column=0, columnspan=2, pady=20)

    def make_sale(self):
        # Логика продажи (без изменений)
        b_id = self.shop_book_id.get()
        c_id = self.shop_client_id.get()
        qty = self.shop_qty.get()
        if not b_id or not c_id or not qty: return
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Price, StockQuantity FROM Books WHERE BookID = ?", (b_id,))
            book = cursor.fetchone()
            if not book:
                messagebox.showerror("Қате", "Кітап табылмады!")
                return
            price, stock = book[0], book[1]
            if stock < int(qty):
                messagebox.showerror("Қате", f"Қоймада жеткіліксіз! Бар болғаны: {stock}")
                return
            total = price * int(qty)
            cursor.execute("INSERT INTO Sales (CustomerID, TotalAmount) OUTPUT INSERTED.SaleID VALUES (?, ?)",
                           (c_id, total))
            sale_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO SaleDetails (SaleID, BookID, Quantity, Price) VALUES (?, ?, ?, ?)",
                           (sale_id, b_id, qty, price))
            cursor.execute("UPDATE Books SET StockQuantity = StockQuantity - ? WHERE BookID = ?", (qty, b_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Сәтті", f"Сатылды! Чек №{sale_id}\nСомасы: {total}")
            self.load_books()
            if self.user_role == 'Admin': self.load_sales_report()
        except Exception as e:
            messagebox.showerror("Қате", str(e))

    # --- Вкладка 3: ЕСЕПТЕР ---
    def init_reports_tab(self):
        btn_frame = ttk.Frame(self.tab_reports)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Есепті жаңарту", command=self.load_sales_report).pack(side='left')
        ttk.Button(btn_frame, text="Excel-ге жүктеу", command=self.export_excel).pack(side='left', padx=10)
        self.tree_sales = ttk.Treeview(self.tab_reports, columns=('Date', 'Book', 'Qty', 'Total'), show='headings')
        self.tree_sales.heading('Date', text='Уақыты')
        self.tree_sales.heading('Book', text='Кітап')
        self.tree_sales.heading('Qty', text='Саны')
        self.tree_sales.heading('Total', text='Сомасы')
        self.tree_sales.pack(fill='both', expand=True, padx=5, pady=5)
        self.load_sales_report()

    def load_sales_report(self):
        for i in self.tree_sales.get_children(): self.tree_sales.delete(i)
        conn = self.get_db_connection()
        if conn:
            sql = """
                  SELECT S.SaleDate, B.Title, SD.Quantity, S.TotalAmount
                  FROM Sales S
                           JOIN SaleDetails SD ON S.SaleID = SD.SaleID
                           JOIN Books B ON SD.BookID = B.BookID
                  ORDER BY S.SaleDate DESC \
                  """
            cursor = conn.cursor()
            cursor.execute(sql)
            for row in cursor:
                self.tree_sales.insert('', 'end', values=(row[0], row[1], row[2], int(row[3])))
            conn.close()

    def export_excel(self):
        conn = self.get_db_connection()
        if conn:
            df = pd.read_sql("SELECT * FROM Sales", conn)
            df.to_excel("sales_report.xlsx", index=False)
            messagebox.showinfo("Сәтті", "Excel файлы сақталды!")
            conn.close()


if __name__ == "__main__":
    # Сначала запускаем окно входа
    login_app = LoginWindow()
    login_app.mainloop()