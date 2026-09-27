-- Search index for one Supabase project.
-- Run this once in the SQL editor as the project owner.
-- Running it again replaces the function and the policy. It does not delete rows.
-- The app signs in as the admin test user. It does not use the service role key.

create extension if not exists vector with schema extensions;

create table if not exists public.chunks (
    session_id text not null,
    chunk_id text not null,
    user_id uuid not null references auth.users (id) on delete cascade,
    source text not null,
    page integer not null check (page >= 1),
    chunk_index integer not null check (chunk_index >= 0),
    headings jsonb not null default '[]'::jsonb,
    content text not null,
    embedding extensions.vector(1024) not null,
    created_at timestamptz not null default now(),
    primary key (session_id, chunk_id)
);

create index if not exists chunks_session_source_idx
    on public.chunks (session_id, source);

create index if not exists chunks_created_at_idx
    on public.chunks (created_at);

create index if not exists chunks_embedding_idx
    on public.chunks
    using hnsw (embedding extensions.vector_cosine_ops);

alter table public.chunks enable row level security;

drop policy if exists chunks_owner on public.chunks;

create policy chunks_owner
    on public.chunks
    for all
    to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

revoke all on public.chunks from anon;
grant select, insert, update, delete on public.chunks to authenticated;

create or replace function public.match_session_chunks(
    query_embedding text,
    match_session_id text,
    match_source text,
    match_count integer
)
returns table (
    chunk_id text,
    content text,
    source text,
    page integer,
    chunk_index integer,
    headings jsonb,
    distance double precision
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
    select
        c.chunk_id,
        c.content,
        c.source,
        c.page,
        c.chunk_index,
        c.headings,
        (c.embedding <=> query_embedding::vector(1024)) as distance
    from public.chunks as c
    where c.session_id = match_session_id
      and c.source = match_source
    order by c.embedding <=> query_embedding::vector(1024)
    limit match_count;
$$;

revoke all on function public.match_session_chunks(text, text, text, integer)
    from public;
revoke all on function public.match_session_chunks(text, text, text, integer)
    from anon;
grant execute on function public.match_session_chunks(text, text, text, integer)
    to authenticated;
