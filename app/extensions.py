"""
Flask extension singletons.

Instantiated here (unbound) and attached to the real app inside
create_app() via extension.init_app(app). Keeping them here — instead of
inside app/__init__.py — lets models/services/blueprints import `db` (etc.)
without importing the app factory itself, avoiding circular imports.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


@event.listens_for(Engine, "connect")
def _enforce_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores every ON DELETE CASCADE / FK constraint declared in
    the schema unless this pragma is turned on for each connection — it's
    off by default. Without this, every cascade/ondelete= declared on the
    models (User->Staff, Trek->TrekImage/Review, etc.) would silently do
    nothing. Harmless no-op for non-SQLite DBAPI connections.
    """
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
