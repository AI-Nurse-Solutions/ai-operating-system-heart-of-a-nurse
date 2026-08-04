// draft-with-ai — Supabase Edge Function (Deno)
//
// Returns an AI-drafted reply for one support conversation so the admin can
// edit, approve, and send it. Governance guarantees (PRD §5.6, §10):
//   * Admin-only: the caller's JWT must belong to an active admin profile.
//   * Minimum necessary context: the question thread, the related action (if
//     any), and the client's approved setup profile. Nothing else is sent.
//   * Human approval: this function never writes to the database. The draft
//     goes back to the admin UI, where a person edits and sends it.
//   * No secrets in the browser: ANTHROPIC_API_KEY lives only in function
//     secrets (supabase secrets set ANTHROPIC_API_KEY=...).
//
// Database reads use the caller's own JWT with the anon key, so row-level
// security stays in force — this function holds no service-role key.

import { createClient } from "npm:@supabase/supabase-js@2.49.4";
import Anthropic from "npm:@anthropic-ai/sdk@0.88.0";

const DRAFT_MODEL = Deno.env.get("DRAFT_MODEL") ?? "claude-opus-5";

// Only the portal deployment may make cross-origin calls; override
// PORTAL_ORIGIN for staging deployments.
const ALLOWED_ORIGIN = Deno.env.get("PORTAL_ORIGIN") ?? "https://nurse-ai-os.org";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const SYSTEM_PROMPT = `You draft support replies for Robert Domondon, the human steward of Nurse AI OS — a governed, no-PHI professional environment for nursing AI work. You are drafting on Robert's behalf; a human reviews, edits, and sends every reply. Nothing you write is delivered automatically.

Context you receive: the client's question thread, their approved setup profile, and sometimes a related maintenance/improvement action. That is all the client data that exists here — the portal holds no patient information.

How to draft:
- Answer the actual question first, concretely, in plain language a busy nurse can act on.
- Recommend small, bounded next steps (numbered when there are several), consistent with Nurse AI OS governance: no PHI anywhere, human judgment reviews every AI result, changes are trialed once before being standardized.
- Technical guidance only — never clinical advice, and never present setup guidance as if it were clinical direction. If a question drifts toward patient care or anything clinical, say plainly that the portal and Nurse AI OS support setup and education only, and that clinical questions belong with their clinical governance channels.
- If you are unsure of a fact about the client's configuration, say so and flag it for Robert to confirm before sending, rather than guessing.
- When useful, end with one clarifying question.
- Warm, competent, brief. No marketing language. Write in the first person as Robert.`;

interface DraftRequest {
  conversation_id?: string;
}

function json(status: number, body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: CORS_HEADERS });
  }
  if (req.method !== "POST") {
    return json(405, { error: "POST only" });
  }

  const authHeader = req.headers.get("Authorization");
  if (!authHeader) {
    return json(401, { error: "Missing authorization" });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } },
  );

  const { data: authData, error: authError } = await supabase.auth.getUser();
  if (authError || !authData?.user) {
    return json(401, { error: "Not signed in" });
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("role, active, name")
    .eq("id", authData.user.id)
    .single();
  if (!profile || !profile.active || profile.role !== "admin") {
    return json(403, { error: "AI drafting is available to the admin only" });
  }

  let body: DraftRequest;
  try {
    body = await req.json();
  } catch {
    return json(400, { error: "Invalid JSON body" });
  }
  const conversationId = body.conversation_id;
  if (!conversationId) {
    return json(400, { error: "conversation_id is required" });
  }

  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .select("id, client_id, subject, category, related_id")
    .eq("id", conversationId)
    .single();
  if (convError || !conversation) {
    return json(404, { error: "Conversation not found" });
  }

  const [{ data: client }, { data: messages }] = await Promise.all([
    supabase
      .from("clients")
      .select("organization, stage, governance_tier, config_label, setup_profile")
      .eq("id", conversation.client_id)
      .single(),
    // Newest twelve, then restored to chronological order below — a long
    // thread must keep the message being answered, not the opening exchange.
    supabase
      .from("messages")
      .select("sender_id, body, created_at")
      .eq("conversation_id", conversationId)
      .order("created_at", { ascending: false })
      .limit(12),
  ]);

  let relatedAction = null;
  if (conversation.related_id) {
    const { data } = await supabase
      .from("action_items")
      .select("title, instructions, category, status, due_date")
      .eq("id", conversation.related_id)
      .maybeSingle();
    relatedAction = data;
  }

  const thread = [...(messages ?? [])].reverse()
    .map((m) => {
      const who = m.sender_id === authData.user.id ? "Robert (support)" : "Client";
      return `${who} (${m.created_at}):\n${m.body}`;
    })
    .join("\n\n");

  const context = [
    `Client workspace: ${client?.organization ?? "unknown"}`,
    `Lifecycle stage: ${client?.stage ?? "unknown"} · Governance tier: ${client?.governance_tier || "n/a"} · Configuration: ${client?.config_label || "n/a"}`,
    `Approved setup profile: ${client?.setup_profile || "none recorded"}`,
    relatedAction
      ? `Related action item: "${relatedAction.title}" (${relatedAction.category}, status ${relatedAction.status}, due ${relatedAction.due_date ?? "n/a"}). Instructions: ${relatedAction.instructions}`
      : "Related action item: none",
    `Conversation subject: ${conversation.subject} (category: ${conversation.category})`,
    "",
    "Thread so far:",
    thread || "(no messages)",
    "",
    "Draft Robert's next reply to the client.",
  ].join("\n");

  const apiKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!apiKey) {
    console.error("draft-with-ai: ANTHROPIC_API_KEY is not configured");
    return json(503, { error: "AI drafting is not configured. Reply directly instead." });
  }

  try {
    const anthropic = new Anthropic({ apiKey });
    // Server-side fallbacks: if the model's safety classifiers decline the
    // request, the API retries it on Anthropic's recommended fallback model
    // in the same call instead of returning an empty draft.
    const response = await anthropic.beta.messages.create({
      model: DRAFT_MODEL,
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      messages: [{ role: "user", content: context }],
      // deno-lint-ignore no-explicit-any
    } as any);

    if (response.stop_reason === "refusal") {
      return json(200, {
        error:
          "The model declined to draft this reply. Please answer this one yourself — no draft was produced.",
      });
    }

    const draft = response.content
      .filter((block: { type: string }) => block.type === "text")
      .map((block: { text?: string }) => block.text ?? "")
      .join("\n")
      .trim();

    if (!draft) {
      return json(200, { error: "The model returned an empty draft. Try again or reply directly." });
    }
    return json(200, { draft });
  } catch (err) {
    console.error("draft-with-ai failed:", err instanceof Error ? err.message : err);
    return json(502, { error: "AI drafting is temporarily unavailable. Reply directly instead." });
  }
});
