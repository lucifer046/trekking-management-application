from flask import Flask, render_template, request, redirect, url_for, flash, session
from backend.model import db, User, Trek, Booking, Staff
from functools import wraps
from app import app
from datetime import datetime

# wrapper to block random people from visiting pages without logging in first
def login_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner


# Redirecting to the dashboard
@app.route('/')
@login_required
def index():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))
    return render_template('index.html')

# login logic... mostly just checking password hash and checking if they are banned
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()

        if not email or not password:
            flash('Email or password field cannot be empty.', 'warning')
            return redirect(url_for('login'))
            
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
        
        if user.is_blocked:
            flash('Your account has been blacklisted. Contact admin.', 'danger')
            return redirect(url_for('login'))
        
        if user.role == 'staff':
            profile = Staff.query.filter_by(user_id=user.id).first()
            if not profile or profile.staff_status != 'Approved':
                flash('Pending ADMIN approval', 'warning')
                return redirect(url_for('login'))

        session["user_id"] = user.id
        session['role'] = user.role

        flash('Login successful!', 'success')
        return redirect(url_for('index'))

    return render_template('auth/login.html')

# Sign Up Logic
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password or not confirm_password:
            flash('Input fields cannot be empty.', 'warning')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Incorrect password!', 'warning')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('User with this email already exists. Try logging in.', 'danger')
            return redirect(url_for('register'))

        user = User(email=email, name=name, role=role, phone=phone, is_active=True, is_blocked=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == 'staff':
            profile = Staff(user_id=user.id, contact=phone)
            db.session.add(profile)
            flash('Registration successful! Wait for admin approval.', 'success')
        else:
            flash('Registration successful! You can now login.', 'success')

        db.session.commit()
        return redirect('/login')
 
    return render_template('auth/register.html')

# logging out by just clearing the session completely
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect('/login')
