# Trekking Management Application (TMA)
## Complete Authentication, Registration, Profile & Account Management Redesign

Redesign and upgrade the **entire authentication and user profile system** of my existing **Trekking Management Application (TMA)**.

This is an actual working **Flask/Jinja application**, not a static UI mockup.

The objective is to combine:

1. A complete premium redesign of Login and Registration.
2. Additional user/staff profile information during registration.
3. A complete profile and edit-profile system.
4. Admin profile and account management.
5. Secure password management.
6. Immutable account email addresses.
7. Database/schema/migration updates.
8. Seed/demo data updates.
9. Validation and authorization updates.
10. Application-wide propagation of the new profile fields.
11. Tests and documentation.

Do not implement these as disconnected frontend changes. Treat the **underlying database model as the single source of truth** and trace every change through the entire application.

---

# 1. CORE REQUIREMENT

Update the existing TMA end-to-end.

The implementation must cover:

- Login UI
- Registration UI
- Authentication
- User database model
- Staff database model if applicable
- Admin account/profile
- User profile
- Staff profile
- Edit profile
- Admin profile management
- Password management
- Validation
- Authorization
- Database schema
- Existing records
- Migration/setup
- Seed/demo data
- Admin management pages
- Dashboards where profile data is displayed
- Booking-related displays where relevant
- Tests
- Documentation
- CSS
- JavaScript

You have permission to modify the existing models, routes, database setup, seed logic, templates, CSS, JavaScript, and related backend code wherever necessary.

Do not break existing functionality.

---

# 2. PREMIUM AUTHENTICATION EXPERIENCE

Completely replace the current plain centered-card Login/Register design.

The current screenshots are only a reference for the existing implementation. Do not preserve the existing visual layout.

The new authentication experience should feel like a **premium trekking/adventure platform**.

The strongest design direction is:

> **Immersive adventure environment on the left + elegant authentication workspace on the right + subtle motion + efficient viewport usage + responsive behavior.**

---

# 3. CRITICAL VIEWPORT REQUIREMENT

The current authentication pages have a major usability problem:

> The complete authentication form does not fit inside the initial desktop/laptop viewport and forces unnecessary scrolling.

Fix this completely.

On normal desktop/laptop screens:

- The complete Login form should be visible immediately.
- The user should not need to scroll just to access the form.
- The page should naturally fit within the viewport.
- Do not solve this by making the form microscopic.
- Maintain comfortable typography and spacing.
- Account for header height, padding, browser viewport, and responsive breakpoints.

Use an appropriate viewport-aware structure such as:

```css
min-height: 100vh;
height: 100vh;
```

or an equivalent responsive implementation.

Test at:

- 1920×1080
- 1600×900
- 1440×900
- 1366×768
- 1280×720

Mobile scrolling is acceptable when the complete form genuinely cannot fit vertically.

---

# 4. SPLIT-SCREEN AUTHENTICATION DESIGN

Use a split-screen layout.

Conceptually:

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   LEFT: ADVENTURE VISUAL     │   RIGHT: AUTHENTICATION      │
│                              │                              │
│   Mountains / trekking       │   Login / Register           │
│   Atmospheric effects        │   Clean inputs               │
│   TMA branding               │   Strong CTA                 │
│   Animated trail             │   Supporting information     │
│                              │                              │
└─────────────────────────────────────────────────────────────┘
```

Suggested proportions:

- Left: approximately 50–55%
- Right: approximately 45–50%

Use design judgment rather than rigidly following these values.

The composition should feel balanced and intentional.

---

# 5. LEFT SIDE: ADVENTURE EXPERIENCE

The left side should be the memorable visual portion of the authentication experience.

Create a cinematic trekking-inspired environment communicating:

- Mountains
- Exploration
- Adventure
- Travel
- Trails
- Nature
- Discovery

Do not simply place one static mountain image.

Create depth using:

- Distant mountains
- Foreground terrain
- Mountain silhouettes
- Sky gradient
- Fog
- Clouds
- Atmospheric layers
- Subtle lighting

---

# 6. LEFT-SIDE ANIMATION

Add tasteful, slow animations such as:

- Slowly moving clouds
- Drifting mist
- Floating particles
- Subtle mountain parallax
- Moving sunlight glow
- Distant birds
- Animated trekking route
- Floating topographic contour lines

Animations should be:

- Slow
- Smooth
- Subtle
- Premium

The goal is cinematic motion, not distracting animation.

Respect accessibility and usability. Avoid excessive motion.

---

# 7. OPTIONAL ANIMATED TREKKING ROUTE

Consider an elegant animated trekking route/path.

For example:

```text
START ●──────────────╮
                     ╲
                      ╲────────● SUMMIT
