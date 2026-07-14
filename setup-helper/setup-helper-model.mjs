export const STORAGE_KEY = 'naio.setup-helper.phase1.v1';

export const IDENTITY_ROLES = Object.freeze([
  { value: 'student', label: 'Student' },
  { value: 'staff', label: 'Staff nurse' },
  { value: 'leader', label: 'Nurse leader / manager / educator' },
  { value: 'other', label: 'Other' }
]);

export const POST_SETUP_LANES = Object.freeze([
  { value: 'student_nurse', label: 'Student Nurse' },
  { value: 'staff_nurse', label: 'Staff Nurse' },
  { value: 'nurse_leader_manager', label: 'Nurse Leader and Manager' },
  { value: 'nurse_educator', label: 'Nurse Educator' },
  { value: 'nurse_connected_ally', label: 'Nurse-Connected Ally' }
]);

export const ERROR_CODES = Object.freeze([
  { value: 'download_missing', label: 'A download is missing' },
  { value: 'soul_export_missing', label: 'SOUL files did not download' },
  { value: 'hermes_command_missing', label: 'Terminal says: hermes command not found' },
  { value: 'hermes_doctor_failed', label: 'hermes doctor reported a problem' },
  { value: 'desktop_did_not_open', label: 'Hermes Desktop did not open' },
  { value: 'permission_or_managed_device', label: 'Permission or employer-managed device problem' },
  { value: 'unknown', label: 'Something else happened' }
]);

const BROWSER_FLOW = Object.freeze([
  {
    id: 'browser-boundary',
    title: 'Prepare a no-PHI workspace',
    time: '3 minutes',
    risk: 'Green · A1 advisory',
    why: 'A clean boundary protects patients, your license, your employer, and you.',
    actions: [
      'Use a personal browser profile when possible.',
      'Do not paste patient stories, screenshots, identifiers, credentials, or employer-confidential information.',
      'Create or choose a personal Documents folder for Nurse AI OS files.'
    ],
    verify: 'I am in a personal, no-PHI workspace.'
  },
  {
    id: 'browser-soul',
    title: 'Complete the SOUL Quiz',
    time: '30–45 minutes or multiple sessions',
    risk: 'Green · A1/A2',
    why: 'Broad identity, explicit lane, values, and boundaries make later help more useful without surrendering judgment.',
    actions: [
      'Open the SOUL Quiz in a new tab.',
      'Use broad strokes now and go deeper later.',
      'Download and keep every exported SOUL file on your device.'
    ],
    links: [{ label: 'Open the SOUL Quiz', href: '../soul-quiz.html' }],
    verify: 'I saved my SOUL export files.'
  },
  {
    id: 'browser-starter-kit',
    title: 'Download the Starter Kit',
    time: '5 minutes',
    risk: 'Green · A1',
    why: 'The Starter Kit gives your work one predictable, reviewable home.',
    actions: [
      'Download the ZIP from Nurse AI OS.',
      'Unzip it into Documents or another personal folder you can find again.',
      'Do not place it inside an employer-managed or patient-data folder.'
    ],
    links: [{ label: 'Download the Starter Kit', href: '../assets/nurse-ai-os-starter-kit.zip', download: true }],
    verify: 'I can open the unzipped My-Nurse-AI-OS folder.'
  },
  {
    id: 'browser-first-conversation',
    title: 'Start in the browser AI you already use',
    time: '5–10 minutes',
    risk: 'Green · A2 drafting',
    why: 'Door 1 proves the workflow before you install or connect anything.',
    actions: [
      'Open ChatGPT, Claude, or another browser assistant you already trust for personal no-PHI work.',
      'Paste only the non-sensitive SOUL content you intend the assistant to use; do not upload unrelated folders.',
      'Say: “Treat this as my standing preferences. Show me your plan before you do anything.”'
    ],
    verify: 'The assistant summarized my boundaries accurately, and I corrected anything wrong.'
  },
  {
    id: 'browser-first-win',
    title: 'Complete one safe first task',
    time: '10–15 minutes',
    risk: 'Green · A2 drafting',
    why: 'A reversible personal win builds confidence without expanding authority.',
    actions: ['Use the role-lane prompt shown below.', 'Review the answer yourself.', 'Do not send, publish, schedule, or connect anything from this helper.'],
    verify: 'I reviewed one useful, reversible result.'
  }
]);

