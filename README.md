# Service Sathi - Project 

## Description
Service Sathi is a web-based platform connecting local service providers (Sellers) like electricians, plumbers, and cleaners with customers (Users) across lahore. This iteration covers user registration, login, and the service discovery dashboard.

## Team Members
* [Syeda Faryal Zehra] - [24l-2556]
* [Syeda Ume Abeeha Naqvi] - [24l-2528]
* [ Ibrahim Qaiser ] - [24l-2513]

## Tech Stack
* **Frontend:** HTML, CSS
* **Backend:** Python (Flask)
* **Database:** SQL Server (MS SQL)
* **Connection:** pyodbc with .env configuration

## Project Structure
- backend/: Flask application logic (app.py)
- frontend/: Templates and static assets (CSS)
-  database/: (schema.sql), (seed.sql),(procedures.sql),(views.sql) and (erd.png)
- docs/: Project reports and iteration documents

## How to Run
1. **Database Setup:** - Open SQL Server Management Studio.
   - Run the scripts in (database) to create tables,procedures and views in order
   - 1 schema.sql
   - 2 views.sql
   - 3 procedures.sql
   - Run (database/seed.sql) to populate sample data.
2. **Environment Setup:**
   - Install requirements: `pip install flask pyodbc python-dotenv`
   - Create a (.env) file based on `.env.example` and add your local (DB_SERVER) name.
3. **Run App:**
   - Navigate to the backend folder: (cd backend)
   - Run the command: (python app.py)
   - Open (http://127.0.0.1:5000) in your browser.
