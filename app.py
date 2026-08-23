import sys
import os
if __name__ == '__main__':
    sys.modules['app'] = sys.modules[__name__]

from flask import Flask, render_template, request, redirect, url_for, flash
from backend.model import db, User, Staff, Booking, Trek

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# setting up the first admin so i can actually login and test stuff
def create_admin():
    admin = User.query.filter_by(email='admin@trekking.com').first()
    if not admin:
        admin = User(
            name = 'Admin',
            email = 'admin@trekking.com',
            role= 'admin',
            is_active = True,
            is_blocked = False
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created: admin@trekking.com / admin123")


# creating instance folder if it doesnt exist and setting up db
os.makedirs("instance", exist_ok=True)
with app.app_context():
    db.create_all()
    create_admin()


from backend import auth_routes, admin_routes, staff_routes, user_routes

if __name__ == '__main__':
    app.run(debug=True)