```

The route can appear as if it is slowly being drawn.

Possible technologies:

- SVG
- CSS
- JavaScript
- SVG stroke animation

The effect should remain subtle.

---

# 8. LEFT-SIDE BRANDING

Integrate TMA branding naturally into the adventure scene.

Possible concept:

```text
TMA

Find your trail.
Discover your next adventure.
```

Create original copy rather than blindly copying this example.

The branding should feel integrated into the visual environment instead of appearing as a random text block.

---

# 9. OPTIONAL DATABASE-DRIVEN INFORMATION

A small informational panel may be included, for example:

```text
↗ 120+ Adventures
◎ Multiple Destinations
✓ Verified Trek Staff
```

However:

**Never invent fake statistics.**

If actual database-driven statistics exist, use them.

Otherwise omit the statistics completely.

---

# 10. RIGHT-SIDE AUTHENTICATION WORKSPACE

The right side should be:

- Bright
- Clean
- Elegant
- Minimal
- Highly readable
- Focused

Do not use another oversized floating card similar to the old design.

Instead, create a polished authentication workspace.

Example:

```text
Welcome back

Continue your journey with TMA.

Email
[________________________]

Password
[________________________]

□ Remember me          Forgot password?

[          Log in          ]

New to TMA?
Create an account
```

Registration must use the exact same visual language.

---

# 11. LOGIN PAGE

Redesign the Login page completely.

Include:

- TMA branding/logo
- Welcome heading
- Supporting text
- Email
- Password
- Password visibility toggle
- Remember me
- Forgot password if backend support exists
- Login CTA
- Register link

Do not overstuff the page.

The complete Login form should comfortably fit within the desktop viewport.

---

# 12. REGISTRATION PAGE

The Registration page must use the same design system as Login.

It should not look like a separate website.

The final registration fields should include:

### Basic information

- Full Name
- Phone
- Email

### Additional profile information

- Date of Birth
- Gender
- City

### Account information

- Account Type
- Password
- Confirm Password

---

# 13. REGISTRATION LAYOUT

Use an efficient desktop layout.

For example:

```text
Full Name              Phone
[______________]       [______________]

Email
[____________________________]

Date of Birth          Gender
[______________]       [______________]

City
[____________________________]

Account Type
[ Trekker ] [ Trek Staff ]

Password               Confirm Password
[______________]       [______________]

[        Create Account        ]
```

The exact layout can change according to the final design.

The important requirement is that the form remains:

- Clean
- Comfortable
- Readable
- Efficient
- Responsive

On desktop, use two-column fields where appropriate.

On mobile, switch to a single-column layout.

---

# 14. ACCOUNT TYPE

Clearly communicate the account type.

Preferred UI:

```text
I am joining as

┌──────────────────────┐
│  Trekker             │
│  Book and explore    │
└──────────────────────┘

┌──────────────────────┐
│  Trek Staff          │
│  Lead adventures     │
└──────────────────────┘
```

Use Bootstrap Icons or SVG rather than unnecessary emoji.

The role selector must remain compatible with the existing backend role system.

---

# 15. STAFF REGISTRATION

Staff registration should collect useful information as well.

At minimum, consider:

- Full Name
- Phone
- Email
- Date of Birth
- Gender
- City
- Password
- Confirm Password

Clearly communicate:

> Staff applications require administrator approval before dashboard access.

Unapproved staff must not receive access to staff operations.

Preserve the existing approval/blacklist workflow.

---

# 16. NEW PROFILE FIELDS

The underlying user/staff profile model must support:

```text
full_name
email
phone
date_of_birth
gender
city
password_hash
role
status
created_at
updated_at
```

Use the actual architecture already present in the application.

Do not blindly create a new model if an existing shared model is already appropriate.

If Users and Staff use separate models, update both where necessary.

If a shared User model is already used for all roles, extend it carefully.

---

# 17. DATABASE IS THE SINGLE SOURCE OF TRUTH

Do not implement the new fields independently in:

- Signup
- Profile
- Admin
- Seed data

Instead:

```text
Database Model
      ↓
