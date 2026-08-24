# TMA: Trekking Management Association

A full-stack trek discovery and booking platform: trekkers browse and book guided treks, staff guides manage the trips they're assigned to, and admins run the whole operation: approvals, scheduling, assignments, and analytics.

Originally a college CRUD assignment (single-file Flask app, four tables, no styling beyond Bootstrap defaults). This is a ground-up rebuild into a portfolio-quality product: a proper package architecture, a real design system, ten interrelated tables with a real trek-lifecycle state machine, CSRF-protected forms, role-based authorization with IDOR checks, and an 87-test automated suite.

> **Demo project.** Locations, treks, guides, and testimonials are realistic seed data generated for this showcase; not a real booking service.

## Screenshots

Not included in this repo; run it locally (two commands, see below) to see it live. Nothing here is a static mockup; every page in the walkthrough below is backed by the real Flask app and the seeded SQLite database.

## Features

**Trekkers:** browse/search/filter treks by name, location, difficulty, duration, date, and availability; view a full trek detail page (itinerary, highlights, requirements, safety info, guide, reviews); book with a participant count and special requests; get a real booking-confirmation page with a reference code; cancel bookings where the trek hasn't started; save treks to a wishlist; review completed trips; manage their profile; see in-app notifications.

**Staff guides:** register and wait for admin approval (with a real "application pending/rejected" page, not just a bounced login); manage only the treks they're assigned to (enforced server-side, not just hidden in the UI); update available slots; move a trek through its operational lifecycle (open → closed → started → completed); view and remove participants.

