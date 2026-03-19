from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc
import os                     
from dotenv import load_dotenv  


load_dotenv()

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_for_dev") 

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    try:
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
          f'SERVER={os.getenv("DB_SERVER")};' 
            f'DATABASE={os.getenv("DB_NAME")};' 
            r'Trusted_Connection=yes;'
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error: {e}")
        return None

# ---------------- HOME ----------------
@app.route('/')
def home():
    search_query = request.args.get('search')

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute("""
            SELECT category_name, base_description, category_id
            FROM Categories
            WHERE category_name LIKE ?
        """, ('%' + search_query + '%',))
    else:
        cursor.execute("""
            SELECT category_name, base_description, category_id
            FROM Categories
        """)

    categories = cursor.fetchall()
    conn.close()

    return render_template('index.html', categories=categories, search_query=search_query)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form['username']
        name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        cnic = request.form['cnic']
        dob = request.form['dob']
        address = request.form['address']
        bio = request.form.get('bio', '').strip()

        if role == 'seller' and not bio:
            return render_template('register.html', error="Seller must provide bio")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("EXEC RegisterUser ?,?,?,?,?,?,?,?,?,?",
                (role, username, name, email, password, phone, cnic, dob, address, bio))
            conn.commit()
            conn.close()
            flash("Registered successfully! Please login.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            return render_template('register.html', error=str(e))

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        identifier = request.form['identifier']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("EXEC LoginUser ?, ?", (role, identifier))
        account = cursor.fetchone()
        conn.close()

        if account and account.password == password:
            session['loggedin'] = True
            session['id'] = account[0]
            session['name'] = account[1]
            session['role'] = role

            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))

        return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ---------------- CATEGORY VIEW ----------------
@app.route('/category/<int:cat_id>')
def view_category(cat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, description, average_rating, price_per_hour,
               experience_years, seller_id, profile_picture
        FROM View_Category_Providers
        WHERE category_id = ?
    """, (cat_id,))
    providers = cursor.fetchall()

    cursor.execute("SELECT category_name FROM Categories WHERE category_id = ?", (cat_id,))
    category = cursor.fetchone()

    conn.close()

    return render_template('category_view.html', providers=providers, category=category[0])

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    u_id = session['id']
    role = session['role']

    conn = get_db_connection()
    cursor = conn.cursor()

    # PROFILE
    if role == 'seller':
        cursor.execute("SELECT seller_id, name, cnic, phone, address, profile_picture FROM Sellers WHERE seller_id = ?", (u_id,))
    else:
        cursor.execute("SELECT user_id, name, cnic, phone, address, profile_picture FROM Users WHERE user_id = ?", (u_id,))
    profile = cursor.fetchone()

    # BOOKINGS
    if role == 'user':
        cursor.execute("""
            SELECT seller_name, category_name, booking_date,
                   start_time, end_time, status
            FROM View_User_Bookings
            WHERE user_id = ?
        """, (u_id,))
    else:
        cursor.execute("""
            SELECT user_name, category_name, booking_date,
                   start_time, end_time, status
            FROM View_Seller_Bookings
            WHERE seller_id = ?
        """, (u_id,))

    bookings = cursor.fetchall()

    # SELLER CATEGORIES
    categories = []
    if role == 'seller':
        cursor.execute("SELECT category_id, category_name FROM Categories")
        categories = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           profile=profile,
                           bookings=bookings,
                           role=role,
                           categories=categories)

# ---------------- ADD SERVICE ----------------
@app.route('/add_service', methods=['POST'])
def add_service():
    if session.get('role') != 'seller':
        return redirect(url_for('login'))

    seller_id = session['id']
    category_id = request.form.get('category_id')
    price = request.form.get('price')
    experience = request.form.get('experience')
    description = request.form.get('description')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("EXEC AddService ?,?,?,?,?",
            (seller_id, category_id, price, experience, description))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    except Exception as e:
        return f"Error: {str(e)}"

# ---------------- ADMIN ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username, name, email, phone FROM Users")
    users = cursor.fetchall()

    cursor.execute("SELECT seller_id, username, name, email, phone, bio FROM Sellers")
    sellers = cursor.fetchall()

    conn.close()

    return render_template('admin.html', users=users, sellers=sellers)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)