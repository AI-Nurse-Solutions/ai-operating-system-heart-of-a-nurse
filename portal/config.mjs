/*
 * Deployment configuration for the Client Care Portal.
 *
 * GitHub Pages serves this file publicly, so ONLY publishable values belong
 * here. The Supabase URL and anon (publishable) key are safe to expose —
 * row-level security enforces client isolation server-side. Never put a
 * service-role key, an AI API key, or any private record in this file or
 * anywhere else in this repository.
 *
 * Leave both values empty to run the portal in demo mode: a browser-local
 * sandbox with fictional data and no network calls, useful for review and
 * for trying the flows before a backend exists.
 */

export const config = Object.freeze({
  supabaseUrl: '',        // e.g. 'https://abcdefghijkl.supabase.co'
  supabaseAnonKey: '',    // the project's anon/publishable key (safe to publish)

  // Pinned browser build of supabase-js, fetched only when configured above.
  // Upgrade deliberately, by exact version, after reviewing upstream changes
  // (same supply-chain policy as the gstack pin in CLAUDE.md).
  supabaseJsUrl: 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/+esm',

  // Where magic-link emails should land after sign-in.
  redirectUrl: 'https://nurse-ai-os.org/portal/'
});

export function isConfigured(cfg = config) {
  return Boolean(cfg.supabaseUrl && cfg.supabaseAnonKey);
}