Validation
      ↓
Registration
      ↓
Profile
      ↓
Edit Profile
      ↓
Admin Management
      ↓
Dashboards
      ↓
Bookings where relevant
      ↓
Seed Data
      ↓
Tests
```

Every layer must remain synchronized.

Whenever a new profile field is introduced, trace it through the entire application.

---

# 18. EMAIL IMMUTABILITY

This is a strict business rule.

After account creation:

> **The account email address cannot be changed by anyone through normal profile editing.**

This applies to:

- Trekker
- Staff
- Admin

Users may update other profile information, but the account email must remain permanently associated with the account.

---

# 19. EMAIL IMMUTABILITY: FRONTEND

On profile/edit-profile pages, show:

```text
Email
admin@example.com

🔒 Email cannot be changed
```

Use a professional locked/read-only presentation.

Do not make it look like a broken form field.

Do not rely only on HTML `disabled` or `readonly`.

---

# 20. EMAIL IMMUTABILITY: BACKEND

The backend must independently enforce immutability.

For example, if someone manually submits:

```text
POST /profile/update
email=attacker@example.com
```

the backend must reject or ignore the attempted email modification.

Never trust the frontend.

Email must not be exposed as a writable property in profile-update business logic.

---

# 21. EMAIL DATABASE CONSTRAINT

The email should remain unique and non-null where required by the existing architecture.

For example:

```python
email = db.Column(
    db.String(...),
    unique=True,
    nullable=False
)
```

Use the existing model conventions.

Email immutability should be protected through:

1. Frontend
2. Flask route
3. Business/service logic
4. Database design where appropriate

---

# 22. PROFILE SYSTEM

Every account should have a complete profile page.

Example:

```text
Profile
────────────────────────

Profile Photo / Avatar

Full Name
Phone
Email 🔒
Date of Birth
Gender
City

Account Status
Member Since

[ Edit Profile ]
[ Change Password ]
```

Use the same premium TMA visual language as the authentication pages.

---

# 23. USER PROFILE

Users should be able to view:

- Full Name
- Phone
- Email
- Date of Birth
- Gender
- City
- Account status
- Member since
- Role where appropriate
- Profile avatar where supported

Users may edit:

- Full Name
- Phone
- Date of Birth
- Gender
- City
- Profile image if supported

Users cannot edit:

- Email
- User ID
- Role
- Account creation date
- System status
- Admin-controlled fields

---

# 24. STAFF PROFILE

Staff should have equivalent profile functionality.

Staff can update:

- Full Name
- Phone
- Date of Birth
- Gender
- City
- Profile image if supported

Staff cannot update:

- Email
- Staff ID
- Role
- Approval state
- Blacklist/deactivation state
- System timestamps

Staff must never be able to modify administrator-controlled account properties.

---

# 25. ADMIN PROFILE

Admin must have a complete profile page as well.

Admin can update:

- Full Name
- Phone
- Date of Birth
- Gender
- City
- Profile image if supported
- Password through the password workflow

Admin email remains immutable.

---

# 26. ADMIN USER PROFILE MANAGEMENT

Admin must be able to open a user's profile from the admin panel and manage permitted information.

Example:

```text
User Profile
────────────────────────

Name
[________________]

Email
[admin@example.com] 🔒

Phone
[________________]

Date of Birth
[________________]

Gender
[________________]

City
[________________]

Account Status
[ Active ▼ ]

Role
Trekker

[ Save Changes ]
```

Admin may update:

- Name
- Phone
- Date of Birth
- Gender
- City
- Account status
- Password through a dedicated reset mechanism

Admin must not change:

- User email
- User ID
- Creation timestamp

Do not expose role editing unless the existing permission architecture explicitly supports controlled role management.

---

# 27. ADMIN STAFF PROFILE MANAGEMENT

Admin must also be able to manage Staff profiles.

Admin may update:

- Full Name
- Phone
- Date of Birth
- Gender
- City
- Account status
- Approval state where applicable
- Password through controlled reset

Email remains immutable.

Preserve existing staff approval and blacklist/deactivation rules.

---

# 28. USER-CONTROLLED VS SYSTEM-CONTROLLED DATA

Clearly separate:

### User-controlled

- Name
- Phone
- Date of Birth
- Gender
- City
- Profile image where supported

### Admin/system-controlled

- Email
- User/Staff ID
- Role
- Account status
- Approval status
- Creation timestamp
- Other system fields

Do not accidentally expose system-controlled fields through generic profile-update forms.

---

# 29. PASSWORD MANAGEMENT

Separate profile editing from password changes.

Create a dedicated:

**Change Password**

workflow.

Example:

```text
Current Password
[________________]

