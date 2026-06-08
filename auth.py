"""
routes/auth.py
Authentication routes: register, login, logout, forgot password.
All passwords are hashed with Werkzeug. CSRF protected via Flask-WTF.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models.models import db, User, Notification
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

# ── REGISTER ──────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        fname    = request.form.get('fullname', '').strip()
        email    = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        # Validation
        if not all([fname, email, username, password, confirm]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return redirect(url_for('auth.register'))

        # Create user
        user = User(fname=fname, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Welcome notification
        notif = Notification(user_id=user.id,
                             message=f'Welcome to E-Library, {fname}! Start exploring our collection.',
                             notif_type='success')
        db.session.add(notif)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.fname}!', 'success')
            if user.is_admin:
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


# ── FORGOT PASSWORD ───────────────────────────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email       = request.form.get('email', '').strip().lower()
        new_pass    = request.form.get('newpassword', '')
        confirm     = request.form.get('confirmpassword', '')

        if new_pass != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if len(new_pass) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        user.set_password(new_pass)
        db.session.commit()
        flash('Password updated successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html')
