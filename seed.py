import os
import sys
import random
from datetime import date, datetime, timedelta

# appending the project root directory to the python path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, create_admin
from backend.model import User, Trek, Booking, Staff

# helper function to generate realistic, unique Indian names so our test database feels authentic
def generate_unique_names(count):
    first_names = ['Rohan', 'Aarav', 'Kabir', 'Vihaan', 'Aditya', 'Arjun', 'Rahul', 'Dev', 'Ananya', 'Diya', 'Priya', 'Riya']
    last_names = ['Sharma', 'Verma', 'Gupta', 'Kumar', 'Singh', 'Patel', 'Mehta', 'Joshi']
    names = set()
    while len(names) < count:
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        names.add(f"{fn} {ln}")
    return list(names)

# main database seeding routine
def seed_database():
    # resetting database to clear any stale records
    print("Resetting database...")
    db.drop_all()
    db.create_all()
    
    # initializing default admin account for easy testing
    print("Initializing admin account via app.py...")
    create_admin()
    
    # generating staff members with typical regional expertise and certifications
    print("Generating 5 Staff members...")
    staff_names = generate_unique_names(5)
    staff_users = []
    
    experience_regions = ["Garhwal Himalayas", "Western Ghats", "Nilgiri Hills", "Zanskar Range"]
    experience_certs = [
        "Nehru Institute of Mountaineering (NIM) Certified", 
        "Himalayan Mountaineering Institute (HMI) Certified", 
        "Wilderness First Aid Certified"
    ]
    
    for i, name in enumerate(staff_names):
        email_prefix = name.lower().replace(" ", "_")
        contact_num = f"+91 99345 678{i:02d}"
        
        # guaranteeing that rohan sharma is always generated as the main staff profile for easy testing
        if i == 0:
            name = "Rohan Sharma"
            email_prefix = "rohan_sharma"
            
        # creating user record for staff member
        user = User(
            name=name,
            email=f"{email_prefix}_staff@trekking.com",
            role="staff",
            phone=contact_num,
            is_active=True,
            is_blocked=False
        )
        user.set_password("staff123")
        db.session.add(user)
        db.session.flush() # flushing to retrieve user.id for relationship referencing
        
        # setting up a mix of approved, pending, and rejected staff status to test admin approval features
        if i < 3:
            staff_status = "Approved"
        elif i < 4:
            staff_status = "Pending"
        else:
            staff_status = "Rejected"
            
        years = random.randint(1, 15)
        region1 = random.choice(experience_regions)
        region2 = random.choice([r for r in experience_regions if r != region1])
        cert = random.choice(experience_certs)
        
        # creating detailed staff profile
        staff_profile = Staff(
            user_id=user.id,
            contact=contact_num,
            experience=f"{years} years of guiding experience in the {region1} and {region2}. Certified from {cert}.",
            staff_status=staff_status
        )
        db.session.add(staff_profile)
        
        # keeping track of approved guides to assign them to treks later
        if staff_status == "Approved":
            staff_users.append(user.id)

    # generating regular users (about 15 is plenty for simple pagination and listing checks)
    print("Generating 15 regular Users...")
    user_names = generate_unique_names(15)
    regular_users = []
    
    for i, name in enumerate(user_names):
        email_prefix = name.lower().replace(" ", "_")
        contact_num = f"+91 91234 567{i:02d}"
        is_active = True
        is_blocked = False
        
        # marking one user as inactive and one as blacklisted/blocked to test security locks
        if i == 5:
            is_active = False
        elif i == 10:
            is_blocked = True
            
        # guaranteeing that aarav verma is always created as the main test user
        if i == 0:
            name = "Aarav Verma"
            email_prefix = "aarav_verma"
            is_active = True
            is_blocked = False
            
        user = User(
            name=name,
            email=f"{email_prefix}@gmail.com",
            role="user",
            phone=contact_num,
            is_active=is_active,
            is_blocked=is_blocked
        )
        user.set_password("user123")
        db.session.add(user)
        
        # only allowing active and non-blocked users to make bookings
        if is_active and not is_blocked:
            regular_users.append(user)
            
    db.session.flush()

    # pre-defined list of 8 treks in India (matches the exact number we generate)
    trek_templates = [
        ("Roopkund Trek", "Uttarakhand, India", "Hard", "High altitude trek to the skeleton lake."),
        ("Valley of Flowers Trek", "Uttarakhand, India", "Easy", "Beautiful valley with diverse alpine flowers."),
        ("Kedarkantha Trek", "Uttarakhand, India", "Moderate", "Popular winter summit trek with great views."),
        ("Hampta Pass Trek", "Himachal Pradesh, India", "Moderate", "Scenic pass connecting Kullu and Spiti valleys."),
        ("Chadar Trek", "Ladakh, India", "Hard", "Unique winter trek over the frozen Zanskar river."),
        ("Har Ki Dun Trek", "Uttarakhand, India", "Moderate", "Historic valley trek with ancient villages."),
        ("Goechala Trek", "Sikkim, India", "Hard", "Trek offering close views of Kanchenjunga."),
        ("Kashmiri Great Lakes Trek", "Jammu and Kashmir, India", "Hard", "Beautiful trail passing multiple alpine lakes.")
    ]

    # creating 8 sample treks representing a mix of completed, open, and closed statuses
    print("Generating 8 Treks...")
    treks = []
    today = date.today()
    
    statuses = ["completed"] * 2 + ["open"] * 4 + ["closed"] * 2
    
    for i in range(8):
        name, location, difficulty, desc = trek_templates[i]
        status = statuses[i]
        
        max_people = random.choice([8, 10, 12, 15, 20, 25])
        days = random.choice([1, 2, 3, 4, 5, 7, 10])
        
        # setting realistic start and end dates based on the trek status
        if status == "completed":
            start_date = today - timedelta(days=random.randint(15, 60))
        else:
            start_date = today + timedelta(days=random.randint(5, 120))
            
        end_date = start_date + timedelta(days=days)
        
        # round-robin assignment of approved guides to treks
        guide_id = staff_users[i % len(staff_users)] if staff_users else None
        
        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            max_people=max_people,
            left_slots=max_people, # left slots will decrement as users register
            days=days,
            start_date=start_date,
            end_date=end_date,
            status=status,
            guide_id=guide_id,
            description=desc
        )
        db.session.add(trek)
        treks.append(trek)
        
    db.session.flush()

    # generating 20 mock bookings to test registration, slot count decrements, and user history
    print("Generating 20 Bookings...")
    bookings_count = 0
    booked_pairs = set()
    
    bookable_treks = [t for t in treks if t.status in ["completed", "open", "closed"]]
    
    while bookings_count < 20 and bookable_treks and regular_users:
        user = random.choice(regular_users)
        available_treks = [t for t in bookable_treks if t.left_slots > 0]
        if not available_treks:
            break
        trek = random.choice(available_treks)
        
        # preventing the same user from booking the same trek multiple times
        pair = (user.id, trek.id)
        if pair not in booked_pairs:
            booked_pairs.add(pair)
            
            # completed treks automatically get 'Completed' booking status
            if trek.status == "completed":
                booking_status = "Completed"
            else:
                booking_status = random.choice(["Booked", "Booked", "Booked", "Cancelled"])
                
            # decrementing available slot count for active/completed bookings
            if booking_status in ["Booked", "Completed"]:
                trek.left_slots -= 1
                
            date_booked = datetime.now() - timedelta(days=random.randint(1, 14))
            
            booking = Booking(
                user_id=user.id,
                trek_id=trek.id,
                date_booked=date_booked,
                status=booking_status
            )
            db.session.add(booking)
            bookings_count += 1

    # committing all database additions
    db.session.commit()
    print("Database seeding completed successfully!")
    
    # printing a nice summary of the seeded data and accounts for the developer's convenience
    print("\nSeeding Summary Statistics:")
    print(f"  - Total Users: {User.query.count()} (including admin)")
    print(f"  - Total Staff Profiles: {Staff.query.count()}")
    print(f"  - Total Treks: {Trek.query.count()}")
    print(f"  - Total Bookings: {Booking.query.count()}")
    print("\nCredentials:")
    print("  - Admin: admin@trekking.com / admin123")
    print(f"  - Staff Users ({Staff.query.count()} accounts): e.g. {User.query.filter_by(role='staff').first().email} / staff123")
    print(f"  - Regular Users ({User.query.filter_by(role='user').count()} accounts): e.g. {User.query.filter_by(role='user').first().email} / user123")

# run seed process if run directly
if __name__ == "__main__":
    with app.app_context():
        seed_database()
