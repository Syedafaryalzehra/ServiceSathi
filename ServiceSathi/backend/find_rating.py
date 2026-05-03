import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

def find_rating(seller_id):
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        r'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    cursor.execute("SELECT AVG(CAST(rating AS FLOAT)) FROM Reviews r JOIN Bookings b ON r.booking_id = b.booking_id JOIN Services s ON b.service_id = s.service_id WHERE s.seller_id = ?", (seller_id,))
    rating = cursor.fetchone()[0]
    print(f"Seller {seller_id} Rating: {rating if rating else 'No ratings yet'}")
    
    conn.close()

if __name__ == "__main__":
    # Example
    find_rating(1)