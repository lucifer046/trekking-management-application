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

# checking if the person is actually an admin before they break stuff
def admin_login(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner



# Dashboard for admin showing all the stats
@app.route('/admin/dashboard')
@login_required
@admin_login
def adminDashboard():
    stats = {
        'total_treks' : Trek.query.count(),
        'total_users' : User.query.filter_by(role='user').count(),
        'total_staff' : User.query.filter_by(role='staff').count(),
        'total_bookings': Booking.query.count()
    }
    latest_bookings = Booking.query.order_by(Booking.date_booked.desc()).limit(4).all()
    return render_template('admin/dashboard.html', stats=stats, latest_bookings=latest_bookings)

# big search bar function. Searches through names, emails and ids
@app.route('/admin/search')
@login_required
@admin_login
def adminSearch():
    query = request.args.get('search', '').strip()
    if not query:
        flash('Please enter a search query.', 'warning')
        return redirect('/admin/dashboard')
        
    if query.isdigit():
        trek_results = Trek.query.filter((Trek.id == int(query)) | (Trek.name.like(f'%{query}%'))).all()
    else:
        trek_results = Trek.query.filter(Trek.name.like(f'%{query}%')).all()

    if query.isdigit():
        user_results = User.query.filter(
            (User.role == 'user') & 
            ((User.id == int(query)) | (User.name.like(f'%{query}%')) | (User.email.like(f'%{query}%')))
        ).all()
    else:
        user_results = User.query.filter(
            (User.role == 'user') & 
            ((User.name.like(f'%{query}%')) | (User.email.like(f'%{query}%')))
        ).all()

    if query.isdigit():
        staff_results = Staff.query.join(User).filter(
            (Staff.id == int(query)) | 
            (User.id == int(query)) | 
            (User.name.like(f'%{query}%')) | 
            (User.email.like(f'%{query}%'))
        ).all()
    else:
        staff_results = Staff.query.join(User).filter(
            (User.name.like(f'%{query}%')) | 
            (User.email.like(f'%{query}%'))
        ).all()

    return render_template(
        'admin/search_results.html',
        query=query,
        treks=trek_results,
        users=user_results,
        staffs=staff_results
    )




# Grabs all the treks based on their status (open/closed/completed)
@app.route('/admin/treks')
@login_required
@admin_login
def adminTreks():
    status = request.args.get('status', 'open')
    
    if status in ['open', 'closed', 'completed']:
        treks = Trek.query.filter_by(status=status).all()
    else:
        treks = Trek.query.filter_by(status='open').all()
        status = 'open'
        
    open_count = Trek.query.filter_by(status='open').count()
    closed_count = Trek.query.filter_by(status='closed').count()
    completed_count = Trek.query.filter_by(status='completed').count()
    total_count = Trek.query.all()
    
    return render_template(
        'admin/manage_treks.html',
        treks=treks,
        current_status=status,
        open_count=open_count,
        closed_count=closed_count,
        completed_count=completed_count,
        total_count=total_count
    )

# admin page for creating a brand new trek and adding to database
@app.route('/admin/trek/add', methods=['GET', 'POST'])
@login_required
@admin_login
def addTrek():
    if request.method == 'POST':
        max_people = int(request.form['max_people'])

        trek = Trek(
            name = request.form['name'],
            location= request.form['location'],
            difficulty = request.form['difficulty'],
            max_people=max_people,
            left_slots = max_people,    
            days =int(request.form['days']),
            start_date = datetime.strptime(request.form['start_date'],'%Y-%m-%d').date(),
            end_date = datetime.strptime(request.form['end_date'],'%Y-%m-%d').date(),
            status = request.form.get('status', 'open'),
            description = request.form.get('description', '')
        )
        if trek.end_date < trek.start_date:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for('addTrek'))
        db.session.add(trek)
        db.session.commit()
        flash('New trek added successfully...', 'success')
        return redirect('/admin/treks')
    return render_template('admin/add_trek.html')

# editing an existing trek, checking if the fields actually got updated
@app.route('/admin/trek/edit/<int:trek_id>', methods=['GET', "POST"])
@login_required
@admin_login
def editTrek(trek_id):

    # fetches the specific trek from the DB, or throws a 404 error page if it doesn't exist
    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":
        trek.name = request.form.get("name") or trek.name
        trek.location = request.form.get("location") or trek.location
        trek.difficulty = request.form.get("difficulty") or trek.difficulty
        
        status = request.form.get("status")
        if status:
            trek.status = status
            if status == 'completed':
                Booking.query.filter_by(trek_id=trek.id, status='Booked').update({'status': 'Completed'})
                
        trek.description = request.form.get("description") or trek.description

        days = request.form.get("days")
        if days:
            trek.days = int(days)

        start_date = request.form.get("start_date")
        if start_date:
            trek.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        end_date = request.form.get("end_date")
        if end_date:
            trek.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        max_people = request.form.get("max_people")
        if max_people:
            old_max = trek.max_people
            new_max = int(max_people)
            trek.max_people = new_max
            trek.left_slots = max(0, trek.left_slots + (new_max - old_max))

        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("adminTreks"))

    return render_template("admin/edit_trek.html", trek=trek)


