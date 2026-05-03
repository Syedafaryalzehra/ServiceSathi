import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def read_procedure(proc_name):
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        r'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT OBJECT_DEFINITION(OBJECT_ID('{proc_name}'))")
    definition = cursor.fetchone()[0]
    
    if definition:
        print(f"--- Definition of {proc_name} ---")
        print(definition)
    else:
        print(f"Procedure {proc_name} not found.")
    
    conn.close()

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "RegisterUser"
    read_procedure(name)