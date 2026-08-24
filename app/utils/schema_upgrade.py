"""
Tiny, additive-only SQLite schema upgrader.

This project deliberately has no Alembic (see README's Future
Improvements: schema changes are normally applied via `db.create_all()` +
`seed.py` reinitialization, which is fine for disposable demo data). But
`db.create_all()` only creates tables that don't exist yet; it never adds
a column to a table that's already there. Someone with an existing
`instance/trekking.db` from before the profile-fields change (real,
accumulated demo activity they don't want to lose) would otherwise be
stuck with a hard crash on the first query that touches a column SQLite
has never heard of.

`ensure_schema_upgraded(app)` closes exactly that gap and nothing more:
for each (table, column, ddl_type) below, it checks `PRAGMA table_info`
and runs `ALTER TABLE ... ADD COLUMN` only if the column is genuinely
missing. New columns land NULL for every existing row, never a made-up
value, matching "existing records must remain valid, don't invent
personal information for existing accounts". Called once from
create_app(); a no-op (checks, does nothing) on a table that doesn't
exist yet (a fresh DB `db.create_all()` hasn't built), and a no-op on a
column that's already there (which is every table on every normal boot
once this has run once).
"""
from sqlalchemy import inspect, text

# (table, column, SQL column-definition to append)
_ADDITIVE_COLUMNS = [
    ("user", "date_of_birth", "DATE"),
    ("user", "gender", "VARCHAR(20)"),
    ("user", "city", "VARCHAR(80)"),
]


def ensure_schema_upgraded(app):
    from app.extensions import db

    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_tables = set(inspector.get_table_names())
        except Exception:
            # No database file / no permission yet; db.create_all() (seed.py,
            # tests) will build the full current schema from scratch anyway.
            return

        with db.engine.begin() as conn:
            for table, column, ddl_type in _ADDITIVE_COLUMNS:
                if table not in existing_tables:
                    continue
                columns = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
                if column in columns:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
                app.logger.info(f"Schema upgrade: added {table}.{column} ({ddl_type}); existing rows default to NULL.")
