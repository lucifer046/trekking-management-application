"""
Application factory. Replaces the original app.py's module-level global
Flask instance (which ran db.create_all() and admin creation at *import*
time and wired routes together via a `sys.modules` circular-import trick)
with the standard create_app() pattern: nothing touches the database at
import time, and the database/admin bootstrap only ever happens through
`flask create-admin`, `seed.py`, or the test suite's fixtures.
"""
import os

from flask import Flask, flash, redirect, request, url_for
from flask_login import current_user, logout_user

from app.extensions import csrf, db, limiter, login_manager
from app.models import Notification, User
from app.utils.error_handlers import register_error_handlers
from app.utils.formatting import register_template_helpers
from app.utils.schema_upgrade import ensure_schema_upgraded
from config import config_by_name


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    if config_name == "production" and app.config["SECRET_KEY"] == "dev-insecure-secret-key-change-me":
        raise RuntimeError("SECRET_KEY environment variable must be set before running in production.")

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, "uploads", "treks"), exist_ok=True)

    _register_extensions(app)
    ensure_schema_upgraded(app)
    _register_blueprints(app)
    _register_cli(app)
    register_error_handlers(app)
    register_template_helpers(app)
    _register_request_hooks(app)
    _register_context_processors(app)

    return app


def _register_extensions(app):
    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        # Always returns the real user (never None for a blocked/inactive
        # account) so the before_request hook below can force a *specific*
        # logout message instead of a generic "please log in" redirect.
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    from app.blueprints.admin.routes import bp as admin_bp
    from app.blueprints.api.routes import bp as api_bp
    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.public.routes import bp as public_bp
    from app.blueprints.staff.routes import bp as staff_bp
    from app.blueprints.user.routes import bp as user_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")


def _register_cli(app):
    import click

    @app.cli.command("create-admin")
    def create_admin_command():
        """Creates the platform's superuser admin account from
        ADMIN_EMAIL/ADMIN_PASSWORD/ADMIN_NAME (env or config defaults) if
        it doesn't already exist. There is deliberately no /register route
        that can create an admin; this CLI command (also called by
        seed.py) is the only path."""
        from app.models import UserRole

        email = app.config["ADMIN_EMAIL"]
        existing = User.query.filter_by(email=email).first()
        if existing:
            click.echo(f"Admin already exists: {email}")
            return

        admin = User(
            name=app.config["ADMIN_NAME"],
            email=email,
            role=UserRole.ADMIN,
            is_active=True,
            is_blocked=False,
        )
        admin.set_password(app.config["ADMIN_PASSWORD"])
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin created: {email} / {app.config['ADMIN_PASSWORD']}")


def _register_request_hooks(app):
    # Static files, and the small set of endpoints an already-logged-out
    # user must still be able to reach, are skipped so this hook doesn't
    # force redirect loops on the login/static routes themselves.
    _exempt_endpoints = {"auth.login", "auth.logout", "static"}

    @app.before_request
    def enforce_live_account_status():
        """The fix for the original app's session-invalidation gap: a
        blacklisted/deactivated user keeps a valid Flask-Login session
        until this hook catches it on their *next* request and force-logs
        them out with a specific explanation, rather than silently
        staying "logged in" until they happen to log out themselves.

        Staff de-approval mid-session is deliberately handled differently
        (NOT here): approved_staff_required already re-checks live
        staff_status on every dashboard-guarded request and redirects to
        the pending/rejected status page, so a de-approved staff member
        loses dashboard access immediately without being forcibly signed
        out; they can still see *why* and still update their own profile.
        """
        if request.endpoint in _exempt_endpoints or not current_user.is_authenticated:
            return None

        if not current_user.account_is_usable:
            logout_user()
            flash("Your account has been deactivated or blocked. Contact support if you believe this is a mistake.", "danger")
            return redirect(url_for("auth.login"))

        return None


def _register_context_processors(app):
    @app.context_processor
    def inject_globals():
        from app.forms.booking_forms import ConfirmActionForm

        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

        return {
            "confirm_form": ConfirmActionForm(),
            "unread_notification_count": unread_count,
        }
