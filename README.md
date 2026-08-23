# Trekking Management Application

This is a web application designed to help organize and coordinate trekking trips. It has three roles: administrators, staff guides, and trekkers.

## Features

- **For Administrators**: Full control over creating, editing, and scheduling treks. Admins can assign staff members to lead specific treks, review and approve guide registrations, view all booking history, and blacklist users if needed.
- **For Guides (Staff)**: Guides can log in to view their assigned treks, manage slot availability, view participant lists, update the trek status, and manage their profile details.
- **For Trekkers (Users)**: Trekkers can search for open treks by name, location, or difficulty level, make bookings, and view their personal booking history.

## Technology Stack

The application is built using Python, Flask, and Flask-SQLAlchemy on the backend, with standard HTML templates and CSS (Bootstrap) on the frontend.

## Testing Credentials

On startup, or after running the seed script, the database is populated with accounts for testing:

- **Administrator**:
  - Email: admin@trekking.com
  - Password: admin123

- **Trek Staff (Guide)**:
  - Email: rohan_sharma_staff@trekking.com
  - Password: staff123

- **Trekker (User)**:
  - Email: aarav_verma@gmail.com
  - Password: user123