const MAC_FLOW = Object.freeze([
  {
    id: 'mac-boundary',
    title: 'Confirm this Mac is appropriate',
    time: '3 minutes',
    risk: 'Green · A1 advisory',
    why: 'Phase 1 is for a personal Mac where you control installation and storage.',
    actions: [
      'Use a personal Mac or one you are explicitly authorized to configure.',
      'If it is employer-managed, stop and use Browser-first unless your organization approves the installation.',
      'Keep patient data, credentials, employer secrets, and clinical workflows out of this setup.'
    ],
    verify: 'This Mac is personal or explicitly authorized, and the workspace is no-PHI.'
  },
  {
    id: 'mac-preflight',
    title: 'Open the pre-procedure checklist',
    time: '5 minutes',
    risk: 'Green · A1 advisory',
    why: 'The checklist explains permissions, provider choices, and recovery in nurse language.',
    actions: ['Read the install section before opening Terminal.', 'Keep this helper open in a separate browser tab.', 'Never paste an API key, password, token, or recovery code into this website.'],
    links: [
      { label: 'Open the Pre-Procedure Checklist', href: '../cheat-sheet.html' },
      { label: 'Open the Nurse AI OS Hermes Guide', href: '../hermes-downloads/' }
    ],
    verify: 'I reviewed the checklist and know where to return if installation stops.'
  },
  {
    id: 'mac-install',
    title: 'Install Hermes from the official source',
    time: '10–20 minutes',
    risk: 'Yellow · human executes',
    why: 'Nurse AI OS never mirrors the installer. The official Nous Research source remains authoritative.',
    actions: [
      'Open the official installation documentation and follow its current macOS instructions.',
      'If you use the Terminal installer, copy only the verified official command shown below.',
      'Read any macOS permission prompt before approving it.'
    ],
    command: 'curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash',
    links: [
      { label: 'Official Hermes installation docs', href: 'https://hermes-agent.nousresearch.com/docs/getting-started/installation', external: true },
      { label: 'Official Hermes site', href: 'https://hermes-agent.nousresearch.com/', external: true }
    ],
    verify: 'The official installer finished without an unresolved error.'
  },
  {
    id: 'mac-doctor',
    title: 'Run the Hermes health check',
    time: '3–10 minutes',
    risk: 'Green · verification',
    why: 'A real health check is stronger evidence than assuming installation worked.',
    actions: ['Open Terminal.', 'Run the health-check command below.', 'If it reports a problem, choose “Something went wrong” instead of continuing.'],
    command: 'hermes doctor',
    verify: 'hermes doctor completed without an unresolved blocking problem.'
  },
  {
    id: 'mac-desktop',
    title: 'Open Hermes Desktop',
    time: '3–10 minutes',
    risk: 'Yellow · local launch',
    why: 'The desktop app gives beginners a familiar chat surface while preserving the same Hermes runtime.',
    actions: [
      'Run the launch command below or follow the official desktop instructions.',
      'Complete model/provider setup inside Hermes—not inside this website.',
      'Do not paste credentials into Setup Helper.'
    ],
    command: 'hermes desktop',
    links: [{ label: 'Official Hermes quick start', href: 'https://hermes-agent.nousresearch.com/docs/getting-started/quickstart', external: true }],
    verify: 'Hermes Desktop opened and I can see its setup or chat screen.'
  },
  {
    id: 'mac-soul',
    title: 'Complete and save your SOUL foundation',
    time: '30–45 minutes or multiple sessions',
    risk: 'Green · A1/A2',
    why: 'Installation provides the engine; SOUL provides your identity, lane, values, and boundaries.',
    actions: ['Open the SOUL Quiz.', 'Use broad strokes now and go deeper later.', 'Save the exported files locally. Do not include PHI or credentials.'],
    links: [{ label: 'Open the SOUL Quiz', href: '../soul-quiz.html' }],
    verify: 'I saved my SOUL export files on this Mac.'
  },
  {
    id: 'mac-starter-kit',
    title: 'Place the Starter Kit in Documents',
    time: '5 minutes',
    risk: 'Green · reversible file setup',
    why: 'A dedicated folder limits confusion and unnecessary file access.',
    actions: ['Download and unzip the Starter Kit.', 'Keep it in a personal Documents location.', 'When Hermes asks for file access, grant only the Nurse AI OS folder—not your full disk, Desktop, Downloads, or Photos.'],
    links: [{ label: 'Download the Starter Kit', href: '../assets/nurse-ai-os-starter-kit.zip', download: true }],
    verify: 'I can open the My-Nurse-AI-OS folder and know its location.'
  },
  {
    id: 'mac-first-conversation',
    title: 'Run one governed first conversation',
    time: '10–15 minutes',
    risk: 'Green · A2 drafting',
    why: 'The first task should prove usefulness while staying reversible and human-judged.',
    actions: [
      'Tell Hermes where your Nurse AI OS folder lives.',
      'Provide only the SOUL content you intend it to use.',
      'Say: “Show me your plan before you do anything. No PHI, no clinical decisions, and no external action.”',
      'Use the role-lane prompt shown below and review the result.'
    ],
    verify: 'I reviewed one useful result and no connector, cron job, memory rule, role pack, or enforcement mode was silently activated.'
  }
]);