New Password
[________________]

Confirm New Password
[________________]

[ Update Password ]
```

Requirements:

- Verify current password for normal users/staff.
- Securely hash new passwords.
- Never store plaintext passwords.
- Never show passwords on profile pages.
- Never expose password hashes.
- Admin may have controlled password-reset capability for other accounts.

---

# 30. ADMIN PASSWORD RESET

Admin may reset another user's/staff member's password when required.

Never:

- Display the existing password.
- Retrieve the existing password.
- Decrypt passwords.
- Store plaintext passwords.

Always create/store a new secure password hash.

Prefer a dedicated:

```text
Reset Password
```

action rather than putting password fields inside every normal profile-edit form.

---

# 31. AUTHENTICATION FUNCTIONALITY

Do not replace existing backend authentication with fake frontend interactions.

Login must continue to work as:

```text
Form
 ↓
Flask route
 ↓
Validation
 ↓
Authentication
 ↓
Session
 ↓
Redirect
```

Registration must continue to work as:

```text
Form
 ↓
Flask route
 ↓
Validation
 ↓
Account creation
 ↓
Redirect
```

Preserve:

- Login logic
- Registration logic
- User roles
- Staff registration
- Admin authentication
- Password hashing
- Flash messages
- Redirect behavior
- Session handling
- Staff approval
- Existing access-control rules

---

# 32. FORM VALIDATION

Implement proper server-side validation.

### Name

- Required
- Reasonable length
- Reject obviously invalid input

### Phone

- Validate format appropriately
- Follow the existing product requirement for required/optional status

### Email

- Required
- Valid format
- Unique
- Normalize case where appropriate

### Date of Birth

- Valid date
- Must not be in the future

### Gender

Only allow defined values such as:

- Male
- Female
- Non-binary
- Prefer not to say

Do not impose unnecessary restrictions based on gender.

### City

- Reasonable length
- Sanitize appropriately

### Password

Use sensible password requirements.

### Confirm Password

Must exactly match the password.

Backend validation remains authoritative.

---

# 33. FORM UX

Inputs should have:

- Clear labels
- Clean borders
- Consistent height
- Subtle focus glow
- Smooth transitions
- Clear validation states

States:

```text
Normal → subtle border
Hover → slightly stronger border
Focus → TMA accent + subtle glow
Error → clear error state
Success → clear success state
```

Do not rely only on placeholders.

Maintain accessible labels.

---

# 34. PASSWORD VISIBILITY

Keep password visibility functionality.

Use a modern eye icon.

Allow switching between:

- Password hidden
- Password visible

The toggle must not break the input layout.

---

# 35. VALIDATION UX

Display errors close to the relevant field.

For example:

```text
Password
[____________________]

