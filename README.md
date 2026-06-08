# 📚 E-Library Management System
### Python Flask · MySQL · Modern UI

A complete, production-ready E-Library Management System converted from PHP to Python/Flask — with glassmorphism UI, dark mode, admin analytics, role-based access, and full CRUD.

---

## ✅ STEP 5 — Complete Folder Structure

```
elibrary/
│
├── app.py                      ← Flask app factory — START HERE
├── requirements.txt            ← Python dependencies
├── .env.example                ← Copy to .env and fill in your DB details
│
├── config/
│   ├── __init__.py
│   └── config.py               ← DB URI, SECRET_KEY, Flask settings
│
├── models/
│   ├── __init__.py
│   └── models.py               ← All SQLAlchemy models (10 tables)
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                 ← Register, Login, Logout, Forgot Password
│   ├── main.py                 ← Home, Dashboard, Search, Issue, Return, Review
│   └── admin.py                ← Admin Dashboard, Book CRUD, Users, Fines
│
├── templates/
│   ├── base.html               ← Master layout (sidebar, topbar, dark mode)
│   ├── home.html               ← Landing page
│   ├── login.html              ← Login form
│   ├── register.html           ← Registration form
│   ├── forgot_password.html    ← Password reset + CAPTCHA
│   ├── dashboard.html          ← User dashboard
│   ├── search.html             ← Book search & browse
│   ├── book_detail.html        ← Book info + reviews + borrow
│   ├── update_profile.html     ← Edit email/username
│   ├── history.html            ← Borrow history table
│   ├── 404.html                ← Error page
│   └── admin/
│       ├── dashboard.html      ← Admin stats + charts
│       ├── books.html          ← All books table
│       ├── book_entry.html     ← Add new book form
│       ├── edit_book.html      ← Edit book form
│       ├── users.html          ← User management
│       ├── issued.html         ← Currently issued books
│       └── fines.html          ← Fines management
│
├── database/
│   └── seed.py                 ← Run once to populate sample data
│
├── static/
│   ├── css/                    ← (place custom CSS here if needed)
│   ├── js/                     ← (place custom JS here)
│   └── images/                 ← (copy your JPG backgrounds here)
│
└── uploads/                    ← Book cover uploads (future use)
```

---

## ✅ STEP 6 — Database Schema (Auto-created by SQLAlchemy)

| Table           | Columns                                                              |
|-----------------|----------------------------------------------------------------------|
| `user`          | id, fname, email, username, password (hashed), role, created_at     |
| `category`      | id, name                                                             |
| `books`         | id, bname, aname, bid, bcategory, category_id, total_copies, available, added_at, description |
| `issued_books`  | id, user_id, book_id, issue_date, due_date, status                   |
| `borrow_history`| id, user_id, book_id, borrowed_on, returned_on, fine_amount          |
| `fines`         | id, user_id, issued_book_id, amount, per_day_rate, paid              |
| `reviews`       | id, user_id, book_id, rating, comment, created_at                    |
| `notifications` | id, user_id, message, is_read, notif_type, created_at                |
| `category`      | id, name                                                             |

---

## ✅ STEP 9 — Installation Steps

### Prerequisites
- Python 3.9+
- MySQL 8.0+ (XAMPP / WAMP / standalone)
- pip

### 1. Set up the project

```bash
# Navigate into the folder
cd elibrary

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure the database

```bash
# Copy the example env file
cp .env.example .env
```

Edit `.env`:
```
SECRET_KEY=pick-any-long-random-string
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=          ← leave blank for XAMPP default
DB_NAME=library
FLASK_ENV=development
```

### 3. Create the MySQL database

Open **phpMyAdmin** (XAMPP) or MySQL CLI and run:
```sql
CREATE DATABASE library CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## ✅ STEP 10 — Run the Website

```bash
# Make sure MySQL / XAMPP is running first!

# Run Flask
python app.py
```

Open browser → **http://localhost:5000**

### First-time: Seed sample data
```bash
python database/seed.py
```

This creates:
- **Admin**: username `admin` | password `Admin@123`
- **Users**: alice / Alice@123 · bob / Bob@123 · carol / Carol@123
- **15 sample books** across all categories

---

## ✅ STEP 11 — Create .exe (Desktop App)

```bash
pip install pyinstaller

pyinstaller --onefile --windowed \
  --add-data "templates;templates" \
  --add-data "static;static" \
  --name "ELibrary" \
  app.py
```

Find the `.exe` in `dist/ELibrary.exe`.

> **Note**: For a true desktop experience, consider pairing with `webview` (pywebview) to open the app in a frameless browser window instead of the system browser.

---

## ✅ STEP 12 — Deployment Guide

### Option A: PythonAnywhere (free)
1. Upload the project zip
2. Create a MySQL database in the dashboard
3. Set environment variables in the WSGI config
4. Point WSGI to `app.py → create_app()`

### Option B: Render.com
1. Push to GitHub
2. Connect repo on render.com
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:create_app()`
5. Add MySQL via Railway or PlanetScale

### Option C: VPS (Ubuntu)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
# Use Nginx as reverse proxy on port 80
```

---

## 🔒 Security Features Implemented

| Feature              | Implementation                              |
|----------------------|---------------------------------------------|
| Password hashing     | `Werkzeug generate_password_hash`           |
| SQL injection        | SQLAlchemy ORM (parameterised queries)      |
| Session management   | Flask-Login secure sessions                 |
| Protected routes     | `@login_required` + `@admin_required`       |
| CSRF protection      | Flask-WTF (WTF_CSRF_ENABLED)                |
| Input validation     | Server-side checks on all POST routes       |
| Role-based access    | `user.role` field ('user' / 'admin')        |

---

## 🌟 Features Summary

| Feature                  | User | Admin |
|--------------------------|------|-------|
| Register / Login / Logout | ✅  | ✅   |
| Browse & Search Books     | ✅  | ✅   |
| Borrow / Return Books     | ✅  | —    |
| Borrow History            | ✅  | ✅   |
| Fine Calculation (₹2/day) | ✅  | ✅   |
| Notifications             | ✅  | —    |
| Star Reviews              | ✅  | —    |
| Edit Profile              | ✅  | ✅   |
| Dark Mode                 | ✅  | ✅   |
| Add / Edit / Delete Books | —   | ✅   |
| Manage Users              | —   | ✅   |
| Admin Analytics Chart     | —   | ✅   |
| Clear Fines               | —   | ✅   |

---

## 📂 Where to Place Your Original Images

Copy your original images into `static/images/`:

```
static/images/
  ├── pic1.jpg      ← home background
  ├── pic2.jpg      ← register/login background
  ├── adm.jpg       ← admin background
  ├── booksearch.jpg← search background
  ├── upd.jpg       ← update profile background
  └── book.jpg      ← book card image
```

> The new UI uses CSS gradients as backgrounds by default, so images are optional.

---

## 💡 Tech Stack

```
Backend  : Python 3.x + Flask 3.0
ORM      : SQLAlchemy (Flask-SQLAlchemy)
Auth     : Flask-Login + Werkzeug
Database : MySQL 8 (PyMySQL driver)
Frontend : Jinja2 templates + custom CSS (no framework)
Charts   : Chart.js (CDN)
Icons    : Font Awesome 6 (CDN)
Fonts    : Google Fonts — Playfair Display + DM Sans
```
