from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc
import os                     
from dotenv import load_dotenv  
from datetime import date, datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
import re
from flask import jsonify
import cloudinary
import cloudinary.uploader


load_dotenv()

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_for_dev") 

cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET") 
)

def get_db_connection():
    try:
        print(f"Connecting to: {os.getenv('DB_SERVER')} | DB: {os.getenv('DB_NAME')}")
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
            hashed_pw = generate_password_hash(password)
            cursor.execute("{CALL RegisterUser(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}", 
                           (role, username, name, email, hashed_pw, phone, cnic, dob, address, bio))
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

        if account and check_password_hash(account[2], password):
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
                   job_address, total_payment, is_paid
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
                   job_address, total_payment, is_paid
            FROM View_User_Bookings WHERE user_id = ?
        """, (u_id,))
        bookings = cursor.fetchall()
        categories = []

    reviewed_ids = set()
    if role == 'user':
        cursor.execute("""
            SELECT r.booking_id FROM Reviews r
            JOIN Bookings b ON r.booking_id = b.booking_id
            WHERE b.user_id = ?
        """, (u_id,))
        reviewed_ids = {row[0] for row in cursor.fetchall()}

    from datetime import timedelta
    processed_bookings = []
    now = datetime.now()

    for b in bookings:
        b_list = list(b)
        try:
            start_t = b[4]
            if isinstance(start_t, str):
                start_t = datetime.strptime(start_t, "%H:%M").time()
            elif isinstance(start_t, datetime):
                start_t = start_t.time()

            end_t = b[5]
            if isinstance(end_t, str):
                end_t = datetime.strptime(end_t, "%H:%M").time()
            elif isinstance(end_t, datetime):
                end_t = end_t.time()

            b_dt = datetime.combine(b[3], start_t)
            b_end_dt = datetime.combine(b[3], end_t)

            status = b[6].lower()
            can_cancel = (status == 'pending') and (now < b_dt - timedelta(minutes=30))
            can_delete = (status in ['rejected', 'cancelled']) or (status == 'pending' and now > b_dt)
            can_complete = (role == 'user') and (status == 'accepted') and (now >= b_end_dt)
            is_paid_flag = bool(b_list[11])
            can_update_payment = (role == 'seller') and (status == 'completed') and (not is_paid_flag)
            has_reviewed = (role == 'user') and (b[8] in reviewed_ids)

        except Exception as e:
            print(f"DEBUG: Time processing error for booking {b[8]}: {e}")
            can_cancel = False
            can_delete = False
            can_complete = False
            can_update_payment = False
            has_reviewed = False

        b_list.append(can_cancel)         # Index 12
        b_list.append(can_delete)         # Index 13
        b_list.append(can_complete)       # Index 14
        b_list.append(can_update_payment) # Index 15
        b_list.append(has_reviewed)       # Index 16
        processed_bookings.append(b_list)

    conn.close()
    return render_template('dashboard.html', profile=profile, bookings=processed_bookings, role=role, categories=categories)
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

    cursor.execute("SELECT category_id, category_name, base_description FROM Categories")
    categories = cursor.fetchall()

    conn.close()
    return render_template('admin.html', users=users, sellers=sellers, categories=categories, user_search=user_search, seller_search=seller_search)

@app.route('/admin/delete_category/<int:cat_id>', methods=['POST'])
def delete_category(cat_id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM Reviews WHERE booking_id IN (
                SELECT b.booking_id FROM Bookings b
                JOIN Services s ON b.service_id = s.service_id
                WHERE s.category_id = ?
            )
        """, (cat_id,))
        
        cursor.execute("""
            DELETE FROM Bookings WHERE service_id IN (
                SELECT service_id FROM Services WHERE category_id = ?
            )
        """, (cat_id,))
        
        cursor.execute("DELETE FROM Services WHERE category_id = ?", (cat_id,))
        
        cursor.execute("DELETE FROM Categories WHERE category_id = ?", (cat_id,))
        
        conn.commit()
        flash("Category and its associated services removed successfully. Seller accounts remain active.", "success")
    except Exception as e:
        conn.rollback()
        print(f"ADMIN DELETE CATEGORY ERROR: {e}")
        flash(f"System Error: {str(e)}", "danger")
    finally:
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

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
    if session.get('role') != 'seller':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("EXEC UpdateBookingStatus ?, 'accepted'", (b_id,))
    conn.commit()
    conn.close()
    
    flash("Booking Accepted!", "success")
    return redirect(url_for('dashboard'))

