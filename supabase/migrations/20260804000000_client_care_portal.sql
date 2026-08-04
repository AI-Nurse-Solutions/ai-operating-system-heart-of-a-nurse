-- Nurse AI OS Client Care Portal — core schema, row-level security, audit trail.
--
-- Governance invariants this migration enforces (PRD §10):
--   * Client isolation: every table is RLS-enabled; clients only ever see rows
--     for their own workspace, admins see everything.
--   * No PHI: the schema has no patient fields anywhere, by design.
--   * Auditability: activity_events rows are written by SECURITY DEFINER
--     triggers with timestamps; clients cannot write them directly.
--   * Human approval: messages.ai_assisted can only be set by an admin; the
--     AI never inserts messages (the edge function only returns drafts).
--
-- Apply with: supabase db push   (or paste into the SQL editor)

-- ---------------------------------------------------------------- tables

create table public.clients (
  id uuid primary key default gen_random_uuid(),
  organization text not null,
  stage text not null default 'getting-started'
    check (stage in ('getting-started', 'configuring', 'operational', 'optimizing')),
  governance_tier text not null default '',
  config_label text not null default '',
  setup_profile text not null default '',
  last_review date,
  next_review date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  name text not null default '',
  email text not null default '',
  role text not null default 'client' check (role in ('client', 'admin', 'specialist')),
  client_id uuid references public.clients (id) on delete set null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table public.milestones (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients (id) on delete cascade,
  title text not null,
  description text not null default '',
  status text not null default 'not-started'
    check (status in ('not-started', 'started', 'complete')),
  completed_at date,
  display_order integer not null default 1
);

create table public.progress_reports (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients (id) on delete cascade,
  report_date date not null default current_date,
  summary text not null default '',
  accomplishments jsonb not null default '[]',
  capabilities jsonb not null default '[]',
  risks jsonb not null default '[]',
  next_priorities jsonb not null default '[]',
  acknowledge_note text not null default '',
  published boolean not null default false,
  created_at timestamptz not null default now()
);

create table public.action_items (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients (id) on delete cascade,
  category text not null default 'maintain'
    check (category in ('maintain', 'improve', 'learn', 'review')),
  title text not null,
  instructions text not null default '',
  priority text not null default 'medium' check (priority in ('high', 'medium', 'low')),
  owner text not null default 'client',
  status text not null default 'not-started'
    check (status in ('not-started', 'started', 'complete')),
  due_date date,
  link text not null default '',
  client_comment text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.conversations (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients (id) on delete cascade,
  subject text not null,
  category text not null default 'other'
    check (category in ('setup', 'maintenance', 'improvement', 'training', 'governance', 'other')),
  related_id uuid,
  status text not null default 'new'
    check (status in ('new', 'in-review', 'waiting-for-client', 'answered', 'closed')),
  created_by uuid not null references public.profiles (id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Note on author references: messages.sender_id and conversations.created_by
-- deliberately keep the default restrictive delete behavior. Deleting an auth
-- user who has posted history is therefore blocked — the supported removal
-- path is deactivation (profiles.active = false), which preserves the audit
-- trail and thread attribution required by PRD §10.
create table public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations (id) on delete cascade,
  sender_id uuid not null references public.profiles (id),
  body text not null,
  ai_assisted boolean not null default false,
  created_at timestamptz not null default now()
);

create table public.activity_events (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients (id) on delete cascade,
  actor uuid,
  action text not null,
  record_type text not null,
  record_id text not null,
  created_at timestamptz not null default now()
);

create index milestones_client_idx on public.milestones (client_id, display_order);
create index reports_client_idx on public.progress_reports (client_id, report_date desc);
create index actions_client_idx on public.action_items (client_id, status);
create index conversations_client_idx on public.conversations (client_id, updated_at desc);
create index messages_conversation_idx on public.messages (conversation_id, created_at);
create index activity_client_idx on public.activity_events (client_id, created_at desc);

-- ------------------------------------------------------------- helpers
-- SECURITY DEFINER so profile lookups don't recurse through profiles RLS.
-- Each helper only reveals facts about the calling user, and an inactive
-- (deactivated) profile yields no role and no client — access simply stops.

create or replace function public.portal_is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select coalesce(
    (select role = 'admin' from public.profiles where id = auth.uid() and active),
    false
  );
$$;

create or replace function public.portal_client_id()
returns uuid language sql stable security definer set search_path = public as $$
  select client_id from public.profiles where id = auth.uid() and active;
$$;

-- Create a profile row automatically for every invited auth user.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, name)
  values (
    new.id,
    coalesce(new.email, ''),
    coalesce(new.raw_user_meta_data ->> 'name', split_part(coalesce(new.email, ''), '@', 1))
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

create or replace function public.portal_touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create trigger clients_touch before update on public.clients
  for each row execute function public.portal_touch_updated_at();
create trigger actions_touch before update on public.action_items
  for each row execute function public.portal_touch_updated_at();
create trigger conversations_touch before update on public.conversations
  for each row execute function public.portal_touch_updated_at();

-- A new message bumps its conversation (SECURITY DEFINER: clients cannot
-- update conversations directly, and should not need to).
create or replace function public.portal_touch_conversation()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  update public.conversations set updated_at = now() where id = new.conversation_id;
  return new;
end;
$$;

create trigger messages_touch_conversation after insert on public.messages
  for each row execute function public.portal_touch_conversation();

-- Clients may move an action's status and leave a comment — nothing else.
create or replace function public.portal_guard_client_action_update()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if public.portal_is_admin() then
    return new;
  end if;
  if new.id             is distinct from old.id
     or new.client_id   is distinct from old.client_id
     or new.category    is distinct from old.category
     or new.title       is distinct from old.title
     or new.instructions is distinct from old.instructions
     or new.priority    is distinct from old.priority
     or new.owner       is distinct from old.owner
     or new.due_date    is distinct from old.due_date
     or new.link        is distinct from old.link
     or new.created_at  is distinct from old.created_at then
    raise exception 'Clients may update only an action''s status and comment';
  end if;
  return new;
end;
$$;

create trigger actions_guard_client_update before update on public.action_items
  for each row execute function public.portal_guard_client_action_update();

-- Audit trail: written by triggers only, with server timestamps.
create or replace function public.portal_log_activity()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  v_client uuid;
  v_action text;
  v_type text;
begin
  if tg_table_name = 'messages' then
    select c.client_id into v_client from public.conversations c where c.id = new.conversation_id;
    v_action := 'sent message';
    v_type := 'message';
  elsif tg_table_name = 'conversations' then
    v_client := new.client_id;
    v_action := case when tg_op = 'INSERT' then 'opened conversation' else 'set conversation to ' || new.status end;
    v_type := 'conversation';
  elsif tg_table_name = 'progress_reports' then
    v_client := new.client_id;
    -- Unpublished drafts are invisible to clients; logging them would leak a
    -- "published" notice for a report the client cannot open.
    if not new.published then
      return new;
    end if;
    v_action := case
      when tg_op = 'INSERT' then 'published progress report'
      when old.published is distinct from new.published then 'published progress report'
      else 'updated progress report'
    end;
    v_type := 'report';
  elsif tg_table_name = 'action_items' then
    v_client := new.client_id;
    v_action := case when tg_op = 'INSERT' then 'assigned action' else 'set action to ' || new.status end;
    v_type := 'action';
  elsif tg_table_name = 'milestones' then
    v_client := new.client_id;
    v_action := case when tg_op = 'INSERT' then 'added milestone' else 'set milestone to ' || new.status end;
    v_type := 'milestone';
  else
    return new;
  end if;
  insert into public.activity_events (client_id, actor, action, record_type, record_id)
  values (v_client, auth.uid(), v_action, v_type, new.id::text);
  return new;
end;
$$;

create trigger conversations_log after insert or update of status on public.conversations
  for each row execute function public.portal_log_activity();
create trigger messages_log after insert on public.messages
  for each row execute function public.portal_log_activity();
create trigger reports_log after insert or update on public.progress_reports
  for each row execute function public.portal_log_activity();
create trigger actions_log after insert or update of status on public.action_items
  for each row execute function public.portal_log_activity();
create trigger milestones_log after insert or update of status on public.milestones
  for each row execute function public.portal_log_activity();

-- ------------------------------------------------- row-level security
-- Deny-by-default: RLS on everywhere, then narrow policies. "Specialist"
-- accounts intentionally get no policies yet — the optional support role
-- ships in a later phase with an explicit assignment table.

alter table public.clients enable row level security;
alter table public.profiles enable row level security;
alter table public.milestones enable row level security;
alter table public.progress_reports enable row level security;
alter table public.action_items enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.activity_events enable row level security;

-- profiles
create policy "profiles: read own or admin" on public.profiles
  for select using (id = auth.uid() or public.portal_is_admin());
create policy "profiles: admin manages" on public.profiles
  for update using (public.portal_is_admin()) with check (public.portal_is_admin());

-- clients
create policy "clients: read own workspace or admin" on public.clients
  for select using (id = public.portal_client_id() or public.portal_is_admin());
create policy "clients: admin insert" on public.clients
  for insert with check (public.portal_is_admin());
create policy "clients: admin update" on public.clients
  for update using (public.portal_is_admin()) with check (public.portal_is_admin());

-- milestones
create policy "milestones: read own or admin" on public.milestones
  for select using (client_id = public.portal_client_id() or public.portal_is_admin());
create policy "milestones: admin insert" on public.milestones
  for insert with check (public.portal_is_admin());
create policy "milestones: admin update" on public.milestones
  for update using (public.portal_is_admin()) with check (public.portal_is_admin());
create policy "milestones: admin delete" on public.milestones
  for delete using (public.portal_is_admin());

-- progress reports: clients see only published reports for their workspace
create policy "reports: read published own or admin" on public.progress_reports
  for select using (
    public.portal_is_admin()
    or (client_id = public.portal_client_id() and published)
  );
create policy "reports: admin insert" on public.progress_reports
  for insert with check (public.portal_is_admin());
create policy "reports: admin update" on public.progress_reports
  for update using (public.portal_is_admin()) with check (public.portal_is_admin());

-- action items: clients read + update (columns guarded by trigger above)
create policy "actions: read own or admin" on public.action_items
  for select using (client_id = public.portal_client_id() or public.portal_is_admin());
create policy "actions: admin insert" on public.action_items
  for insert with check (public.portal_is_admin());
create policy "actions: update own or admin" on public.action_items
  for update using (client_id = public.portal_client_id() or public.portal_is_admin())
  with check (client_id = public.portal_client_id() or public.portal_is_admin());
create policy "actions: admin delete" on public.action_items
  for delete using (public.portal_is_admin());

-- conversations
create policy "conversations: read own or admin" on public.conversations
  for select using (client_id = public.portal_client_id() or public.portal_is_admin());
create policy "conversations: open own or admin" on public.conversations
  for insert with check (
    created_by = auth.uid()
    and (client_id = public.portal_client_id() or public.portal_is_admin())
  );
create policy "conversations: admin update" on public.conversations
  for update using (public.portal_is_admin()) with check (public.portal_is_admin());

-- messages: clients write into their own threads only, never AI-labeled
create policy "messages: read own thread or admin" on public.messages
  for select using (
    public.portal_is_admin()
    or exists (
      select 1 from public.conversations c
      where c.id = conversation_id and c.client_id = public.portal_client_id()
    )
  );
create policy "messages: send as self" on public.messages
  for insert with check (
    sender_id = auth.uid()
    and (
      public.portal_is_admin()
      or (
        ai_assisted = false
        and exists (
          select 1 from public.conversations c
          where c.id = conversation_id and c.client_id = public.portal_client_id()
        )
      )
    )
  );

-- activity events: read-only in the API; rows come from definer triggers
create policy "activity: read own or admin" on public.activity_events
  for select using (client_id = public.portal_client_id() or public.portal_is_admin());

-- ------------------------------------------------- helper RPC and views

-- Open a conversation and its first message in one transaction, so a failed
-- message insert can never leave an empty thread the client cannot repair.
-- SECURITY DEFINER re-implements the same checks the RLS policies make:
-- caller must be signed in, and must be the workspace's client or an admin.
create or replace function public.portal_open_conversation(
  p_client_id uuid,
  p_subject text,
  p_category text,
  p_related_id uuid,
  p_body text
) returns public.conversations
language plpgsql security definer set search_path = public as $$
declare
  v_conversation public.conversations;
begin
  if auth.uid() is null then
    raise exception 'Not signed in';
  end if;
  if not (public.portal_is_admin() or p_client_id = public.portal_client_id()) then
    raise exception 'Not authorized for this workspace';
  end if;
  insert into public.conversations (client_id, subject, category, related_id, created_by)
  values (p_client_id, p_subject, p_category, p_related_id, auth.uid())
  returning * into v_conversation;
  insert into public.messages (conversation_id, sender_id, body)
  values (v_conversation.id, auth.uid(), p_body);
  return v_conversation;
end;
$$;

revoke all on function public.portal_open_conversation(uuid, text, text, uuid, text) from anon, public;
grant execute on function public.portal_open_conversation(uuid, text, text, uuid, text) to authenticated;

-- Name-only directory so message threads can attribute authors on both
-- sides. Clients resolve their own team plus admin names; admins resolve
-- everyone. Emails, roles, and all other profile fields stay private —
-- this is deliberately narrower than widening the profiles select policy.
create or replace view public.portal_directory
with (security_invoker = false) as
select p.id, p.name
from public.profiles p
where p.active
  and (
    p.role = 'admin'
    or p.client_id = public.portal_client_id()
    or public.portal_is_admin()
  );

revoke all on public.portal_directory from anon;
grant select on public.portal_directory to authenticated;

-- ------------------------------------------------------------ admin view
-- Portfolio rollup for the admin client list. security_invoker keeps the
-- caller's RLS in force, so a client querying it sees at most their own row.

create or replace view public.client_overview
with (security_invoker = true) as
select
  c.*,
  (select count(*) from public.action_items a
     where a.client_id = c.id and a.status <> 'complete') as open_actions,
  (select count(*) from public.conversations v
     where v.client_id = c.id and v.status not in ('answered', 'closed')) as open_questions
from public.clients c;
