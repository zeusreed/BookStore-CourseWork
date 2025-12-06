import tkinter as tk
from tkinter import ttk, messagebox
import hashlib  # Библиотека для шифрования
from database import get_db_connection
from admin_view import AdminWindow
from client_view import ClientWindow


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Авторизация")
        self.geometry("350x300")
        self.eval('tk::PlaceWindow . center')

        ttk.Label(self, text="Кітап Дүкені", font=("Arial", 14, "bold")).pack(pady=15)

        frame = ttk.Frame(self)
        frame.pack(pady=5)

        ttk.Label(frame, text="Логин:").grid(row=0, column=0, padx=5, sticky='e')
        self.entry_login = ttk.Entry(frame)
        self.entry_login.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="Құпия сөз:").grid(row=1, column=0, padx=5, sticky='e', pady=5)
        self.entry_pass = ttk.Entry(frame, show="*")
        self.entry_pass.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self, text="Кіру", command=self.login, width=20).pack(pady=10)
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=20, pady=5)
        ttk.Button(self, text="Тіркелу (Регистрация)", command=self.register_dialog).pack(pady=5)

    # --- ФУНКЦИЯ ХЕШИРОВАНИЯ ---
    def hash_password(self, password):
        # Превращаем "123" в "a665a45..."
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):
        login = self.entry_login.get()
        password = self.entry_pass.get()

        # Хешируем введенный пароль, чтобы сравнить с базой
        hashed_pass = self.hash_password(password)

        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Проверяем логин и ХЕШ пароля
            # Также берем CustomerID, чтобы знать, кто это
            cursor.execute("SELECT Role, UserID, CustomerID FROM Users WHERE Username=? AND Password=?",
                           (login, hashed_pass))
            row = cursor.fetchone()
            conn.close()

            if row:
                role = row[0]
                user_id = row[1]
                customer_id = row[2]  # ID клиента из таблицы Customers

                self.destroy()

                if role == 'Admin':
                    AdminWindow(user_id).mainloop()
                else:
                    # Клиенту передаем именно его CustomerID, чтобы покупки записывались на него
                    if customer_id:
                        ClientWindow(customer_id).mainloop()
                    else:
                        messagebox.showerror("Қате", "Бұл пайдаланушыда Клиент деректері жоқ!")
            else:
                messagebox.showerror("Қате", "Логин немесе құпия сөз қате!")

    def register_dialog(self):
        reg_win = tk.Toplevel(self)
        reg_win.title("Тіркелу")
        reg_win.geometry("400x450")

        # Поля для таблицы Customers
        fields = ["Аты (Имя)", "Тегі (Фамилия)", "Телефон", "Email", "Логин", "Құпия сөз"]
        entries = {}

        for f in fields:
            ttk.Label(reg_win, text=f).pack(pady=2)
            # Для пароля скрываем символы
            show_char = "*" if f == "Құпия сөз" else None
            e = ttk.Entry(reg_win, show=show_char, width=30)
            e.pack(pady=2)
            entries[f] = e

        def save_user():
            # Собираем данные
            fname = entries["Аты (Имя)"].get().strip()
            lname = entries["Тегі (Фамилия)"].get().strip()
            phone = entries["Телефон"].get().strip()
            email = entries["Email"].get().strip()
            login = entries["Логин"].get().strip()
            raw_pass = entries["Құпия сөз"].get().strip()

            if not all([fname, lname, phone, login, raw_pass]):
                messagebox.showwarning("!", "Барлық міндетті өрістерді толтырыңыз!")
                return

            try:
                conn = get_db_connection()
                cur = conn.cursor()

                # 1. Проверяем логин
                cur.execute("SELECT Count(*) FROM Users WHERE Username=?", (login,))
                if cur.fetchone()[0] > 0:
                    messagebox.showerror("Қате", "Бұл логин бос емес!")
                    conn.close()
                    return

                # 2. Создаем Клиента (Customers)
                # Email может быть пустым, если не введен
                email_val = email if email else None

                cur.execute("""
                            INSERT INTO Customers (FirstName, LastName, Phone, Email)
                                OUTPUT INSERTED.CustomerID
                            VALUES (?, ?, ?, ?)
                            """, (fname, lname, phone, email_val))

                new_customer_id = cur.fetchone()[0]

                # 3. Хешируем пароль
                hashed_pass = self.hash_password(raw_pass)

                # 4. Создаем Пользователя (Users) и привязываем к Клиенту
                cur.execute("""
                            INSERT INTO Users (Username, Password, Role, CustomerID)
                            VALUES (?, ?, 'Client', ?)
                            """, (login, hashed_pass, new_customer_id))

                conn.commit()
                conn.close()

                messagebox.showinfo("Сәтті", "Тіркелу сәтті өтті!\nЕнді жаңа логинмен кіріңіз.")
                reg_win.destroy()

            except Exception as e:
                messagebox.showerror("Қате", f"Тіркелу қатесі:\n{e}")

        ttk.Button(reg_win, text="Тіркелу", command=save_user).pack(pady=15)