export function createInitialState() {
  return {
    schemaVersion: 1,
    stage: 0,
    safety: { noPhi: false, noClinical: false, noSecrets: false, guideOnly: false },
    door: '',
    environment: { device: '', ownership: '', admin: '', browser: '', hermesStatus: '' },
    identityRole: '',
    postSetupLane: '',
    readiness: { time: false, folder: false, recovery: false, boundaries: false },
    route: '',
    flowIndex: 0,
    completedFlowIds: [],
    issueCode: '',
    updatedAt: ''
  };
}

export function determineRoute(state) {
  if (state.door !== 'mac') return 'browser';
  const env = state.environment || {};
  if (env.device !== 'mac' || !['personal', 'authorized'].includes(env.ownership) || env.admin !== 'yes') return 'browser';
  return 'mac';
}

export function getFlow(route) {
  return route === 'mac' ? MAC_FLOW : BROWSER_FLOW;
}

function isRecord(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function hasBooleanShape(value, keys) {
  return isRecord(value) && keys.every((key) => typeof value[key] === 'boolean');
}

export function normalizeSavedState(candidate) {
  if (!isRecord(candidate) || candidate.schemaVersion !== 1) return null;
  if (!Number.isInteger(candidate.stage) || candidate.stage < 0 || candidate.stage > 6) return null;
  if (!hasBooleanShape(candidate.safety, ['noPhi', 'noClinical', 'noSecrets', 'guideOnly'])) return null;
  if (!hasBooleanShape(candidate.readiness, ['time', 'folder', 'recovery', 'boundaries'])) return null;
  if (!isRecord(candidate.environment)) return null;

  const allowed = {
    door: ['', 'browser', 'mac'],
    device: ['', 'mac', 'windows', 'mobile', 'other'],
    ownership: ['', 'personal', 'authorized', 'employer', 'shared'],
    admin: ['', 'yes', 'no'],
    browser: ['', 'chrome', 'safari', 'firefox', 'other'],
    hermesStatus: ['', 'not-installed', 'installed', 'not-sure'],
    identityRole: ['', ...IDENTITY_ROLES.map((item) => item.value)],
    postSetupLane: ['', ...POST_SETUP_LANES.map((item) => item.value)],
    route: ['', 'browser', 'mac'],
    issueCode: ['', ...ERROR_CODES.map((item) => item.value)]
  };
  const fields = [
    ['door', candidate.door],
    ['device', candidate.environment.device],
    ['ownership', candidate.environment.ownership],
    ['admin', candidate.environment.admin],
    ['browser', candidate.environment.browser],
    ['hermesStatus', candidate.environment.hermesStatus],
    ['identityRole', candidate.identityRole],
    ['postSetupLane', candidate.postSetupLane],
    ['route', candidate.route],
    ['issueCode', candidate.issueCode]
  ];
  if (fields.some(([name, value]) => !allowed[name].includes(value))) return null;
  if (!Array.isArray(candidate.completedFlowIds) || candidate.completedFlowIds.some((id) => typeof id !== 'string')) return null;
  if (!Number.isInteger(candidate.flowIndex) || candidate.flowIndex < 0) return null;
  if (typeof candidate.updatedAt !== 'string') return null;
  if (candidate.stage >= 5 && !['browser', 'mac'].includes(candidate.route)) return null;

  const route = candidate.route;
  const flow = route ? getFlow(route) : [];
  if ((!route && (candidate.flowIndex !== 0 || candidate.completedFlowIds.length)) ||
      (route && (candidate.flowIndex >= flow.length || candidate.completedFlowIds.some((id) => !flow.some((step) => step.id === id))))) return null;

  return {
    schemaVersion: 1,
    stage: candidate.stage,
    safety: Object.fromEntries(['noPhi', 'noClinical', 'noSecrets', 'guideOnly'].map((key) => [key, candidate.safety[key]])),
    door: candidate.door,
    environment: Object.fromEntries(['device', 'ownership', 'admin', 'browser', 'hermesStatus'].map((key) => [key, candidate.environment[key]])),
    identityRole: candidate.identityRole,
    postSetupLane: candidate.postSetupLane,
    readiness: Object.fromEntries(['time', 'folder', 'recovery', 'boundaries'].map((key) => [key, candidate.readiness[key]])),
    route,
    flowIndex: candidate.flowIndex,
    completedFlowIds: [...new Set(candidate.completedFlowIds)],
    issueCode: candidate.issueCode,
    updatedAt: candidate.updatedAt
  };
}

export function validateStage(stage, state) {
  if (stage === 0) return ['noPhi', 'noClinical', 'noSecrets', 'guideOnly'].every((key) => state.safety?.[key] === true);
  if (stage === 1) return ['browser', 'mac'].includes(state.door);
  if (stage === 2) {
    const env = state.environment || {};
    return Boolean(env.device && env.ownership && env.admin && env.browser && env.hermesStatus);
  }
  if (stage === 3) {
    return IDENTITY_ROLES.some((r) => r.value === state.identityRole) &&
      POST_SETUP_LANES.some((l) => l.value === state.postSetupLane);
  }
  if (stage === 4) return ['time', 'folder', 'recovery', 'boundaries'].every((key) => state.readiness?.[key] === true);
  return true;
}

export function safeTaskForLane(lane) {
  const tasks = {
    student_nurse: 'No-PHI task: Build a plain-language study map for one public nursing topic. Ask me five Socratic questions, one at a time. Do not use patient data or answer for me.',
    staff_nurse: 'No-PHI task: Draft a personal after-shift recovery checklist based only on the non-sensitive preferences I provide. Do not discuss a patient, unit incident, or clinical decision.',
    nurse_leader_manager: 'No-PHI task: Help me map one generic workflow burden using only public or fictional process steps. Separate burden, possible benefit, possible harm, and the human gate.',
    nurse_educator: 'No-PHI task: Draft a fictional lesson outline for a public nursing topic. Include objectives, an activity, and an academic-integrity reminder. Use no real learner or patient data.',
    nurse_connected_ally: 'No-PHI task: Draft a one-page brief for a project that supports nurses. Separate what I know, what I assume, what nurses must decide, and the smallest reversible next step.'
  };
  return tasks[lane] || tasks.nurse_connected_ally;
}

export function buildSupportSummary(state, issueCode) {
  const route = state.route || determineRoute(state);
  const flow = getFlow(route);
  const current = flow[Math.min(state.flowIndex || 0, flow.length - 1)];
  return [
    'Nurse AI OS Setup Helper — sanitized support summary',
    `Setup door: ${route === 'mac' ? 'macOS Hermes' : 'Browser-first'}`,
    `Device category: ${state.environment?.device || 'not recorded'}`,
    `Ownership: ${state.environment?.ownership || 'not recorded'}`,
    `Current step ID: ${current?.id || 'not started'}`,
    `Broad identity: ${state.identityRole || 'not recorded'}`,
    `Post-setup lane: ${state.postSetupLane || 'not recorded'}`,
    `Issue code: ${issueCode || state.issueCode || 'unknown'}`,
    'No PHI, patient narrative, credentials, or employer-confidential content included: user must confirm before sharing',
    'Expected next action: human review by Nurse AI OS support / Lamp Huddle'
  ].join('\n');
}

export function completionSummary(state) {
  const route = state.route || determineRoute(state);
  const identity = IDENTITY_ROLES.find((x) => x.value === state.identityRole)?.label || state.identityRole;
  const lane = POST_SETUP_LANES.find((x) => x.value === state.postSetupLane)?.label || state.postSetupLane;
  return {
    route,
    identity,
    lane,
    task: safeTaskForLane(state.postSetupLane),
    boundary: 'No PHI. No patient-specific clinical decisions. No credentials. No silent automation.',
    posture: 'This helper does not activate enforcement, connectors, cron, memory, or role packs. Published governance posture remains shadow/observe-only.'
  };
}
