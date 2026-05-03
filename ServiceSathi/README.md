# Service Sathi 

## Description
Service Sathi is a web-based platform connecting local service providers (Sellers) like electricians, plumbers, and cleaners with customers (Users) across Lahore. Features include user registration, login, service discovery dashboard, seller profiles, AI chatbot support, admin panel, responsive design, and Cloudinary image management.

## Team Members
* [Ibrahim Qaiser] - [24l-2513]
* [Syeda Faryal Zehra] - [24l-2556]
* [Syeda Ume Abeeha Naqvi] - [24l-2528]


## Tech Stack
* **Frontend:** HTML, CSS, JavaScript (Flask Templates) - Responsive Design
* **Backend:** Python (Flask 3.1.3)
* **Database:** SQL Server (MS SQL) with pyODBC
* **Image Management:** Cloudinary
* **AI Chatbot:** Google Generative AI (Gemini)
* **Styling:** Custom CSS with Flexbox, Glass Morphism Effects
* **3D Graphics:** Three.js for hero section canvas

## Features
- ✅ User Registration & Login (Customer & Seller roles)
- ✅ Service Discovery & Search
- ✅ Seller Dashboard & Profile Management
- ✅ Admin Panel for system management
- ✅ AI Chatbot (SaathiBot) powered by Google Gemini
- ✅ Cloudinary Image Upload & Management
- ✅ Responsive Design (Mobile, Tablet, Desktop)
- ✅ Cross-browser Compatible (Chrome, Firefox, Edge, Safari)

## Project Structure
```
ServiceSathi/
├── backend/
│   ├── app.py                 # Main Flask application & routes
│   ├── saathi_bot.py          # AI Chatbot logic (Gemini API)
│   ├── requirements.txt        # Python dependencies
│   ├── bulk_seed.py           # Database seeding script
│   ├── check_categories.py    # Utility: Check Categories table schema
│   ├── check_shema.py         # Utility: Check database schema
│   ├── find_rating.py         # Utility: Calculate seller ratings
│   ├── read_proc.py           # Utility: Read stored procedure definitions
│   └── reset_password.py      # Utility: Reset user password (admin tool)
├── frontend/
│   ├── templates/             # HTML templates
│   │   ├── base.html          # Base layout template
│   │   ├── index.html         # Home page
│   │   ├── login.html         # Login page
│   │   ├── register.html      # Registration page
│   │   ├── dashboard.html     # User dashboard
│   │   ├── admin.html         # Admin panel
│   │   └── chat.html          # Chatbot interface
│   └── static/                # CSS and images
│       ├── style.css          # Main stylesheet
│       └── images/            # Logo, icons
├── database/
│   ├── schema.sql             # Database tables
│   ├── views.sql              # Database views
│   ├── procedures.sql         # Stored procedures
│   └── seed.sql               # Sample data
├── Docs/                      # Project reports & documentation
└── README.md                  # This file
```

## Prerequisites
- **Python 3.8+** (Windows/Linux/Mac)
- **SQL Server 2016+** (Windows or Linux)
- **ODBC Driver 17 for SQL Server** installed
- **pip** (Python package manager)

## Installation & Setup
### 1. Clone or Extract Project
cd ServiceSathi
### 2. Install Python Dependencies
cd backend
pip install -r requirements.txt
### 3. Set Up Environment Variables
Create a `.env` file in the `backend/` with the help of .env.example file

### 4. Database Setup
1. Open **SQL Server Management Studio** (SSMS)
2. Run the database scripts **in this order:**
   ```
   1. database/schema.sql        (creates tables)
   2. database/views.sql         (creates views)
   3. database/procedures.sql    (creates stored procedures)
   ```
3. and run the Python seed script:
   cd backend
   python bulk_seed.py

### 5. Run the Application
```bash
cd backend
python app.py
```
The app will start at: **http://127.0.0.1:5000**


## Platform Support
### Operating Systems
- ✅ Windows 10/11
- ✅ Linux (Ubuntu 18.04+, Debian, CentOS)
- ✅ macOS (Intel/Apple Silicon)
### Browsers
- ✅ Google Chrome (v90+)
- ✅ Mozilla Firefox (v88+)
- ✅ Microsoft Edge (v90+)
- ✅ Safari (v14+)
### Devices
- ✅ Desktop Computers
- ✅ Tablets (iPad, Android)
- ✅ Mobile Phones (iOS, Android)





