"""Central registration of HTTP error pages — replaces Flask's default
plain-text error pages with the app's own visual identity."""
from flask import render_template
from werkzeug.exceptions import HTTPException

from app.extensions import db


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html", error=e), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template("errors/405.html", error=e), 405

    @app.errorhandler(429)
    def rate_limited(e):
        return render_template("errors/429.html", error=e), 429

    @app.errorhandler(500)
    def internal_error(e):
        # A failed request may have left the session mid-transaction —
        # roll back so the error page itself can still safely query the DB
        # (e.g. to render the navbar).
        db.session.rollback()
        return render_template("errors/500.html", error=e), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        if isinstance(e, HTTPException):
            return e
        db.session.rollback()
        app.logger.exception("Unhandled exception")
        return render_template("errors/500.html", error=e), 500