**Admins:** approve/reject staff applications; create/edit treks (rich content: highlights, day-by-day itinerary, requirements, safety info, cancellation policy, photos); drive the full trek lifecycle including cancellation; assign/reassign/unassign guides; view staff workload and unassigned treks; manage users (blacklist/unblacklist, which force-expires a blacklisted user's active session on their next request, not just blocks a future login); browse/search all bookings; a real activity/audit log; a dashboard with KPIs and charts, all computed from live database rows.

## Tech stack

Flask 3, SQLAlchemy 2 (Flask-SQLAlchemy), SQLite · Flask-Login, Flask-WTF (CSRF + form validation), Flask-Limiter · Jinja2, Bootstrap 5 (layout primitives only; the actual visual design is a custom CSS system), vanilla JS (no frontend framework/bundler), Chart.js for admin analytics · pytest for the test suite.

## Architecture

App-factory pattern (`create_app()`), not a global app object: nothing touches the database at import time. Six Blueprints (`public`, `auth`, `user`, `staff`, `admin`, `api`) instead of one flat route file. Business rules (slot arithmetic, the trek status state machine, staff approval, reviews, notifications, audit logging) live in a `services/` layer, not in route handlers: every route calls a service function and either succeeds or catches one `ServiceError` with a user-facing message.

```
app/
├── __init__.py         create_app() factory, before_request guard, CLI commands
├── extensions.py       db / login_manager / csrf / limiter singletons + SQLite FK pragma
├── models/              10 SQLAlchemy models + enums (see Database design)
├── blueprints/           public/ auth/ user/ staff/ admin/ api/ (route handlers only)
├── services/             booking_service, trek_service, staff_service, review_service,
│                          notification_service, activity_log_service, wishlist_service
├── forms/                Flask-WTF forms, one module per entity, real server-side validation
├── utils/                 decorators (role/approval checks), permissions (ownership checks),
│                          error_handlers, slugify, formatting (Jinja filters), uploads
├── templates/             layout/ public/ auth/ user/ staff/ admin/ errors/ components/ (macros)
└── static/                css/ (tokens → base → components → utilities) js/ (vanilla ES5-ish, no build step)
```

## Database design

10 tables. Every status field (`TrekStatus`, `BookingStatus`, `StaffStatus`, `Difficulty`, `UserRole`) is a real Python enum mapped via SQLAlchemy's portable non-native `Enum` type.

| Table | Purpose |
|---|---|
| `user` | Every account (admin/staff/trekker), one table, discriminated by `role` |
| `staff` | 1:1 approval-workflow profile for staff users (pending/approved/rejected) |
| `location` | Normalized trek destinations (powers "Popular Locations" + filters) |
| `trek` | The core listing: slug, price, capacity/available_slots, full lifecycle `status` |
| `trek_image` | 0..n photos per trek, one flagged primary |
| `booking` | One row per booking *attempt* (see below): participant count, reference code |
| `review` | Rating + write-up, tied to one specific completed `booking_id` |
| `notification` | In-app notifications, written only via `notification_service.notify()` |
| `wishlist` | Saved treks |
| `activity_log` | Append-only audit trail, written only via `activity_log_service.log()` |

**Trek status is a real state machine**, not a free-text field:

```
draft → pending_approval → approved → open ⇄ closed → started → completed
  └──────────────────────── cancelled ◄─────────────┘   (from any pre-terminal state)
```

Enforced by `Trek.can_transition_to()` and applied only through `trek_service.transition_status()`; no route or template ever assigns `.status` directly. Completing a trek auto-completes its active bookings; cancelling one cascades to cancel them (with notifications).

**Booking intentionally has no `UNIQUE(user_id, trek_id)` constraint.** The original schema had one, which forced it to reuse a single row (toggling status) on cancel then rebook, destroying the actual history of what happened. Here, every booking attempt gets its own row; "no duplicate *active* booking" is enforced by `booking_service` at write time instead. Trade-off: this isn't race-proof under concurrent double-submits, which is an acceptable limitation for a single-process SQLite dev project (see Limitations).

**Foreign key cascades** are real, not just "eventually consistent": `Staff.user_id` cascades on delete (fixes a bug in the original schema: it would raise an IntegrityError deleting a staff user); `Trek.assigned_staff_id`/`created_by_id` `SET NULL`; `ActivityLog.actor_id` `SET NULL` with a denormalized `actor_name_snapshot` so log entries stay readable after the actor is deleted. **SQLite ignores all of this by default.** `PRAGMA foreign_keys=ON` has to be set per-connection, which `app/extensions.py` does via a SQLAlchemy `connect` event listener; without it every cascade above would silently do nothing.

## Roles & authorization

Centralized decorators (`app/utils/decorators.py`): `admin_required` / `staff_required` / `user_required` / `approved_staff_required`, replacing four copy-pasted role checks in the original route files. A wrong role gets a real 403, not a silent redirect. Ownership is checked separately (`app/utils/permissions.py`): `assert_owns_booking()`, `assert_assigned_to_trek()`; the spec's core staff rule ("staff can only manage treks assigned to them") is enforced here, server-side, on every request, never inferred from what the UI happens to show.

A global `before_request` hook force-logs-out a blacklisted/deactivated user on their next request (the original app left existing sessions valid until manual logout). Staff de-approval mid-session is handled differently and deliberately *not* via forced logout: `approved_staff_required` re-checks live status on every dashboard request, so a de-approved staff member loses dashboard access immediately while staying logged in; they can still see why, on a real status page, and still edit their profile.

## Security

CSRF protection (Flask-WTF) on every state-changing request, including AJAX (`X-CSRFToken` header). All 7 destructive actions that were plain, unconfirmed GET links in the original app (staff approve/reject/delete, user blacklist/unblacklist/delete, trek delete) are now POST + CSRF + a shared confirmation modal. Passwords hashed with Werkzeug's `generate_password_hash`. Rate limiting (Flask-Limiter) on `/login` and `/register`. Trek photo uploads are validated by extension allowlist *and* a magic-byte signature check (catches a renamed non-image file even if its extension looks fine), saved under a random filename via `secure_filename()`, with `MAX_CONTENT_LENGTH` capping request size. `SECRET_KEY` / database URI / debug flag all come from environment variables (`config.py` + `.env`, loaded via python-dotenv) instead of being hardcoded. There's no `/register` path that can create an admin; the only way one exists is `flask create-admin` or `seed.py`.

## Testing

```bash
python -m pytest -v
```

87 tests, all passing, across 9 modules: `test_auth`, `test_authorization` (role checks + IDOR), `test_staff_approval` (including mid-session de-approval), `test_trek_management`, `test_trek_assignment`, `test_trek_state_machine` (every legal transition parametrized, plus a representative set of illegal ones), `test_booking`, `test_booking_integrity` (overbooking, duplicate-active booking, booking a closed/completed/cancelled trek, a blacklisted/inactive user, a trek that's already started, boundary cases), `test_reviews`. Fixtures spin up a real temp-file SQLite database per test function (see `tests/conftest.py` for why not `:memory:`).

The suite caught two real bugs during this rebuild (both fixed, see the commit history): an admin "reassign staff" action that silently no-op'd (a form helper was clobbering the submitted value before validation), and a SQLAlchemy autoflush warning from constructing a trek before its foreign keys were set.

## Running locally

```bash
git clone <this-repo>
cd trekking_management_application
python -m venv .venv
.venv\Scripts\activate          # Windows (use `source .venv/bin/activate` on macOS/Linux)
pip install -r requirements.txt

copy .env.example .env          # macOS/Linux: cp .env.example .env
python seed.py                  # resets the DB and populates realistic demo data
python run.py                   # http://127.0.0.1:5000
```

## Environment variables

See `.env.example`. `SECRET_KEY` is the only one that actually matters for local dev (it ships an insecure default so the app runs out of the box); `python -c "import secrets; print(secrets.token_hex(32))"` generates a real one. `DATABASE_URL` is optional (defaults to `instance/trekking.db`). `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` control the bootstrap admin account created by `seed.py` / `flask create-admin`.

## Demo credentials

Only accounts `seed.py` actually creates:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@trekking.com` | `Admin@12345` |
| Staff (approved) | `rohan_sharma_staff@trekking.com` | `Staff@123` |
| Staff (pending approval) | printed by `seed.py` on each run (names are randomized) | `Staff@123` |
| Trekker | `aarav_verma@gmail.com` | `User@123` |

All other seeded staff/trekker accounts follow the pattern `firstname_lastname_staff@trekking.com` / `Staff@123` and `firstname_lastname@gmail.com` / `User@123`; run `python seed.py` and read its summary output for the exact list generated that run.

## Project structure

```
trekking_management_application/
├── app/                 see Architecture above
├── tests/                pytest suite + conftest.py fixtures
├── instance/              trekking.db (gitignored, created by seed.py)
├── config.py              Development / Testing / Production config classes
├── run.py                 dev entry point: python run.py
├── seed.py                 resets + populates demo data
├── requirements.txt
├── .env.example
└── README.md
```

## Future improvements

Being direct about what this project deliberately doesn't do:

- **No real payment processing.** `Trek.price` is a real, displayed field, but there's no payment gateway integration, out of scope for a Flask/SQLite portfolio stack. Booking is "reserve a slot," not "pay for a slot."
- **No database migration tooling (Alembic).** Schema changes are applied via `db.create_all()` + `seed.py` reinitialization, which is appropriate for a dev/demo project with disposable seed data but wouldn't be how you'd evolve a schema with real user data in production.
- **Booking creation isn't race-proof under concurrent double-submits:** the "no duplicate active booking" and slot-count checks are correct for sequential requests (and are exactly what the test suite exercises) but two simultaneous requests from the same user could theoretically both pass the check before either commits. A `SELECT ... FOR UPDATE`-equivalent row lock (or a unique partial index) would close this; not implemented, since SQLite's locking model makes it a bigger change than the risk justifies here.
- **Rate limiting resets on restart** (Flask-Limiter's in-memory storage). Fine at demo scale; a real deployment would point it at Redis.
- **No email notifications:** only in-app ones. Booking confirmations, staff approval, etc. all generate a `Notification` row, not an email.
- **Trek photos are either uploaded by an admin or fall back to an illustrated SVG placeholder:** no stock photo library is bundled (deliberately, to keep every asset in the repo original).