Password must contain at least 8 characters.
```

Avoid ugly browser-default error presentation where possible.

However, frontend validation must never replace backend validation.

---

# 36. PAGE TRANSITIONS

Add subtle transitions between Login and Register.

Possible effects:

- Fade
- Slight slide
- Opacity
- Small scale

Keep transitions around a few hundred milliseconds.

Never make users wait several seconds.

---

# 37. AUTHENTICATION PAGE LOAD ANIMATION

On page load:

### Left side

Animate:

- Background layers
- Mountains
- Clouds
- Branding
- Route path

### Right side

Use subtle:

```css
opacity: 0 → 1;
transform: translateY(12px) → translateY(0);
```

Keep the animation short and unobtrusive.

---

# 38. PARALLAX / DEPTH

Where appropriate:

- Foreground mountain: slower movement
- Background mountain: very slow movement
- Clouds: continuous slow movement

The effect should create cinematic depth without affecting usability.

Respect reduced-motion preferences where practical.

---

# 39. COLOR SYSTEM

Continue the existing TMA identity while making it more sophisticated.

Use a coherent palette around:

- Deep forest green
- Muted sage
- Warm off-white
- Charcoal
- Soft grey
- Earthy accents

Do not blindly use these exact colors.

The final design should have strong contrast and readability.

---

# 40. NAVBAR

The current public navbar contributes to the viewport problem.

Do not preserve it simply because it already exists.

Choose between:

### Option A

A minimal authentication header:

```text
TMA                              Back to Explore
```

### Option B

Remove the standard navbar and integrate TMA branding directly into the split-screen experience.

Choose whichever produces the strongest premium result.

---

# 41. RESPONSIVE DESIGN

### Desktop

```text
┌──────────── LEFT ────────────┬────────── RIGHT ──────────┐
│                              │                          │
│   Adventure Environment      │      Authentication      │
│                              │                          │
└──────────────────────────────┴──────────────────────────┘
```

### Tablet

Use an appropriately resized split layout.

### Mobile

Stack intelligently:

```text
┌─────────────────────────┐
│     TMA / Adventure     │
│     Compact Hero        │
├─────────────────────────┤
│                         │
│      Auth Form          │
│                         │
└─────────────────────────┘
```

On mobile, the adventure section may become a compact hero/banner.

Ensure:

- No horizontal overflow
- Inputs remain usable
- Buttons remain accessible
- Text does not overflow
- Vertical scrolling occurs only when genuinely necessary
- Registration switches to one-column layout

---

# 42. ACCESSIBILITY

Ensure:

- Proper labels
- Keyboard navigation
- Visible focus states
- Sufficient color contrast
- Accessible button labels
- Meaningful alt text
- Appropriate semantic HTML
- ARIA only where necessary

Do not sacrifice accessibility for aesthetics.

---

# 43. PROFILE PHOTO / AVATAR

A profile image may be implemented if it fits the existing architecture.

If implementing uploads:

- Validate extension
- Validate MIME type
- Validate file size
- Generate safe filenames
- Never trust user-provided filenames
- Store uploads safely
- Prevent executable uploads
- Provide a default avatar

If uploads introduce unnecessary complexity, use a generated initials avatar instead.

---

# 44. PROFILE DATA PROPAGATION

Once the new profile fields exist, use them consistently throughout the application.

Examples:

### Dashboard

```text
Welcome back, Divy
```

### Booking

```text
Booked by
Full Name
```

### Admin

```text
Full Name
Email
City
Account Status
```

### Staff participant list

```text
Name
Phone
City
Booking Status
```

Only expose information appropriate to the context.

Do not publicly expose unnecessary personal information.

---

# 45. SECURITY AND PRIVACY

Enforce backend authorization.

### Users

Users may only access their own private profile.

### Staff

Staff may only access information required for their operational responsibilities.

### Admin

Admin may access necessary account-management information.

### Public users

Public trek pages must not expose sensitive participant details.

Do not expose unnecessary personal information anywhere in the application.

---

# 46. DATABASE MIGRATION

Because new fields are being introduced, update the actual SQLite database.

Do not only modify SQLAlchemy models.

Existing records must remain valid.

Preserve:

- Existing names
- Existing email addresses
- Existing passwords
- Existing roles
- Existing bookings
- Existing trek relationships
- Existing assignments
- Existing reviews

For existing records without the new information, use nullable defaults:

```text
date_of_birth = NULL
gender = NULL
city = NULL
```

Do not invent personal information for existing accounts.

Handle migration/setup cleanly according to the current project architecture.

---

# 47. SEED DATA

Update the development/demo seed process.

New seed records must include the new profile fields.

Use obviously fake/demo data.

Example:

```text
Demo Trekker
Email: trekker@example.com
Phone: +91XXXXXXXXXX
DOB: 2002-05-14
Gender: Prefer not to say
City: Chennai
Role: Trekker
```

Staff:

```text
Demo Trek Guide
Email: staff@example.com
Phone: +91XXXXXXXXXX
DOB: 1995-08-20
Gender: Prefer not to say
City: Dehradun
Role: Trek Staff
Approval: Approved
```

Admin:

```text
TMA Administrator
Email: admin@example.com
City: Chennai
Role: Admin
```

Do not overwrite real credentials or real user data.

---

# 48. REALISTIC DEMO DATABASE

The development database should look realistically populated.

Maintain coherent fake data for:

- Admin
- Staff
- Users
- Treks
- Bookings
- Reviews
- Notifications
- Assignments

Relationships must be logically consistent.

For example:

- Booking users must exist.
- Assigned staff must exist.
- Staff must be approved before assignment.
- Completed bookings must correspond to appropriate treks.
- Reviews should correspond to users who completed the trek.
- Existing relationships must remain valid.

Do not create impossible database states.

---

# 49. ROUTE ARCHITECTURE

Use the existing route conventions where appropriate.

Possible structure:

```text
/profile
/profile/edit
/profile/password
```

Admin:

```text
/admin/users/<id>
/admin/users/<id>/edit
/admin/users/<id>/reset-password
```

Staff:

```text
/staff/profile
/staff/profile/edit
/staff/profile/password
```

Do not duplicate unnecessary business logic.

---

# 50. APPLICATION STRUCTURE

Adapt the existing Flask/Jinja architecture.

A possible structure:

```text
templates/
    auth/
        login.html
        register.html
    profile/
        profile.html
        edit_profile.html
        change_password.html