# cancel booking seller
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
        flash("Too Late Cannot cancel a booking less than 30 minutes before the start time.", "danger")
        conn.rollback()
        
    conn.close()
    return redirect(url_for('dashboard'))

# ---------------- HELPER: CATEGORY TO PROVIDER NOUN ----------------
def get_provider_noun(category_name):
    cat = category_name.lower().strip()
    
    mapping = {
        'baking': 'baker',
        'plumbing': 'plumber',
        'cleaning': 'cleaner',
        'babysitting': 'babysitter',
        'cooking': 'cook',
        'driving': 'driver',
        'electrical': 'electrician',
        'painting': 'painter',
        'carpentry': 'carpenter',
        'security': 'security guard',
        'laundry': 'laundry assistant'
    }
    
    if cat in mapping:
        provider = mapping[cat]
    elif cat.endswith('ing'):
        provider = cat[:-3] + 'er'
    elif cat.endswith('ry'):
        provider = cat[:-2] + 'er'
    else:
        provider = cat
        
    article = "an" if provider[0].lower() in 'aeiou' else "a"
    return f"{article} {provider}"

# ---------------- SAATHI BOT CHAT ----------------


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    language = request.args.get('lang', 'en')
    user_message = None
    bot_response = None
    error = None
    bot_providers = []

    if request.method == 'POST':
        if 'clear' in request.form:
            session.pop('chat_history', None)
            return redirect(url_for('chat'))

        user_message = request.form.get('message', '').strip()
        
        if not os.getenv("GROQ_API_KEY"):
            error = "Groq API Key is missing. Please configure it in .env file."
        elif user_message:
            if 'chat_history' not in session:
                session['chat_history'] = []
                
            session['chat_history'].append({'role': 'user', 'content': user_message})
            session.modified = True
            
            try:
                from saathi_bot import search_services_by_category
                
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.category_name, v.name, v.price_per_hour, v.average_rating, v.seller_id, v.profile_picture, v.description, v.experience_years
                    FROM View_Category_Providers v
                    JOIN Categories c ON v.category_id = c.category_id
                """)
                all_providers = cursor.fetchall()
                conn.close()
                
                db_context = "Available services in the database right now:\n"
                for i, p in enumerate(all_providers):
                    db_context += f"- [KEY: {i}] Category: {p.category_name}, Provider: {p.name}, Price: Rs. {p.price_per_hour}, Rating: {p.average_rating}, Desc: {p.description}\n"
                
                system_instruction = f"""You are Saathi Bot, the official AI assistant for ServiceSathi.
                Do NOT use ANY markdown formatting whatsoever in your responses. 
                DATABASE CONTEXT:
                {db_context}
                """
                
                groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                completion = groq_client.chat.completions.create(
                   model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.3
                )
                bot_response = completion.choices[0].message.content
                print(f"✓ Groq AI Response: {bot_response[:80]}...")
                
                match = re.search(r'\[KEYS:\s*(.*?)\]', bot_response)
                if match:
                    ids_str = match.group(1)
                    bot_response = re.sub(r'\[KEYS:\s*(.*?)\]', '', bot_response).strip()
                    keys = [int(i.strip()) for i in ids_str.split(',') if i.strip().isdigit()]
                    for k in keys:
                        if 0 <= k < len(all_providers):
                            p = all_providers[k]
                            bot_providers.append((p.name, p.description, float(p.average_rating) if p.average_rating else 0.0, float(p.price_per_hour), p.experience_years, p.seller_id, p.profile_picture))

            except Exception as e:
                print(f"❌ Groq API Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print(f"Falling back to local NLP.")
                msg_lower = user_message.lower()
                matched_ids = []
              
                
                price_match = re.search(r'(under|below|less than|max|within)\s*(\d+)', msg_lower)
                max_price = float(price_match.group(2)) if price_match else float('inf')
                
                if msg_lower in ['hello', 'hi', 'hey', 'hii', 'hiii', 'whats up']:
                    bot_response = "Hello! I am Saathi Bot. How can I help you find services today?"
                elif 'how' in msg_lower and any(w in msg_lower for w in ['use', 'book', 'find']):
                    bot_response = "To use ServiceSathi, browse categories or search for specific services!"
                elif any(w in msg_lower for w in ['sell', 'add', 'provide', 'become', 'register']):
                    bot_response = "To sell services, go to your dashboard and select 'Add Service'!"
                else:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT c.category_name, v.name, v.price_per_hour, v.average_rating, v.seller_id, v.profile_picture, v.description, v.experience_years FROM View_Category_Providers v JOIN Categories c ON v.category_id = c.category_id")
                    all_providers_fallback = cursor.fetchall()
                    conn.close()

                    for i, p in enumerate(all_providers_fallback):
                        p_cat = p[0].lower()
                        p_price = float(p[2])
                        if p_cat in msg_lower or p_cat.replace('ing', 'er') in msg_lower or p_cat.replace('ing', '') in msg_lower:
                            if p_price <= max_price:
                                matched_ids.append(i)
                    
                    if not matched_ids:
                        for i, p in enumerate(all_providers_fallback):
                            if any(len(w)>3 and w in p[6].lower() for w in msg_lower.split()):
                                if float(p[2]) <= max_price:
                                    matched_ids.append(i)
                    
                    matched_ids = list(set(matched_ids))
                    words = [w for w in msg_lower.replace('?','').split() if len(w) > 3 and w not in ['need', 'want', 'looking', 'there', 'find']]
                    inferred_topic = words[-1] if words else "service"
                    
                    if matched_ids:
                        bot_response = f"I found some options for '{inferred_topic}': [KEYS: {','.join(str(k) for k in matched_ids)}]"
                    else:
                        bot_response = f"I couldn't find providers for '{inferred_topic}'. Try another category!"

                    match = re.search(r'\[KEYS:\s*(.*?)\]', bot_response)
                    if match:
                        ids_str = match.group(1)
                        bot_response = re.sub(r'\[KEYS:\s*(.*?)\]', '', bot_response).strip()
                        keys = [int(i.strip()) for i in ids_str.split(',') if i.strip().isdigit()]
                        for k in keys:
                            if 0 <= k < len(all_providers_fallback):
                                p = all_providers_fallback[k]
                                bot_providers.append((p[1], p[6], float(p[3]) if p[3] else 0.0, float(p[2]), p[7], p[4], p[5]))
                
            session['chat_history'].append({'role': 'bot', 'content': bot_response})
            session.modified = True
                
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM Categories")
    categories_raw = [row[0] for row in cursor.fetchall()]
    conn.close()

    categories = []
    for cat in categories_raw:
        provider = get_provider_noun(cat)
        categories.append({
            'original': cat,
            'provider': provider
        })
                
    return render_template('chat.html', language=language, error=error, providers=bot_providers, categories=categories)


# ---------------- EDIT PROFILE ----------------
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    u_id = session['id']
    role = session['role']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form.get('password', '').strip()
        bio = request.form.get('bio', '').strip()

        image_url = None
        if 'profile_image' in request.files:
            file_to_upload = request.files['profile_image']
            if file_to_upload.filename != '':
                # This sends the file to Cloudinary
                upload_result = cloudinary.uploader.upload(file_to_upload)
                image_url = upload_result.get('secure_url')

        table = "Sellers" if role == 'seller' else "Users"
        pk = "seller_id" if role == 'seller' else "user_id"

        try:
            print(f"DEBUG: Updating profile for {role} {u_id}")
            
            cursor.execute(f"UPDATE {table} SET name=?, email=?, phone=?, address=? WHERE {pk}=?", 
                           (name, email, phone, address, u_id))
            
           
            if image_url:
                cursor.execute(f"UPDATE {table} SET profile_picture=? WHERE {pk}=?", (image_url, u_id))
            
            session['name'] = name
            
            if password:
                hashed_new_pw = generate_password_hash(password)
                cursor.execute(f"UPDATE {table} SET password=? WHERE {pk}=?", (hashed_new_pw, u_id))
            
            if role == 'seller':
                cursor.execute(f"UPDATE Sellers SET bio=? WHERE seller_id=?", (bio, u_id))

            conn.commit()
            print("DEBUG: Profile update committed successfully")
            session.modified = True
            flash("Profile updated successfully!", "success")
            return redirect(url_for('dashboard'))

        except Exception as e:
            conn.rollback()
        
            return render_template('edit_profile.html', profile=request.form, error=str(e))
        finally:
            conn.close()

    table = "Sellers" if role == 'seller' else "Users"
    pk = "seller_id" if role == 'seller' else "user_id"
    cursor.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (u_id,))
    row = cursor.fetchone()
    
    columns = [column[0] for column in cursor.description]
    profile_dict = dict(zip(columns, row))
    
    conn.close()
    return render_template('edit_profile.html', profile=profile_dict)

# ---------------- REVIEWS ----------------
@app.route('/add_review', methods=['POST'])
def add_review():
    if 'loggedin' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
        
    booking_id = request.form.get('booking_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment', '')
    
    if not booking_id or not rating:
        flash("Rating is required to submit a review.", "danger")
        return redirect(url_for('dashboard'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT status, is_paid FROM Bookings WHERE booking_id = ? AND user_id = ?", (booking_id, session['id']))
        booking = cursor.fetchone()
        
        if not booking:
            flash("Invalid booking.", "danger")
            return redirect(url_for('dashboard'))

        if booking[0].lower() != 'completed':
            flash("You can only review a completed service.", "warning")
            return redirect(url_for('dashboard'))

        if not booking[1]:
            flash("Review is only available after the seller confirms payment.", "warning")
            return redirect(url_for('dashboard'))
            
        cursor.execute("SELECT review_id FROM Reviews WHERE booking_id = ?", (booking_id,))
        if cursor.fetchone():
            flash("You have already reviewed this booking.", "warning")
            return redirect(url_for('dashboard'))
            
        cursor.execute("""
            INSERT INTO Reviews (booking_id, rating, comment, review_date)
            VALUES (?, ?, ?, GETDATE())
        """, (booking_id, rating, comment))

        cursor.execute("""
            INSERT INTO Notifications (seller_id, message, type, created_at)
            SELECT s.seller_id, ?, 'review', GETDATE()
            FROM Bookings b
            JOIN Services s ON b.service_id = s.service_id
            WHERE b.booking_id = ?
        """, (f"New {rating}-star review from {session['name']}!", booking_id))
        
        conn.commit()
        conn.close()
        flash("Thank you! Your review has been submitted.", "success")
    except Exception as e:
        flash(f"Error submitting review: {str(e)}", "danger")
        
    return redirect(url_for('dashboard'))


# ---------------- API: NOTIFICATIONS ----------------

@app.route('/api/notifications')
def get_notifications():
    if not session.get('loggedin'):
        return jsonify([])
        
    conn = get_db_connection()
    cursor = conn.cursor()
    notifications = []
    
    try:
        u_id = session['id']
        role = session['role']
        
        
        if role == 'seller':
            cursor.execute("SELECT notification_id, message, type FROM Notifications WHERE seller_id = ? AND is_read = 0 ORDER BY created_at DESC", (u_id,))
        else:
            cursor.execute("SELECT notification_id, message, type FROM Notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC", (u_id,))
            
        for row in cursor.fetchall():
            title = "New Review!" if row[2] == 'review' else "System Alert"
            if row[2] == 'booking': title = "Booking Update"
            
            notifications.append({
                'id': f"db_{row[0]}",
                'title': title,
                'message': row[1]
            })

        if role == 'seller':
            cursor.execute("""
                SELECT b.booking_id, u.name 
                FROM Bookings b 
                JOIN Services s ON b.service_id = s.service_id 
                JOIN Users u ON b.user_id = u.user_id
                WHERE s.seller_id = ? AND b.status = 'pending'
            """, (u_id,))
            
            for row in cursor.fetchall():
                notifications.append({
                    'id': f"booking_{row[0]}",
                    'title': 'New Booking Request!',
                    'message': f"{row[1]} wants to book your service."
                })
                
        elif session.get('role') == 'user':
            
            cursor.execute("""
                SELECT b.booking_id, b.status, s.name 
                FROM Bookings b 
                JOIN Services sv ON b.service_id = sv.service_id 
                JOIN Sellers s ON sv.seller_id = s.seller_id 
                WHERE b.user_id = ? AND b.status IN ('accepted', 'rejected')
                ORDER BY b.booking_id DESC
            """, (session['id'],))
            
            for row in cursor.fetchall():
                status_capitalized = row[1].capitalize()
                notifications.append({
                    'id': f"user_{row[0]}_{row[1]}",
                    'title': f"Booking {status_capitalized}",
                    'message': f"{row[2]} has {row[1]} your booking request!"
                })
    except Exception as e:
        print(f"Notification Error: {e}")
    finally:
        conn.close()
        
    return jsonify(notifications)
    
@app.route('/api/reviews/<int:seller_id>')
def get_reviews(seller_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.rating, r.comment, FORMAT(r.review_date, 'MMM dd, yyyy') as date, u.name 
        FROM Reviews r
        JOIN Bookings b ON r.booking_id = b.booking_id
        JOIN Services s ON b.service_id = s.service_id
        JOIN Users u ON b.user_id = u.user_id
        WHERE s.seller_id = ?
        ORDER BY r.review_date DESC
    """, (seller_id,))
    
    reviews = []
    for row in cursor.fetchall():
        reviews.append({
            'rating': row[0],
            'comment': row[1],
            'date': row[2],
            'user': row[3]
        })
    conn.close()
    return jsonify(reviews)


