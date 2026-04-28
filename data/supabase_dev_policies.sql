-- Development-only RLS policies for publishable-key backend access.
-- WARNING: These policies are permissive and intended for local/dev testing.
-- For production, use SUPABASE_SERVICE_ROLE_KEY on backend and tighter policies.

-- Core privileges for PostgREST roles
grant usage on schema public to anon, authenticated;

-- -----------------------------
-- categories: public read
-- -----------------------------
alter table public.categories enable row level security;
grant select on table public.categories to anon, authenticated;

drop policy if exists categories_public_read on public.categories;
create policy categories_public_read
on public.categories
for select
to anon, authenticated
using (true);

-- -----------------------------
-- products: public read
-- -----------------------------
alter table public.products enable row level security;
grant select on table public.products to anon, authenticated;

drop policy if exists products_public_read on public.products;
create policy products_public_read
on public.products
for select
to anon, authenticated
using (true);

-- -----------------------------
-- users: register/login/profile fields used by app
-- -----------------------------
alter table public.users enable row level security;
grant select, insert, update on table public.users to anon, authenticated;

drop policy if exists users_dev_select on public.users;
create policy users_dev_select
on public.users
for select
to anon, authenticated
using (true);

drop policy if exists users_dev_insert on public.users;
create policy users_dev_insert
on public.users
for insert
to anon, authenticated
with check (true);

drop policy if exists users_dev_update on public.users;
create policy users_dev_update
on public.users
for update
to anon, authenticated
using (true)
with check (true);

-- -----------------------------
-- otps: send/verify OTP flow
-- -----------------------------
alter table public.otps enable row level security;
grant select, insert, update on table public.otps to anon, authenticated;

drop policy if exists otps_dev_select on public.otps;
create policy otps_dev_select
on public.otps
for select
to anon, authenticated
using (true);

drop policy if exists otps_dev_insert on public.otps;
create policy otps_dev_insert
on public.otps
for insert
to anon, authenticated
with check (true);

drop policy if exists otps_dev_update on public.otps;
create policy otps_dev_update
on public.otps
for update
to anon, authenticated
using (true)
with check (true);

-- -----------------------------
-- support_tickets: create/list/update support requests
-- -----------------------------
alter table public.support_tickets enable row level security;
grant select, insert, update on table public.support_tickets to anon, authenticated;

drop policy if exists support_tickets_dev_select on public.support_tickets;
create policy support_tickets_dev_select
on public.support_tickets
for select
to anon, authenticated
using (true);

drop policy if exists support_tickets_dev_insert on public.support_tickets;
create policy support_tickets_dev_insert
on public.support_tickets
for insert
to anon, authenticated
with check (true);

drop policy if exists support_tickets_dev_update on public.support_tickets;
create policy support_tickets_dev_update
on public.support_tickets
for update
to anon, authenticated
using (true)
with check (true);

-- -----------------------------
-- support_messages: ticket replies
-- -----------------------------
alter table public.support_messages enable row level security;
grant select, insert, update on table public.support_messages to anon, authenticated;

drop policy if exists support_messages_dev_select on public.support_messages;
create policy support_messages_dev_select
on public.support_messages
for select
to anon, authenticated
using (true);

drop policy if exists support_messages_dev_insert on public.support_messages;
create policy support_messages_dev_insert
on public.support_messages
for insert
to anon, authenticated
with check (true);

drop policy if exists support_messages_dev_update on public.support_messages;
create policy support_messages_dev_update
on public.support_messages
for update
to anon, authenticated
using (true)
with check (true);

-- -----------------------------
-- carts: add/view/update/remove cart items
-- -----------------------------
alter table public.carts enable row level security;
grant select, insert, update, delete on table public.carts to anon, authenticated;

drop policy if exists carts_dev_select on public.carts;
create policy carts_dev_select
on public.carts
for select
to anon, authenticated
using (true);

drop policy if exists carts_dev_insert on public.carts;
create policy carts_dev_insert
on public.carts
for insert
to anon, authenticated
with check (true);

drop policy if exists carts_dev_update on public.carts;
create policy carts_dev_update
on public.carts
for update
to anon, authenticated
using (true)
with check (true);

drop policy if exists carts_dev_delete on public.carts;
create policy carts_dev_delete
on public.carts
for delete
to anon, authenticated
using (true);

-- -----------------------------
-- orders: create/list user orders
-- -----------------------------
alter table public.orders enable row level security;
grant select, insert, update on table public.orders to anon, authenticated;

drop policy if exists orders_dev_select on public.orders;
create policy orders_dev_select
on public.orders
for select
to anon, authenticated
using (true);

drop policy if exists orders_dev_insert on public.orders;
create policy orders_dev_insert
on public.orders
for insert
to anon, authenticated
with check (true);

drop policy if exists orders_dev_update on public.orders;
create policy orders_dev_update
on public.orders
for update
to anon, authenticated
using (true)
with check (true);

-- -----------------------------
-- order_items: create/read order line items
-- -----------------------------
alter table public.order_items enable row level security;
grant select, insert, update on table public.order_items to anon, authenticated;

drop policy if exists order_items_dev_select on public.order_items;
create policy order_items_dev_select
on public.order_items
for select
to anon, authenticated
using (true);

drop policy if exists order_items_dev_insert on public.order_items;
create policy order_items_dev_insert
on public.order_items
for insert
to anon, authenticated
with check (true);

drop policy if exists order_items_dev_update on public.order_items;
create policy order_items_dev_update
on public.order_items
for update
to anon, authenticated
using (true)
with check (true);

-- -----------------------------
-- payments: create/read/update payment records
-- -----------------------------
alter table public.payments enable row level security;
grant select, insert, update on table public.payments to anon, authenticated;

drop policy if exists payments_dev_select on public.payments;
create policy payments_dev_select
on public.payments
for select
to anon, authenticated
using (true);

drop policy if exists payments_dev_insert on public.payments;
create policy payments_dev_insert
on public.payments
for insert
to anon, authenticated
with check (true);

drop policy if exists payments_dev_update on public.payments;
create policy payments_dev_update
on public.payments
for update
to anon, authenticated
using (true)
with check (true);

-- Optional: inspect applied policies
-- select policyname, schemaname, tablename, roles, cmd, qual, with_check
-- from pg_policies
-- where schemaname = 'public'
--   and tablename in ('categories', 'products', 'users', 'otps', 'support_tickets', 'support_messages', 'carts', 'orders', 'order_items', 'payments')
-- order by tablename, policyname;
