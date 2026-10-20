-- Структура данных каталога и история проверок.
-- Доступ ограничен владельцем записи через RLS.

create table public.catalog_items (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    article text not null check (length(article) between 1 and 256),
    manufacturer text not null check (length(manufacturer) between 1 and 256),
    product_group text not null check (length(product_group) between 1 and 256),
    created_at timestamptz not null default now()
);

create index catalog_items_owner_idx on public.catalog_items (owner_id);

create table public.validation_runs (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null references auth.users(id) on delete cascade,
    status text not null default 'pending'
        check (status in ('pending', 'completed', 'failed')),
    total_count integer not null default 0 check (total_count >= 0),
    accepted_count integer not null default 0 check (accepted_count >= 0),
    rejected_count integer not null default 0 check (rejected_count >= 0),
    created_at timestamptz not null default now()
);

create index validation_runs_owner_idx
    on public.validation_runs (owner_id, created_at desc);

alter table public.catalog_items enable row level security;
alter table public.validation_runs enable row level security;

create policy "read own catalog"
    on public.catalog_items for select to authenticated
    using ((select auth.uid()) = owner_id);

create policy "insert own catalog"
    on public.catalog_items for insert to authenticated
    with check ((select auth.uid()) = owner_id);

create policy "delete own catalog"
    on public.catalog_items for delete to authenticated
    using ((select auth.uid()) = owner_id);

create policy "read own runs"
    on public.validation_runs for select to authenticated
    using ((select auth.uid()) = owner_id);

revoke all on public.catalog_items, public.validation_runs from anon;
