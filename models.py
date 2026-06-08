"""
models/models.py
All database models for the E-Library Management System.
Tables: User, Admin, Book, Category, IssuedBook, Fine, BorrowHistory, Review, Notification
"""
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─── USER ───────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname     = db.Column(db.String(100), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)
    username  = db.Column(db.String(80),  unique=True, nullable=False)
    password  = db.Column(db.String(256), nullable=False)
    role      = db.Column(db.String(10),  default='user')   # 'user' | 'admin'
    created_at= db.Column(db.DateTime,   default=datetime.utcnow)
    is_active = db.Column(db.Boolean,    default=True)

    issued_books  = db.relationship('IssuedBook',   back_populates='user', lazy='dynamic')
    borrow_history= db.relationship('BorrowHistory',back_populates='user', lazy='dynamic')
    reviews       = db.relationship('Review',       back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')
    fines         = db.relationship('Fine',         back_populates='user', lazy='dynamic')

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


# ─── CATEGORY ────────────────────────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'category'
    id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    books= db.relationship('Book', back_populates='category_rel', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


# ─── BOOK ────────────────────────────────────────────────────────────────────
class Book(db.Model):
    __tablename__ = 'books'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bname       = db.Column(db.String(200), nullable=False)
    aname       = db.Column(db.String(100), nullable=False)
    bid         = db.Column(db.String(50),  unique=True, nullable=False)
    bcategory   = db.Column(db.String(80),  nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    total_copies= db.Column(db.Integer, default=1)
    available   = db.Column(db.Integer, default=1)
    added_at    = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(200), nullable=True)

    category_rel   = db.relationship('Category', back_populates='books')
    issued_books   = db.relationship('IssuedBook',    back_populates='book', lazy='dynamic')
    borrow_history = db.relationship('BorrowHistory', back_populates='book', lazy='dynamic')
    reviews        = db.relationship('Review',        back_populates='book', lazy='dynamic')

    def __repr__(self):
        return f'<Book {self.bname}>'


# ─── ISSUED BOOK ─────────────────────────────────────────────────────────────
class IssuedBook(db.Model):
    __tablename__ = 'issued_books'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id     = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    issue_date  = db.Column(db.Date,  default=date.today)
    due_date    = db.Column(db.Date,  default=lambda: date.today() + timedelta(days=14))
    status      = db.Column(db.String(20), default='issued')  # issued | returned | overdue

    user = db.relationship('User', back_populates='issued_books')
    book = db.relationship('Book', back_populates='issued_books')
    fine = db.relationship('Fine', back_populates='issued_book', uselist=False)

    @property
    def is_overdue(self):
        return date.today() > self.due_date and self.status == 'issued'

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0

    def __repr__(self):
        return f'<IssuedBook user={self.user_id} book={self.book_id}>'


# ─── BORROW HISTORY ───────────────────────────────────────────────────────────
class BorrowHistory(db.Model):
    __tablename__ = 'borrow_history'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id      = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrowed_on  = db.Column(db.Date, default=date.today)
    returned_on  = db.Column(db.Date, nullable=True)
    fine_amount  = db.Column(db.Float, default=0.0)

    user = db.relationship('User', back_populates='borrow_history')
    book = db.relationship('Book', back_populates='borrow_history')

    def __repr__(self):
        return f'<BorrowHistory user={self.user_id} book={self.book_id}>'


# ─── FINE ─────────────────────────────────────────────────────────────────────
class Fine(db.Model):
    __tablename__ = 'fines'
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'),         nullable=False)
    issued_book_id = db.Column(db.Integer, db.ForeignKey('issued_books.id'), nullable=False)
    amount         = db.Column(db.Float,   default=0.0)
    per_day_rate   = db.Column(db.Float,   default=2.0)   # ₹2 per day
    paid           = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    user        = db.relationship('User',       back_populates='fines')
    issued_book = db.relationship('IssuedBook', back_populates='fine')

    def __repr__(self):
        return f'<Fine ₹{self.amount} user={self.user_id}>'


# ─── REVIEW ──────────────────────────────────────────────────────────────────
class Review(db.Model):
    __tablename__ = 'reviews'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'),  nullable=False)
    book_id    = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    rating     = db.Column(db.Integer, nullable=False)   # 1–5
    comment    = db.Column(db.Text,    nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='reviews')
    book = db.relationship('Book', back_populates='reviews')

    def __repr__(self):
        return f'<Review {self.rating}★ book={self.book_id}>'


# ─── NOTIFICATION ─────────────────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message    = db.Column(db.String(300), nullable=False)
    is_read    = db.Column(db.Boolean,  default=False)
    notif_type = db.Column(db.String(30), default='info')  # info|warning|success|danger
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.notif_type} user={self.user_id}>'
