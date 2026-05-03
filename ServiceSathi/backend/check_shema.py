import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def check_schema(table_name):
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        r'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    columns = cursor.fetchall()
    
    print(f"--- Schema of {table_name} ---")
    for col in columns:
        print(f"{col[0]}: {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_schema("Sellers")
    check_schema("Users")