# Selecting a guide and assigning them to a specific trek
@app.route('/admin/trek/assign/<int:trek_id>', methods=['GET', 'POST'])
@login_required
@admin_login
def assignTrek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        if staff_id:
            trek.guide_id = int(staff_id)
        else:
            trek.guide_id = None
        db.session.commit()
        flash('Staff assigned to trek successfully.', 'success')
        return redirect('/admin/treks')
        
    approved_staff = Staff.query.filter_by(staff_status='Approved').all()
    return render_template(
        'admin/assign_trek.html',
        trek=trek,
        staff_members=approved_staff
    )


# Completely deleting a trek from the database
@app.route('/admin/trek/delete/<int:trek_id>')
@login_required
@admin_login
def deleteTrek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully.', 'success')
    return redirect(url_for('adminTreks'))



# handling the staff portal... checking who is approved or pending
@app.route('/admin/staff')
@login_required
@admin_login
def manageStaff():
    status = request.args.get('status', "Pending")
    staffs = Staff.query.filter_by(staff_status=status).all()
    pending_count = Staff.query.filter_by(staff_status='Pending').count()
    approved_count = Staff.query.filter_by(staff_status='Approved').count()
    rejected_count = Staff.query.filter_by(staff_status='Rejected').count()
    total_count = User.query.filter_by(role='staff').all()
    return render_template(
        "admin/manage_staff.html",
        staffs=staffs,
        current_status=status,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_count=total_count
    )

# Approving a staff (guide)
@app.route('/admin/staff/approve/<int:staff_id>')
@login_required
@admin_login
def approveStaff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if staff:
        staff.staff_status = 'Approved'
        db.session.commit()
        flash('Staff approved!', 'success')
    return redirect('/admin/staff')

# Rejecting a staff (guide)
@app.route('/admin/staff/reject/<int:staff_id>')
@login_required
@admin_login
def rejectStaff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if staff:
        staff.staff_status = 'Rejected'
        db.session.commit()
        flash('Staff rejected!', 'success')
    return redirect('/admin/staff')

# Deleting a staff (guide)
@app.route('/admin/staff/delete/<int:staff_id>')
@login_required
@admin_login
def deleteStaff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff deleted successfully.', 'success')
    return redirect(url_for('manageStaff'))

# manually adding a new staff account from the admin side
@app.route('/admin/staff/add', methods=['GET', 'POST'])
@login_required
@admin_login
def addStaff():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        staff_status = request.form.get('staff_status', 'Approved')
        experience = request.form.get('experience')

        if not name or not email or not password:
            flash('Name, email, and password are required fields.', 'warning')
            return redirect(url_for('addStaff'))

        if User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'danger')
            return redirect(url_for('addStaff'))

        user = User(
            name=name,
            email=email,
            phone=phone,
            role="staff",
            is_active=True,
            is_blocked=False
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = Staff(
            user_id=user.id,
            contact=phone,
            experience=experience,
            staff_status=staff_status
        )
        db.session.add(profile)
        db.session.commit()

        flash('New staff member added successfully.', 'success')
        return redirect(url_for('manageStaff'))

    return render_template('admin/add_staff.html')



# Listing all the regular trekkers and checking if they are blocked or not
@app.route('/admin/users')
@app.route('/admin/user')
@login_required
@admin_login
def adminUsers():
    status = request.args.get('status', 'all')
    
    if status == 'active':
        users = User.query.filter_by(role='user', is_blocked=False).all()
    elif status == 'blacklisted':
        users = User.query.filter_by(role='user', is_blocked=True).all()
    else:
        users = User.query.filter_by(role='user').all()
        status = 'all'
        
    all_count = User.query.filter_by(role='user').count()
    active_count = User.query.filter_by(role='user', is_blocked=False).count()
    blacklisted_count = User.query.filter_by(role='user', is_blocked=True).count()
    total_count = User.query.filter_by(role='user').all()
    
    return render_template(
        'admin/manage_users.html',
        users=users,
        current_status=status,
        all_count=all_count,
        active_count=active_count,
        blacklisted_count=blacklisted_count,
        total_count=total_count
    )

# Blocking a user 
@app.route('/admin/user/blacklist/<int:user_id>')
@login_required
@admin_login
def blacklistUser(user_id):
    user = User.query.get_or_404(user_id)
    if user:
        user.is_blocked = True
        db.session.commit()
        flash('User blacklisted successfully.', 'success')
    return redirect(url_for('adminUsers'))

# Unblocking a user
@app.route('/admin/user/unblacklist/<int:user_id>')
@login_required
@admin_login
def unblacklistUser(user_id):
    user = User.query.get_or_404(user_id)
    if user:
        user.is_blocked = False
        db.session.commit()
        flash('User unblacklisted successfully.', 'success')
    return redirect(url_for('adminUsers'))

# deleting a user account
@app.route('/admin/user/delete/<int:user_id>')
@login_required
@admin_login
def deleteUser(user_id):
    user = User.query.get_or_404(user_id)
    if user:
        Booking.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    return redirect(url_for('adminUsers'))


# Listing all the bookings 
@app.route('/admin/bookings')
@login_required
@admin_login
def adminBookings():
    bookings = Booking.query.order_by(Booking.date_booked.desc()).all()
    return render_template('admin/all_bookings.html', bookings=bookings)

