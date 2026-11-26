-- Pete Media booking core. Target: Supabase (PostgreSQL 15+). Business rules are enforced here, not in the UI.
create extension if not exists btree_gist;

create type staff_role as enum ('owner','admin','staff');
create type booking_status as enum ('enquiry','quoted','pending_payment','confirmed','completed','cancelled');

create table staff (user_id uuid primary key references auth.users(id) on delete cascade, role staff_role not null, full_name text not null);

create function my_role() returns staff_role language sql stable security definer set search_path = public as
$$ select role from staff where user_id = auth.uid() $$;

create table clients (
  id uuid primary key default gen_random_uuid(),
  full_name text not null check (length(full_name) between 1 and 120),
  phone text not null check (length(phone) between 7 and 30),
  email text check (email is null or email like '%_@_%'),
  preferred_channel text not null default 'whatsapp' check (preferred_channel in ('whatsapp','phone','email')),
  notes text, created_at timestamptz not null default now());

create table bookings (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references clients(id),
  category text not null,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  time_zone text not null default 'Africa/Lagos',
  location text not null,
  coverage text, live_stream boolean, deliverables text, budget_range text, special_requests text,
  status booking_status not null default 'enquiry',
  created_at timestamptz not null default now(),
  check (ends_at > starts_at),
  -- no two confirmed bookings may overlap
  constraint no_double_booking exclude using gist (tstzrange(starts_at, ends_at) with &&) where (status = 'confirmed'));

create table quotations (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references bookings(id),
  currency text not null default 'NGN' check (currency in ('NGN','USD','GBP','EUR')),
  total numeric(14,2) not null check (total > 0),
  discount numeric(14,2) not null default 0 check (discount >= 0),
  discount_approved_by uuid,
  deposit_required numeric(14,2) not null check (deposit_required > 0),
  details text not null,
  accepted boolean not null default false,
  created_at timestamptz not null default now(),
  check (discount < total),
  check (deposit_required <= total - discount));
create unique index one_accepted_quote on quotations(booking_id) where accepted;

create table payments (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid not null references bookings(id),
  amount numeric(14,2) not null check (amount <> 0), -- negative = refund (owner only)
  currency text not null default 'NGN' check (currency in ('NGN','USD','GBP','EUR')),
  reference text not null unique,
  verified_at timestamptz, verified_by uuid,
  created_at timestamptz not null default now());

create table calendar_events (
  booking_id uuid primary key references bookings(id), -- one event per booking
  google_event_id text unique,
  state text not null default 'to_create' check (state in ('to_create','created','to_cancel','cancelled')));

create table audit_log (id bigserial primary key, at timestamptz not null default now(), actor uuid, table_name text not null, action text not null, row_data jsonb not null);

create function audit() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into audit_log(actor, table_name, action, row_data)
  values (auth.uid(), tg_table_name, tg_op, to_jsonb(case when tg_op = 'DELETE' then old else new end));
  return coalesce(new, old);
end $$;

create function guard_quotation() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'UPDATE' then
    if old.accepted then raise exception 'An accepted quotation cannot be changed'; end if;
  end if;
  if new.discount > 0 then
    if my_role() = 'owner' then new.discount_approved_by := auth.uid();
    elsif tg_op = 'UPDATE' and new.discount = old.discount and new.total = old.total then new.discount_approved_by := old.discount_approved_by;
    else new.discount_approved_by := null;
    end if;
  else new.discount_approved_by := null;
  end if;
  if new.accepted and new.discount > 0 and new.discount_approved_by is null then
    raise exception 'Discount requires owner approval';
  end if;
  return new;
end $$;

create function guard_payment() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.amount < 0 and coalesce(my_role() <> 'owner', true) then raise exception 'Only the owner can record a refund'; end if;
  if tg_op = 'INSERT' then
    if new.verified_at is not null or new.verified_by is not null then raise exception 'Record the payment first, then verify it'; end if;
  else
    if old.verified_at is not null then raise exception 'A verified payment cannot be changed'; end if;
    if new.verified_at is not null then
      if coalesce(my_role() not in ('owner','admin'), true) then raise exception 'Only the owner or an admin can verify payments'; end if;
      new.verified_at := now(); new.verified_by := auth.uid();
    else new.verified_by := null;
    end if;
  end if;
  return new;
