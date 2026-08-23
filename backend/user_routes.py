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

# checking if the person is actually a regular user before they break stuff
def user_login(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if session.get('role') != 'user':
            flash('User access required.', 'danger')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner




# trekkers main screen showing what they booked
@app.route('/user/dashboard')
@login_required
@user_login
def userDashboard():
    # Gets the logged in user's details
    user = User.query.get(session['user_id'])
    # fetches their bookings from newest to oldest
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.date_booked.desc()).all()
    available_treks = Trek.query.filter_by(status='open').all()
    
    stats = {
        'total_bookings': len(bookings),
        'active_bookings': sum(1 for b in bookings if b.status == 'Booked'),
        'cancelled_bookings': sum(1 for b in bookings if b.status == 'Cancelled'),
        'available_treks': len(available_treks)
    }
    
    return render_template(
        'user/dashboard.html',
        user=user,
        bookings=bookings,
        available_treks=available_treks,
        stats=stats
    )

# handles booking a trek and also makes sure there are actually seats left
@app.route('/user/book/<int:trek_id>', methods=['POST'])
@login_required
@user_login
def bookTrek(trek_id):
    user_id = session['user_id']
    # fetches the specific trek from the DB, or throws a 404 error page if it doesn't exist
    trek = Trek.query.get_or_404(trek_id)
    
    if trek.status != 'open':
        flash('This trek is not open for bookings.', 'danger')
        return redirect(url_for('userDashboard'))
        
    existing = Booking.query.filter_by(user_id=user_id, trek_id=trek_id).first()
    if existing:
        if existing.status == 'Booked':
            flash('You have already booked this trek.', 'info')
            return redirect(url_for('userDashboard'))
        elif existing.status == 'Cancelled':
            if trek.left_slots <= 0:
                flash('No slots available for this trek.', 'warning')
                return redirect(url_for('userDashboard'))
            existing.status = 'Booked'
            trek.left_slots -= 1
            db.session.commit()
            flash('Trek booked successfully!', 'success')
            return redirect(url_for('userDashboard'))
            
    if trek.left_slots <= 0:
        flash('No slots available for this trek.', 'warning')
        return redirect(url_for('userDashboard'))
        
    booking = Booking(user_id=user_id, trek_id=trek_id, status='Booked')
    trek.left_slots -= 1
    db.session.add(booking)
    db.session.commit()
    flash('Trek booked successfully!', 'success')
    return redirect(url_for('userDashboard'))


# if they cancel, we give the slot back so someone else can go
@app.route('/user/cancel-booking/<int:booking_id>', methods=['POST'])
@login_required
@user_login
def cancelBooking(booking_id):
    user_id = session['user_id']
    # fetching the booking or throwing a 404 if it is not in the database
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != user_id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('userDashboard'))
        
    if booking.status == 'Cancelled':
        flash('Booking is already cancelled.', 'info')
        return redirect(url_for('userDashboard'))
        
    trek = booking.trek
    booking.status = 'Cancelled'
    trek.left_slots = min(trek.max_people, trek.left_slots + 1)
    db.session.commit()
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('userDashboard'))


# changing user details like phone number and password
@app.route('/user/profile/update', methods=['GET', 'POST'])
@login_required
@user_login
def userUpdateProfile():
    # Gets the logged in user's details
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not name or not email:
            flash('Name and Email are required.', 'warning')
            return redirect(url_for('userUpdateProfile'))
            
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash('Email is already in use.', 'danger')
            return redirect(url_for('userUpdateProfile'))
            
        if password:
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('userUpdateProfile'))
            user.set_password(password)
            
        user.name = name
        user.email = email
        user.phone = contact
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('userDashboard'))
        
    return render_template('user/update_profile.html', user=user)

# list of previous trips they took
@app.route('/user/history')
@login_required
@user_login
def userHistory():
    # Gets the logged in user's details
    user = User.query.get(session['user_id'])
    # fetches their bookings from newest to oldest
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.date_booked.desc()).all()
    return render_template('user/trekking_history.html', user=user, bookings=bookings)


# Search function so they can filter by difficulty
@app.route('/user/treks/search', methods=['GET'])
@login_required
@user_login
def userSearchTreks():
    # Gets the logged in user's details
    user = User.query.get(session['user_id'])
    # Fetches search query and difficulty level from the request
    query = request.args.get('query', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    
    treks_query = Trek.query.filter_by(status='open')
    if query:
        treks_query = treks_query.filter(
            (Trek.name.like(f'%{query}%')) | 
            (Trek.location.like(f'%{query}%'))
        )
    if difficulty and difficulty != 'All':
        treks_query = treks_query.filter_by(difficulty=difficulty)
        
    results = treks_query.all()
    
    bookings = Booking.query.filter_by(user_id=user.id, status='Booked').all()
    booked_trek_ids = {b.trek_id for b in bookings}
    
    return render_template(
        'user/trek_option_search.html',
        user=user,
        treks=results,
        query=query,
        difficulty=difficulty,
        booked_trek_ids=booked_trek_ids
    )

