#!/usr/bin/env bash
# Needs a local PostgreSQL where you can create databases (set PGHOST/PGUSER as required).
set -euo pipefail
cd "$(dirname "$0")/.."
db=pm_test_$$
createdb "$db"; trap 'dropdb "$db"' EXIT
for f in supabase/tests/local_auth_stub.sql supabase/migrations/*.sql supabase/tests/booking_rules.sql; do
  psql -q -v ON_ERROR_STOP=1 -d "$db" -At -f "$f"
done
