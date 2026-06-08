"""
routes/main.py
Main user-facing routes: home, dashboard, search, profile update, notifications.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.models import db, Book, Category, IssuedBook, BorrowHistory, Notification, Fine, Review, User
from datetime import date
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)


# ── HOME ──────────────────────────────────────────────────────────────────────
@main_bp.route('/')
def home():
    total_books = Book.query.count()
    total_users = User.query.filter_by(role='user').count()
    categories  = Category.query.count()
    return render_template('home.html',
                           total_books=total_books,
                           total_users=total_users,
                           categories=categories)


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    # User stats
    issued      = IssuedBook.query.filter_by(user_id=current_user.id, status='issued').all()
    history     = BorrowHistory.query.filter_by(user_id=current_user.id).order_by(BorrowHistory.borrowed_on.desc()).limit(10).all()
    notifs      = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    total_fines = db.session.query(db.func.sum(Fine.amount)).filter_by(user_id=current_user.id, paid=False).scalar() or 0
    overdue     = [b for b in issued if b.is_overdue]

    # Mark overdue notifications
    for book in overdue:
        existing = Notification.query.filter_by(
            user_id=current_user.id,
            message=f'Overdue: "{book.book.bname}" — please return ASAP!'
        ).first()
        if not existing:
            n = Notification(user_id=current_user.id,
                             message=f'Overdue: "{book.book.bname}" — please return ASAP!',
                             notif_type='danger')
            db.session.add(n)
    db.session.commit()

    return render_template('dashboard.html',
                           issued=issued, history=history,
                           notifs=notifs, total_fines=total_fines,
                           overdue=overdue)


# ── SEARCH ────────────────────────────────────────────────────────────────────
@main_bp.route('/search', methods=['GET', 'POST'])
def search():
    categories = Category.query.order_by(Category.name).all()
    books      = []
    query_str  = ''
    selected_cat = ''

    if request.method == 'POST':
        mode      = request.form.get('mode', '')        # category filter
        query_str = request.form.get('search_query', '').strip()
        selected_cat = mode

        q = Book.query
        if mode:
            q = q.filter_by(bcategory=mode)
        if query_str:
            q = q.filter(or_(
                Book.bname.ilike(f'%{query_str}%'),
                Book.aname.ilike(f'%{query_str}%'),
                Book.bid.ilike(f'%{query_str}%')
            ))
        books = q.all()

    elif request.method == 'GET' and request.args.get('q'):
        query_str = request.args.get('q', '').strip()
        books = Book.query.filter(or_(
            Book.bname.ilike(f'%{query_str}%'),
            Book.aname.ilike(f'%{query_str}%')
        )).all()

    return render_template('search.html', books=books, categories=categories,
                           query_str=query_str, selected_cat=selected_cat)


# ── BOOK DETAIL ───────────────────────────────────────────────────────────────
@main_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book    = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.created_at.desc()).all()
    avg_rating = 0
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)
    return render_template('book_detail.html', book=book, reviews=reviews, avg_rating=avg_rating)


# ── ISSUE BOOK ────────────────────────────────────────────────────────────────
@main_bp.route('/issue/<int:book_id>', methods=['POST'])
@login_required
def issue_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.available <= 0:
        flash('Sorry, no copies available right now.', 'danger')
        return redirect(url_for('main.book_detail', book_id=book_id))

    already = IssuedBook.query.filter_by(user_id=current_user.id,
                                          book_id=book_id, status='issued').first()
    if already:
        flash('You have already borrowed this book.', 'warning')
        return redirect(url_for('main.dashboard'))

    issued = IssuedBook(user_id=current_user.id, book_id=book_id)
    book.available -= 1
    db.session.add(issued)

    notif = Notification(user_id=current_user.id,
                         message=f'"{book.bname}" issued successfully. Due: {issued.due_date}.',
                         notif_type='success')
    db.session.add(notif)
    db.session.commit()

    flash(f'"{book.bname}" issued! Due date: {issued.due_date}', 'success')
    return redirect(url_for('main.dashboard'))


# ── RETURN BOOK ───────────────────────────────────────────────────────────────
@main_bp.route('/return/<int:issue_id>', methods=['POST'])
@login_required
def return_book(issue_id):
    issued = IssuedBook.query.get_or_404(issue_id)
    if issued.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.dashboard'))

    issued.status = 'returned'
    issued.book.available += 1

    # Calculate fine
    fine_amount = 0.0
    if issued.is_overdue:
        fine_amount = issued.days_overdue * 2.0  # ₹2/day
        fine = Fine(user_id=current_user.id, issued_book_id=issued.id,
                    amount=fine_amount)
        db.session.add(fine)

    # Log to history
    hist = BorrowHistory(user_id=current_user.id, book_id=issued.book_id,
                         borrowed_on=issued.issue_date, returned_on=date.today(),
                         fine_amount=fine_amount)
    db.session.add(hist)

    msg = f'"{issued.book.bname}" returned successfully.'
    if fine_amount > 0:
        msg += f' Fine: ₹{fine_amount:.2f}'
    notif = Notification(user_id=current_user.id, message=msg,
                         notif_type='warning' if fine_amount else 'success')
    db.session.add(notif)
    db.session.commit()

    flash(msg, 'success' if not fine_amount else 'warning')
    return redirect(url_for('main.dashboard'))


# ── REVIEW ────────────────────────────────────────────────────────────────────
@main_bp.route('/review/<int:book_id>', methods=['POST'])
@login_required
def add_review(book_id):
    rating  = int(request.form.get('rating', 3))
    comment = request.form.get('comment', '').strip()
    existing = Review.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if existing:
        existing.rating  = rating
        existing.comment = comment
    else:
        r = Review(user_id=current_user.id, book_id=book_id,
                   rating=rating, comment=comment)
        db.session.add(r)
    db.session.commit()
    flash('Review submitted!', 'success')
    return redirect(url_for('main.book_detail', book_id=book_id))


# ── UPDATE PROFILE ────────────────────────────────────────────────────────────
@main_bp.route('/update-profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        new_email    = request.form.get('new_email', '').strip().lower()
        new_username = request.form.get('new_username', '').strip()

        if not new_email or not new_username:
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.update_profile'))

        # Check uniqueness (excluding self)
        email_taken = User.query.filter(User.email == new_email, User.id != current_user.id).first()
        uname_taken = User.query.filter(User.username == new_username, User.id != current_user.id).first()

        if email_taken:
            flash('Email already in use.', 'danger')
            return redirect(url_for('main.update_profile'))
        if uname_taken:
            flash('Username already taken.', 'danger')
            return redirect(url_for('main.update_profile'))

        current_user.email    = new_email
        current_user.username = new_username
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('update_profile.html')


# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
@main_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def read_all_notifications():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})


# ── BORROW HISTORY PAGE ───────────────────────────────────────────────────────
@main_bp.route('/history')
@login_required
def history():
    records = BorrowHistory.query.filter_by(user_id=current_user.id)\
                .order_by(BorrowHistory.borrowed_on.desc()).all()
    return render_template('history.html', records=records)
