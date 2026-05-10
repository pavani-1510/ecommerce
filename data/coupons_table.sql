-- ========================================
-- COUPONS TABLE - Discount coupon codes
-- ========================================
-- Run this SQL in Supabase SQL Editor to create the coupons table

-- Create coupons table
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

-- Enable Row Level Security
alter table public.coupons enable row level security;

-- Grant permissions (this is critical for RLS to work)
-- For development: allow authenticated users full access
grant all on table public.coupons to authenticated;
grant all on table public.coupons to anon;

-- Policy: Users can read active coupons
drop policy if exists coupons_public_read on public.coupons;
create policy coupons_public_read
on public.coupons
for select
to anon, authenticated
using (true);  -- Allow all reads for now (can restrict to is_active later)

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

-- Optional: Insert sample coupons for testing
-- insert into public.coupons (code, description, discount_type, discount_value, min_amount, max_discount, is_active)
-- values 
--     ('WELCOME10', '10% off on orders above ₹500', 'percent', 10, 500, 300, true),
--     ('SAVE100', '₹100 off on orders above ₹1000', 'flat', 100, 1000, 100, true),
--     ('MANTRA15', '15% off on orders above ₹1500', 'percent', 15, 1500, 500, true);