static/
    css/
        auth.css
        profile.css

    js/
        auth.js
        profile.js
```

Adapt this to the actual project structure instead of forcing a new architecture.

Use:

- Flask
- Jinja2
- Bootstrap
- Bootstrap Icons
- CSS
- SVG
- JavaScript

Do not introduce React, Vue, or another frontend framework.

---

# 51. DO NOT CREATE STATIC MOCKUPS

This is an actual working Flask application.

The UI must connect to the existing backend.

Do not create fake frontend-only Login/Register interactions.

Do not replace Flask routes with mock JavaScript behavior.

All forms must submit through the actual Flask backend and preserve existing authentication/session behavior.

---

# 52. DO NOT BREAK EXISTING APPLICATION FUNCTIONALITY

Before and after the redesign, preserve:

- Authentication
- Role-based access
- Admin access
- Staff approval
- Staff operations
- User operations
- Trek management
- Booking functionality
- Assignments
- Reviews
- Notifications
- Existing redirects
- Flash messages
- Sessions

Modify backend logic only where required to support the new system or fix genuine issues.

---

# 53. ADMIN MANAGEMENT UI

Admin pages should not look like raw Bootstrap tables.

When Admin opens a user/staff member, provide a professional profile/detail view.

Include where relevant:

- Avatar
- Full Name
- Email
- Role
- Status
- Registration date
- Contact information
- Booking statistics
- Trek history
- Assigned treks for staff
- Recent activity
- Edit action
- Password reset action
- Status management

Email must visibly appear locked/read-only.

---

# 54. DESIGN CONSISTENCY

Login, Register, Profile, Edit Profile, Change Password, and Admin Profile Management must belong to the same product.

Share:

- Typography
- Colors
- Spacing
- Button styles
- Icons
- Form styles
- Focus states
- Animation language
- Visual hierarchy
- Border radius philosophy
- Overall TMA design language

Do not create separate visual systems for each page.

---

# 55. OPTIONAL CREATIVE DIRECTION

A strong visual concept is:

## "Start Your Next Trail"

Left:

A mountain landscape with an animated trekking route moving toward a summit.

Right:

The authentication form.

On load:

- Route draws itself
- Summit marker subtly pulses
- Clouds move slowly
- Authentication form fades into view

The visual metaphor should communicate:

**Login → Start your adventure**

Use this only as inspiration. Do not implement it in an overly literal or childish way.

---

# 56. TESTS

Add or update tests for the complete functionality.

### Registration

Test:

- New user registration
- New staff registration
- Duplicate email
- Invalid email
- Password mismatch
- Invalid DOB
- Invalid gender
- Invalid profile values
- Required fields

### User Profile

Test:

- User can update name
- User can update phone
- User can update DOB
- User can update gender
- User can update city
- User cannot update email
- User cannot modify role
- User cannot modify system status

### Staff

Test:

- Staff can update allowed fields
- Staff cannot update email
- Staff cannot modify approval state
- Staff cannot modify system-controlled fields

### Admin

Test:

- Admin can edit users
- Admin can edit staff
- Admin cannot change email
- Admin cannot expose password
- Admin can perform controlled password reset
- Admin permissions remain enforced

---

# 57. EMAIL IMMUTABILITY REGRESSION TEST

Create an explicit test for malicious/manual email modification.

Example:

```python
old_email = user.email

submit_profile_update(
    email="changed@example.com",
    ...
)

