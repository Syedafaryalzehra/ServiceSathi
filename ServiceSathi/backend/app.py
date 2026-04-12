from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc
import os                     
from dotenv import load_dotenv  
from datetime import date, datetime

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
    seller_name = request.args.get('seller_name', '').strip()
    max_price = request.args.get('max_price')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT name, description, average_rating, price_per_hour,
               experience_years, seller_id, profile_picture
        FROM View_Category_Providers
        WHERE category_id = ?
    """
    params = [cat_id]

    if seller_name:
        query += " AND name LIKE ?"
        params.append(f'%{seller_name}%')

    if max_price:
        query += " AND price_per_hour <= ?"
        params.append(float(max_price))

    cursor.execute(query, params)
    providers = cursor.fetchall()

    cursor.execute("SELECT category_name FROM Categories WHERE category_id = ?", (cat_id,))
    category = cursor.fetchone()
    conn.close()

    return render_template('category_view.html', 
                           providers=providers, 
                           category=category[0], 
                           cat_id=cat_id, 
                           seller_name=seller_name, 
                           max_price=max_price)

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    u_id = session['id']
    role = session['role']
    conn = get_db_connection()
    cursor = conn.cursor()

    table = "Sellers" if role == 'seller' else "Users"
    pk = "seller_id" if role == 'seller' else "user_id"
    cursor.execute(f"SELECT {pk}, name, cnic, phone, address, profile_picture FROM {table} WHERE {pk} = ?", (u_id,))
    profile = cursor.fetchone()

    if role == 'seller':
       cursor.execute("""
            SELECT seller_id, name, category_name, booking_date, 
                   start_time, end_time, status, instructions, booking_id,
                   job_address, total_payment
            FROM View_Seller_Bookings 
            WHERE seller_id = ? AND status != 'rejected'
        """, (u_id,))
       bookings = cursor.fetchall()
       cursor.execute("SELECT category_id, category_name FROM Categories")
       categories = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT user_id, name, category_name, booking_date, 
                   start_time, end_time, status, instructions, booking_id,
                   job_address, total_payment
            FROM View_User_Bookings WHERE user_id = ?
        """, (u_id,))
        bookings = cursor.fetchall()
        categories = []

    conn.close()
    return render_template('dashboard.html', profile=profile, bookings=bookings, role=role, categories=categories)


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
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    user_search = request.args.get('user_search', '')
    seller_search = request.args.get('seller_search', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username, name, email, phone FROM Users WHERE name LIKE ?", ('%' + user_search + '%',))
    users = cursor.fetchall()

    cursor.execute("SELECT seller_id, username, name, email, phone, bio FROM Sellers WHERE name LIKE ?", ('%' + seller_search + '%',))
    sellers = cursor.fetchall()

    conn.close()
    return render_template('admin.html', users=users, sellers=sellers, user_search=user_search, seller_search=seller_search)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC DeleteUserByAdmin ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_seller/<int:seller_id>', methods=['POST'])
def delete_seller(seller_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC DeleteSellerByAdmin ?", (seller_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# ---------------- ADMIN: ADD NEW CATEGORY ----------------
@app.route('/admin/add_category', methods=['POST'])
def add_category():
    if session.get('role') != 'admin': 
        return redirect(url_for('login'))

    category_name = request.form.get('category_name').strip()
    base_description = request.form.get('base_description', '').strip()

    if not category_name:
        flash("Error: Category name cannot be empty.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert the new category into the database
        cursor.execute("""
            INSERT INTO Categories (category_name, base_description) 
            VALUES (?, ?)
        """, (category_name, base_description))
        
        conn.commit()
        flash(f"Category '{category_name}' added successfully!", "success")
        
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        flash("Failed to add category. It might already exist.", "danger")
        conn.rollback()
        
    finally:
        conn.close()

    return redirect(url_for('admin_dashboard'))


# ---------------- BOOK SERVICE ----------------
@app.route('/book/<int:seller_id>', methods=['GET', 'POST'])
def book_service(seller_id):
    if not session.get('loggedin') or session.get('role') != 'user':
        flash("Please login as a user to book a service.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        service_id = request.form['service_id']
        booking_date = request.form['booking_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        job_address = request.form['address']
        instructions = request.form.get('instructions', '').strip()

        if not instructions:
            flash("Error: Instructions are mandatory.", "danger")
            return redirect(url_for('book_service', seller_id=seller_id))

        try:
            cursor.execute("""
                SET NOCOUNT ON;
                EXEC BookService @user_id=?, @service_id=?, @booking_date=?, @start_time=?, @end_time=?, @job_address=?, @instructions=?
            """, (int(session['id']), int(service_id), booking_date, start_time, end_time, job_address, instructions))
            
            conn.commit()
            flash("Booking request sent successfully!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"\n\n!!! DATABASE ERROR !!!\n{e}\n\n") 
            flash(f"Booking Failed: {str(e).split(']')[-1]}", "danger")
            conn.rollback()

    # GET Method logic
    cursor.execute("""
        SELECT s.name, sv.price_per_hour, sv.service_id, c.category_name 
        FROM Sellers s 
        JOIN Services sv ON s.seller_id = sv.seller_id 
        JOIN Categories c ON sv.category_id = c.category_id
        WHERE s.seller_id = ?""", (seller_id,))
    details = cursor.fetchone()
    conn.close()

    if not details:
        return "Service details not found", 404

    return render_template('book_form.html', details=details, today=date.today().isoformat())


@app.route('/accept_booking/<int:b_id>', methods=['POST'])
def accept_booking(b_id):
    if session.get('role') != 'seller': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC UpdateBookingStatus ?, 'accepted'", (b_id,))
    conn.commit()
    conn.close()
    flash("Booking Accepted!", "success")
    return redirect(url_for('dashboard'))

@app.route('/reject_booking/<int:b_id>', methods=['POST'])
def reject_booking(b_id):
    if session.get('role') != 'seller': return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC UpdateBookingStatus ?, 'rejected'", (b_id,))
    conn.commit()
    conn.close()
    flash("Booking Rejected", "danger")
    return redirect(url_for('dashboard'))

# ---------------- CANCEL BOOKING (USER) ----------------
@app.route('/cancel_booking/<int:b_id>', methods=['POST'])
def cancel_booking(b_id):
    if session.get('role') != 'user': 
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        local_time_now = datetime.now()
        
        cursor.execute("""
            SET NOCOUNT ON;
            EXEC CancelUserBooking ?, ?, ?
        """, (b_id, session['id'], local_time_now))
        
        conn.commit()
        flash("Booking successfully cancelled.", "success")
        
    except Exception as e:
        flash(f"Cancellation Failed: {str(e).split(']')[-1]}", "danger")
        conn.rollback()
        
    conn.close()
    return redirect(url_for('dashboard'))

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