# ---------------- BULK DELETE BOOKINGS ----------------
@app.route('/delete_bookings', methods=['POST'])
def delete_bookings():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
        
    booking_ids = request.form.getlist('booking_ids')
    if not booking_ids:
        flash("No bookings selected to delete.", "warning")
        return redirect(url_for('dashboard'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify ownership
        valid_ids = []
        for bid in booking_ids:
            if session['role'] == 'seller':
                cursor.execute("""
                    SELECT b.booking_id FROM Bookings b
                    JOIN Services s ON b.service_id = s.service_id
                    WHERE b.booking_id = ? AND s.seller_id = ?
                """, (bid, session['id']))
            else:
                cursor.execute("SELECT booking_id FROM Bookings WHERE booking_id = ? AND user_id = ?", (bid, session['id']))
            
            if cursor.fetchone():
                valid_ids.append(bid)
                
        if not valid_ids:
            flash("You do not have permission to delete these bookings.", "danger")
            return redirect(url_for('dashboard'))
            
        placeholders = ','.join('?' for _ in valid_ids)
        
        cursor.execute(f"DELETE FROM Reviews WHERE booking_id IN ({placeholders})", valid_ids)
        
        cursor.execute(f"DELETE FROM Bookings WHERE booking_id IN ({placeholders})", valid_ids)
        conn.commit()
        
        flash(f"Successfully deleted {len(valid_ids)} booking(s).", "success")
    except Exception as e:
        print(f"Delete Error: {e}")
        flash("An error occurred while deleting bookings.", "danger")
    finally:
        conn.close()
        
    return redirect(url_for('dashboard'))


# ---------------- COMPLETE SERVICE (USER) ----------------
@app.route('/complete_booking/<int:b_id>', methods=['POST'])
def complete_booking(b_id):
    if session.get('role') != 'user':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT b.booking_id, b.user_id, s.seller_id
            FROM Bookings b
            JOIN Services s ON b.service_id = s.service_id
            WHERE b.booking_id = ? AND b.user_id = ? AND b.status = 'accepted'
        """, (b_id, session['id']))
        booking = cursor.fetchone()
        if not booking:
            flash("Invalid booking or not eligible to mark as complete.", "danger")
            return redirect(url_for('dashboard'))
        cursor.execute("UPDATE Bookings SET status = 'completed' WHERE booking_id = ?", (b_id,))
        cursor.execute("""
            INSERT INTO Notifications (seller_id, message, type, created_at)
            VALUES (?, ?, 'booking', GETDATE())
        """, (booking[2], f"{session['name']} has marked the service as completed. Please update the payment status."))
        conn.commit()
        flash("Service marked as completed! The seller will now update the payment.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))


# ---------------- UPDATE PAYMENT STATUS (SELLER) ----------------
@app.route('/update_payment/<int:b_id>', methods=['POST'])
def update_payment(b_id):
    if session.get('role') != 'seller':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT b.booking_id, b.user_id
            FROM Bookings b
            JOIN Services s ON b.service_id = s.service_id
            WHERE b.booking_id = ? AND s.seller_id = ? AND b.status = 'completed' AND b.is_paid = 0
        """, (b_id, session['id']))
        booking = cursor.fetchone()
        if not booking:
            flash("Invalid booking or payment already updated.", "danger")
            return redirect(url_for('dashboard'))
        cursor.execute("UPDATE Bookings SET is_paid = 1 WHERE booking_id = ?", (b_id,))
        cursor.execute("""
            INSERT INTO Notifications (user_id, message, type, created_at)
            VALUES (?, ?, 'booking', GETDATE())
        """, (booking[1], "Payment confirmed by the seller! You can now leave a review."))
        conn.commit()
        flash("Payment status updated! The user can now leave a review.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for('dashboard'))
    
# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
