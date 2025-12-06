import pyodbc
from tkinter import messagebox

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ---
CONN_STR = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=ALESSANDRO\SQLEXPRESS01;'  
    r'DATABASE=BookStoreDB;'
    r'Trusted_Connection=yes;'
)

def get_db_connection():
    try:
        conn = pyodbc.connect(CONN_STR)
        return conn
    except Exception as e:
        messagebox.showerror("Дерекқор қатесі", f"Серверге қосылу мүмкін болмады:\n{e}")
        return None