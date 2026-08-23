from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()



# Main user table for storing all users (trekkers, guides, admins)
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(96), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(48), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    
    # Linking tables so we can get bookings and treks easily
    bookings = db.relationship('Booking', backref='trekker', lazy=True)
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True, foreign_keys='Trek.guide_id')
    staff_profile = db.relationship('Staff', backref='user', uselist=False)

    # Simple function to check if the password matches the hash in the database
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password=password)
    

# table for all the treks we offer
class Trek(db.Model):
    __tablename__ = 'trek'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    location = db.Column(db.String(56), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False) # Easy/Moderate/Hard
    max_people = db.Column(db.Integer, nullable=False)
    left_slots = db.Column(db.Integer, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(32), default="open") # open/closed/completed
    guide_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    description = db.Column(db.Text, default=" ")

    
    bookings = db.relationship('Booking', backref='trek',cascade="all, delete-orphan", lazy=True)

# keeping track of who booked what trek
class Booking(db.Model):
    __tablename__ = 'bookings'

    # making sure one user cant book the same trek multiple times
    __table_args__ = (db.UniqueConstraint('user_id', 'trek_id', name='unique_user_trek_booking'),)

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    date_booked = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(48), default="Booked") # Booked/Cancelled/Completed

# extra details for users who are guide staff
class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),unique=True ,nullable=False)
    contact = db.Column(db.String(20))
    experience = db.Column(db.Text)
    staff_status = db.Column(db.String(20), default="Pending") # Pending/Approved/Rejected

