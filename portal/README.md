# Nurse AI OS Client Care Portal

A private portal where each Nurse AI OS client sees their setup progress,
maintenance plan, and support conversations — and where Robert manages every
client from one admin workspace, with AI-assisted (human-approved) replies.

Built to the Client Care Portal PRD (v1.0 MVP). The portal is a
client-success and system-maintenance tool, **not** a clinical system:
no PHI, no patient-facing features, ever.

## Architecture

| Layer | What | Where |
|---|---|---|
| Frontend | Static ES-module app (`index.html`, `portal.mjs`, `portal-data.mjs`, `portal-model.mjs`, `portal.css`) | GitHub Pages, this directory |
| Auth + database | Supabase Auth (passwordless magic links) + Postgres with row-level security | `../supabase/migrations/` |
| AI drafting | `draft-with-ai` edge function calling the Claude API server-side | `../supabase/functions/draft-with-ai/` |

GitHub Pages hosts **only** the static interface. The repository and browser
bundle contain no service-role key, no AI API key, and no client records.
The only backend values that ever appear client-side are the Supabase project
URL and its anon/publishable key (in `config.mjs`), which are designed to be
public — row-level security enforces client isolation server-side.

### Demo mode

With `config.mjs` left unconfigured (the default in this repo), the portal
runs as a browser-local demo: fictional seeded data, both roles switchable,
no network calls. This keeps the app reviewable on GitHub Pages before a
backend exists and doubles as a safe environment to rehearse the flows.

## Production setup

1. **Create a Supabase project**, then apply the migration:

   ```bash
   supabase link --project-ref <your-project-ref>
   supabase db push
   ```

2. **Deploy the edge function and set its secret** (the AI key never leaves
   Supabase):

   ```bash
   supabase functions deploy draft-with-ai
   supabase secrets set ANTHROPIC_API_KEY=<server-side key>
   # optional: supabase secrets set DRAFT_MODEL=claude-opus-5
   ```

3. **Configure the frontend**: edit `portal/config.mjs` and fill in
   `supabaseUrl` and `supabaseAnonKey` (Project Settings → API → anon public
   key). Commit — these values are publishable by design.

4. **Auth settings** (Supabase dashboard → Authentication):
   - Disable public sign-ups; the portal is invitation-only.
   - Add `https://nurse-ai-os.org/portal/` to the redirect allow-list.

5. **Create the admin account**: invite Robert's email from
   Authentication → Users, then promote the auto-created profile:

   ```sql
   update public.profiles set role = 'admin', name = 'Robert Domondon'
   where email = 'robert@nurse-ai-os.org';
   ```

6. **Onboard a client**: create the client in the admin portal (or SQL),
   invite the client's email from the dashboard, then link the profile:

   ```sql
   update public.profiles set client_id = '<client uuid>', name = '<client name>'
   where email = '<client email>';
   ```

## Security model

- **Client isolation** — every table has RLS enabled; clients can only reach
  rows for their own `client_id`, verified by the deny-by-default policies in
  the migration. Permission testing belongs in every release checklist.
- **Column guarding** — clients may update only an action item's status and
  comment; a trigger rejects everything else.
- **Audit trail** — `activity_events` rows are written by SECURITY DEFINER
  triggers with server timestamps; the API offers them read-only.
- **AI boundaries** — drafting is admin-only, receives the minimum necessary
  context (thread, related action, approved setup profile), returns a draft
  only, and never writes to the database. Sent replies carry a visible
  "AI-assisted · human approved" label when applicable.
- **No PHI** — the schema has no patient fields; the UI shows the no-PHI
  boundary on every screen and re-warns on every entry form, with a soft
  client-side screen for obvious PHI/secret patterns. These checks are a
  courtesy, not DLP; governance and human review remain the real controls.

## Tests

- `python3 -m unittest tests.test_client_care_portal -v` — structural,
  policy-coverage, and no-secrets checks.
- `node tests/test_portal_model.mjs` — pure model logic.
