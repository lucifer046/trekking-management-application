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


# checking if the person is actually a staff member before they break stuff
def staff_login(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if session.get('role') != 'staff':
            flash('Staff access required.', 'danger')
            return redirect(url_for('staffDashboard'))    
        return func(*args, **kwargs)
    return inner





# main portal where guides can see all their assigned trips
@app.route('/staff/dashboard')
@login_required
@staff_login
def staffDashboard():
    staff_id = session['user_id']
    assigned_treks = Trek.query.filter_by(guide_id=staff_id).all()
    open_treks = Trek.query.filter_by(guide_id=staff_id, status='open').all()
    total_treks = User.query.filter_by(role='user').all()
    trek_details = Trek.query.filter_by(guide_id=staff_id).all()
    return render_template(
        'staff/dashboard.html', 
        assigned_treks = assigned_treks,
        total_treks = total_treks,
        open_treks = open_treks,
        trek_details = trek_details
    )

# view page so the guide can see who is coming on the trip
@app.route('/staff/view/<int:trek_id>')
@login_required
@staff_login
def viewTrek(trek_id):
    # fetches the specific trek from the DB, or throws a 404 error page if it doesn't exist
    trek = Trek.query.get_or_404(trek_id)
    if trek.guide_id != session['user_id']:
        flash('Access denied. You are not assigned to this trek.', 'danger')
        return redirect(url_for('staffDashboard'))
    return render_template(
        'staff/view_trek.html',
        trek=trek
    )

# guide updating the slots if someone cancels or the trek finishes
@app.route('/staff/trek/update/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@staff_login
def staffUpdateTrek(trek_id):
    # fetches the specific trek from the DB, or throws a 404 error page if it doesn't exist
    trek = Trek.query.get_or_404(trek_id)
    if trek.guide_id != session['user_id']:
        flash('Access denied. You are not assigned to this trek.', 'danger')
        return redirect(url_for('staffDashboard'))
    
    if request.method == 'POST':
        available_slots = request.form.get('available_slots')
        if available_slots is not None:
            try:
                available_slots = int(available_slots)
                if available_slots < 0 or available_slots > trek.max_people:
                    flash(f'Available slots must be between 0 and {trek.max_people}.', 'warning')
                    return redirect(url_for('staffUpdateTrek', trek_id=trek.id))
                trek.left_slots = available_slots
            except ValueError:
                flash('Invalid slots number.', 'danger')
                return redirect(url_for('staffUpdateTrek', trek_id=trek.id))
                
        status = request.form.get('status')
        if status in ['open', 'closed', 'ongoing', 'completed']:
            trek.status = status
            if status == 'completed':
                Booking.query.filter_by(trek_id=trek.id, status='Booked').update({'status': 'Completed'})
            
        db.session.commit()
        flash('Trek updated successfully.', 'success')
        return redirect(url_for('staffDashboard'))
        
    return render_template(
        'staff/update_trek.html',
        trek=trek
    )

# lets staff kick out someone from the roster if needed
@app.route('/staff/trek/<int:trek_id>/remove-participant/<int:booking_id>', methods=['POST'])
@login_required
@staff_login
def staffRemoveParticipant(trek_id, booking_id):
    # fetches the specific trek from the DB, or throws a 404 error page if it doesn't exist
    trek = Trek.query.get_or_404(trek_id)
    if trek.guide_id != session['user_id']:
        flash('Access denied. You are not assigned to this trek.', 'danger')
        return redirect(url_for('staffDashboard'))
    
    # fetching the booking or throwing a 404 if it is not in the database
    booking = Booking.query.get_or_404(booking_id)
    if booking.trek_id != trek.id:
        flash('Booking does not belong to this trek.', 'danger')
        return redirect(url_for('staffUpdateTrek', trek_id=trek.id))
        
    if booking.status == 'Booked':
        trek.left_slots = min(trek.max_people, trek.left_slots + 1)
        
    db.session.delete(booking)
    db.session.commit()
    flash('Participant removed successfully.', 'success')
    return redirect(url_for('staffUpdateTrek', trek_id=trek.id))

# letting guides update their own bio and contact info
@app.route('/staff/profile/update', methods=['GET', 'POST'])
@login_required
@staff_login
def staffUpdateProfile():
    # grabs the logged in staff user's details
    user = User.query.get(session['user_id'])
    # gets the associated staff profile info
    staff = user.staff_profile
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        experience = request.form.get('experience')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not name or not email:
            flash('Name and Email are required.', 'warning')
            return redirect(url_for('staffUpdateProfile'))
            
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash('Email is already in use by another account.', 'danger')
            return redirect(url_for('staffUpdateProfile'))
            
        if password:
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('staffUpdateProfile'))
            user.set_password(password)
            
        user.name = name
        user.email = email
        user.phone = contact
        if staff:
            staff.contact = contact
            staff.experience = experience
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('staffDashboard'))
        
    return render_template(
        'staff/update_profile.html',
        user=user,
        staff=staff
    )
