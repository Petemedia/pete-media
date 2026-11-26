# Database and API
Schema: `supabase/migrations/0001_booking_core.sql`. **Not applied to any live project**; tested on local PostgreSQL 16 with a stand-in for Supabase auth, so re-test on Supabase.

Flow: enquiry → quoted → pending_payment → confirmed → completed (or cancelled).
Enforced: verified payments must cover the deposit; only owner/admin verify and confirm; only owner approves discounts and records refunds; no overlapping confirmed bookings; one calendar record per booking, only after confirmation; verified payments immutable; audit log; public role has no access.

Limitations: one shared calendar (two crews cannot be booked at the same time); a refund does not change a booking's status, so the owner cancels it manually; custom or high-value escalation is a procedure, not enforced.

Setup: create a Supabase project, run the migration in the SQL editor, create your user under Authentication, then
`insert into staff values ('<your user id>', 'owner', 'Emmanuel Denis Peter');`

API: no custom endpoints exist. Supabase would expose the tables to signed-in staff under the row-level policies.
A public enquiry endpoint still needs a server function with validation, CAPTCHA and rate limiting.
