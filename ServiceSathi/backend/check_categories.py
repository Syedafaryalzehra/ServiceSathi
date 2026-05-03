import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def check_categories_schema():
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        r'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    print("--- Schema of Categories ---")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Categories'")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_categories_schema()