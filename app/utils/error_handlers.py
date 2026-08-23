"""Central registration of HTTP error pages — replaces Flask's default
plain-text error pages with the app's own visual identity. All six codes
render the same errors/error.html shell parameterized by copy, which is
what actually guarantees visual consistency across them (identical
markup, not just similarly-styled separate files)."""
from flask import render_template
from werkzeug.exceptions import HTTPException

from app.extensions import db

_ERROR_COPY = {
    400: ("exclamation-octagon", "That request doesn't look right", "We couldn't understand that request. Double-check the link or form and try again."),
    403: ("shield-lock", "Access denied", "You don't have permission to view this page. If you think that's wrong, contact the platform admin."),
    404: ("signpost-2", "Trail not found", "This page has wandered off the map. It may have moved, or the link might be out of date."),
    405: ("cone-striped", "Method not allowed", "That action isn't supported on this page."),
    429: ("hourglass-split", "Slow down a little", "You've made too many attempts in a short time. Please wait a minute and try again."),
    500: ("tools", "Something went wrong on our end", "An unexpected error occurred. It's been logged — please try again in a moment."),
}


def register_error_handlers(app):
    def render_error(code, error):
        icon, title, text = _ERROR_COPY.get(code, _ERROR_COPY[500])
        return render_template("errors/error.html", code=code, icon=icon, title=title, text=text), code

    @app.errorhandler(400)
    def bad_request(e):
        return render_error(400, e)

    @app.errorhandler(403)
    def forbidden(e):
        return render_error(403, e)

    @app.errorhandler(404)
    def not_found(e):
        return render_error(404, e)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_error(405, e)

    @app.errorhandler(429)
    def rate_limited(e):
        return render_error(429, e)

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_error(500, e)

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        if isinstance(e, HTTPException):
            return e
        db.session.rollback()
        app.logger.exception("Unhandled exception")
        return render_error(500, e)