end $$;

create function guard_booking() returns trigger language plpgsql security definer set search_path = public as $$
declare q quotations; paid numeric;
begin
  if tg_op = 'INSERT' then
    if new.status <> 'enquiry' then raise exception 'A new booking must start as an enquiry'; end if;
    return new;
  end if;
  if new.status = old.status then return new; end if;
  if not ( (old.status = 'enquiry' and new.status in ('quoted','cancelled'))
        or (old.status = 'quoted' and new.status in ('pending_payment','cancelled'))
        or (old.status = 'pending_payment' and new.status in ('confirmed','cancelled'))
        or (old.status = 'confirmed' and new.status in ('completed','cancelled'))) then
    raise exception 'Invalid status change: % to %', old.status, new.status;
  end if;
  if new.status = 'quoted' and not exists (select 1 from quotations where booking_id = new.id) then
    raise exception 'Create a quotation first';
  end if;
  if new.status in ('pending_payment','confirmed') then
    select * into q from quotations where booking_id = new.id and accepted;
    if q.id is null then raise exception 'An accepted quotation is required'; end if;
  end if;
  if new.status = 'confirmed' then
    if coalesce(my_role() not in ('owner','admin'), true) then raise exception 'Only the owner or an admin can confirm'; end if;
    select coalesce(sum(amount), 0) into paid from payments where booking_id = new.id and verified_at is not null and currency = q.currency;
    if paid < q.deposit_required then raise exception 'Verified payment is less than the required deposit'; end if;
  end if;
  return new;
end $$;

create function sync_calendar() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status = 'confirmed' and old.status <> 'confirmed' then
    insert into calendar_events(booking_id) values (new.id) on conflict (booking_id) do nothing;
  elsif new.status = 'cancelled' then
    update calendar_events set state = 'to_cancel' where booking_id = new.id;
  elsif new.status = 'confirmed' and (new.starts_at, new.ends_at, new.location) is distinct from (old.starts_at, old.ends_at, old.location) then
    update calendar_events set state = 'to_create' where booking_id = new.id;
  end if;
  return new;
end $$;

create trigger quotation_guard before insert or update on quotations for each row execute function guard_quotation();
create trigger payment_guard before insert or update on payments for each row execute function guard_payment();
create trigger booking_guard before insert or update on bookings for each row execute function guard_booking();
create trigger booking_calendar after update on bookings for each row execute function sync_calendar();

do $$ declare t text; begin
  foreach t in array array['staff','clients','bookings','quotations','payments','calendar_events'] loop
    execute format('create trigger audit_%I after insert or update or delete on %I for each row execute function audit()', t, t);
  end loop;
  foreach t in array array['staff','clients','bookings','quotations','payments','calendar_events','audit_log'] loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on %I from anon, authenticated', t);
  end loop;
end $$;

-- Least privilege: no deletes anywhere; the public (anon) role has no table access at all.
grant select, insert, update on staff, clients, bookings, quotations, payments to authenticated;
grant select, update on calendar_events to authenticated;
grant select on audit_log to authenticated;
grant usage on sequence audit_log_id_seq to authenticated;

create policy staff_read on staff for select to authenticated using (user_id = auth.uid() or my_role() = 'owner');
create policy staff_add on staff for insert to authenticated with check (my_role() = 'owner');
create policy staff_edit on staff for update to authenticated using (my_role() = 'owner') with check (my_role() = 'owner');
create policy clients_all on clients for all to authenticated using (my_role() is not null) with check (my_role() is not null);
create policy bookings_all on bookings for all to authenticated using (my_role() is not null) with check (my_role() is not null);
create policy quotes_all on quotations for all to authenticated using (my_role() is not null) with check (my_role() is not null);
create policy payments_all on payments for all to authenticated using (my_role() is not null) with check (my_role() is not null);
create policy calendar_read on calendar_events for select to authenticated using (my_role() is not null);
create policy calendar_edit on calendar_events for update to authenticated using (my_role() in ('owner','admin'));
create policy audit_read on audit_log for select to authenticated using (my_role() = 'owner');
