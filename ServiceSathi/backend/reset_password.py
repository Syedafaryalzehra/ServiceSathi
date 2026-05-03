import sys
from werkzeug.security import generate_password_hash
import pyodbc
import os
from dotenv import load_dotenv

def reset():
    if len(sys.argv) < 4:
        print("Usage: python reset_password.py <user|seller|admin> <username_or_email> <new_password>")
        return

    role = sys.argv[1].lower()
    identifier = sys.argv[2]
    new_pass = sys.argv[3]
    
    load_dotenv()
    
    # Connection string
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        r'Trusted_Connection=yes;'
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        hashed = generate_password_hash(new_pass)
        
        if role == 'user':
            cursor.execute("UPDATE Users SET password = ? WHERE username = ?", (hashed, identifier))
        elif role == 'seller':
            cursor.execute("UPDATE Sellers SET password = ? WHERE username = ?", (hashed, identifier))
        elif role == 'admin':
            cursor.execute("UPDATE Admins SET password = ? WHERE email = ?", (hashed, identifier))
        else:
            print("Error: Role must be 'user', 'seller', or 'admin'.")
            return
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"Success: Password for {identifier} ({role}) has been reset.")
        else:
            print(f"Error: Could not find {role} with identifier '{identifier}'.")
        
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    reset()