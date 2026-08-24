"""
Development/demo seed script.

    python seed.py

Resets the database and populates it with realistic (but fake) data
across every table: admin, staff (mixed approval states), trekkers (some
inactive/blacklisted), locations, treks spanning every lifecycle status,
bookings, reviews, notifications, wishlist entries, and activity log
entries. Booking/status/approval writes go through the same
app.services layer the live app uses wherever the timeline allows (open
treks, approvals, reviews); both to avoid duplicating slot/notification/
audit-log logic here and to exercise that logic as an extra integration
check every time this script runs. Historical states that predate "now"
(completed treks, their bookings) are constructed directly, since the
service layer models real-time transitions, not backfilling history.
"""
import random
import sys
from datetime import date, datetime, timedelta, timezone


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

from app import create_app
from app.extensions import db
from app.models import (
    ActivityLog, Booking, BookingStatus, Difficulty, Location, Notification,
    Review, Staff, StaffStatus, Trek, TrekStatus, User, UserRole, Wishlist,
)
from app.services import booking_service, review_service, staff_service, trek_service
from app.services.exceptions import ServiceError
from app.utils.slugify import unique_slug

random.seed(42)  # reproducible demo data across runs

FIRST_NAMES = ["Rohan", "Aarav", "Kabir", "Vihaan", "Aditya", "Arjun", "Rahul", "Dev",
               "Ananya", "Diya", "Priya", "Riya", "Meera", "Isha", "Kavya", "Neha", "Sanya", "Tara"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Kumar", "Singh", "Patel", "Mehta", "Joshi", "Nair", "Rao"]


def unique_names(count):
    names = set()
    while len(names) < count:
        names.add(f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}")
    return list(names)


def seed():
    print("Resetting database...")
    db.drop_all()
    db.create_all()

    from flask import current_app
    cfg = current_app.config

    print("Creating admin account...")
    admin = User(name=cfg["ADMIN_NAME"], email=cfg["ADMIN_EMAIL"], role=UserRole.ADMIN, is_active=True, is_blocked=False)
    admin.set_password(cfg["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()

    print("Creating locations...")
    location_defs = [
        ("Uttarakhand", "North India"),
        ("Himachal Pradesh", "North India"),
        ("Ladakh", "North India"),
        ("Sikkim", "Northeast India"),
        ("Jammu and Kashmir", "North India"),
        ("Karnataka (Western Ghats)", "South India"),
    ]
    locations = {}
    for name, region in location_defs:
        slug = unique_slug(name, lambda candidate: Location.query.filter_by(slug=candidate).first() is not None)
        loc = Location(name=name, state_region=region, slug=slug)
        db.session.add(loc)
        db.session.flush()
        locations[name] = loc
    db.session.commit()

    print("Creating staff...")
    staff_names = unique_names(7)
    staff_names[0] = "Rohan Sharma"  # guaranteed, well-known demo account
    staff_users = []  # (user, approved: bool)
    for i, name in enumerate(staff_names):
        email_prefix = name.lower().replace(" ", "_")
        user = User(name=name, email=f"{email_prefix}_staff@trekking.com", role=UserRole.STAFF,
                    phone=f"+91 98{i:03d}00{i:02d}0", is_active=True, is_blocked=False)
        user.set_password("Staff@123")
        db.session.add(user)
        db.session.flush()

        if i < 5:
            status = StaffStatus.APPROVED
        elif i == 5:
            status = StaffStatus.PENDING
        else:
            status = StaffStatus.REJECTED

        years = random.randint(2, 15)
        region1, region2 = random.sample(list(locations.keys()), 2)
        cert = random.choice(["Nehru Institute of Mountaineering (NIM) Certified",
                               "Himalayan Mountaineering Institute (HMI) Certified",
                               "Wilderness First Aid Certified"])
        staff = Staff(
            user_id=user.id, contact=user.phone,
            experience=f"{years} years of guiding experience across {region1} and {region2}. {cert}.",
            staff_status=status,
            reviewed_at=_utcnow() if status != StaffStatus.PENDING else None,
            reviewed_by_id=admin.id if status != StaffStatus.PENDING else None,
        )
        db.session.add(staff)
        staff_users.append((user, status == StaffStatus.APPROVED))
    db.session.commit()
    approved_staff = [u for u, approved in staff_users if approved]

    print("Creating trekkers...")
    trekker_names = unique_names(18)
    trekker_names[0] = "Aarav Verma"  # guaranteed, well-known demo account
    trekkers = []
    for i, name in enumerate(trekker_names):
        email_prefix = name.lower().replace(" ", "_")
        is_active, is_blocked = True, False
        if i == 6:
            is_active = False
        elif i == 12:
            is_blocked = True
        user = User(name=name, email=f"{email_prefix}@gmail.com", role=UserRole.USER,
                    phone=f"+91 91{i:03d}00{i:02d}0", is_active=is_active, is_blocked=is_blocked)
        user.set_password("User@123")
        db.session.add(user)
        trekkers.append(user)
    db.session.commit()
    bookable_trekkers = [t for t in trekkers if t.is_active and not t.is_blocked]

    print("Creating treks...")
    trek_defs = [
        ("Kedarkantha Trek", "Uttarakhand", Difficulty.MODERATE, 6, 8500,
         "A popular winter summit trek through pine and oak forests, ending on a 360-degree Himalayan viewpoint.",
         "Summit day with panoramic Himalayan views\nCamping on snow in Juda ka Talab\nDense pine and oak forest trails",
         "Drive from Dehradun to Sankri, the trek's base village\nTrek to Juda ka Talab through pine forests\nAcclimatization day and short hike around the frozen lake\nTrek to Kedarkantha base camp\nSummit day: early start, reach Kedarkantha peak, descend to Hargaon\nTrek back to Sankri, drive to Dehradun",
         "Sturdy waterproof trekking shoes\nWarm layered clothing (temperatures can drop below freezing)\nPersonal medical kit\nValid government-issued ID"),
        ("Valley of Flowers Trek", "Uttarakhand", Difficulty.EASY, 4, 6000,
         "A gentle, breathtaking walk through a UNESCO World Heritage valley carpeted in alpine flowers.",
         "UNESCO World Heritage alpine meadow\nHundreds of flowering species in bloom\nViews of Nanda Devi range",
         "Drive to Govindghat and trek to Ghangaria\nDay trek into the Valley of Flowers and back\nDay trek to Hemkund Sahib\nReturn trek and drive back",
         "Comfortable walking shoes\nRain protection (the valley is best visited in monsoon)\nSun protection"),
        ("Hampta Pass Trek", "Himachal Pradesh", Difficulty.MODERATE, 5, 9500,
         "A dramatic crossover trek from the green Kullu valley to the stark, dry landscape of Lahaul.",
         "Crossing from lush green valley to arid mountain desert in a single day\nCamping by the Chandratal lake (optional extension)\nRiver crossings",
         "Drive from Manali to Jobra, trek to Jwara\nTrek to Balu ka Ghera\nCross Hampta Pass, descend to Shea Goru\nTrek to Chatru\nDrive back to Manali",
         "Trekking poles recommended for river crossings\nWaterproof trekking shoes\nWarm sleeping layers"),
        ("Chadar Trek", "Ladakh", Difficulty.HARD, 9, 21000,
         "A once-in-a-lifetime winter trek walking on the frozen surface of the Zanskar river.",
         "Walking directly on the frozen Zanskar river\nOvernight stays in riverside caves\nExtreme sub-zero winter landscapes",
         "Fly to Leh, acclimatize for 2 days\nDrive to Chilling, start trek on the frozen river\nTrek to Tibb cave\nTrek to Naerak, the turnaround point\nReturn trek to Chilling over multiple days",
         "High-altitude winter gear rated for -20°C\nPrior high-altitude trekking experience recommended\nMedical fitness certificate"),
        ("Har Ki Dun Trek", "Uttarakhand", Difficulty.MODERATE, 7, 10500,
         "A historic valley trek through centuries-old villages to a hanging valley shaped like a cradle.",
         "Ancient villages with centuries-old wooden architecture\nViews of Swargarohini peaks\nRich Garhwali culture along the trail",
         "Drive to Sankri via Dehradun\nTrek to Taluka and onward to Osla village\nTrek to Har Ki Dun valley\nExplore the valley, return to Osla\nTrek back to Sankri, drive to Dehradun",
         "Trekking shoes with good ankle support\nWarm clothing for high-altitude camps\nPersonal water bottles and purification tablets"),
        ("Goechala Trek", "Sikkim", Difficulty.HARD, 10, 24000,
         "A high-altitude trek to a viewpoint offering the closest possible look at Kanchenjunga.",
         "Closest trekking viewpoint to Kanchenjunga, the world's third-highest peak\nRhododendron forests in bloom (spring season)\nRemote high-altitude lakes",
         "Drive from Yuksom, trek to Sachen\nTrek to Tshoka village\nTrek to Dzongri, acclimatization day\nTrek to Kokchurang\nTrek to Thangsing and onward to Lamuney\nEarly morning viewpoint trek to Goechala, return towards Yuksom",
         "Permits required (arranged by the operator)\nHigh-altitude trekking experience recommended\nWarm layered clothing for camps above 4000m"),
        ("Kashmir Great Lakes Trek", "Jammu and Kashmir", Difficulty.HARD, 8, 19000,
         "A spectacular high-altitude trail connecting a series of alpine lakes through Kashmir's meadows.",
         "Seven pristine alpine lakes along the route\nVast alpine meadows (\"marg\") used by local shepherds\nDramatic mountain passes above 4200m",
         "Drive from Srinagar to Sonamarg, trek to Nichnai\nCross Nichnai pass to Vishansar lake\nTrek to Gadsar via Gadsar pass\nTrek to Satsar, a cluster of lakes\nTrek to Gangbal lake via Zaj pass\nDescend to Naranag, drive back to Srinagar",
         "High-altitude trekking fitness\nWarm and waterproof gear (weather changes quickly)\nValid ID for permit checks"),
        ("Coorg Coffee Trail Trek", "Karnataka (Western Ghats)", Difficulty.EASY, 2, 4000,
         "A relaxed, scenic trek through coffee plantations and misty Western Ghats forest trails.",
         "Walks through working coffee estates\nWaterfalls and dense shola forest\nLocal Kodava cuisine",
         "Arrive in Coorg, short orientation walk through a coffee estate\nFull-day forest and waterfall trek, return in the evening",
         "Light trekking shoes\nInsect repellent\nLight rain jacket"),
        ("Brahmatal Trek", "Uttarakhand", Difficulty.MODERATE, 6, 8000,
         "A winter trek to a high-altitude lake with uninterrupted views of Trishul and Nanda Ghunti.",
         "Frozen alpine lake at Brahmatal\nSummit-like ridge walk with 180-degree Himalayan views\nSnow-laden forest trails in winter",
         "Drive to Lohajung, trek to Bekaltal\nTrek to Brahmatal via dense forest\nSummit ridge walk and descend to Tilandi\nTrek back to Lohajung",
         "Snow gaiters recommended in peak winter\nWarm layered clothing\nSturdy trekking shoes"),
    ]

    treks = []
    today = date.today()
    for i, (name, loc_name, difficulty, days, price, desc, highlights, itinerary, requirements) in enumerate(trek_defs):
        capacity = random.choice([10, 12, 15, 20, 25])
        # Placeholder dates; every trek gets its real start/end date once
        # its final lifecycle status is known, in the loop below. NOT NULL
        # columns need *something* here so the initial insert succeeds.
        placeholder_start = today + timedelta(days=30 + i)
        trek = Trek(
            name=name, slug=trek_service.generate_slug(name), location_id=locations[loc_name].id,
            difficulty=difficulty, duration_days=days, capacity=capacity, available_slots=capacity,
            start_date=placeholder_start, end_date=placeholder_start + timedelta(days=days),
            price=price, description=desc, highlights=highlights, itinerary=itinerary,
            requirements=requirements, safety_info="A certified guide accompanies the group at all times. "
            "Basic first-aid and emergency evacuation protocols are in place for every batch.",
            cancellation_policy="Full refund up to 7 days before departure. 50% refund within 3-7 days. "
            "No refund within 48 hours of departure.",
            meeting_point=f"{loc_name} base point (details shared after booking)",
            status=TrekStatus.DRAFT, created_by_id=admin.id, is_featured=(i < 3),
        )
        db.session.add(trek)
        db.session.flush()
        treks.append(trek)
    db.session.commit()

    print("Advancing treks through their lifecycle...")
    # Distribute treks across every status the state machine supports, using
    # trek_service.transition_status (not raw assignment) so this seed run
    # doubles as a sanity check that the transition table itself is correct.
    plan = (
        ["draft"] * 1 +
        ["pending_approval"] * 1 +
        ["approved"] * 1 +
        ["open"] * 4 +
        ["closed"] * 1 +
        ["completed"] * 1
    )
    for trek, target in zip(treks, plan):
        path = {
            "pending_approval": [TrekStatus.PENDING_APPROVAL],
            "approved": [TrekStatus.PENDING_APPROVAL, TrekStatus.APPROVED],
            "open": [TrekStatus.PENDING_APPROVAL, TrekStatus.APPROVED, TrekStatus.OPEN],
            "closed": [TrekStatus.PENDING_APPROVAL, TrekStatus.APPROVED, TrekStatus.OPEN, TrekStatus.CLOSED],
            "completed": [TrekStatus.PENDING_APPROVAL, TrekStatus.APPROVED, TrekStatus.OPEN, TrekStatus.STARTED, TrekStatus.COMPLETED],
        }.get(target, [])
        for step in path:
            trek_service.transition_status(trek, step, admin)

    # Assign approved staff to every non-draft trek (round robin).
    for i, trek in enumerate(t for t in treks if t.status != TrekStatus.DRAFT):
        if approved_staff:
            staff_service.assign_staff(trek, approved_staff[i % len(approved_staff)], admin)

    # Dates: completed/closed treks are in the past, open/approved/draft/pending are upcoming.
    for trek in treks:
        if trek.status == TrekStatus.COMPLETED:
            start = today - timedelta(days=random.randint(20, 90))
        elif trek.status == TrekStatus.CLOSED:
            start = today + timedelta(days=random.randint(3, 10))
        else:
            start = today + timedelta(days=random.randint(10, 150))
        trek.start_date = start
        trek.end_date = start + timedelta(days=trek.duration_days)
    db.session.commit()

    print("Creating bookings...")
    all_bookings = []
    open_treks = [t for t in treks if t.status == TrekStatus.OPEN]
    for trek in open_treks:
        n_bookings = random.randint(2, 5)
        chosen = random.sample(bookable_trekkers, min(n_bookings, len(bookable_trekkers)))
        for trekker in chosen:
            party = random.choice([1, 1, 2, 2, 3])
            try:
                booking = booking_service.create_booking(trekker, trek, party)
                all_bookings.append(booking)
            except ServiceError:
                continue  # trek ran out of slots; fine, keeps data realistic

    # A couple of those active bookings get cancelled, to populate that state too.
    for booking in random.sample(all_bookings, min(2, len(all_bookings))):
        try:
            booking_service.cancel_booking(booking, booking.trekker, reason="Change of plans.")
        except ServiceError:
            pass

    # Completed trek: construct historical bookings + reviews directly.
    completed_treks = [t for t in treks if t.status == TrekStatus.COMPLETED]
    for trek in completed_treks:
        reviewers = random.sample(bookable_trekkers, min(6, len(bookable_trekkers)))
        booked_total = 0
        for trekker in reviewers:
            party = random.choice([1, 1, 2])
            booked_total += party
            booking = Booking(
                user_id=trekker.id, trek_id=trek.id, participant_count=party, status=BookingStatus.COMPLETED,
                booking_reference=f"TMA-{trek.id:02d}{trekker.id:03d}",
                booked_at=_utcnow() - timedelta(days=random.randint(25, 95)),
            )
            db.session.add(booking)
            db.session.flush()
            if random.random() < 0.7:  # most trekkers leave a review
                review_service.create_review(
                    booking, rating=random.choice([4, 4, 5, 5, 5, 3]),
                    title=random.choice(["Unforgettable trip!", "Great guide, great trail", "Would do it again", "Beautiful but tough"]),
                    body=random.choice([
                        "The guide was incredibly knowledgeable and kept the group safe throughout.",
                        "Stunning views the whole way; well worth the early mornings.",
                        "Well organized from start to finish, would recommend to any first-timer.",
                        "Challenging in parts but the support crew made it manageable.",
                    ]),
                )
        trek.available_slots = max(0, trek.capacity - booked_total)
    db.session.commit()

    print("Creating wishlist entries...")
    for trekker in random.sample(bookable_trekkers, min(8, len(bookable_trekkers))):
        for trek in random.sample(treks, random.randint(1, 3)):
            existing = Wishlist.query.filter_by(user_id=trekker.id, trek_id=trek.id).first()
            if not existing:
                db.session.add(Wishlist(user_id=trekker.id, trek_id=trek.id))
    db.session.commit()

    print("Seeding a few extra notifications and activity log entries...")
    db.session.add(Notification(user_id=bookable_trekkers[0].id, type="account", title="Welcome to TMA",
                                 message="Thanks for joining! Explore treks to plan your next trip.", link_url="/explore"))
    db.session.add(ActivityLog(actor_id=admin.id, actor_name_snapshot=admin.name, action="platform_seeded",
                                description="Demo data was generated for this environment.", target_type="platform"))
    db.session.commit()

    print("\nSeeding complete.")
    print(f"  Locations: {Location.query.count()}")
    print(f"  Users total: {User.query.count()}  (staff: {User.query.filter_by(role=UserRole.STAFF).count()}, trekkers: {User.query.filter_by(role=UserRole.USER).count()})")
    print(f"  Treks: {Trek.query.count()}  (open: {Trek.query.filter_by(status=TrekStatus.OPEN).count()}, completed: {Trek.query.filter_by(status=TrekStatus.COMPLETED).count()})")
    print(f"  Bookings: {Booking.query.count()}")
    print(f"  Reviews: {Review.query.count()}")
    print(f"  Wishlist entries: {Wishlist.query.count()}")
    print(f"  Activity log entries: {ActivityLog.query.count()}")
    print("\nDemo credentials:")
    print(f"  Admin:    {cfg['ADMIN_EMAIL']} / {cfg['ADMIN_PASSWORD']}")
    print(f"  Staff (approved): rohan_sharma_staff@trekking.com / Staff@123")
    print(f"  Staff (pending):  {staff_names[5].lower().replace(' ', '_')}_staff@trekking.com / Staff@123")
    print(f"  Trekker:  aarav_verma@gmail.com / User@123")


if __name__ == "__main__":
    env = sys.argv[1] if len(sys.argv) > 1 else "development"
    app = create_app(env)
    with app.app_context():
        seed()
