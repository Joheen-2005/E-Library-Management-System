"""
routes/admin.py
Admin-only routes: dashboard, book CRUD, user management, analytics.
All routes protected by @admin_required decorator.
"""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.models import db, User, Book, Category, IssuedBook, BorrowHistory, Fine, Notification
from datetime import date
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator: restrict route to admin users only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return login_required(decorated)


# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_books  = Book.query.count()
    total_users  = User.query.filter_by(role='user').count()
    total_issued = IssuedBook.query.filter_by(status='issued').count()
    overdue      = IssuedBook.query.filter(
        IssuedBook.status == 'issued',
        IssuedBook.due_date < date.today()
    ).count()
    total_fines  = db.session.query(func.sum(Fine.amount)).filter_by(paid=False).scalar() or 0
    categories   = Category.query.count()

    # Recent activity
    recent_issued = IssuedBook.query.order_by(IssuedBook.issue_date.desc()).limit(8).all()

    # Books per category for chart
    cat_data = db.session.query(
        Book.bcategory, func.count(Book.id)
    ).group_by(Book.bcategory).all()
    cat_labels  = [c[0] for c in cat_data]
    cat_counts  = [c[1] for c in cat_data]

    return render_template('admin/dashboard.html',
                           total_books=total_books, total_users=total_users,
                           total_issued=total_issued, overdue=overdue,
                           total_fines=total_fines, categories=categories,
                           recent_issued=recent_issued,
                           cat_labels=cat_labels, cat_counts=cat_counts)


# ── BOOK MANAGEMENT ───────────────────────────────────────────────────────────
@admin_bp.route('/books')
@admin_required
def books():
    all_books  = Book.query.order_by(Book.added_at.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/books.html', books=all_books, categories=categories)


@admin_bp.route('/books/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        bname    = request.form.get('bookname', '').strip()
        aname    = request.form.get('authorname', '').strip()
        bid      = request.form.get('bookid', '').strip()
        bcat     = request.form.get('select', '').strip()
        copies   = int(request.form.get('copies', 1))
        desc     = request.form.get('description', '').strip()

        if not all([bname, aname, bid, bcat]):
            flash('All required fields must be filled.', 'danger')
            return redirect(url_for('admin.add_book'))

        if Book.query.filter_by(bid=bid).first():
            flash(f'Book ID "{bid}" already exists.', 'danger')
            return redirect(url_for('admin.add_book'))

        cat = Category.query.filter_by(name=bcat).first()
        book = Book(bname=bname, aname=aname, bid=bid, bcategory=bcat,
                    category_id=cat.id if cat else None,
                    total_copies=copies, available=copies, description=desc)
        db.session.add(book)
        db.session.commit()
        flash(f'"{bname}" added successfully!', 'success')
        return redirect(url_for('admin.books'))

    return render_template('admin/book_entry.html', categories=categories)


@admin_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book       = Book.query.get_or_404(book_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        book.bname   = request.form.get('bookname', book.bname).strip()
        book.aname   = request.form.get('authorname', book.aname).strip()
        book.bcategory = request.form.get('select', book.bcategory)
        book.description = request.form.get('description', '').strip()
        new_copies = int(request.form.get('copies', book.total_copies))
        diff = new_copies - book.total_copies
        book.total_copies = new_copies
        book.available    = max(0, book.available + diff)
        cat = Category.query.filter_by(name=book.bcategory).first()
        book.category_id = cat.id if cat else None
        db.session.commit()
        flash(f'"{book.bname}" updated!', 'success')
        return redirect(url_for('admin.books'))

    return render_template('admin/edit_book.html', book=book, categories=categories)


@admin_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if IssuedBook.query.filter_by(book_id=book_id, status='issued').first():
        flash('Cannot delete — book is currently issued.', 'danger')
        return redirect(url_for('admin.books'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.', 'success')
    return redirect(url_for('admin.books'))


# ── USER MANAGEMENT ───────────────────────────────────────────────────────────
@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    state = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} {state}.', 'success')
    return redirect(url_for('admin.users'))


# ── ISSUED BOOKS MANAGEMENT ───────────────────────────────────────────────────
@admin_bp.route('/issued')
@admin_required
def issued():
    all_issued = IssuedBook.query.filter_by(status='issued')\
                   .order_by(IssuedBook.issue_date.desc()).all()
    return render_template('admin/issued.html', issued=all_issued, today=date.today())


@admin_bp.route('/issued/return/<int:issue_id>', methods=['POST'])
@admin_required
def admin_return(issue_id):
    issued = IssuedBook.query.get_or_404(issue_id)
    issued.status = 'returned'
    issued.book.available += 1
    fine_amount = 0.0
    if date.today() > issued.due_date:
        fine_amount = (date.today() - issued.due_date).days * 2.0
        fine = Fine(user_id=issued.user_id, issued_book_id=issued.id, amount=fine_amount)
        db.session.add(fine)
    hist = BorrowHistory(user_id=issued.user_id, book_id=issued.book_id,
                          borrowed_on=issued.issue_date, returned_on=date.today(),
                          fine_amount=fine_amount)
    db.session.add(hist)
    notif = Notification(user_id=issued.user_id,
                         message=f'"{issued.book.bname}" marked as returned by admin.' +
                                 (f' Fine: ₹{fine_amount:.2f}' if fine_amount else ''),
                         notif_type='info')
    db.session.add(notif)
    db.session.commit()
    flash(f'Book returned. Fine: ₹{fine_amount:.2f}', 'success')
    return redirect(url_for('admin.issued'))


# ── FINES ─────────────────────────────────────────────────────────────────────
@admin_bp.route('/fines')
@admin_required
def fines():
    all_fines = Fine.query.order_by(Fine.created_at.desc()).all()
    return render_template('admin/fines.html', fines=all_fines)


@admin_bp.route('/fines/clear/<int:fine_id>', methods=['POST'])
@admin_required
def clear_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    fine.paid = True
    db.session.commit()
    flash('Fine cleared.', 'success')
    return redirect(url_for('admin.fines'))


# ── ANALYTICS JSON ────────────────────────────────────────────────────────────
@admin_bp.route('/analytics/json')
@admin_required
def analytics_json():
    """Return JSON data for dashboard charts."""
    cat_data = db.session.query(
        Book.bcategory, func.count(Book.id)
    ).group_by(Book.bcategory).all()
    monthly = db.session.query(
        func.month(BorrowHistory.borrowed_on),
        func.count(BorrowHistory.id)
    ).group_by(func.month(BorrowHistory.borrowed_on)).all()
    return jsonify({
        'categories': {'labels': [c[0] for c in cat_data], 'data': [c[1] for c in cat_data]},
        'monthly':    {'labels': [f'Month {m[0]}' for m in monthly], 'data': [m[1] for m in monthly]}
    })
