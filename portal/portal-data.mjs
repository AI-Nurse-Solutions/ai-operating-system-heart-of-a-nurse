/*
 * Data layer for the Client Care Portal.
 *
 * One interface, two backends:
 *  - DemoStore: browser-local sandbox seeded from portal-model.mjs. Used when
 *    portal/config.mjs has no Supabase project configured. No network calls.
 *  - SupabaseStore: Supabase Auth + Postgres with row-level security. The
 *    browser only ever holds the anon key; client isolation is enforced by
 *    RLS policies in supabase/migrations, and AI drafting happens in the
 *    draft-with-ai edge function (server-side key, admin-only).
 */

import { config as defaultConfig, isConfigured } from './config.mjs';
import { DEMO_STORAGE_KEY, demoSeed, demoDraft } from './portal-model.mjs';

export async function createStore(cfg = defaultConfig) {
  if (isConfigured(cfg)) {
    const store = new SupabaseStore(cfg);
    await store.init();
    return store;
  }
  const store = new DemoStore();
  await store.init();
  return store;
}

/* ============================ Demo store ============================ */

function uid(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export class DemoStore {
  constructor(storage) {
    this.mode = 'demo';
    this.storage = storage || (typeof localStorage !== 'undefined' ? localStorage : null);
    this.data = null;
    this.userId = null;
  }

  async init() {
    let saved = null;
    try {
      saved = this.storage ? JSON.parse(this.storage.getItem(DEMO_STORAGE_KEY) || 'null') : null;
    } catch {
      saved = null;
    }
    this.data = saved && saved.data && saved.data.schemaVersion === demoSeed().schemaVersion
      ? saved.data
      : demoSeed();
    this.userId = saved ? saved.userId : null;
    this.save();
    return this.session();
  }

  save() {
    if (!this.storage) return;
    try {
      this.storage.setItem(DEMO_STORAGE_KEY, JSON.stringify({ userId: this.userId, data: this.data }));
    } catch {
      /* storage full or blocked — demo state just won't persist */
    }
  }

  reset() {
    this.data = demoSeed();
    this.userId = null;
    this.save();
  }

  session() {
    const user = this.data.users.find((u) => u.id === this.userId) || null;
    return user ? { user } : null;
  }

  /* Demo sign-in: no email is sent; pick a seeded role instead. */
  async signInAs(role) {
    const user = this.data.users.find((u) => u.role === role);
    if (!user) throw new Error(`No demo user with role ${role}`);
    this.userId = user.id;
    this.save();
    return this.session();
  }

  async signInWithEmail() {
    throw new Error('Demo mode has no email sign-in. Choose a demo role instead.');
  }

  async signOut() {
    this.userId = null;
    this.save();
  }

  requireUser() {
    const session = this.session();
    if (!session) throw new Error('Not signed in.');
    return session.user;
  }

  requireAdmin() {
    const user = this.requireUser();
    if (user.role !== 'admin') throw new Error('Admin access required.');
    return user;
  }

  canSee(clientId) {
    const user = this.requireUser();
    return user.role === 'admin' || user.clientId === clientId;
  }

  userName(userId) {
    const user = this.data.users.find((u) => u.id === userId);
    return user ? user.name : 'Unknown';
  }

  logActivity(clientId, action, recordType, recordId) {
    this.data.activity.unshift({
      id: uid('evt'),
      clientId,
      actor: this.requireUser().id,
      action,
      recordType,
      recordId,
      at: new Date().toISOString()
    });
  }

  async getWorkspace(clientId) {
    if (!this.canSee(clientId)) throw new Error('Not authorized for this workspace.');
    const d = this.data;
    const conversations = d.conversations.filter((c) => c.clientId === clientId);
    const conversationIds = new Set(conversations.map((c) => c.id));
    return {
      client: d.clients.find((c) => c.id === clientId) || null,
      milestones: d.milestones.filter((m) => m.clientId === clientId).sort((a, b) => a.order - b.order),
      reports: d.reports.filter((r) => r.clientId === clientId && r.published).sort((a, b) => (a.reportDate < b.reportDate ? 1 : -1)),
      actions: d.actions.filter((a) => a.clientId === clientId),
      conversations,
      messages: d.messages.filter((m) => conversationIds.has(m.conversationId)),
      activity: d.activity.filter((e) => e.clientId === clientId)
    };
  }

  async listClients() {
    this.requireAdmin();
    return this.data.clients.map((client) => {
      const actions = this.data.actions.filter((a) => a.clientId === client.id);
      const open = this.data.conversations.filter((c) => c.clientId === client.id && !['answered', 'closed'].includes(c.status));
      return { ...client, openActions: actions.filter((a) => a.status !== 'complete').length, openQuestions: open.length };
    });
  }

  async updateActionStatus(actionId, status, comment) {
    const action = this.data.actions.find((a) => a.id === actionId);
    if (!action || !this.canSee(action.clientId)) throw new Error('Action not found.');
    action.status = status;
    if (comment !== undefined) action.comment = comment;
    this.logActivity(action.clientId, `set action to ${status}`, 'action', actionId);
    this.save();
    return action;
  }

  async createConversation({ clientId, subject, category, relatedId, body }) {
    if (!this.canSee(clientId)) throw new Error('Not authorized.');
    const user = this.requireUser();
    const now = new Date().toISOString();
    const conversation = {
      id: uid('conv'), clientId, subject, category,
      relatedId: relatedId || null, status: 'new',
      createdBy: user.id, createdAt: now, updatedAt: now
    };
    this.data.conversations.unshift(conversation);
    this.data.messages.push({ id: uid('msg'), conversationId: conversation.id, senderId: user.id, body, aiAssisted: false, createdAt: now });
    this.logActivity(clientId, 'opened question', 'conversation', conversation.id);
    this.save();
    return conversation;
  }

  async addMessage(conversationId, body, { aiAssisted = false } = {}) {
    const conversation = this.data.conversations.find((c) => c.id === conversationId);
    if (!conversation || !this.canSee(conversation.clientId)) throw new Error('Conversation not found.');
    const user = this.requireUser();
    const now = new Date().toISOString();
    const message = {
      id: uid('msg'), conversationId, senderId: user.id, body,
      aiAssisted: user.role === 'admin' ? Boolean(aiAssisted) : false,
      createdAt: now
    };
    this.data.messages.push(message);
    conversation.updatedAt = now;
    conversation.status = user.role === 'admin' ? 'answered' : conversation.status === 'answered' ? 'in-review' : conversation.status;
    this.logActivity(conversation.clientId, 'sent reply', 'message', message.id);
    this.save();
    return message;
  }

  async setConversationStatus(conversationId, status) {
    const conversation = this.data.conversations.find((c) => c.id === conversationId);
    if (!conversation || !this.canSee(conversation.clientId)) throw new Error('Conversation not found.');
    conversation.status = status;
    conversation.updatedAt = new Date().toISOString();
    this.save();
    return conversation;
  }

  async getConversationClientId(conversationId) {
    const conversation = this.data.conversations.find((c) => c.id === conversationId);
    if (!conversation || !this.canSee(conversation.clientId)) throw new Error('Conversation not found.');
    return conversation.clientId;
  }

  /* Draft is returned for editing only — sending stays a human action. */
  async draftWithAi(conversationId) {
    this.requireAdmin();
    const conversation = this.data.conversations.find((c) => c.id === conversationId);
    if (!conversation) throw new Error('Conversation not found.');
    const client = this.data.clients.find((c) => c.id === conversation.clientId);
    const firstMessage = this.data.messages.find((m) => m.conversationId === conversationId);
    return { draft: demoDraft({ question: firstMessage ? firstMessage.body : conversation.subject, clientProfile: client ? client.setupProfile : '' }) };
  }

  async createClient(fields) {
    this.requireAdmin();
    const client = {
      id: uid('client'),
      organization: fields.organization,
      stage: fields.stage || 'getting-started',
      governanceTier: fields.governanceTier || '',
      configLabel: fields.configLabel || '',
      setupProfile: fields.setupProfile || '',
      lastReview: fields.lastReview || null,
      nextReview: fields.nextReview || null
    };
    this.data.clients.push(client);
    this.logActivity(client.id, 'created client', 'client', client.id);
    this.save();
    return client;
  }

  async updateClient(clientId, fields) {
    this.requireAdmin();
    const client = this.data.clients.find((c) => c.id === clientId);
    if (!client) throw new Error('Client not found.');
    Object.assign(client, fields);
    this.logActivity(clientId, 'updated client profile', 'client', clientId);
    this.save();
    return client;
  }

  async publishReport(clientId, fields) {
    this.requireAdmin();
    const report = {
      id: uid('rep'), clientId,
      reportDate: fields.reportDate || new Date().toISOString().slice(0, 10),
      summary: fields.summary || '',
      accomplishments: fields.accomplishments || [],
      capabilities: fields.capabilities || [],
      risks: fields.risks || [],
      nextPriorities: fields.nextPriorities || [],
      acknowledgeNote: fields.acknowledgeNote || '',
      published: true
    };
    this.data.reports.unshift(report);
    this.logActivity(clientId, 'published progress report', 'report', report.id);
    this.save();
    return report;
  }

  async updateMilestone(milestoneId, status) {
    this.requireAdmin();
    const milestone = this.data.milestones.find((m) => m.id === milestoneId);
    if (!milestone) throw new Error('Milestone not found.');
    milestone.status = status;
    milestone.completedAt = status === 'complete' ? new Date().toISOString().slice(0, 10) : null;
    this.logActivity(milestone.clientId, `set milestone to ${status}`, 'milestone', milestoneId);
    this.save();
    return milestone;
  }

  async createMilestone(clientId, fields) {
    this.requireAdmin();
    const order = Math.max(0, ...this.data.milestones.filter((m) => m.clientId === clientId).map((m) => m.order)) + 1;
    const milestone = {
      id: uid('ms'), clientId,
      title: fields.title,
      description: fields.description || '',
      status: 'not-started',
      completedAt: null,
      order
    };
    this.data.milestones.push(milestone);
    this.logActivity(clientId, 'added milestone', 'milestone', milestone.id);
    this.save();
    return milestone;
  }

  async createAction(clientId, fields) {
    this.requireAdmin();
    const action = {
      id: uid('act'), clientId,
      category: fields.category || 'maintain',
      title: fields.title,
      instructions: fields.instructions || '',
      priority: fields.priority || 'medium',
      owner: fields.owner || 'client',
      status: 'not-started',
      dueDate: fields.dueDate || null,
      link: fields.link || '',
      comment: ''
    };
    this.data.actions.push(action);
    this.logActivity(clientId, 'assigned action', 'action', action.id);
    this.save();
    return action;
  }
}

/* ========================== Supabase store ========================== */

const mapUser = (r) => r && ({ id: r.id, name: r.name, email: r.email, role: r.role, clientId: r.client_id, active: r.active });
const mapClient = (r) => r && ({
  id: r.id, organization: r.organization, stage: r.stage, governanceTier: r.governance_tier,
  configLabel: r.config_label, setupProfile: r.setup_profile, lastReview: r.last_review, nextReview: r.next_review
});
const mapMilestone = (r) => ({ id: r.id, clientId: r.client_id, title: r.title, description: r.description, status: r.status, completedAt: r.completed_at, order: r.display_order });
const mapReport = (r) => ({
  id: r.id, clientId: r.client_id, reportDate: r.report_date, summary: r.summary,
  accomplishments: r.accomplishments || [], capabilities: r.capabilities || [], risks: r.risks || [],
  nextPriorities: r.next_priorities || [], acknowledgeNote: r.acknowledge_note || '', published: r.published
});
const mapAction = (r) => ({
  id: r.id, clientId: r.client_id, category: r.category, title: r.title, instructions: r.instructions,
  priority: r.priority, owner: r.owner, status: r.status, dueDate: r.due_date, link: r.link || '', comment: r.client_comment || ''
});
const mapConversation = (r) => ({
  id: r.id, clientId: r.client_id, subject: r.subject, category: r.category, relatedId: r.related_id,
  status: r.status, createdBy: r.created_by, createdAt: r.created_at, updatedAt: r.updated_at
});
const mapMessage = (r) => ({ id: r.id, conversationId: r.conversation_id, senderId: r.sender_id, body: r.body, aiAssisted: r.ai_assisted, createdAt: r.created_at });
const mapActivity = (r) => ({ id: r.id, clientId: r.client_id, actor: r.actor, action: r.action, recordType: r.record_type, recordId: r.record_id, at: r.created_at });

function throwOn(error) {
  if (error) throw new Error(error.message || String(error));
}

export class SupabaseStore {
  constructor(cfg) {
    this.mode = 'supabase';
    this.cfg = cfg;
    this.supabase = null;
    this.profile = null;
    this.profiles = new Map();
  }

  async init() {
    const { createClient } = await import(this.cfg.supabaseJsUrl);
    this.supabase = createClient(this.cfg.supabaseUrl, this.cfg.supabaseAnonKey);
    const { data } = await this.supabase.auth.getSession();
    if (data && data.session) await this.loadProfile();
    return this.session();
  }

  session() {
    return this.profile ? { user: this.profile } : null;
  }

  async loadProfile() {
    const { data: authData, error: authError } = await this.supabase.auth.getUser();
    throwOn(authError);
    const { data, error } = await this.supabase.from('profiles').select('*').eq('id', authData.user.id).single();
    throwOn(error);
    this.profile = mapUser(data);
    if (!this.profile.active) {
      await this.signOut();
      throw new Error('This account has been deactivated. Contact support@nurse-ai-os.org.');
    }
    return this.profile;
  }

  async signInWithEmail(email) {
    const { error } = await this.supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: this.cfg.redirectUrl }
    });
    throwOn(error);
    return { sent: true };
  }

  async signOut() {
    await this.supabase.auth.signOut();
    this.profile = null;
  }

  userName(userId) {
    return this.profiles.get(userId) || 'Team member';
  }

  async getWorkspace(clientId) {
    const supabase = this.supabase;
    const [client, milestones, reports, actions, conversations] = await Promise.all([
      supabase.from('clients').select('*').eq('id', clientId).single(),
      supabase.from('milestones').select('*').eq('client_id', clientId).order('display_order'),
      supabase.from('progress_reports').select('*').eq('client_id', clientId).eq('published', true).order('report_date', { ascending: false }),
      supabase.from('action_items').select('*').eq('client_id', clientId),
      supabase.from('conversations').select('*').eq('client_id', clientId).order('updated_at', { ascending: false })
    ]);
    for (const res of [client, milestones, reports, actions, conversations]) throwOn(res.error);

    const conversationIds = (conversations.data || []).map((c) => c.id);
    let messages = { data: [] };
    if (conversationIds.length) {
      messages = await supabase.from('messages').select('*').in('conversation_id', conversationIds).order('created_at');
      throwOn(messages.error);
    }
    // portal_directory is a name-only view: clients resolve their own team
    // plus admin names, admins resolve everyone. Names are cosmetic, so a
    // failure degrades to the 'Team member' fallback rather than erroring.
    const { data: names, error: namesError } = await supabase.from('portal_directory').select('id,name');
    if (namesError) console.warn('portal: name lookup failed —', namesError.message);
    for (const row of names || []) this.profiles.set(row.id, row.name);
    if (this.profile) this.profiles.set(this.profile.id, this.profile.name);

    const activity = await supabase.from('activity_events').select('*').eq('client_id', clientId).order('created_at', { ascending: false }).limit(50);
    throwOn(activity.error);

    return {
      client: mapClient(client.data),
      milestones: (milestones.data || []).map(mapMilestone),
      reports: (reports.data || []).map(mapReport),
      actions: (actions.data || []).map(mapAction),
      conversations: (conversations.data || []).map(mapConversation),
      messages: (messages.data || []).map(mapMessage),
      activity: (activity.data || []).map(mapActivity)
    };
  }

  async listClients() {
    const { data, error } = await this.supabase.from('client_overview').select('*');
    throwOn(error);
    return (data || []).map((r) => ({ ...mapClient(r), openActions: r.open_actions, openQuestions: r.open_questions }));
  }

  async updateActionStatus(actionId, status, comment) {
    const patch = { status };
    if (comment !== undefined) patch.client_comment = comment;
    const { data, error } = await this.supabase.from('action_items').update(patch).eq('id', actionId).select().single();
    throwOn(error);
    return mapAction(data);
  }

  /* One transaction server-side: a failed message insert must not leave an
   * empty conversation the client cannot repair (only admins can delete). */
  async createConversation({ clientId, subject, category, relatedId, body }) {
    const { data, error } = await this.supabase.rpc('portal_open_conversation', {
      p_client_id: clientId,
      p_subject: subject,
      p_category: category,
      p_related_id: relatedId || null,
      p_body: body
    });
    throwOn(error);
    return mapConversation(data);
  }

  async getConversationClientId(conversationId) {
    const { data, error } = await this.supabase.from('conversations').select('client_id').eq('id', conversationId).single();
    throwOn(error);
    return data.client_id;
  }

  async addMessage(conversationId, body, { aiAssisted = false } = {}) {
    const { data, error } = await this.supabase.from('messages')
      .insert({ conversation_id: conversationId, sender_id: this.profile.id, body, ai_assisted: this.profile.role === 'admin' ? aiAssisted : false })
      .select().single();
    throwOn(error);
    if (this.profile.role === 'admin') await this.setConversationStatus(conversationId, 'answered');
    return mapMessage(data);
  }

  async setConversationStatus(conversationId, status) {
    const { data, error } = await this.supabase.from('conversations').update({ status }).eq('id', conversationId).select().single();
    throwOn(error);
    return mapConversation(data);
  }

  async draftWithAi(conversationId) {
    const { data, error } = await this.supabase.functions.invoke('draft-with-ai', { body: { conversation_id: conversationId } });
    throwOn(error);
    if (data && data.error) throw new Error(data.error);
    return { draft: data.draft };
  }

  async createClient(fields) {
    const { data, error } = await this.supabase.from('clients').insert({
      organization: fields.organization,
      stage: fields.stage || 'getting-started',
      governance_tier: fields.governanceTier || '',
      config_label: fields.configLabel || '',
      setup_profile: fields.setupProfile || '',
      last_review: fields.lastReview || null,
      next_review: fields.nextReview || null
    }).select().single();
    throwOn(error);
    return mapClient(data);
  }

  async updateClient(clientId, fields) {
    const patch = {};
    if (fields.organization !== undefined) patch.organization = fields.organization;
    if (fields.stage !== undefined) patch.stage = fields.stage;
    if (fields.governanceTier !== undefined) patch.governance_tier = fields.governanceTier;
    if (fields.configLabel !== undefined) patch.config_label = fields.configLabel;
    if (fields.setupProfile !== undefined) patch.setup_profile = fields.setupProfile;
    if (fields.lastReview !== undefined) patch.last_review = fields.lastReview;
    if (fields.nextReview !== undefined) patch.next_review = fields.nextReview;
    const { data, error } = await this.supabase.from('clients').update(patch).eq('id', clientId).select().single();
    throwOn(error);
    return mapClient(data);
  }

  async publishReport(clientId, fields) {
    const { data, error } = await this.supabase.from('progress_reports').insert({
      client_id: clientId,
      report_date: fields.reportDate || new Date().toISOString().slice(0, 10),
      summary: fields.summary || '',
      accomplishments: fields.accomplishments || [],
      capabilities: fields.capabilities || [],
      risks: fields.risks || [],
      next_priorities: fields.nextPriorities || [],
      acknowledge_note: fields.acknowledgeNote || '',
      published: true
    }).select().single();
    throwOn(error);
    return mapReport(data);
  }

  async updateMilestone(milestoneId, status) {
    const patch = { status, completed_at: status === 'complete' ? new Date().toISOString().slice(0, 10) : null };
    const { data, error } = await this.supabase.from('milestones').update(patch).eq('id', milestoneId).select().single();
    throwOn(error);
    return mapMilestone(data);
  }

  async createMilestone(clientId, fields) {
    const { data: existing } = await this.supabase.from('milestones').select('display_order').eq('client_id', clientId).order('display_order', { ascending: false }).limit(1);
    const order = existing && existing.length ? existing[0].display_order + 1 : 1;
    const { data, error } = await this.supabase.from('milestones').insert({
      client_id: clientId,
      title: fields.title,
      description: fields.description || '',
      display_order: order
    }).select().single();
    throwOn(error);
    return mapMilestone(data);
  }

  async createAction(clientId, fields) {
    const { data, error } = await this.supabase.from('action_items').insert({
      client_id: clientId,
      category: fields.category || 'maintain',
      title: fields.title,
      instructions: fields.instructions || '',
      priority: fields.priority || 'medium',
      owner: fields.owner || 'client',
      due_date: fields.dueDate || null,
      link: fields.link || ''
    }).select().single();
    throwOn(error);
    return mapAction(data);
  }
}
