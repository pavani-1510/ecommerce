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
--   and tablename in ('categories', 'products', 'users', 'otps', 'support_tickets', 'support_messages', 'carts', 'orders', 'order_items', 'payments', 'coupons')
-- order by tablename, policyname;

-- ========================================
-- COUPONS TABLE - Discount coupon codes
-- ========================================

-- Create coupons table if it doesn't exist
create table if not exists public.coupons (
    id uuid primary key default gen_random_uuid(),
    code varchar(50) unique not null,
    description text,
    discount_type varchar(20) not null check (discount_type in ('percent', 'flat')),
    discount_value decimal(10, 2) not null,
    min_amount decimal(10, 2),
    max_discount decimal(10, 2),
    usage_limit integer,
    usage_count integer default 0,
    is_active boolean default true,
    expiry_date timestamp with time zone,
    created_at timestamp with time zone default now(),
    updated_at timestamp with time zone default now()
);

-- Enable RLS on coupons
alter table public.coupons enable row level security;

-- Grant permissions for reading active coupons (public/anon can view)
grant select on table public.coupons to anon, authenticated;

-- Grant permissions (critical for RLS)
grant all on table public.coupons to authenticated;
grant all on table public.coupons to anon;

-- Policy: Anyone can read coupons
drop policy if exists coupons_public_read on public.coupons;
create policy coupons_public_read
on public.coupons
for select
to anon, authenticated
using (true);

-- Policy: Authenticated users can insert coupons
drop policy if exists coupons_admin_insert on public.coupons;
create policy coupons_admin_insert
on public.coupons
for insert
to authenticated
with check (true);

-- Policy: Authenticated users can update coupons
drop policy if exists coupons_admin_update on public.coupons;
create policy coupons_admin_update
on public.coupons
for update
to authenticated
using (true)
with check (true);

-- Policy: Authenticated users can delete coupons
drop policy if exists coupons_admin_delete on public.coupons;
create policy coupons_admin_delete
on public.coupons
for delete
to authenticated
using (true);

-- Create indexes for faster queries
create index if not exists coupons_code_idx on public.coupons(code);
create index if not exists coupons_is_active_idx on public.coupons(is_active);
create index if not exists coupons_expiry_idx on public.coupons(expiry_date);
