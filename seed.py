"""
database/seed.py
Run this ONCE after creating tables to populate sample data.
Usage: python database/seed.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from models.models import db, User, Book, Category, Notification
from datetime import datetime

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ── Categories ────────────────────────────────
        cats = ['Horror', 'Comedy', 'Science Fiction', 'Thriller', 'Encyclopedia',
                'Romance', 'Biography', 'History', 'Self-Help', 'Technology']
        cat_objs = {}
        for c in cats:
            existing = Category.query.filter_by(name=c).first()
            if not existing:
                obj = Category(name=c)
                db.session.add(obj)
                db.session.flush()
                cat_objs[c] = obj
            else:
                cat_objs[c] = existing
        db.session.commit()

        # ── Admin User ────────────────────────────────
        if not User.query.filter_by(username='admin').first():
            admin = User(fname='Library Admin', email='admin@elibrary.com',
                         username='admin', role='admin')
            admin.set_password('Admin@123')
            db.session.add(admin)

        # ── Sample Users ──────────────────────────────
        sample_users = [
            ('Alice Sharma',  'alice@example.com',  'alice',  'Alice@123'),
            ('Bob Mehta',     'bob@example.com',    'bob',    'Bob@123'),
            ('Carol Singh',   'carol@example.com',  'carol',  'Carol@123'),
        ]
        for fname, email, uname, pwd in sample_users:
            if not User.query.filter_by(username=uname).first():
                u = User(fname=fname, email=email, username=uname)
                u.set_password(pwd)
                db.session.add(u)
        db.session.commit()

        # ── Sample Books ──────────────────────────────
        books_data = [
            ('It',              'Stephen King',       'B001', 'Horror',          3, 3),
            ('The Shining',     'Stephen King',       'B002', 'Horror',          2, 2),
            ('Three Men in a Boat','Jerome K. Jerome','B003', 'Comedy',          4, 4),
            ('Dune',            'Frank Herbert',      'B004', 'Science Fiction', 5, 5),
            ('Foundation',      'Isaac Asimov',       'B005', 'Science Fiction', 3, 3),
            ('Gone Girl',       'Gillian Flynn',      'B006', 'Thriller',        4, 4),
            ('Britannica Vol 1','Various Authors',    'B007', 'Encyclopedia',    1, 1),
            ('Sapiens',         'Yuval Noah Harari',  'B008', 'History',         6, 6),
            ('Atomic Habits',   'James Clear',        'B009', 'Self-Help',       5, 5),
            ('Clean Code',      'Robert C. Martin',   'B010', 'Technology',      3, 3),
            ('The Hitchhiker\'s Guide','Douglas Adams','B011','Science Fiction', 4, 4),
            ('Pride & Prejudice','Jane Austen',       'B012', 'Romance',         3, 3),
            ('Steve Jobs',      'Walter Isaacson',    'B013', 'Biography',       2, 2),
            ('The Da Vinci Code','Dan Brown',         'B014', 'Thriller',        4, 4),
            ('Jokes & Humor',   'Various Authors',    'B015', 'Comedy',          2, 2),
        ]
        for bname, aname, bid, bcat, total, avail in books_data:
            if not Book.query.filter_by(bid=bid).first():
                cat_obj = Category.query.filter_by(name=bcat).first()
                b = Book(bname=bname, aname=aname, bid=bid, bcategory=bcat,
                         category_id=cat_obj.id if cat_obj else None,
                         total_copies=total, available=avail)
                db.session.add(b)
        db.session.commit()

        # ── Sample Notifications ──────────────────────
        alice = User.query.filter_by(username='alice').first()
        if alice:
            n = Notification(user_id=alice.id,
                             message='Welcome to E-Library! Start exploring books.',
                             notif_type='success')
            db.session.add(n)
        db.session.commit()

        print("✅ Database seeded successfully!")
        print("   Admin login → username: admin | password: Admin@123")

if __name__ == '__main__':
    seed()
