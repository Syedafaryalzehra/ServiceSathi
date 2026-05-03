import pyodbc
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

def get_db_connection():
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DB_SERVER")};'
        f'DATABASE={os.getenv("DB_NAME")};'
        r'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

def seed_bulk():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. ADMIN DATA
    admin_data = ('Ibrahim Qaiser', 'ibri123@gmail.com', 'admin1**')
    
    # 2. USER DATA
    users = [
        ('ibrahim_q', 'Ibrahim Qaiser', 'ibrahim@email.com', 'password123', '03001234567', '3520112345678', '2003-09-03', 'Block L, Gulberg III'),
        ('fatima_lhr', 'Fatima Ali', 'fatima@email.com', 'fatima2026', '03214567890', '3520198765432', '1998-11-20', 'Phase 5, DHA'),
        ('ali_johar', 'Ali Hamza', 'ali.h@email.com', 'aliHamza99', '03005554433', '3520122334455', '1995-01-12', 'Block J, Johar Town'),
        ('zoya_model', 'Zoya Malik', 'zoya@email.com', 'zoyaMalik1', '03331112233', '3520166778899', '2000-04-05', 'Extension, Model Town'),
        ('usman_valencia', 'Usman Sheikh', 'usman@email.com', 'usmanSheikh', '03224445566', '3520100112233', '1992-08-30', 'Block C, Valencia'),
        ('sara_wapda', 'Sara Khan', 'sara@email.com', 'saraKhan22', '03017778899', '3520133445566', '1997-12-01', 'Phase 1, WAPDA Town'),
        ('bilal_iqbal', 'Bilal Ahmed', 'bilal@email.com', 'bilalAhmed', '03451239876', '3520155667788', '1994-06-18', 'Canal View, Iqbal Town'),
        ('ayesha_cantt', 'Ayesha Omer', 'ayesha@email.com', 'ayeshaOmer', '03210009988', '3520199001122', '2001-02-28', 'Falcon Complex, Cantt'),
        ('omer_garden', 'Omer Farooq', 'omer@email.com', 'omerFarooq', '03314455667', '3520177665544', '1996-09-14', 'Main Blvd, Garden Town'),
        ('nadia_bahria', 'Nadia Batool', 'nadia@email.com', 'nadia2025', '03028887766', '3520111223344', '1999-07-07', 'Sector C, Bahria Town')
    ]

    # 3. SELLER DATA
    sellers = [
        ('aslam_electric', 'Muhammad Aslam', 'aslam@serv.com', 'aslam1234', '03451112233', '3520211122233', '1985-06-15', 'Township', 'Expert electrician with 12 years exp.'),
        ('saima_cooks', 'Saima Bibi', 'saima@serv.com', 'saima5678', '03125556667', '3520244455566', '1990-02-10', 'Nishtar Colony', 'Home cooking specialist (Desi food).'),
        ('rashid_drive', 'Rashid Mehmood', 'rashid@serv.com', 'rashid9012', '03009998877', '3520277788899', '1982-11-05', 'Chungi Amar Sidhu', 'Licensed driver for luxury cars.'),
        ('tariq_plumber', 'Tariq Mehmood', 'tariq@serv.com', 'tariq3456', '03211234567', '3520233445566', '1988-04-20', 'Green Town', 'Expert in pipe leakage & water pumps.'),
        ('zara_clean', 'Zara Khan', 'zara@serv.com', 'zara7890', '03334445556', '3520266778899', '1993-09-12', 'Ferozepur Road', 'Deep cleaning & sofa washing specialist.'),
        ('kamran_ac', 'Kamran Ali', 'kamran@serv.com', 'kamran2345', '03001110011', '3520200112233', '1987-03-22', 'Cavalry Ground', 'AC installation and gas refilling pro.'),
        ('maryam_nanny', 'Maryam Batool', 'maryam@serv.com', 'maryam6789', '03227776655', '3520288990011', '1995-05-30', 'Garhi Shahu', 'Certified nanny with first aid training.'),
        ('hanif_cooks', 'Hanif Ahmed', 'hanif@serv.com', 'hanif0123', '03412233445', '3520233221100', '1980-08-15', 'Samnabad', 'Chef with catering experience.'),
        ('imran_driver', 'Imran Khan', 'imran@serv.com', 'imran4567', '03110099887', '3520255443322', '1991-01-10', 'Wassanpura', 'Available for inter-city travel.'),
        ('shafiq_plumb', 'Shafiq Dogar', 'shafiq@serv.com', 'shafiq8901', '03008887766', '3520299887766', '1984-12-01', 'Bund Road', 'Master plumber for sanitary fittings.')
    ]

    try:
        # Insert Admin
        cursor.execute("INSERT INTO Admins (name, email, password) VALUES (?, ?, ?)", 
                       (admin_data[0], admin_data[1], generate_password_hash(admin_data[2])))
        
        # Insert Users
        for u in users:
            cursor.execute("""INSERT INTO Users (username, name, email, password, phone, cnic, dob, address) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                           (u[0], u[1], u[2], generate_password_hash(u[3]), u[4], u[5], u[6], u[7]))
        
        # Insert Sellers
        for s in sellers:
            cursor.execute("""INSERT INTO Sellers (username, name, email, password, phone, cnic, dob, address, bio) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (s[0], s[1], s[2], generate_password_hash(s[3]), s[4], s[5], s[6], s[7], s[8]))

        conn.commit()
        print("Successfully seeded all Users, Sellers, and Admin!")
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_bulk()