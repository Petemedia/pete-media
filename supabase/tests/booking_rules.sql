\set ON_ERROR_STOP on
insert into auth.users values ('00000000-0000-0000-0000-000000000001'),('00000000-0000-0000-0000-000000000002'),('00000000-0000-0000-0000-000000000003');
insert into staff values ('00000000-0000-0000-0000-000000000001','owner','Test Owner'),('00000000-0000-0000-0000-000000000002','staff','Test Staff');

create function must_fail(q text, label text) returns text language plpgsql as $$
declare n int;
begin
  begin execute q; get diagnostics n = row_count;
  exception when others then return 'PASS ' || label || ' (' || sqlerrm || ')'; end;
  if n = 0 then return 'PASS ' || label || ' (0 rows)'; end if;
  raise exception 'FAIL %', label;
end $$;
create function must_be(ok boolean, label text) returns text language plpgsql as $$
begin if ok is not true then raise exception 'FAIL %', label; end if; return 'PASS ' || label; end $$;

set role authenticated;
set test.uid = '00000000-0000-0000-0000-000000000002'; -- staff
insert into clients(id,full_name,phone) values ('10000000-0000-0000-0000-000000000001','Test Client','08000000000');
insert into bookings(id,client_id,category,starts_at,ends_at,location) values
 ('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','Wedding','2030-01-10 09:00+01','2030-01-10 15:00+01','Eket'),
 ('20000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000001','Wedding','2030-01-10 12:00+01','2030-01-10 18:00+01','Uyo');
select must_fail($q$insert into bookings(client_id,category,starts_at,ends_at,location,status) values ('10000000-0000-0000-0000-000000000001','X','2031-01-01','2031-01-02','Eket','confirmed')$q$, 'cannot create a booking as confirmed');
select must_fail($q$update bookings set status='confirmed' where id='20000000-0000-0000-0000-000000000001'$q$, 'enquiry cannot jump to confirmed');
insert into quotations(id,booking_id,total,deposit_required,details) select ('30000000-0000-0000-0000-00000000000'||n)::uuid, ('20000000-0000-0000-0000-00000000000'||n)::uuid, 1000, 500, 'test figures' from generate_series(1,2) n;
update bookings set status='quoted';
select must_fail($q$update quotations set discount=100, accepted=true where id='30000000-0000-0000-0000-000000000001'$q$, 'staff cannot approve a discount');
update quotations set accepted=true;
select must_fail($q$update quotations set deposit_required=1$q$, 'accepted quotation is locked');
update bookings set status='pending_payment';
select must_be((select count(*)=0 from calendar_events), 'no calendar entry before payment');
insert into payments(booking_id,amount,reference) values ('20000000-0000-0000-0000-000000000001',500,'T1'),('20000000-0000-0000-0000-000000000002',500,'T2');
select must_fail($q$insert into payments(booking_id,amount,reference,verified_at) values ('20000000-0000-0000-0000-000000000001',1,'T3',now())$q$, 'payment cannot arrive pre-verified');
select must_fail($q$update payments set verified_at=now()$q$, 'staff cannot verify payment');
select must_fail($q$update staff set role='owner' where user_id=auth.uid()$q$, 'staff cannot promote themselves');
select must_fail($q$insert into calendar_events values ('20000000-0000-0000-0000-000000000001')$q$, 'calendar cannot be written by hand');

set test.uid = '00000000-0000-0000-0000-000000000001'; -- owner
select must_fail($q$update bookings set status='confirmed' where id='20000000-0000-0000-0000-000000000001'$q$, 'unverified payment does not confirm');
update payments set verified_at=now();
update bookings set status='confirmed' where id='20000000-0000-0000-0000-000000000001';
select must_be((select count(*)=1 from calendar_events), 'one calendar entry after confirmation');
select must_fail($q$update bookings set status='confirmed' where id='20000000-0000-0000-0000-000000000002'$q$, 'overlapping confirmed booking blocked');
select must_fail($q$update payments set amount=1$q$, 'verified payment is immutable');
select must_fail($q$delete from audit_log$q$, 'audit log cannot be deleted');
update bookings set status='cancelled' where id='20000000-0000-0000-0000-000000000001';
select must_be((select state='to_cancel' from calendar_events), 'cancellation flags the calendar entry');

set test.uid = '00000000-0000-0000-0000-000000000003'; -- signed in, not staff
select must_be((select count(*)=0 from clients), 'non-staff sees no clients');
select must_fail($q$insert into clients(full_name,phone) values ('x','08000000000')$q$, 'non-staff cannot write');
reset role; set role anon;
select must_fail($q$select * from clients$q$, 'public has no access');