assert user.email == old_email
```

This must remain true even when the request is manually constructed rather than submitted through the normal UI.

---

# 58. PASSWORD SECURITY TESTS

Verify:

- Passwords are never stored in plaintext.
- New passwords are hashed.
- Existing password hashes remain valid.
- Password hashes are never rendered in templates.
- Normal users/staff must provide the current password before changing it.
- Admin password reset creates a new secure hash.
- Existing passwords cannot be retrieved/decrypted.

---

# 59. DOCUMENTATION

Update README/documentation with:

- Extended registration
- New profile fields
- Profile management
- Immutable email policy
- Admin profile management
- Staff profile management
- Password management
- Database fields
- Migration/setup process
- Seed data
- New routes
- Testing instructions

---

# 60. FINAL VISUAL QUALITY CHECK

Test Login, Register, Profile, Edit Profile, Change Password, and Admin profile pages at:

- 1920×1080
- 1600×900
- 1440×900
- 1366×768
- 1280×720
- Tablet
- Mobile

Verify:

- No unnecessary desktop scrolling
- Complete Login form visible
- Registration layout is efficient
- Profile pages are balanced
- No horizontal overflow
- Animations are smooth
- Animations do not interfere with interaction
- Forms work
- Validation works
- Links work
- Password visibility works
- Password change works
- Admin reset works
- Email remains immutable
- Responsive behavior works
- Browser resizing does not break layouts

---

# 61. FINAL ACCEPTANCE CRITERIA

The implementation is complete only when all of the following are true:

✅ Login has been completely redesigned.

✅ Registration has been completely redesigned.

✅ Authentication uses a premium split-screen adventure design.

✅ Login fits naturally within the desktop viewport without unnecessary scrolling.

✅ Registration uses efficient responsive field layouts.

✅ Registration collects Full Name, Phone, Email, DOB, Gender, City, Account Type, Password and Confirm Password.

✅ Staff registration supports the required profile information.

✅ New profile information is stored in SQLite.

✅ Existing users remain valid.

✅ Existing bookings, treks, assignments and relationships remain intact.

✅ Seed/demo data contains the new profile fields.

✅ Existing records are not populated with invented personal information.

✅ User profile displays all relevant information.

✅ User can edit permitted profile fields.

✅ User cannot change email.

✅ Staff profile displays relevant information.

✅ Staff can edit permitted profile fields.

✅ Staff cannot change email or approval/system fields.

✅ Admin has a complete profile.

✅ Admin can edit permitted information.

✅ Admin can manage permitted User profiles.

✅ Admin can manage permitted Staff profiles.

✅ Admin cannot change account email.

✅ Admin can perform controlled password reset.

✅ Passwords remain securely hashed.

✅ Password hashes are never exposed.

✅ Backend prevents email modification through crafted requests.

✅ New profile information propagates consistently through the application.

✅ Appropriate privacy restrictions are enforced.

✅ Database schema is updated.

✅ Existing database data is preserved.

✅ Seed logic is updated.

✅ Routes are updated.

✅ Validation is updated.

✅ Templates are updated.

✅ CSS is updated.

✅ JavaScript is updated where required.

✅ Tests are updated.

✅ Documentation is updated.

✅ Authentication functionality remains intact.

---

# 62. FINAL IMPLEMENTATION RULE

Do not only modify the signup HTML.

This is an **end-to-end feature and design change**.

Whenever a new user/staff profile field is introduced, trace it through everything that depends on the profile model:

```text
Models
 ↓
Database
 ↓
Migration / Setup
 ↓
Validation
 ↓
Authentication
 ↓
Registration
 ↓
Profile Display
 ↓
Profile Editing
 ↓
Password Management
 ↓
Admin Management
 ↓
Dashboards
 ↓
Bookings
 ↓
Seed Data
 ↓
Templates
 ↓
CSS
 ↓
JavaScript
 ↓
Tests
 ↓
Documentation
```

Do not leave partially implemented fields or disconnected UI.

The final result should feel like **one coherent, professionally engineered TMA system**, not a collection of unrelated changes.

The most important business rule remains:

> **Email addresses are immutable after account creation for every role: Trekker, Staff, and Admin.**

The most important design rule remains:

> **Create a premium, immersive trekking authentication experience while keeping the actual Flask backend, database, authentication, authorization, validation, and existing application functionality fully operational.**

Build the actual implementation in the existing Flask application. Do not return only a concept, static mockup, or design proposal.