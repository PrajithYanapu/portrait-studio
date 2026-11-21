create table if not exists public.portraits (
 id uuid primary key,
 customer_name text not null,
 style text not null,
 settings jsonb not null default '{}'::jsonb,
 original_path text not null,
 generated_path text not null,
 created_at timestamptz not null default now(),
 download_count integer not null default 0
);
alter table public.portraits enable row level security;
insert into storage.buckets (id,name,public) values ('portrait-uploads','portrait-uploads',false) on conflict (id) do nothing;
-- Keep service-role credentials on the backend only. No public table/storage policies are created.
