(function () {
  "use strict";

  const APP_VERSION = "2.0.0";
  const PROFILE_SCHEMA = "DISCOVER-MISSION-CONTROL-PROFILE-2";
  const SOUL_PROFILE_SCHEMA = "NAIO-SOUL-PROFILE-ADAPTER-1";
  const DISCOVER_PACKET_SCHEMA = "NAIO-DISCOVER-PACKET-ADAPTER-1";
  const STORAGE_KEY = "discover.nurse-ai-os.mission-control.v2";
  const MAX_IMPORT_BYTES = 1024 * 1024;
  const MAX_SOUL_IMPORT_BYTES = 100 * 1024;
  const MAX_DISCOVER_IMPORT_BYTES = 100 * 1024;

  const GROUPS = [
    {
      id: "direction",
      code: "D",
      name: "Direction & Portfolio",
      archetype: "Purpose Pathfinder",
      color: "var(--group-1)",
      soft: "var(--group-1-soft)",
      icon: "D",
      summary: "Clarify mission, needs, portfolio choices and accountable decision gates.",
      workflowIds: ["DSC-WF-01", "DSC-WF-02", "DSC-WF-03", "DSC-WF-13"]
    },
    {
      id: "evidence",
      code: "I",
      name: "Boundaries & Governance",
      archetype: "Evidence Steward",
      color: "var(--group-2)",
      soft: "var(--group-2-soft)",
      icon: "I",
      summary: "Preserve inquiry integrity, provenance, rights, privacy and official routes.",
      workflowIds: ["DSC-WF-04", "DSC-WF-05", "DSC-WF-06", "DSC-WF-14"]
    },
    {
      id: "rigor",
      code: "S",
      name: "Study & Operational Readiness",
      archetype: "Study Architect",
      color: "var(--group-3)",
      soft: "var(--group-3-soft)",
      icon: "S",
      summary: "Prepare design options, feasibility, measures and readiness questions before results.",
      workflowIds: ["DSC-WF-07", "DSC-WF-08", "DSC-WF-09", "DSC-WF-15"]
    },
    {
      id: "connection",
      code: "C",
      name: "People, Partners & Resources",
      archetype: "Trust Weaver",
      color: "var(--group-4)",
      soft: "var(--group-4-soft)",
      icon: "C",
      summary: "Center reciprocity, community voice, team clarity, resources and succession.",
      workflowIds: ["DSC-WF-10", "DSC-WF-11", "DSC-WF-12", "DSC-WF-23"]
    },
    {
      id: "translation",
      code: "OV",
      name: "Innovation, Value & Translation",
      archetype: "Translation Catalyst",
      color: "var(--group-5)",
      soft: "var(--group-5-soft)",
      icon: "OV",
      summary: "Test bounded assumptions and prepare responsible value, implementation and scale/stop choices.",
      workflowIds: ["DSC-WF-16", "DSC-WF-17", "DSC-WF-18", "DSC-WF-20"]
    },
    {
      id: "renewal",
      code: "ER",
      name: "Evidence, Dissemination & Renewal",
      archetype: "Future Steward",
      color: "var(--group-6)",
      soft: "var(--group-6-soft)",
      icon: "ER",
      summary: "Translate evidence with human voice, govern bounded agents and protect renewal.",
      workflowIds: ["DSC-WF-19", "DSC-WF-21", "DSC-WF-22", "DSC-WF-24"]
    }
  ];

  const WORKFLOWS = [
    wf(1, "Define My Research & Innovation Mission and 90-Day Focus", "PWR-01", "TPL-01", "leader_identity_authority_mission", "direction", "Turn purpose, authority and a 90-day focus into a human-reviewed compass."),
    wf(2, "Frame an Unmet Need Without Locking in a Solution", "PWR-02", "TPL-02", "opportunity_boundary_intake", "direction", "Clarify the need, affected people, evidence gaps and opportunity cost before choosing a solution."),
    wf(3, "Compare Portfolio Options and Prepare a Stop/Continue Decision", "PWR-03", "TPL-03", "portfolio_decision_orchestration", "direction", "Compare options and prepare a named human decision queue with stop/continue questions."),
    wf(4, "Route a Research–QI–Clinical–Innovation Boundary Question", "PWR-04", "TPL-04", "opportunity_boundary_intake", "evidence", "Prepare possible pathways and official review questions without making the classification."),
    wf(5, "Build a Reproducible Evidence and Integrity Trace", "PWR-05", "TPL-05", "evidence_provenance", "evidence", "Bind claims to sources, versions, status, limitations, contradictions and correction routes."),
    wf(6, "Map Data, Privacy, Rights, Retention and IP Questions", "PWR-06", "TPL-06", "data_rights_governance", "evidence", "Surface data-flow, rights, privacy, retention and IP questions for qualified human owners."),
    wf(7, "Draft a Study Concept and Compare Design Options", "PWR-07", "TPL-07", "study_concept_design", "rigor", "Prepare study-concept options, comparators, outcomes and specialist review routes."),
    wf(8, "Prepare Feasibility, Burden and Safety Readiness Questions", "PWR-08", "TPL-09", "feasibility_safety_readiness", "rigor", "Examine capacity, access, burden, continuity, safety routes and stop criteria."),
    wf(9, "Define Outcomes, Measures and Analysis Intent Before Results", "PWR-09", "TPL-10", "measurement_analysis_intent", "rigor", "Predeclare measure definitions, missingness questions, subgroup equity and analysis intent."),
    wf(10, "Plan Reciprocal Participant, Patient and Community Co-Design", "PWR-10", "TPL-11", "engagement_collaboration_plan", "connection", "Prepare accessible, reciprocal co-design questions and feedback-back commitments."),
    wf(11, "Design the Team RACI, Expertise, Partnership and Conflict Map", "PWR-11", "TPL-12", "engagement_collaboration_plan", "connection", "Clarify roles, expertise, conflicts, shared decisions, authorship and exit questions."),
    wf(12, "Prepare a Funding, Grant or Sponsor Readiness Brief", "PWR-12", "TPL-13", "funding_partnership_readiness", "connection", "Compare public requirements, fit, capabilities, milestones and institutional routes."),
    wf(13, "Orchestrate Portfolio Milestones, Dependencies and Decision Gates", "PWR-13", "TPL-14", "portfolio_decision_orchestration", "direction", "Make dependencies, milestones, owners and requested human decisions visible."),
    wf(14, "Prepare Governance and Submission Readiness Without Submitting", "PWR-14", "TPL-15", "governance_submission_readiness", "evidence", "Build a readiness-only checklist for official human and institutional review."),
    wf(15, "Compare Site, Vendor, Technology and Pilot Readiness", "PWR-15", "TPL-16", "feasibility_safety_readiness", "rigor", "Compare capacity, burden, continuity, exit and safety questions without procurement or deployment."),
    wf(16, "Design a Bounded Non-Production Innovation Experiment", "PWR-16", "TPL-17", "innovation_validation_experiment", "translation", "Test the smallest synthetic or non-production assumption with predeclared stop and rollback rules."),
    wf(17, "Build Value, Economics, Equity and Burden Scenarios", "PWR-17", "TPL-18", "value_translation_scenario", "translation", "Prepare ranges and trade-off questions without financial certification or burden transfer."),
    wf(18, "Map Translation, Commercialization and Scale/Stop Gates", "PWR-18", "TPL-19", "value_translation_scenario", "translation", "Prepare responsible translation, maintenance, exit and scale/stop questions."),
    wf(19, "Create an Evidence Landscape and Reproducible Horizon Scan", "PWR-19", "TPL-20", "evidence_provenance", "renewal", "Map public evidence, search logic, source status, gaps and applicability review."),
    wf(20, "Plan Implementation, Adoption Evaluation and Responsible Withdrawal", "PWR-20", "TPL-21", "implementation_evaluation", "translation", "Prepare adoption, learning, maintenance and responsible withdrawal questions."),
    wf(21, "Prepare a Human-Voice Dissemination or Evidence-to-Decision Package", "PWR-21", "TPL-22", "dissemination_output_plan", "renewal", "Prepare audience, claims, limitations, contributor voice and release questions without publishing."),
    wf(22, "Charter and Evaluate One Bounded AI-Agent Run", "PWR-22", "TPL-23", "agent_charter_trace", "renewal", "Prepare a one-run agent charter with exact allowlists, caps, kill and reconciliation—agents remain disabled."),
    wf(23, "Build My Research Leadership, Capability and Succession Plan", "PWR-23", "TPL-24", "leader_identity_authority_mission", "connection", "Map capability, mentoring, protected time, succession and renewal questions."),
    wf(24, "Create My Private Whole-Life Purpose and Renewal Plan", "PWR-24", "TPL-25", "whole_life_private", "renewal", "Prepare an owner-private reflection for an approved encrypted store; this browser never stores its content.")
  ];

  const POWERS = [
    power(1, "Mission, Impact & Research Leadership Compass", "direction"),
    power(2, "Unmet Need & Opportunity Framing Studio", "direction"),
    power(3, "Portfolio Prioritization & Stop/Continue Navigator", "direction"),
    power(4, "Research–QI–Clinical–Innovation Boundary Navigator", "evidence"),
    power(5, "Research Integrity, Reproducibility & Provenance Studio", "evidence"),
    power(6, "Data, Privacy, Rights & IP Governance Mapper", "evidence"),
    power(7, "Study Concept & Design Options Architect", "rigor"),
    power(8, "Feasibility, Participant Burden & Safety Readiness Lens", "rigor"),
    power(9, "Outcomes, Measures & Analysis-Intent Studio", "rigor"),
    power(10, "Participant, Patient, Community & Workforce Co-Design Planner", "connection"),
    power(11, "Scientific Team, Partnership, RACI & Conflict Navigator", "connection"),
    power(12, "Funding, Grant & Sponsor Readiness Studio", "connection"),
    power(13, "Portfolio Milestone, Dependency & Decision Orchestrator", "direction"),
    power(14, "Governance & Submission-Readiness Navigator", "evidence"),
    power(15, "Site, Vendor, Technology & Pilot Readiness Studio", "rigor"),
    power(16, "Innovation Assumption & Bounded Experiment Lab", "translation"),
    power(17, "Value, Health-Economics, Equity & Burden Scenario Studio", "translation"),
    power(18, "Translation, Commercialization & Scale/Stop Pathway Architect", "translation"),
    power(19, "Evidence Landscape, Systematic Search & Horizon-Scan Navigator", "renewal"),
    power(20, "Implementation Science, Adoption & Learning-System Studio", "translation"),
    power(21, "Dissemination, Publication & Evidence-to-Decision Studio", "renewal"),
    power(22, "Responsible AI Use-Case, Agent & Model Governance Command", "renewal"),
    power(23, "Research Leadership, Capability, Career & Succession Builder", "connection"),
    power(24, "Whole-Life Purpose, Capacity & Renewal Navigator", "renewal")
  ];

  const TEMPLATES = [
    "Mission & Impact Compass",
    "Unmet Need & Opportunity Brief",
    "Portfolio Prioritization and Stop/Continue Matrix",
    "FRAME Boundary Classification Intake",
    "TRACE Evidence Provenance Card",
    "Data, Privacy, Rights and IP Governance Intake",
    "Study Concept Synopsis",
    "Design Options, Bias and Validity Canvas",
    "Feasibility, Burden and Safety Readiness Checklist",
    "Outcome, Measure and Analysis-Intent Shell",
    "Participant, Patient and Community Co-Design Plan",
    "Team RACI, Expertise and Conflict Disclosure Map",
    "Funding, Grant and Partner Readiness Brief",
    "Portfolio Milestone, Dependency and Decision Board",
    "Governance and Submission-Readiness Checklist",
    "Site, Vendor, Technology and Pilot Readiness Matrix",
    "PROBE Assumption and Experiment Card",
    "Value, Economics, Equity and Burden Scenario",
    "Translation, Commercialization and Scale/Stop Pathway",
    "Evidence Landscape and Horizon-Scan Map",
    "Implementation Strategy and Adoption Evaluation Plan",
    "Dissemination, Publication and Evidence-to-Decision Plan",
    "ORBIT Agent Charter and One-Run Evaluation Card",
    "Leadership Capability, Career and Succession Plan",
    "Private Whole-Life Purpose and Renewal Plan",
    "Participant Rights and Consent Question Set",
    "Data Management, Retention and Sharing Plan",
    "Source, Policy, Registry and Obligation Watch Card",
    "Decision, Approval, Exception and Escalation Receipt",
    "After-Action, Learning and Closeout Record"
  ].map((title, index) => ({ id: `TPL-${String(index + 1).padStart(2, "0")}`, title }));

  const ROLES = [
    role("shared-identity", "My Shared Mission Control", "A neutral whole-person starting view for values, learning, planning, life goals and governed AI boundaries before any professional role is selected.", [1, 2, 5, 24]),
    role("research-innovation", "Healthcare Research & Innovation Leader", "Cross-portfolio mission, evidence, implementation, human partnership and responsible innovation.", [1, 3, 4, 13, 19, 20]),
    role("prelicensure-support", "Pre-licensure Student or Nursing Assistant", "Foundational learning, supervised care, academic integrity, escalation, work-school balance and future formation.", [1, 2, 8, 23]),
    role("staff-nurse", "Staff Nurse & Quality Contributor", "Practice improvement, evidence, teamwork, safe escalation, quality participation and professional renewal.", [2, 4, 5, 20]),
    role("advanced-practice", "Advanced-Practice Clinician", "Advanced assessment support, evidence synthesis, care orchestration, professional growth and accountable judgment.", [5, 7, 9, 20]),
    role("nurse-educator", "Nurse Educator or Clinical Preceptor", "Learner-centered design, simulation, assessment integrity, feedback, faculty workflow and evidence-based education.", [5, 7, 10, 21]),
    role("medical-resident", "Medical Resident or Fellow", "Postgraduate learning, care orchestration, evidence, team communication and governed AI-agent supervision.", [5, 8, 13, 22]),
    role("nurse-manager", "Nurse Leader or Healthcare Manager", "People, quality, operations, staffing, culture, strategy and accountable organizational decisions.", [1, 3, 11, 20]),
    role("clinic-manager", "Clinic Manager", "Access, flow, patient experience, workforce coordination, quality, capacity and community responsiveness.", [2, 8, 13, 20]),
    role("hospital-administrator", "Hospital Administrator", "Enterprise strategy, operations, quality, finance questions, governance, innovation and stakeholder alignment.", [3, 13, 17, 20]),
    role("wellness-manager", "Wellness Services Marketer or Manager", "Ethical service design, engagement, trust, outcomes, marketing boundaries and sustainable growth.", [2, 10, 17, 21]),
    role("quality-safety", "Quality, Safety or Governance Contributor", "Measures, risk, improvement cycles, systems learning, escalation and responsible implementation.", [4, 9, 14, 20]),
    role("researcher", "Researcher or Evidence Specialist", "Question design, reproducible evidence, study rigor, dissemination and integrity.", [5, 7, 9, 19]),
    role("digital-ai", "Digital Health, Informatics or Responsible-AI Leader", "Intended use, data governance, human factors, monitoring, agent containment, kill and rollback.", [6, 16, 18, 22]),
    role("entrepreneur", "Healthcare Entrepreneur or Consultant", "Need validation, bounded experimentation, responsible value, partnership, commercialization and scale/stop choices.", [2, 12, 16, 18]),
    role("community", "Community, Family or Personal Advocate", "Personal, family, business and community missions supported by safe planning, learning and service.", [1, 2, 10, 24]),
    role("advanced-studies", "Advanced Studies Overlay", "Certification, degree, residency, fellowship, specialization or continuing professional development alongside another role.", [1, 5, 23, 24])
  ];

  const DIMENSIONS = [
    { id: "direction", label: "Direction & Discovery", archetype: "Purpose Pathfinder", tagline: "You begin with purpose, possibility and the courage to name the real need." },
    { id: "evidence", label: "Inquiry & Integrity", archetype: "Evidence Steward", tagline: "You protect trustworthy questions, traceable evidence and clean boundaries." },
    { id: "rigor", label: "Study Design & Rigor", archetype: "Study Architect", tagline: "You give promising ideas structure, testability and scientific discipline." },
    { id: "connection", label: "Collaboration & Dignity", archetype: "Trust Weaver", tagline: "You build legitimacy through reciprocity, voice, clarity and shared ownership." },
    { id: "translation", label: "Operations, Value & Translation", archetype: "Translation Catalyst", tagline: "You turn insight into bounded experiments, implementation and responsible value." },
    { id: "renewal", label: "Responsible Innovation & Renewal", archetype: "Future Steward", tagline: "You hold the long view: evidence, human voice, governed agents and sustainable renewal." }
  ];

  const QUIZ = [
    q(1, "direction", "When an opportunity appears, I first reconnect it to mission, affected people and the change that truly matters."),
    q(2, "direction", "I am energized by framing an unmet need before anyone locks in a favored solution."),
    q(3, "evidence", "I instinctively ask what is fact, interpretation, assumption, contradiction or still unknown."),
    q(4, "evidence", "Source versions, corrections, rights, privacy and governance routes are part of the work—not paperwork after it."),
    q(5, "rigor", "I enjoy turning a promising question into design options, measures and testable assumptions."),
    q(6, "rigor", "I want feasibility, burden, bias and safety questions visible before results create momentum."),
    q(7, "connection", "The quality of a project depends on whose voice, expertise and lived experience shape it."),
    q(8, "connection", "I naturally clarify roles, conflicts, shared decisions, reciprocity and how learning returns to people."),
    q(9, "translation", "I am drawn to the smallest responsible experiment that can reduce uncertainty without creating hidden burden."),
    q(10, "translation", "Implementation, value, maintenance and stopping rules matter as much as the original idea."),
    q(11, "renewal", "I think about how evidence will travel, how AI agents will be contained and how people remain accountable."),
    q(12, "renewal", "I protect capacity, succession and renewal so that important work can continue without consuming its people.")
  ];

  const MISSION_STAGES = [
    { id: "assess", label: "Assess" },
    { id: "define", label: "Define or Diagnose" },
    { id: "plan", label: "Plan" },
    { id: "implement", label: "Implement" },
    { id: "evaluate", label: "Evaluate" }
  ];

  const ARTIFACT_STATES = ["exploration", "simulation", "recommendation", "draft_artifact", "approved_plan", "authorized_execution", "completed_action", "evaluated_outcome"];
  const ROLE_STATES = ["primary", "supporting", "emerging", "contextual"];
  const EDENA_POLICY = {
    id: "EDENA-MC-ADVISORY",
    version: "1.0.0-draft",
    tiers: {
      unclassified: { label: "Unclassified · Preview Only", summary: "Classify the context before any handoff. Exploration remains local and no external action is available." },
      green: { label: "EDENA Green · bounded", summary: "Low-consequence, reversible sandbox work using public, synthetic or approved non-sensitive information." },
      yellow: { label: "EDENA Yellow · verify", summary: "Facts, scope, evidence, intended use or destination require deliberate verification before handoff." },
      orange: { label: "EDENA Orange · qualified review", summary: "High-consequence, complex, sensitive or automation-related work requires structured qualified-human review." },
      red: { label: "EDENA Red · high-risk advisory", summary: "Potential for serious harm, unauthorized scope/data/action or consequential use without required authority. Sanitized exploration only." }
    }
  };

  const CAPABILITIES = [
    capability("ai-literacy", "AI literacy", "Model limits, appropriate tool choice and hallucination awareness."),
    capability("prompt-design", "Prompt design", "Versioned instructions, constraints, tests and failure handling."),
    capability("evidence-research", "Evidence-informed research", "Reproducible search, provenance, appraisal and contradiction handling."),
    capability("critical-thinking", "Critical thinking", "Facts, assumptions, unknowns, alternatives and bias challenge."),
    capability("structured-problem-solving", "Structured problem-solving", "Complete, evaluated and repeated five-stage missions."),
    capability("workflow-design", "Workflow design", "Inputs, outputs, human gates, exceptions, rollback and measures."),
    capability("project-management", "Project management", "Milestones, dependencies, risk, ownership and outcome review."),
    capability("privacy-stewardship", "Data & privacy stewardship", "Classification, minimization, retention and safe substitutes."),
    capability("ethical-ai", "Ethical AI practice", "Stakeholders, harms, bias, mitigation and escalation."),
    capability("edena-governance", "EDENA governance", "Classification, reason, acknowledgment, review and stopping behavior."),
    capability("agent-supervision", "Agent supervision", "Output inspection, exception handling, stop decisions and run review."),
    capability("multi-agent", "Multi-agent orchestration", "Task graphs, permissions, conflict adjudication and recovery."),
    capability("knowledge-base", "Knowledge-base development", "Curated sources, provenance, freshness and retrieval evaluation."),
    capability("automation-design", "Automation design", "Preview prototypes, authority gates, monitored tests and rollback."),
    capability("artifact-creation", "Artifact creation", "Versioning, accuracy, accessibility and approved release states."),
    capability("evaluation-qi", "Evaluation & quality improvement", "Baseline, measures, comparison, limitations and next-cycle decision."),
    capability("role-development", "Role-specific professional development", "Growth evidence within the role boundary—never credential verification.")
  ];

  const MASTERY_LEVELS = [
    { id: "none", label: "Not started", minimum: 0 },
    { id: "basic", label: "Basic", minimum: 1 },
    { id: "intermediate", label: "Intermediate", minimum: 3 },
    { id: "advanced", label: "Advanced", minimum: 6 },
    { id: "master", label: "AI Agent Orchestration Master", minimum: 10 }
  ];

  const QUICK_LAUNCH_IDS = ["DSC-WF-04", "DSC-WF-19", "DSC-WF-03", "DSC-WF-16"];
  const ALLOWED_ROLE_IDS = new Set(ROLES.map((item) => item.id));
  const ALLOWED_WORKFLOW_IDS = new Set(WORKFLOWS.map((item) => item.id));
  const ALLOWED_DIMENSION_IDS = new Set(DIMENSIONS.map((item) => item.id));
  const ALLOWED_CAPABILITY_IDS = new Set(CAPABILITIES.map((item) => item.id));
  const ALLOWED_STAGE_IDS = new Set(MISSION_STAGES.map((item) => item.id));

  let state = loadState();
  let workflowFilter = "all";
  let activeWorkflow = null;
  let activeMissionStage = "assess";
  let pendingSoulProfile = null;
  let pendingDiscoverPacket = null;
  let onboardingStep = 0;
  let toastTimer = null;

  const el = {};

  document.addEventListener("DOMContentLoaded", init);

  function wf(number, title, powerId, templateId, schema, groupId, description) {
    const short = `WF-${String(number).padStart(2, "0")}`;
    return { id: `DSC-${short}`, short, number, title, powerId, templateId, schema, groupId, description };
  }

  function power(number, title, groupId) {
    return { id: `PWR-${String(number).padStart(2, "0")}`, number, title, groupId };
  }

  function role(id, name, summary, workflowNumbers) {
    return { id, name, summary, workflowIds: workflowNumbers.map((n) => `DSC-WF-${String(n).padStart(2, "0")}`) };
  }

  function q(number, dimension, prompt) { return { number, dimension, prompt }; }
  function capability(id, name, description) { return { id, name, description }; }

  function init() {
    cacheElements();
    ensureDashboardPartitions();
    bindNavigation();
    bindControls();
    renderQuiz();
    renderAll();
    const requested = String(location.hash || "").replace(/^#/, "");
    const initialView = document.querySelector(`[data-view-panel="${cssEscape(requested)}"]`) ? requested : "dashboard";
    showView(initialView, false);
    updateMobileSidebarState();
    window.addEventListener("resize", updateMobileSidebarState);
    if (!state.onboardingComplete) window.setTimeout(() => openOnboarding(0), 180);
  }

  function cacheElements() {
    [
      "sidebar", "menuButton", "pageTitle", "roleSelect", "activeRolePill", "heroTitle", "heroCopy", "heroSoulButton",
      "soulSummaryTitle", "soulSummaryCopy", "roleMetric", "quickLaunchGrid", "roleFocusCard", "attentionList", "groupGrid",
      "workflowSearch", "workflowFilters", "workflowGrid", "workflowEmpty", "powerSections", "templateLibrary", "soulQuizForm", "quizQuestions",
      "quizConsent", "quizStatus", "quizResultHeading", "quizResultCopy", "dimensionBars", "quizResultActions", "downloadSoulProfile",
      "deleteSoulProfile", "roleForm", "roleGrid", "roleStatus", "exportHermesProfile", "exportProfile", "importProfile", "resetProfile",
      "profileStatus", "workflowDialog", "workflowDialogForm", "workflowDialogMeta", "workflowDialogTitle", "workflowDialogDetails",
      "workflowContext", "handoffEdena", "handoffEdenaReason", "handoffConsent", "handoffStatus", "buildHandoff", "cancelHandoff", "closeWorkflowDialog", "handoffOutputWrap",
      "handoffOutput", "copyHandoff", "downloadHandoff", "rebuildHandoff", "hermesUrl", "openHermes", "toast",
      "startMissionHero", "missionMetric", "badgeMetric", "newMission", "emptyStartMission", "loadSampleMission", "missionCount",
      "missionList", "missionListEmpty", "missionEmptyState", "missionForm", "missionId", "missionTitle", "missionRole", "missionEdition",
      "missionEdena", "missionEdenaReason", "missionArtifactState", "missionStatusState", "missionRetention", "missionSummary", "missionEdenaPanel", "missionGatePanel", "missionRiskAck",
      "institutionalGate", "missionApprovalAttested", "missionApprovalRef", "missionProgress", "missionProgressBar", "missionProgressText", "saveMission",
      "prepareMissionHandoff", "startNextIteration", "deleteMission", "missionStatus", "stageAssessNotes", "stageAssessOutcome",
      "stageAssessComplete", "stageDefineNotes", "stageDefineOutcome", "stageDefineComplete", "stagePlanNotes", "stagePlanOutcome",
      "stagePlanComplete", "stageImplementNotes", "stageImplementOutcome", "stageImplementComplete", "stageEvaluateNotes",
      "stageEvaluateOutcome", "stageEvaluateComplete", "missionHandoffDialog", "missionHandoffMeta", "missionHandoffTitle",
      "closeMissionHandoff", "missionHandoffOutput", "missionHandoffReview", "copyMissionHandoff", "downloadMissionHandoff",
      "missionHermesUrl", "openMissionHermes", "missionHandoffStatus", "capabilityGrid", "capabilityEvidenceCount", "evidenceForm",
      "evidenceCapability", "evidenceMission", "evidenceType", "evidenceProvenance", "evidenceEdena", "evidenceSummary",
      "evidenceAttestation", "evidenceStatus", "evidenceList", "exportCapabilityReport", "downloadSoulTemplate", "importSoulProfile",
      "loadSampleSoul", "restoreSoulProfile", "clearSoulProfile", "soulProfileStatus", "soulProfilePreviewHeading", "soulProfilePreview", "soulPreviewActions",
      "applySoulProfile", "cancelSoulPreview", "onboardingDialog", "closeOnboarding", "onboardingProgress", "onboardingSafetyAck",
      "onboardingBack", "onboardingNext", "onboardingFinish", "restartOnboarding", "downloadDiscoverTemplate", "importDiscoverPacket",
      "loadSampleDiscover", "clearDiscoverPacket", "discoverPacketStatus", "discoverPacketPreviewHeading", "discoverPacketPreview",
      "discoverPacketPreviewActions", "applyDiscoverPacket", "cancelDiscoverPacketPreview"
    ].forEach((id) => { el[id] = document.getElementById(id); });
  }

  function bindNavigation() {
    document.querySelectorAll("[data-view]").forEach((button) => {
      button.addEventListener("click", () => showView(button.dataset.view));
    });
    document.querySelectorAll("[data-view-target]").forEach((button) => {
      button.addEventListener("click", () => showView(button.dataset.viewTarget));
    });
    el.menuButton.addEventListener("click", () => {
      const open = el.sidebar.classList.toggle("is-open");
      el.menuButton.setAttribute("aria-expanded", String(open));
      updateMobileSidebarState();
      if (open) el.sidebar.querySelector(".nav-item")?.focus();
    });
    document.querySelectorAll(".file-button").forEach((label) => {
      label.addEventListener("keydown", (event) => {
        if (!["Enter", " "].includes(event.key)) return;
        event.preventDefault();
        document.getElementById(label.htmlFor)?.click();
      });
    });
  }

  function bindControls() {
    el.roleSelect.addEventListener("change", () => {
      if (!state.selectedRoleIds.includes(el.roleSelect.value)) return;
      state.activeRoleId = el.roleSelect.value;
      saveState();
      renderAll();
      announce("Role dashboard changed. This does not grant authority.");
    });

    el.workflowSearch.addEventListener("input", renderWorkflows);
    el.soulQuizForm.addEventListener("submit", completeSoulQuiz);
    el.soulQuizForm.addEventListener("reset", () => setStatus(el.quizStatus, "Answers cleared. Nothing was saved.", true));
    el.downloadSoulProfile.addEventListener("click", exportProfile);
    el.deleteSoulProfile.addEventListener("click", deleteSoulResult);
    el.roleForm.addEventListener("submit", saveRoleDashboards);
    el.exportHermesProfile.addEventListener("click", exportHermesHandoff);
    el.exportProfile.addEventListener("click", exportProfile);
    el.importProfile.addEventListener("change", importProfile);
    el.resetProfile.addEventListener("click", resetProfile);

    el.closeWorkflowDialog.addEventListener("click", closeWorkflowDialog);
    el.cancelHandoff.addEventListener("click", closeWorkflowDialog);
    el.workflowDialog.addEventListener("cancel", () => clearTransientHandoff());
    el.workflowDialog.addEventListener("click", (event) => {
      if (event.target === el.workflowDialog) closeWorkflowDialog();
    });
    el.buildHandoff.addEventListener("click", buildHandoff);
    el.copyHandoff.addEventListener("click", copyHandoff);
    el.downloadHandoff.addEventListener("click", downloadHandoff);
    el.openHermes.addEventListener("click", openHermesSeparately);
    el.rebuildHandoff.addEventListener("click", () => {
      el.handoffOutputWrap.hidden = true;
      el.workflowContext.focus();
    });

    [el.startMissionHero, el.newMission, el.emptyStartMission].forEach((button) => button.addEventListener("click", () => createMission(false)));
    el.loadSampleMission.addEventListener("click", () => createMission(true));
    el.missionForm.addEventListener("submit", saveMissionFromForm);
    const stageTabs = Array.from(document.querySelectorAll("[data-mission-stage]"));
    stageTabs.forEach((button, index) => {
      button.addEventListener("click", () => selectMissionStage(button.dataset.missionStage));
      button.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const nextIndex = event.key === "Home" ? 0 : event.key === "End" ? stageTabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + stageTabs.length) % stageTabs.length;
        selectMissionStage(stageTabs[nextIndex].dataset.missionStage);
        stageTabs[nextIndex].focus();
      });
    });
    [el.missionEdition, el.missionEdena, el.missionArtifactState, el.missionStatusState].forEach((control) => control.addEventListener("change", renderMissionGovernance));
    el.prepareMissionHandoff.addEventListener("click", prepareMissionHandoff);
    el.startNextIteration.addEventListener("click", beginNextIteration);
    el.deleteMission.addEventListener("click", deleteActiveMission);
    el.missionHandoffReview.addEventListener("change", () => {
      el.copyMissionHandoff.disabled = !el.missionHandoffReview.checked;
      el.downloadMissionHandoff.disabled = !el.missionHandoffReview.checked;
    });
    el.closeMissionHandoff.addEventListener("click", closeMissionHandoff);
    el.missionHandoffDialog.addEventListener("cancel", closeMissionHandoff);
    el.copyMissionHandoff.addEventListener("click", () => copyText(el.missionHandoffOutput, "Mission handoff copied. It was not sent."));
    el.downloadMissionHandoff.addEventListener("click", downloadMissionStageHandoff);
    el.openMissionHermes.addEventListener("click", openMissionHermesSeparately);

    el.evidenceForm.addEventListener("submit", addCapabilityEvidence);
    el.exportCapabilityReport.addEventListener("click", exportCapabilityReport);
    el.downloadSoulTemplate.addEventListener("click", downloadSoulProfileTemplate);
    el.importSoulProfile.addEventListener("change", importSoulProfileFile);
    el.loadSampleSoul.addEventListener("click", previewSampleSoulProfile);
    el.applySoulProfile.addEventListener("click", applyPendingSoulProfile);
    el.cancelSoulPreview.addEventListener("click", cancelSoulPreview);
    el.restoreSoulProfile.addEventListener("click", restorePreviousSoulProfile);
    el.clearSoulProfile.addEventListener("click", clearAppliedSoulProfile);
    el.downloadDiscoverTemplate.addEventListener("click", downloadDiscoverPacketTemplate);
    el.importDiscoverPacket.addEventListener("change", importDiscoverPacketFile);
    el.loadSampleDiscover.addEventListener("click", previewSampleDiscoverPacket);
    el.applyDiscoverPacket.addEventListener("click", applyPendingDiscoverPacket);
    el.cancelDiscoverPacketPreview.addEventListener("click", cancelDiscoverPacketPreview);
    el.clearDiscoverPacket.addEventListener("click", clearAppliedDiscoverPacket);

    el.closeOnboarding.addEventListener("click", closeOnboardingWithoutFinish);
    el.onboardingBack.addEventListener("click", () => showOnboardingStep(onboardingStep - 1));
    el.onboardingNext.addEventListener("click", advanceOnboarding);
    el.onboardingFinish.addEventListener("click", finishOnboarding);
    el.onboardingDialog.addEventListener("cancel", (event) => {
      if (!state.onboardingComplete) {
        event.preventDefault();
        showOnboardingStep(1);
        announce("Review and acknowledge the safety boundary before entering Mission Control.");
      }
    });
    el.restartOnboarding.addEventListener("click", () => openOnboarding(0));
  }

  function showView(viewId, updateHash = true) {
    const panel = document.querySelector(`[data-view-panel="${cssEscape(viewId)}"]`);
    if (!panel) return;
    document.querySelectorAll("[data-view-panel]").forEach((item) => {
      const visible = item === panel;
      item.hidden = !visible;
      item.classList.toggle("is-visible", visible);
    });
    document.querySelectorAll(".nav-item").forEach((item) => {
      const active = item.dataset.view === viewId;
      item.classList.toggle("is-active", active);
      if (active) item.setAttribute("aria-current", "page");
      else item.removeAttribute("aria-current");
    });
    const titles = {
      dashboard: "My DISCOVER Mission Control",
      missions: "Governed Mission Loop",
      workflows: "Workflow Launchers",
      powers: "24 DISCOVER SuperPowers",
      soul: "Soul Profile & Personalization",
      roles: "My Role Dashboards",
      capabilities: "Capabilities & Mastery",
      guide: "DISCOVER Guide"
    };
    el.pageTitle.textContent = titles[viewId] || "My DISCOVER Mission Control";
    if (viewId === "guide") {
      state.guideSeen = true;
      saveState();
      renderAttention();
    }
    if (updateHash) {
      try {
        if (history.replaceState) history.replaceState(null, "", viewId === "dashboard" ? `${location.pathname}${location.search}` : `#${viewId}`);
        else location.hash = viewId === "dashboard" ? "" : viewId;
      } catch (_error) {
        location.hash = viewId === "dashboard" ? "" : viewId;
      }
    }
    el.sidebar.classList.remove("is-open");
    el.menuButton.setAttribute("aria-expanded", "false");
    updateMobileSidebarState();
    document.getElementById("main-content").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  function updateMobileSidebarState() {
    const mobile = typeof window.matchMedia === "function" && window.matchMedia("(max-width: 900px)").matches;
    const open = el.sidebar.classList.contains("is-open");
    el.sidebar.inert = Boolean(mobile && !open);
    if (mobile && !open) el.sidebar.setAttribute("aria-hidden", "true");
    else el.sidebar.removeAttribute("aria-hidden");
  }

  function renderAll() {
    applySoulTheme();
    renderRoleSwitcher();
    renderDashboard();
    renderWorkflowFilters();
    renderWorkflows();
    renderPowers();
    renderTemplates();
    renderSoulResult();
    renderRoles();
    renderMissions();
    renderCapabilities();
    renderSoulProfileState();
    renderDiscoverPacketState();
  }

  function renderDashboard() {
    const activeRole = getActiveRole();
    const soul = getSoulPresentation();
    el.activeRolePill.textContent = activeRole.name;
    el.heroTitle.textContent = soul.hero;
    el.heroCopy.textContent = `${activeRole.summary} ${soul.coaching}`;
    el.heroSoulButton.textContent = state.soulProfile ? "Review my Soul Profile" : (state.soul ? "Review provisional presentation" : "Import Soul results");
    el.missionMetric.textContent = String(state.missions.filter((mission) => !mission.sample).length);
    el.roleMetric.textContent = String(state.selectedRoleIds.length);
    el.badgeMetric.textContent = String(CAPABILITIES.filter((item) => capabilityLevel(item.id).id !== "none").length);
    renderSoulSummary();
    renderQuickLaunchers();
    renderRoleFocus();
    renderAttention();
    renderGroups();
  }

  function renderRoleSwitcher() {
    el.roleSelect.replaceChildren();
    state.selectedRoleIds.forEach((roleId) => {
      const item = getRole(roleId);
      if (!item) return;
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = `${item.name} · ${state.roleStates[item.id] || "supporting"}`;
      option.selected = item.id === state.activeRoleId;
      el.roleSelect.append(option);
    });
  }

  function renderSoulSummary() {
    if (state.soulProfile) {
      const primary = state.soulProfile.role_constellation.find((roleItem) => roleItem.state === "primary") || state.soulProfile.role_constellation[0];
      el.soulSummaryTitle.textContent = primary ? `Personalized · ${primary.label}` : "Personalized Soul Profile";
      el.soulSummaryCopy.textContent = state.soulProfile.mission_and_purpose.mission || "Your shared values, roles and governance preferences are active.";
      return;
    }
    if (!state.soul) {
      el.soulSummaryTitle.textContent = state.discoverPacket ? "Discover Packet active · Soul neutral" : "Not yet personalized";
      el.soulSummaryCopy.textContent = state.discoverPacket ? (state.discoverPacket.mission_statement || "Goals and governance settings are active; Soul presentation remains neutral.") : "Import approved derived Soul Quiz results when available. Mission Control is fully usable in neutral mode.";
      return;
    }
    const result = getSoulPresentation();
    el.soulSummaryTitle.textContent = result.title;
    el.soulSummaryCopy.textContent = result.tagline;
  }

  function renderQuickLaunchers() {
    el.quickLaunchGrid.replaceChildren();
    const packetLaunchers = state.discoverPacket ? state.discoverPacket.recommended_workflow_ids.slice(0, 4) : [];
    unique(packetLaunchers.concat(QUICK_LAUNCH_IDS)).slice(0, 4).forEach((id) => {
      const item = getWorkflow(id);
      const group = getGroup(item.groupId);
      const card = document.createElement("article");
      card.className = "quick-card";
      setGroupVars(card, group);
      const icon = node("div", "card-icon", group.icon);
      icon.setAttribute("aria-hidden", "true");
      card.append(icon, node("h3", "", item.title), node("p", "", item.description));
      const button = node("button", "text-button", "Prepare preview →");
      button.type = "button";
      button.addEventListener("click", () => openWorkflowDialog(item.id));
      card.append(button);
      el.quickLaunchGrid.append(card);
    });
  }

  function renderRoleFocus() {
    const activeRole = getActiveRole();
    const wrapper = node("article", "role-focus-card");
    wrapper.append(node("h3", "", activeRole.name), node("p", "", activeRole.summary));
    const roleGoal = state.discoverPacket && state.discoverPacket.role_goals.find((item) => item.role_id === activeRole.id);
    if (roleGoal) wrapper.append(node("p", "role-goal-copy", `Packet goal: ${roleGoal.goal} · Success: ${roleGoal.success_measure} · Default EDENA ${roleGoal.default_edena.toUpperCase()}`));
    const note = node("p", "", "View-only recipe · does not verify identity or authority");
    note.className = "section-note";
    wrapper.append(note);
    const row = node("div", "workflow-chip-row");
    activeRole.workflowIds.forEach((id) => {
      const item = getWorkflow(id);
      const button = node("button", "workflow-chip", item.short);
      button.type = "button";
      button.title = item.title;
      button.addEventListener("click", () => openWorkflowDialog(id));
      row.append(button);
    });
    wrapper.append(row);
    el.roleFocusCard.replaceChildren(wrapper);
  }

  function renderAttention() {
    const activeRole = getActiveRole();
    const favorites = currentFavorites();
    const items = [];
    if (state.discoverPacket) state.discoverPacket.current_priorities.slice(0, 2).forEach((priority) => items.push(`Discover priority: ${priority}`));
    else items.push("Import a reviewed derived Discover Packet—or define goals safely through a mission.");
    if (!state.soulProfile) items.push("Import an approved derived Soul Profile when the redesigned quiz is ready—or continue safely in neutral mode.");
    if (!state.guideSeen) items.push("Read the embedded Guide before the first Hermes handoff.");
    const activeMissions = state.missions.filter((mission) => mission.roleId === state.activeRoleId && !mission.sample);
    if (activeMissions.length) items.push(`Resume ${activeMissions.length} mission${activeMissions.length === 1 ? "" : "s"} owned by this role dashboard.`);
    else items.push("Start a mission to turn a goal into an Assess–Define–Plan–Implement–Evaluate loop.");
    items.push(`Confirm that “${activeRole.name}” is only your current view—not proof of delegated authority.`);
    items.push("Confirm Preview Only, D0/D1 metadata, agents disabled and external actions off.");
    activeRole.workflowIds.slice(0, 2).forEach((id) => items.push(`Consider ${getWorkflow(id).short}: ${getWorkflow(id).title}.`));
    if (favorites.length) items.push(`Review ${favorites.length} favorite workflow${favorites.length === 1 ? "" : "s"} for this role dashboard.`);
    else items.push("Favorite a workflow to create a role-specific starting shelf.");
    el.attentionList.replaceChildren();
    items.slice(0, 7).forEach((text) => el.attentionList.append(node("li", "", text)));
  }

  function renderGroups() {
    el.groupGrid.replaceChildren();
    getOrderedGroups().forEach((group) => {
      const card = node("article", "group-card");
      setGroupVars(card, group);
      const header = node("div", "group-card-header");
      const icon = node("div", "card-icon", group.icon);
      icon.setAttribute("aria-hidden", "true");
      const title = node("h3", "", group.name);
      const count = node("span", "count", "4");
      count.setAttribute("aria-label", "4 workflows");
      header.append(icon, title, count);
      card.append(header, node("p", "", group.summary));
      el.groupGrid.append(card);
    });
  }

  function renderWorkflowFilters() {
    el.workflowFilters.replaceChildren();
    [{ id: "all", name: "All 24" }, { id: "favorites", name: "★ Favorites" }].concat(GROUPS).forEach((item) => {
      const button = node("button", "filter-button", item.name);
      button.type = "button";
      button.dataset.filter = item.id;
      button.setAttribute("aria-pressed", String(workflowFilter === item.id));
      button.addEventListener("click", () => {
        workflowFilter = item.id;
        renderWorkflowFilters();
        renderWorkflows();
      });
      el.workflowFilters.append(button);
    });
  }

  function renderWorkflows() {
    if (!el.workflowGrid) return;
    const search = el.workflowSearch.value.trim().toLocaleLowerCase();
    const favorites = currentFavorites();
    const recommended = new Set(getActiveRole().workflowIds.concat(state.discoverPacket ? state.discoverPacket.recommended_workflow_ids : []));
    const ordered = WORKFLOWS.slice().sort((a, b) => {
      const aScore = (recommended.has(a.id) ? 2 : 0) + (favorites.includes(a.id) ? 1 : 0);
      const bScore = (recommended.has(b.id) ? 2 : 0) + (favorites.includes(b.id) ? 1 : 0);
      return bScore - aScore || a.number - b.number;
    });
    const items = ordered.filter((item) => {
      if (workflowFilter === "favorites" && !favorites.includes(item.id)) return false;
      if (workflowFilter !== "all" && workflowFilter !== "favorites" && item.groupId !== workflowFilter) return false;
      if (!search) return true;
      return [item.id, item.short, item.title, item.templateId, item.schema, item.description].join(" ").toLocaleLowerCase().includes(search);
    });

    el.workflowGrid.replaceChildren();
    items.forEach((item) => {
      const group = getGroup(item.groupId);
      const card = node("article", "workflow-card");
      setGroupVars(card, group);
      if (recommended.has(item.id)) card.classList.add("is-recommended");
      const header = node("div", "workflow-card-header");
      header.append(node("span", "workflow-id", item.id));
      const favorite = node("button", "favorite-button", favorites.includes(item.id) ? "★" : "☆");
      favorite.type = "button";
      favorite.setAttribute("aria-label", `${favorites.includes(item.id) ? "Remove" : "Add"} ${item.short} ${favorites.includes(item.id) ? "from" : "to"} favorites for this role view`);
      favorite.setAttribute("aria-pressed", String(favorites.includes(item.id)));
      favorite.addEventListener("click", () => toggleFavorite(item.id));
      header.append(favorite);
      const meta = node("div", "workflow-meta");
      meta.append(node("span", "", "Preview Only"), node("span", "", item.powerId), node("span", "", item.templateId));
      card.append(header, node("h3", "", item.title), meta, node("p", "", item.description));
      const actions = node("div", "button-row");
      const launch = node("button", "primary-button", "Prepare Hermes handoff");
      launch.type = "button";
      launch.addEventListener("click", () => openWorkflowDialog(item.id));
      actions.append(launch);
      card.append(actions);
      el.workflowGrid.append(card);
    });
    el.workflowEmpty.hidden = items.length !== 0;
  }

  function renderPowers() {
    el.powerSections.replaceChildren();
    getOrderedGroups().forEach((group) => {
      const section = node("section", "power-group");
      setGroupVars(section, group);
      const heading = node("div", "power-group-heading");
      const icon = node("div", "card-icon", group.icon);
      icon.setAttribute("aria-hidden", "true");
      const copy = node("div");
      copy.append(node("h3", "", group.name), node("p", "", group.summary));
      heading.append(icon, copy);
      const grid = node("div", "power-grid");
      POWERS.filter((item) => item.groupId === group.id).forEach((item) => {
        const card = node("article", "power-card");
        card.append(node("strong", "", item.id), node("span", "", item.title), node("small", "", "Available Inactive"));
        grid.append(card);
      });
      section.append(heading, grid);
      el.powerSections.append(section);
    });
  }

  function renderTemplates() {
    el.templateLibrary.replaceChildren();
    TEMPLATES.forEach((item) => {
      const card = node("article", "template-item");
      card.append(node("strong", "", item.id), node("span", "", item.title));
      el.templateLibrary.append(card);
    });
  }

  function renderQuiz() {
    el.quizQuestions.replaceChildren();
    QUIZ.forEach((item) => {
      const fieldset = node("fieldset", "quiz-question");
      const legend = document.createElement("legend");
      legend.append(node("span", "question-number", `${String(item.number).padStart(2, "0")} · `), document.createTextNode(item.prompt));
      const row = node("div", "likert-row");
      [
        [1, "Rarely me"], [2, "Sometimes"], [3, "It depends"], [4, "Often me"], [5, "Strongly me"]
      ].forEach(([value, label]) => {
        const wrap = node("div", "likert-option");
        const input = document.createElement("input");
        const id = `q${item.number}-${value}`;
        input.type = "radio";
        input.id = id;
        input.name = `q${item.number}`;
        input.value = String(value);
        input.required = true;
        const optionLabel = document.createElement("label");
        optionLabel.htmlFor = id;
        optionLabel.textContent = label;
        wrap.append(input, optionLabel);
        row.append(wrap);
      });
      fieldset.append(legend, row);
      el.quizQuestions.append(fieldset);
    });
  }

  function completeSoulQuiz(event) {
    event.preventDefault();
    if (!el.soulQuizForm.checkValidity()) {
      el.soulQuizForm.reportValidity();
      setStatus(el.quizStatus, "Please answer all 12 prompts and confirm the privacy statement.");
      return;
    }
    const form = new FormData(el.soulQuizForm);
    const totals = Object.fromEntries(DIMENSIONS.map((d) => [d.id, []]));
    QUIZ.forEach((item) => totals[item.dimension].push(Number(form.get(`q${item.number}`))));
    const scores = {};
    DIMENSIONS.forEach((dimension) => {
      const values = totals[dimension.id];
      const average = values.reduce((sum, value) => sum + value, 0) / values.length;
      scores[dimension.id] = Math.round(((average - 1) / 4) * 100);
    });
    const ordered = DIMENSIONS.slice().sort((a, b) => scores[b.id] - scores[a.id]);
    const spread = scores[ordered[0].id] - scores[ordered[ordered.length - 1].id];
    state.soul = {
      scores,
      primary: spread <= 8 ? "integrator" : ordered[0].id,
      secondary: ordered[1].id,
      completedAt: new Date().toISOString()
    };
    el.soulQuizForm.reset();
    const stored = saveState();
    renderAll();
    setStatus(el.quizStatus, stored ? "Your derived signature is saved locally. Raw answers were discarded." : "Your signature is available for this open page, but browser storage failed. Raw answers were discarded.", stored);
    el.quizResultHeading.focus?.();
    announce("Soul Quiz complete. Raw answers were discarded.");
  }

  function renderSoulResult() {
    el.dimensionBars.replaceChildren();
    if (!state.soul) {
      el.quizResultHeading.textContent = "Your result will appear here";
      el.quizResultCopy.textContent = "Complete every prompt to create your local signature.";
      el.quizResultActions.hidden = true;
      return;
    }
    const result = getSoulPresentation();
    el.quizResultHeading.textContent = result.title;
    el.quizResultCopy.textContent = `${result.tagline} ${result.coaching}`;
    DIMENSIONS.forEach((dimension) => {
      const score = state.soul.scores[dimension.id];
      const row = node("div", "dimension-row");
      row.append(node("label", "", dimension.label), node("strong", "", `${score}%`));
      const track = node("div", "bar-track");
      const fill = node("div", "bar-fill");
      fill.style.width = `${score}%`;
      track.append(fill);
      row.append(track);
      el.dimensionBars.append(row);
    });
    el.quizResultActions.hidden = false;
  }

  function deleteSoulResult() {
    if (!state.soul) return;
    if (!window.confirm("Delete the local DISCOVER Soul result and return to the default presentation?")) return;
    state.soul = null;
    const stored = saveState();
    renderAll();
    setStatus(el.quizStatus, stored ? "Local Soul result deleted. No raw answers existed to delete." : "Soul result cleared for this page, but the stored copy could not be updated and may return after reload.", stored);
  }

  function renderRoles() {
    el.roleGrid.replaceChildren();
    ROLES.forEach((item) => {
      const wrap = node("div", "role-option");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.id = `role-${item.id}`;
      input.name = "role";
      input.value = item.id;
      input.checked = state.selectedRoleIds.includes(item.id);
      const label = document.createElement("label");
      label.htmlFor = input.id;
      label.append(node("strong", "", item.name), node("span", "", item.summary));
      const stateSelect = document.createElement("select");
      stateSelect.className = "role-state-select";
      stateSelect.name = `role-state-${item.id}`;
      stateSelect.setAttribute("aria-label", `Role constellation state for ${item.name}`);
      ROLE_STATES.forEach((roleState) => {
        const option = document.createElement("option");
        option.value = roleState;
        option.textContent = roleState.charAt(0).toUpperCase() + roleState.slice(1);
        option.selected = (state.roleStates[item.id] || (item.id === state.selectedRoleIds[0] ? "primary" : "supporting")) === roleState;
        stateSelect.append(option);
      });
      stateSelect.disabled = !input.checked;
      input.addEventListener("change", () => { stateSelect.disabled = !input.checked; });
      wrap.append(input, label, stateSelect);
      el.roleGrid.append(wrap);
    });
  }

  function saveRoleDashboards(event) {
    event.preventDefault();
    const selected = Array.from(el.roleForm.querySelectorAll('input[name="role"]:checked')).map((input) => input.value).filter((id) => ALLOWED_ROLE_IDS.has(id));
    if (!selected.length) {
      setStatus(el.roleStatus, "Select at least one role dashboard.");
      return;
    }
    const removedWithRecords = state.selectedRoleIds.filter((id) => !selected.includes(id) && (state.missions.some((mission) => mission.roleId === id) || state.evidence.some((record) => record.roleId === id)));
    if (removedWithRecords.length) {
      setStatus(el.roleStatus, "A role with missions or capability evidence cannot be removed. Reassign or delete those records first.");
      return;
    }
    const nextSelectedRoleIds = unique(selected);
    const nextRoleStates = {};
    nextSelectedRoleIds.forEach((roleId, index) => {
      const control = el.roleForm.querySelector(`[name="role-state-${cssEscape(roleId)}"]`);
      const roleState = control && ROLE_STATES.includes(control.value) ? control.value : (index === 0 ? "primary" : "supporting");
      nextRoleStates[roleId] = roleState;
    });
    const primaryRoles = Object.entries(nextRoleStates).filter(([, roleState]) => roleState === "primary").map(([roleId]) => roleId);
    if (!primaryRoles.length) nextRoleStates[nextSelectedRoleIds[0]] = "primary";
    if (primaryRoles.length > 1) {
      setStatus(el.roleStatus, "Choose exactly one Primary role. Other dashboards can be Supporting, Emerging or Contextual.");
      return;
    }
    state.selectedRoleIds = nextSelectedRoleIds;
    state.roleStates = nextRoleStates;
    if (!state.selectedRoleIds.includes(state.activeRoleId)) state.activeRoleId = state.selectedRoleIds[0];
    ensureDashboardPartitions();
    const stored = saveState();
    renderAll();
    setStatus(el.roleStatus, stored ? `${selected.length} role dashboard${selected.length === 1 ? "" : "s"} saved. Views do not grant authority.` : "Role views changed for this page, but browser storage failed; export a backup or retry before closing.", stored);
  }

  function emptyStage() {
    return { notes: "", outcome: "", complete: false, needsReview: false, revision: 0 };
  }

  function blankMission() {
    const packet = state.discoverPacket;
    const roleGoal = packet && packet.role_goals.find((item) => item.role_id === state.activeRoleId);
    const defaultEdena = roleGoal ? roleGoal.default_edena : (packet ? packet.governance_preferences.default_edena : "unclassified");
    return {
      id: makeUuid(),
      schema: "NAIO-MISSION-1",
      title: "Untitled mission",
      roleId: state.activeRoleId,
      edition: "personal",
      edena: defaultEdena,
      edenaReason: packet ? `Defaulted from the reviewed Discover Packet (${roleGoal ? "role-specific" : "shared"} preference); confirm against this mission's actual context.` : "",
      artifactState: "exploration",
      missionStatus: "active",
      retentionMode: packet ? packet.governance_preferences.default_retention : "session_only",
      summary: "",
      iteration: 1,
      parentMissionId: null,
      sample: false,
      riskAcknowledged: false,
      approvalAttested: false,
      approvalReference: "",
      revision: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      stages: Object.fromEntries(MISSION_STAGES.map((stage) => [stage.id, emptyStage()])),
      history: []
    };
  }

  function sampleMission() {
    const mission = blankMission();
    mission.title = "Synthetic example · Improve a monthly evidence-learning huddle";
    mission.summary = "Design and evaluate a 20-minute, nonclinical evidence-learning huddle that helps a volunteer team discuss one public article and choose one safe learning action.";
    mission.edena = "green";
    mission.edenaReason = "Synthetic, nonclinical learning scenario using public information only; low-consequence and reversible.";
    mission.artifactState = "evaluated_outcome";
    mission.missionStatus = "completed";
    mission.retentionMode = "session_only";
    mission.sample = true;
    mission.iteration = 1;
    mission.stages.assess = { notes: "Verified facts: attendance averages four people; the meeting has 20 minutes; only public articles are used.\nUser-provided information: participants want a predictable format.\nAssumptions: one article is manageable.\nUnresolved questions: preferred day and accessibility needs.", outcome: "A small volunteer learning huddle is feasible if the scope stays nonclinical and the format remains brief.", complete: true, needsReview: false, revision: 1 };
    mission.stages.define = { notes: "Central opportunity: make evidence discussion consistent without adding hidden preparation burden.\nContributing factors: changing schedules and unclear facilitation.\nRisk: conversation could drift into identifiable cases, which is prohibited.", outcome: "Create a repeatable, case-free learning huddle using public evidence and a visible stop rule for sensitive discussion.", complete: true, needsReview: false, revision: 1 };
    mission.stages.plan = { notes: "Option A: 20-minute live huddle. Option B: asynchronous summary. Option C: alternate both.\nSelected: pilot Option A twice.\nMeasures: attendance, one-question usefulness rating and facilitator preparation time.\nStop rule: stop immediately if anyone introduces identifiable information.", outcome: "Run two synthetic/public-evidence huddles with a five-part agenda, named facilitator, anonymous usefulness check and stop rule.", complete: true, needsReview: false, revision: 1 };
    mission.stages.implement = { notes: "Prepared a one-page agenda, public article link checklist and anonymous feedback question. A human facilitator reviewed the materials. No message was sent and no real meeting was scheduled by this app.", outcome: "User-reported outside result: two huddles were held using the reviewed agenda; Mission Control did not execute the action.", complete: true, needsReview: false, revision: 1 };
    mission.stages.evaluate = { notes: "Expected: at least three attendees, usefulness at least 4/5 and preparation under 15 minutes.\nObserved (synthetic demonstration): four attendees, 4.3/5 usefulness and 12 minutes preparation.\nLimitation: demonstration data are illustrative, not measured real-world evidence.\nLesson: keep one article and one action.", outcome: "Continue for one additional iteration and test rotating facilitators. This is a synthetic example, not evidence of a real outcome.", complete: true, needsReview: false, revision: 1 };
    mission.revision = 1;
    return mission;
  }

  function createMission(sample) {
    const mission = sample ? sampleMission() : blankMission();
    state.missions.push(mission);
    state.activeMissionId = mission.id;
    activeMissionStage = "assess";
    saveState();
    renderAll();
    showView("missions");
    if (!sample) {
      el.missionTitle.select();
      setStatus(el.missionStatus, "New mission created in session-only mode. Add no PHI, secrets or confidential data.", true);
    } else {
      setStatus(el.missionStatus, "Synthetic five-stage example loaded. It is excluded from badges and saved evidence.", true);
    }
  }

  function renderMissions() {
    el.missionRole.replaceChildren();
    state.selectedRoleIds.forEach((roleId) => {
      const roleItem = getRole(roleId);
      const option = document.createElement("option");
      option.value = roleId;
      option.textContent = `${roleItem.name} · ${state.roleStates[roleId] || "supporting"}`;
      el.missionRole.append(option);
    });

    const visibleMissions = state.missions.filter((mission) => mission.roleId === state.activeRoleId);
    const ordered = visibleMissions.slice().sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt));
    el.missionList.replaceChildren();
    ordered.forEach((mission) => {
      const button = node("button", "mission-list-card");
      button.type = "button";
      button.classList.toggle("is-active", mission.id === state.activeMissionId);
      const roleItem = getRole(mission.roleId);
      button.append(node("strong", "", mission.title), node("span", "", `${roleItem ? roleItem.name : "Unmapped role"} · iteration ${mission.iteration}`), node("small", "", `${mission.missionStatus}${mission.sample ? " · sample" : ""} · ${formatArtifactState(mission.artifactState)}`));
      button.addEventListener("click", () => {
        state.activeMissionId = mission.id;
        activeMissionStage = firstIncompleteStage(mission);
        saveState();
        renderMissions();
      });
      el.missionList.append(button);
    });
    el.missionCount.textContent = String(visibleMissions.length);
    el.missionListEmpty.hidden = visibleMissions.length > 0;
    const active = getActiveMission();
    el.missionEmptyState.hidden = Boolean(active);
    el.missionForm.hidden = !active;
    if (active) loadMissionIntoForm(active);
  }

  function loadMissionIntoForm(mission) {
    el.missionId.value = mission.id;
    el.missionTitle.value = mission.title;
    el.missionRole.value = state.selectedRoleIds.includes(mission.roleId) ? mission.roleId : state.activeRoleId;
    el.missionEdition.value = mission.edition;
    el.missionEdena.value = mission.edena;
    el.missionEdenaReason.value = mission.edenaReason;
    el.missionArtifactState.value = mission.artifactState;
    el.missionStatusState.value = mission.missionStatus;
    el.missionRetention.value = mission.retentionMode;
    el.missionSummary.value = mission.summary;
    el.missionRiskAck.checked = Boolean(mission.riskAcknowledged);
    el.missionApprovalAttested.checked = Boolean(mission.approvalAttested);
    el.missionApprovalRef.value = mission.approvalReference || "";
    MISSION_STAGES.forEach((stage) => {
      const controls = stageControls(stage.id);
      const value = mission.stages[stage.id] || emptyStage();
      controls.notes.value = value.notes;
      controls.outcome.value = value.outcome;
      controls.complete.checked = Boolean(value.complete);
    });
    selectMissionStage(ALLOWED_STAGE_IDS.has(activeMissionStage) ? activeMissionStage : firstIncompleteStage(mission));
    renderMissionGovernance();
    renderMissionProgress(mission);
    el.startNextIteration.disabled = !mission.stages.evaluate.complete;
  }

  function stageControls(stageId) {
    const prefix = stageId.charAt(0).toUpperCase() + stageId.slice(1);
    return { notes: el[`stage${prefix}Notes`], outcome: el[`stage${prefix}Outcome`], complete: el[`stage${prefix}Complete`] };
  }

  function selectMissionStage(stageId) {
    if (!ALLOWED_STAGE_IDS.has(stageId)) return;
    activeMissionStage = stageId;
    document.querySelectorAll("[data-mission-stage]").forEach((button) => {
      const active = button.dataset.missionStage === stageId;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      const mission = getActiveMission();
      const stage = mission && mission.stages[button.dataset.missionStage];
      button.classList.toggle("is-complete", Boolean(stage && stage.complete));
      button.classList.toggle("needs-review", Boolean(stage && stage.needsReview));
      const label = MISSION_STAGES.find((item) => item.id === button.dataset.missionStage)?.label || button.dataset.missionStage;
      button.setAttribute("aria-label", `${label} · ${stage && stage.needsReview ? "needs review" : stage && stage.complete ? "reviewed" : "not yet reviewed"}`);
    });
    document.querySelectorAll("[data-stage-panel]").forEach((panel) => {
      const active = panel.dataset.stagePanel === stageId;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
  }

  function renderMissionProgress(mission) {
    const complete = MISSION_STAGES.filter((stage) => mission.stages[stage.id] && mission.stages[stage.id].complete).length;
    el.missionProgressBar.style.width = `${complete * 20}%`;
    el.missionProgressText.textContent = `${complete} of 5 stages reviewed · iteration ${mission.iteration}`;
    el.missionProgress.setAttribute("aria-valuenow", String(complete));
    el.missionProgress.setAttribute("aria-valuetext", `${complete} of 5 stages reviewed; iteration ${mission.iteration}`);
    selectMissionStage(activeMissionStage);
  }

  function renderMissionGovernance() {
    const tier = EDENA_POLICY.tiers[el.missionEdena.value] || EDENA_POLICY.tiers.unclassified;
    const edition = el.missionEdition.value;
    const artifactIndex = ARTIFACT_STATES.indexOf(el.missionArtifactState.value);
    el.missionEdenaPanel.className = `edena-panel is-${el.missionEdena.value}`;
    const editionCopy = edition === "personal"
      ? "Personal Edition: classification is advisory. Non-sensitive exploration remains available, but no direct external action exists."
      : "Institutional policy preview: demonstrates stricter gates only. This static local app is not managed, tamper-resistant institutional enforcement.";
    el.missionEdenaPanel.replaceChildren(node("strong", "", `${tier.label} · policy ${EDENA_POLICY.id} ${EDENA_POLICY.version}`), node("span", "", `${tier.summary} ${editionCopy}`));
    const needsRiskAck = ["yellow", "orange", "red", "unclassified"].includes(el.missionEdena.value);
    const needsApproval = artifactIndex >= ARTIFACT_STATES.indexOf("approved_plan") || edition === "institutional_preview";
    el.missionGatePanel.hidden = !(needsRiskAck || needsApproval);
    el.institutionalGate.hidden = !needsApproval;
    el.prepareMissionHandoff.textContent = edition === "institutional_preview" && el.missionEdena.value === "red" ? "Prepare blocked-state review request" : "Prepare Hermes stage handoff";
  }

  function saveMissionFromForm(event) {
    event.preventDefault();
    persistMissionFromForm(false);
  }

  function persistMissionFromForm(silent) {
    const existing = getActiveMission();
    if (!existing) return null;
    if (!el.missionForm.checkValidity()) {
      el.missionForm.reportValidity();
      setStatus(el.missionStatus, "Add a title, owning role and desired outcome before saving.");
      return null;
    }
    const collected = collectMissionForm(existing);
    const detected = detectSensitiveText([collected.title, collected.summary, collected.edenaReason, collected.approvalReference, ...Object.values(collected.stages).flatMap((stage) => [stage.notes, stage.outcome])].join("\n"));
    if (detected.length) {
      setStatus(el.missionStatus, `Possible prohibited or sensitive content detected: ${detected.join(", ")}. Remove it before saving.`);
      return null;
    }
    const changedIndices = [];
    MISSION_STAGES.forEach((stage, index) => {
      const before = existing.stages[stage.id] || emptyStage();
      const after = collected.stages[stage.id];
      if (before.notes !== after.notes || before.outcome !== after.outcome || before.complete !== after.complete) changedIndices.push(index);
      after.revision = (before.notes !== after.notes || before.outcome !== after.outcome || before.complete !== after.complete) ? (before.revision || 0) + 1 : (before.revision || 0);
    });
    let rollbackMessage = "";
    let earliestChangedIndex = null;
    let reopenedStageIds = [];
    if (existing.revision > 0 && changedIndices.length) {
      const earliest = Math.min(...changedIndices);
      earliestChangedIndex = earliest;
      const reopened = [];
      for (let index = earliest + 1; index < MISSION_STAGES.length; index += 1) {
        const stage = collected.stages[MISSION_STAGES[index].id];
        if (stage.complete && !changedIndices.includes(index)) {
          stage.complete = false;
          stage.needsReview = true;
          reopened.push(MISSION_STAGES[index].label);
          reopenedStageIds.push(MISSION_STAGES[index].id);
        }
      }
      if (reopened.length) rollbackMessage = `Reopened for review: ${reopened.join(", ")}.`;
    }
    const roleBindingChanged = existing.revision > 0 && existing.roleId !== collected.roleId;
    const missionIntentChanged = existing.revision > 0 && (existing.title !== collected.title || existing.summary !== collected.summary);
    const foundationBindingChanged = roleBindingChanged || missionIntentChanged;
    const governanceBindingChanged = existing.revision > 0 && (foundationBindingChanged || existing.edition !== collected.edition || existing.edena !== collected.edena || existing.edenaReason !== collected.edenaReason);
    if (governanceBindingChanged) {
      const reopenFrom = foundationBindingChanged ? 0 : 2;
      for (let index = reopenFrom; index < MISSION_STAGES.length; index += 1) {
        const stage = collected.stages[MISSION_STAGES[index].id];
        if (stage.complete) {
          stage.complete = false;
          stage.needsReview = true;
          reopenedStageIds.push(MISSION_STAGES[index].id);
        }
      }
      collected.missionStatus = collected.missionStatus === "archived" ? "archived" : "active";
      rollbackMessage = `${rollbackMessage} Material mission intent, role or EDENA context changed; affected stages require review.`.trim();
    }
    const approvalBindingChanged = governanceBindingChanged || (existing.revision > 0 && changedIndices.some((index) => index <= 2));
    const implementBindingChanged = approvalBindingChanged || (existing.revision > 0 && changedIndices.includes(3));
    const evaluateBindingChanged = implementBindingChanged || (existing.revision > 0 && changedIndices.includes(4));
    let maximumArtifactState = null;
    if (approvalBindingChanged) {
      collected.approvalAttested = false;
      collected.approvalReference = "";
      if (foundationBindingChanged) maximumArtifactState = "exploration";
      else if (governanceBindingChanged) maximumArtifactState = "recommendation";
      else if (reopenedStageIds.length && earliestChangedIndex === 0) maximumArtifactState = "simulation";
      else if (reopenedStageIds.length && earliestChangedIndex === 1) maximumArtifactState = "recommendation";
      else maximumArtifactState = "draft_artifact";
      rollbackMessage = `${rollbackMessage} Material role, governance or Plan-foundation changes cleared the prior approval attestation.`.trim();
    } else if (implementBindingChanged) {
      maximumArtifactState = "approved_plan";
    } else if (evaluateBindingChanged) {
      maximumArtifactState = "completed_action";
    }
    if (maximumArtifactState && ARTIFACT_STATES.indexOf(collected.artifactState) > ARTIFACT_STATES.indexOf(maximumArtifactState)) {
      collected.artifactState = maximumArtifactState;
      if (collected.missionStatus === "completed") collected.missionStatus = "active";
      rollbackMessage = `${rollbackMessage} Artifact maturity rolled back to ${formatArtifactState(maximumArtifactState)}.`.trim();
    }
    const gateError = validateMissionTransition(existing, collected);
    if (gateError) {
      setStatus(el.missionStatus, gateError);
      return null;
    }
    collected.revision = (existing.revision || 0) + 1;
    collected.updatedAt = new Date().toISOString();
    const historyChangedStages = changedIndices.map((index) => MISSION_STAGES[index].id);
    if (foundationBindingChanged && !historyChangedStages.includes("assess")) historyChangedStages.unshift("assess");
    else if (governanceBindingChanged && !historyChangedStages.includes("plan")) historyChangedStages.unshift("plan");
    collected.history = (existing.history || []).concat([{ revision: collected.revision, changedStages: historyChangedStages, at: collected.updatedAt }]).slice(-20);
    const index = state.missions.findIndex((mission) => mission.id === existing.id);
    state.missions[index] = collected;
    const stored = saveState();
    renderAll();
    if (!silent) {
      const savedMessage = collected.retentionMode === "session_only"
        ? "Mission updated for this open session only."
        : stored ? "Mission saved in unencrypted local browser storage." : "Mission remains in this open page, but browser storage failed; it was not saved locally.";
      setStatus(el.missionStatus, `${savedMessage}${rollbackMessage ? ` ${rollbackMessage}` : ""}`, collected.retentionMode === "session_only" || stored);
    }
    return collected;
  }

  function collectMissionForm(existing) {
    const stages = {};
    MISSION_STAGES.forEach((stage) => {
      const controls = stageControls(stage.id);
      const prior = existing.stages[stage.id] || emptyStage();
      stages[stage.id] = { notes: controls.notes.value.trim(), outcome: controls.outcome.value.trim(), complete: controls.complete.checked, needsReview: Boolean(prior.needsReview), revision: prior.revision || 0 };
      if (controls.complete.checked) stages[stage.id].needsReview = false;
    });
    return {
      ...existing,
      title: el.missionTitle.value.trim(),
      roleId: el.missionRole.value,
      edition: el.missionEdition.value,
      edena: el.missionEdena.value,
      edenaReason: el.missionEdenaReason.value.trim(),
      artifactState: el.missionArtifactState.value,
      missionStatus: el.missionStatusState.value,
      retentionMode: el.missionRetention.value,
      summary: el.missionSummary.value.trim(),
      riskAcknowledged: el.missionRiskAck.checked,
      approvalAttested: el.missionApprovalAttested.checked,
      approvalReference: el.missionApprovalRef.value.trim(),
      stages
    };
  }

  function validateMissionTransition(existing, mission) {
    if (!state.selectedRoleIds.includes(mission.roleId)) return "Choose an active role dashboard as the mission owner.";
    if (!mission.edenaReason) return "Record a brief, non-sensitive reason for the EDENA classification.";
    if (!ARTIFACT_STATES.includes(mission.artifactState)) return "Unknown artifact state.";
    const requested = ARTIFACT_STATES.indexOf(mission.artifactState);
    const current = ARTIFACT_STATES.indexOf(existing.artifactState);
    if (!existing.sample && requested > current + 1) return "Move through artifact states one gate at a time, beginning with Exploration. You may move backward whenever needed.";
    return validateMissionSemantic(mission, existing.sample);
  }

  function validateMissionSemantic(mission, sample = false) {
    let priorComplete = true;
    for (const stage of MISSION_STAGES) {
      const item = mission.stages[stage.id];
      if (item.complete && (!item.notes || !item.outcome)) return `${stage.label} cannot be marked Reviewed until both working notes and a stage outcome are recorded.`;
      if (item.complete && !priorComplete) return `${stage.label} cannot be marked Reviewed while an earlier stage remains incomplete. You may add later-stage notes without completing it.`;
      if (item.complete && item.needsReview) return `${stage.label} is marked for re-review and cannot also be complete.`;
      if (!item.complete) priorComplete = false;
    }
    const requested = ARTIFACT_STATES.indexOf(mission.artifactState);
    if (requested >= ARTIFACT_STATES.indexOf("recommendation") && !mission.stages.define.complete) return "A Recommendation requires reviewed Assess and Define stages.";
    if (requested >= ARTIFACT_STATES.indexOf("draft_artifact") && !mission.stages.plan.complete) return "A Draft Artifact or later state requires reviewed Assess, Define and Plan stages.";
    if (!sample && requested >= ARTIFACT_STATES.indexOf("approved_plan") && (!mission.approvalAttested || !mission.approvalReference)) return "Record a non-sensitive human-review reference before labeling a plan Approved. This remains user-attested, not system-verified.";
    if (requested >= ARTIFACT_STATES.indexOf("authorized_execution") && !mission.stages.implement.complete) return "Authorized Execution requires reviewed Assess through Implement stages and external authority outside this app.";
    if (!sample && ["orange", "red", "unclassified"].includes(mission.edena) && requested >= ARTIFACT_STATES.indexOf("authorized_execution")) return `${EDENA_POLICY.tiers[mission.edena].label} cannot advance to Authorized Execution in this local package.`;
    if (!sample && mission.edition === "institutional_preview" && ["orange", "red"].includes(mission.edena) && requested >= ARTIFACT_STATES.indexOf("approved_plan")) return "Institutional policy preview blocks this transition. Managed institutional approval cannot be verified by this static local app.";
    if (requested >= ARTIFACT_STATES.indexOf("evaluated_outcome") && !mission.stages.evaluate.complete) return "Evaluated Outcome requires all five reviewed stages.";
    if (mission.missionStatus === "completed" && !MISSION_STAGES.every((stage) => mission.stages[stage.id].complete)) return "A mission can be marked Completed only after all five stages are reviewed.";
    if (!sample && ["yellow", "orange", "red", "unclassified"].includes(mission.edena) && !mission.riskAcknowledged) return "Acknowledge the EDENA advisory before saving this non-Green classification.";
    return "";
  }

  function prepareMissionHandoff() {
    const mission = persistMissionFromForm(true);
    if (!mission) return;
    if (mission.edena === "unclassified") {
      setStatus(el.missionStatus, "Classify the mission before preparing a Hermes handoff.");
      return;
    }
    if (["yellow", "orange", "red"].includes(mission.edena) && !mission.riskAcknowledged) {
      setStatus(el.missionStatus, "Acknowledge the EDENA advisory before preparing a handoff.");
      return;
    }
    const stage = mission.stages[activeMissionStage];
    if (!stage.notes && !stage.outcome) {
      setStatus(el.missionStatus, "Add non-sensitive notes or an outcome for the active stage before preparing a handoff.");
      return;
    }
    el.missionHandoffMeta.textContent = `${MISSION_STAGES.find((item) => item.id === activeMissionStage).label} · ${EDENA_POLICY.tiers[mission.edena].label}`;
    el.missionHandoffTitle.textContent = mission.edition === "institutional_preview" && mission.edena === "red" ? "Blocked-state review request" : `${mission.title} · stage preview`;
    el.missionHandoffOutput.value = buildMissionHandoffMarkdown(mission, activeMissionStage);
    el.missionHandoffReview.checked = false;
    el.copyMissionHandoff.disabled = true;
    el.downloadMissionHandoff.disabled = true;
    el.missionHermesUrl.value = "";
    setStatus(el.missionHandoffStatus, "Review the exact handoff before enabling Copy or Download.");
    if (typeof el.missionHandoffDialog.showModal === "function") el.missionHandoffDialog.showModal();
    else el.missionHandoffDialog.setAttribute("open", "");
  }

  function buildMissionHandoffMarkdown(mission, stageId) {
    const stage = mission.stages[stageId];
    const roleItem = getRole(mission.roleId);
    const blocked = mission.edition === "institutional_preview" && mission.edena === "red";
    const packetBoundary = state.discoverPacket ? `Discover Packet AI boundary: default autonomy ${state.discoverPacket.ai_boundaries.default_autonomy}; never delegate ${state.discoverPacket.ai_boundaries.never_delegate.join(", ") || "nothing specified—use prepare only"}.` : "No Discover Packet AI boundary is applied; use prepare-only behavior and ask before expanding scope.";
    return [
      "# Nurse AI OS · DISCOVER Mission Stage Handoff",
      "",
      "```yaml",
      "schema: naio.hermes-handoff/1",
      "integration_state: manual_handoff",
      "execution_permission: none",
      "memory_directive: session_only_do_not_remember",
      `mission_id: ${mission.id}`,
      `iteration: ${mission.iteration}`,
      `stage: ${stageId}`,
      `role_context: ${roleItem ? roleItem.name : "Unmapped role"} (presentation context only; not proof of authority)`,
      `requested_operation: ${blocked ? "prepare_review_request" : "analyze_compare_simulate_or_draft"}`,
      `edena_edition: ${mission.edition}`,
      `edena_tier: ${mission.edena}`,
      `edena_reason: ${mission.edenaReason.replace(/[\r\n]+/g, " ")}`,
      `edena_policy: ${EDENA_POLICY.id}@${EDENA_POLICY.version}`,
      `artifact_state: ${mission.artifactState}`,
      "external_action: prohibited",
      "```",
      "",
      "## Mission and success definition",
      "",
      mission.summary,
      "",
      `## ${MISSION_STAGES.find((item) => item.id === stageId).label} working record`,
      "",
      stage.notes || "No notes supplied.",
      "",
      "## Current stage outcome",
      "",
      stage.outcome || "No outcome supplied. Ask the minimum safe clarification questions.",
      "",
      "## Non-negotiable operating instruction",
      "",
      "Use only the content above and public, synthetic or explicitly approved non-sensitive information. Separate facts, user-provided information, assumptions, inferences and unresolved questions. Do not invent evidence, citations, approvals, outcomes, authority or credentials.",
      packetBoundary,
      "",
      blocked ? "EDENA Red in Institutional policy preview: do not advance, authorize or operationalize. Prepare only a review/escalation request that names missing policy, authority and safeguards." : "Return one clearly labeled sandbox preview. Do not enable tools, agents, connectors, network activity, memory writes, scheduling, publishing, sending or official-system action.",
      "",
      "The required final line is: **NO EXTERNAL ACTION TAKEN**",
      "",
      "---",
      `Generated locally by DISCOVER Nurse AI OS Mission Control v${APP_VERSION}. Copy/Download is not Send/Execute.`
    ].join("\n");
  }

  function closeMissionHandoff() {
    el.missionHandoffOutput.value = "";
    el.missionHandoffReview.checked = false;
    el.missionHermesUrl.value = "";
    if (typeof el.missionHandoffDialog.close === "function") el.missionHandoffDialog.close();
    else el.missionHandoffDialog.removeAttribute("open");
  }

  function downloadMissionStageHandoff() {
    const mission = getActiveMission();
    if (!mission || !el.missionHandoffReview.checked || !el.missionHandoffOutput.value) return;
    downloadText(`DISCOVER-Mission-${mission.id.slice(0, 8)}-${activeMissionStage}-Hermes-Handoff.md`, el.missionHandoffOutput.value, "text/markdown;charset=utf-8");
    setStatus(el.missionHandoffStatus, "Handoff downloaded. It was not sent or executed.", true);
  }

  function openMissionHermesSeparately() {
    openTrustedAddress(el.missionHermesUrl, el.missionHandoffStatus);
  }

  function beginNextIteration() {
    const current = persistMissionFromForm(true);
    if (!current) return;
    if (!current.stages.evaluate.complete) {
      setStatus(el.missionStatus, "Review Evaluate before beginning a new iteration.");
      return;
    }
    const next = blankMission();
    next.title = current.title.replace(/ · iteration \d+$/, "");
    next.summary = current.summary;
    next.roleId = current.roleId;
    next.edition = current.edition;
    next.edena = current.edena;
    next.edenaReason = `Carry-forward from iteration ${current.iteration}; reconfirm this classification against the new iteration's actual context. ${current.edenaReason}`.slice(0, 300);
    next.retentionMode = current.retentionMode;
    next.iteration = current.iteration + 1;
    next.parentMissionId = current.id;
    next.stages.assess.notes = `Carry-forward lesson from iteration ${current.iteration}:\n${current.stages.evaluate.outcome}`;
    state.missions.push(next);
    state.activeMissionId = next.id;
    activeMissionStage = "assess";
    const stored = saveState();
    renderAll();
    setStatus(el.missionStatus, stored || next.retentionMode === "session_only" ? `Iteration ${next.iteration} started. Reassess rather than assuming the prior context still holds.` : `Iteration ${next.iteration} started in this page, but browser storage failed.`, stored || next.retentionMode === "session_only");
  }

  function deleteActiveMission() {
    const mission = getActiveMission();
    if (!mission) return;
    if (!window.confirm(`Delete “${mission.title}” and any capability evidence linked to it from this browser?`)) return;
    state.missions = state.missions.filter((item) => item.id !== mission.id);
    state.evidence = state.evidence.filter((item) => item.missionId !== mission.id);
    state.activeMissionId = state.missions.find((item) => item.roleId === state.activeRoleId)?.id || null;
    const stored = saveState();
    renderAll();
    setStatus(el.missionStatus, stored ? "Mission and linked local evidence deleted." : "Deleted for this page, but browser storage could not be updated; the records may return after reload.", stored);
  }

  function getActiveMission() {
    return state.missions.find((mission) => mission.id === state.activeMissionId && mission.roleId === state.activeRoleId) || null;
  }

  function firstIncompleteStage(mission) {
    const item = MISSION_STAGES.find((stage) => !mission.stages[stage.id] || !mission.stages[stage.id].complete);
    return item ? item.id : "evaluate";
  }

  function formatArtifactState(value) {
    return String(value || "exploration").replaceAll("_", " ");
  }

  function renderCapabilities() {
    const selectedCapability = el.evidenceCapability.value;
    el.evidenceCapability.replaceChildren();
    CAPABILITIES.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.name;
      option.selected = selectedCapability === item.id;
      el.evidenceCapability.append(option);
    });
    const selectedMission = el.evidenceMission.value;
    el.evidenceMission.replaceChildren(new Option("No mission selected", ""));
    state.missions.filter((mission) => !mission.sample && mission.roleId === state.activeRoleId).forEach((mission) => {
      const option = document.createElement("option");
      option.value = mission.id;
      option.textContent = `${mission.title} · ${getRole(mission.roleId)?.name || "Unmapped role"}`;
      option.selected = selectedMission === mission.id;
      el.evidenceMission.append(option);
    });

    el.capabilityGrid.replaceChildren();
    CAPABILITIES.forEach((item, index) => {
      const progress = capabilityProgress(item.id);
      const card = node("article", "capability-card");
      const header = node("div", "capability-card-header");
      header.append(node("div", "capability-icon", String(index + 1).padStart(2, "0")));
      const copy = node("div");
      copy.append(node("h4", "", item.name), node("p", "", item.description));
      header.append(copy);
      card.append(header, node("span", "level-label", progress.level.label));
      const progressWrap = node("div", "capability-progress");
      const track = node("div", "capability-progress-track");
      const fill = node("span");
      fill.style.width = `${progress.percent}%`;
      track.append(fill);
      progressWrap.append(track, node("small", "", progress.level.id === "master" ? "Capstone criteria met" : `${progress.met} of ${progress.total} requirements toward ${progress.nextLabel}`));
      card.append(progressWrap);
      const metadata = node("dl", "capability-metadata");
      metadata.append(
        node("dt", "", "Evidence"), node("dd", "", `${progress.evidenceCount} record${progress.evidenceCount === 1 ? "" : "s"} · ${progress.evaluatedMissionCount} evaluated mission${progress.evaluatedMissionCount === 1 ? "" : "s"}`),
        node("dt", "", "Date earned"), node("dd", "", progress.earnedAt ? new Date(progress.earnedAt).toLocaleDateString() : "Not yet earned"),
        node("dt", "", "Governance & safety"), node("dd", "", progress.safetySignals.join(" · "))
      );
      card.append(metadata);
      if (progress.evidencePreview.length) {
        const evidenceList = node("ul", "capability-evidence-preview");
        progress.evidencePreview.forEach((record) => evidenceList.append(node("li", "", `${record.summary} (${new Date(record.createdAt).toLocaleDateString()})`)));
        card.append(evidenceList);
      } else {
        card.append(node("p", "capability-no-evidence", "No completed activity is recorded for this capability."));
      }
      card.append(node("p", "capability-next", `Recommended next challenge: ${progress.nextChallenge}`));
      el.capabilityGrid.append(card);
    });

    const roleEvidence = state.evidence.filter((record) => record.roleId === state.activeRoleId);
    el.capabilityEvidenceCount.textContent = `${roleEvidence.length} evidence record${roleEvidence.length === 1 ? "" : "s"} · ${getActiveRole().name}`;
    el.evidenceList.replaceChildren();
    roleEvidence.slice().sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)).forEach((record) => {
      const capabilityItem = CAPABILITIES.find((item) => item.id === record.capabilityId);
      const item = node("article", "evidence-item");
      item.append(node("strong", "", capabilityItem ? capabilityItem.name : "Unknown capability"), node("span", "", record.summary), node("small", "", `${formatEvidenceType(record.type)} · ${formatEvidenceType(record.provenance)} · EDENA ${record.edena.toUpperCase()} · ${new Date(record.createdAt).toLocaleDateString()}`));
      const remove = node("button", "danger-text-button", "Delete evidence");
      remove.type = "button";
      remove.addEventListener("click", () => deleteEvidence(record.id));
      item.append(remove);
      el.evidenceList.append(item);
    });
    if (!roleEvidence.length) el.evidenceList.append(node("p", "muted-copy", "No evidence records for this role dashboard. Finish and evaluate a real non-sensitive mission before documenting development."));
  }

  function addCapabilityEvidence(event) {
    event.preventDefault();
    if (!el.evidenceForm.checkValidity()) {
      el.evidenceForm.reportValidity();
      setStatus(el.evidenceStatus, "Complete the evidence summary and attestation.");
      return;
    }
    const capabilityId = el.evidenceCapability.value;
    const mission = state.missions.find((item) => item.id === el.evidenceMission.value) || null;
    const type = el.evidenceType.value;
    const summary = el.evidenceSummary.value.trim();
    if (!ALLOWED_CAPABILITY_IDS.has(capabilityId)) {
      setStatus(el.evidenceStatus, "Unknown capability.");
      return;
    }
    if (mission && mission.sample) {
      setStatus(el.evidenceStatus, "Synthetic sample missions cannot count as personal development evidence.");
      return;
    }
    if (["mission", "outcome"].includes(type) && (!mission || !mission.stages.evaluate.complete)) {
      setStatus(el.evidenceStatus, "Mission or outcome evidence requires a related mission with a reviewed Evaluate stage.");
      return;
    }
    if (["artifact_review", "assessment", "human_review", "safety_drill", "agent_run", "knowledge_transfer"].includes(type) && !mission) {
      setStatus(el.evidenceStatus, "This evidence type requires a related non-sample mission so the context and role remain reviewable.");
      return;
    }
    if (type === "agent_run" && (!mission || !mission.stages.evaluate.complete)) {
      setStatus(el.evidenceStatus, "An agent-run record requires a related mission completed through Evaluate. Mission Control does not verify the external run.");
      return;
    }
    const detected = detectSensitiveText(summary);
    if (detected.length) {
      setStatus(el.evidenceStatus, `Remove possible sensitive content: ${detected.join(", ")}.`);
      return;
    }
    const duplicate = state.evidence.some((record) => record.capabilityId === capabilityId && record.missionId === (mission ? mission.id : null) && record.type === type);
    if (duplicate) {
      setStatus(el.evidenceStatus, "That mission and evidence type are already recorded for this capability. Repeated clicks do not increase progress.");
      return;
    }
    let provenance = el.evidenceProvenance.value;
    if (provenance === "app_observed" && !(type === "mission" && mission && mission.stages.evaluate.complete)) {
      setStatus(el.evidenceStatus, "App-observed assurance is limited to this app's own evaluated mission record. Choose User-attested or Human-reviewed for external activities.");
      return;
    }
    if (type === "human_review" && provenance !== "human_reviewed_unverified") {
      setStatus(el.evidenceStatus, "Human review evidence must use Human-reviewed assurance. Reviewer identity and authority remain unverified by this app.");
      return;
    }
    if (type === "agent_run" && provenance !== "human_reviewed_unverified") {
      setStatus(el.evidenceStatus, "An agent-run record must be human-reviewed before it can count toward orchestration development.");
      return;
    }
    if (mission && mission.edena !== "unclassified" && el.evidenceEdena.value !== mission.edena) {
      setStatus(el.evidenceStatus, `EDENA evidence must match the related mission (${mission.edena.toUpperCase()}). Reclassify the mission through review rather than choosing a stronger badge value.`);
      return;
    }
    if (!mission && ["yellow", "orange", "red"].includes(el.evidenceEdena.value)) {
      setStatus(el.evidenceStatus, "Non-Green governance evidence requires a related mission with the same reviewed EDENA classification.");
      return;
    }
    state.evidence.push({
      id: makeUuid(),
      schema: "NAIO-CAPABILITY-EVIDENCE-1",
      capabilityId,
      missionId: mission ? mission.id : null,
      roleId: mission ? mission.roleId : state.activeRoleId,
      type,
      provenance,
      edena: el.evidenceEdena.value,
      summary,
      createdAt: new Date().toISOString()
    });
    const stored = saveState();
    el.evidenceForm.reset();
    renderAll();
    setStatus(el.evidenceStatus, stored ? "Evidence added as a development record. It does not grant a credential or permission." : "Evidence exists only in this open page because browser storage failed. It does not grant a credential or permission.", stored);
  }

  function deleteEvidence(evidenceId) {
    if (!window.confirm("Delete this local evidence record and recalculate capability levels?")) return;
    state.evidence = state.evidence.filter((item) => item.id !== evidenceId);
    const stored = saveState();
    renderAll();
    setStatus(el.evidenceStatus, stored ? "Evidence deleted and levels recalculated." : "Evidence was removed from this page, but stored data could not be updated and may return after reload.", stored);
  }

  function capabilityLevel(capabilityId) {
    return capabilityProgress(capabilityId).level;
  }

  function capabilityProgress(capabilityId) {
    const evidence = state.evidence.filter((record) => record.capabilityId === capabilityId && record.roleId === state.activeRoleId);
    const missionIds = unique(evidence.map((record) => record.missionId).filter(Boolean));
    const evaluatedMissions = missionIds.map((id) => state.missions.find((mission) => mission.id === id)).filter((mission) => mission && mission.stages.evaluate.complete && !mission.sample);
    const roleIds = unique(evaluatedMissions.map((mission) => mission.roleId));
    const types = new Set(evidence.map((record) => record.type));
    const nonGreen = evidence.some((record) => ["yellow", "orange", "red"].includes(record.edena));
    const humanReviewed = evidence.some((record) => record.provenance === "human_reviewed_unverified");
    const basicChecks = [evaluatedMissions.length >= 1, types.has("artifact_review"), types.has("reflection"), evidence.length >= 4];
    const intermediateChecks = [evaluatedMissions.length >= 3, roleIds.length >= 2 || evaluatedMissions.some((mission) => mission.iteration > 1), types.has("outcome") || humanReviewed, nonGreen, types.has("knowledge_transfer") || types.has("artifact_review")];
    const advancedChecks = [evaluatedMissions.length >= 4, evidence.length >= 8, humanReviewed, types.has("safety_drill"), types.has("knowledge_transfer"), evaluatedMissions.some((mission) => mission.iteration > 1)];
    const prerequisiteIds = ["workflow-design", "privacy-stewardship", "ethical-ai", "edena-governance", "agent-supervision", "evaluation-qi"];
    const prereqs = capabilityId === "multi-agent" && prerequisiteIds.every((id) => rawLevelRank(id) >= 3);
    const masterChecks = [capabilityId === "multi-agent", evaluatedMissions.length >= 5, evidence.filter((record) => record.type === "agent_run" && record.provenance === "human_reviewed_unverified").length >= 2, humanReviewed, types.has("safety_drill"), types.has("knowledge_transfer"), prereqs];
    let level = MASTERY_LEVELS[0];
    if (basicChecks.every(Boolean)) level = MASTERY_LEVELS[1];
    if (level.id !== "none" && intermediateChecks.every(Boolean)) level = MASTERY_LEVELS[2];
    if (level.id === "intermediate" && advancedChecks.every(Boolean)) level = MASTERY_LEVELS[3];
    if (level.id === "advanced" && masterChecks.every(Boolean)) level = MASTERY_LEVELS[4];
    const nextChecks = level.id === "none" ? basicChecks : level.id === "basic" ? intermediateChecks : level.id === "intermediate" ? advancedChecks : masterChecks;
    const nextLabel = level.id === "none" ? "Basic" : level.id === "basic" ? "Intermediate" : level.id === "intermediate" ? "Advanced" : "AI Agent Orchestration Master";
    const met = nextChecks.filter(Boolean).length;
    const total = nextChecks.length;
    const challenges = {
      none: "Complete one real mission through Evaluate, review an artifact, record a safety check and reflect on the next step.",
      basic: "Build three evaluated missions across more than one context, revise from evidence and handle a non-Green scenario safely.",
      intermediate: "Demonstrate repeated improvement, independent human review, rollback practice and knowledge transfer.",
      advanced: capabilityId === "multi-agent" ? "Complete the governed orchestration capstone and all safety prerequisites." : "Apply this capability within a governed multi-agent capstone; Master is awarded through the orchestration pathway.",
      master: "Maintain evidence quality, review dates, safe boundaries and knowledge transfer."
    };
    const evidencePreview = evidence.slice().sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt)).slice(0, 2);
    const safetySignals = [];
    if (nonGreen) safetySignals.push("non-Green review recorded");
    if (types.has("safety_drill")) safetySignals.push("safety/rollback drill");
    if (humanReviewed) safetySignals.push("human review recorded");
    if (types.has("agent_run")) safetySignals.push("agent run reviewed");
    if (!safetySignals.length) safetySignals.push("not yet demonstrated");
    const chronologicalEvidence = evidence.slice().sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt));
    const earnedRecord = level.id === "none" ? null : chronologicalEvidence.find((_record, index) => levelIdForEvidenceSubset(capabilityId, chronologicalEvidence.slice(0, index + 1)) === level.id);
    const earnedAt = earnedRecord ? earnedRecord.createdAt : null;
    return {
      level,
      met,
      total,
      percent: level.id === "master" ? 100 : Math.round((met / total) * 100),
      nextLabel,
      nextChallenge: challenges[level.id],
      evidenceCount: evidence.length,
      evaluatedMissionCount: evaluatedMissions.length,
      evidencePreview,
      safetySignals,
      earnedAt
    };
  }

  function levelIdForEvidenceSubset(capabilityId, evidence) {
    const missionIds = unique(evidence.map((record) => record.missionId).filter(Boolean));
    const missions = missionIds.map((id) => state.missions.find((mission) => mission.id === id)).filter((mission) => mission && mission.stages.evaluate.complete && !mission.sample);
    const roleIds = unique(missions.map((mission) => mission.roleId));
    const types = new Set(evidence.map((record) => record.type));
    const nonGreen = evidence.some((record) => ["yellow", "orange", "red"].includes(record.edena));
    const humanReviewed = evidence.some((record) => record.provenance === "human_reviewed_unverified");
    const basic = missions.length >= 1 && types.has("artifact_review") && types.has("reflection") && evidence.length >= 4;
    if (!basic) return "none";
    const intermediate = missions.length >= 3 && (roleIds.length >= 2 || missions.some((mission) => mission.iteration > 1)) && (types.has("outcome") || humanReviewed) && nonGreen && (types.has("knowledge_transfer") || types.has("artifact_review"));
    if (!intermediate) return "basic";
    const advanced = missions.length >= 4 && evidence.length >= 8 && humanReviewed && types.has("safety_drill") && types.has("knowledge_transfer") && missions.some((mission) => mission.iteration > 1);
    if (!advanced) return "intermediate";
    const prerequisiteIds = ["workflow-design", "privacy-stewardship", "ethical-ai", "edena-governance", "agent-supervision", "evaluation-qi"];
    const master = capabilityId === "multi-agent" && missions.length >= 5 && evidence.filter((record) => record.type === "agent_run" && record.provenance === "human_reviewed_unverified").length >= 2 && humanReviewed && types.has("safety_drill") && types.has("knowledge_transfer") && prerequisiteIds.every((id) => rawLevelRank(id) >= 3);
    return master ? "master" : "advanced";
  }

  function rawLevelRank(capabilityId) {
    const evidence = state.evidence.filter((record) => record.capabilityId === capabilityId && record.roleId === state.activeRoleId);
    const levelId = levelIdForEvidenceSubset(capabilityId, evidence);
    return { none: 0, basic: 1, intermediate: 2, advanced: 3, master: 4 }[levelId] || 0;
  }

  function exportCapabilityReport() {
    const roleEvidence = state.evidence.filter((record) => record.roleId === state.activeRoleId);
    const lines = [
      "# Nurse AI OS · Capability Development Report",
      "",
      `Generated: ${new Date().toISOString()}`,
      `Mission Control version: ${APP_VERSION}`,
      `Role dashboard: ${getActiveRole().name} (self-selected context; not proof of authority)`,
      "EDENA advisory: Yellow · evidence is user-entered and may be incomplete or externally unverified.",
      "Review requirement: verify every record, role context, date, provenance and intended recipient before external use.",
      "",
      "> These records document development within Mission Control. They are not licensure, certification, CE credit, institutional authorization or proof of clinical competence.",
      "",
      "## Capability summary",
      "",
      ...CAPABILITIES.map((item) => `- **${item.name}:** ${capabilityLevel(item.id).label}`),
      "",
      "## Sanitized evidence records",
      "",
      ...roleEvidence.map((record) => `- ${record.createdAt} · ${CAPABILITIES.find((item) => item.id === record.capabilityId)?.name || record.capabilityId} · ${formatEvidenceType(record.type)} · ${formatEvidenceType(record.provenance)} · EDENA ${record.edena.toUpperCase()} — ${record.summary}`),
      "",
      "No badge in this report changes professional scope, authority, permission or governance requirements."
    ];
    downloadText("DISCOVER-Nurse-AI-OS-Capability-Development-Report.md", lines.join("\n"), "text/markdown;charset=utf-8");
    announce("Development report downloaded. Review it before sharing.");
  }

  function formatEvidenceType(value) {
    return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (character) => character.toUpperCase());
  }

  function soulProfileTemplate() {
    return {
      schema: SOUL_PROFILE_SCHEMA,
      profile_schema_version: "1.0-draft",
      quiz_definition_version: "pending",
      scoring_model_version: "pending",
      completed_at: null,
      user_confirmed_at: null,
      role_constellation: [{ role_id: "shared-identity", label: "My Shared Mission Control", state: "primary", priority: 100, authorization_status: "unverified" }],
      core_values: ["human dignity", "accountable judgment"],
      mission_and_purpose: { mission: "", populations: [], guiding_principles: [] },
      learner_and_developmental_stage: [],
      advanced_studies: [],
      working_and_learning_preferences: { communication_style: "", decision_style: "", learning_preferences: [] },
      presentation_preferences: { theme_token: "direction", tone: "clear and encouraging" },
      role_synergies: [],
      role_tensions: [],
      wellness_limits: [],
      ai_relationship_preferences: [],
      governance_boundaries: { may_support: [], prepare_only: [], requires_confirmation: [], requires_supervision: [], requires_accountable_human_judgment: [], never_delegate: [], memory_allowed: [], memory_denied: [], escalation_rules: [] },
      dashboard_recommendations: ["shared-identity"],
      uncertainties: ["Quiz redesign is not yet final."],
      source_provenance: ["Derived Soul Quiz result; no raw answers."],
      demo: false
    };
  }

  function discoverPacketTemplate() {
    return {
      schema: DISCOVER_PACKET_SCHEMA,
      packet_schema_version: "1.0-draft",
      generated_at: null,
      mission_statement: "",
      core_values: [],
      current_priorities: [],
      goals: { short_term: [], medium_term: [], long_term: [] },
      working_preferences: { communication_style: "", decision_style: "", learning_preferences: [] },
      role_goals: [],
      ai_boundaries: { default_autonomy: "prepare_only", may_support: [], requires_confirmation: [], never_delegate: [] },
      governance_preferences: { risk_tolerance: "conservative", default_edena: "unclassified", default_retention: "session_only" },
      recommended_workflow_ids: [],
      recommended_capability_ids: [],
      uncertainties: ["Confirm this derived configuration with the user before applying it."],
      source_provenance: ["Derived Discover Packet configuration; no raw interview notes."],
      demo: false
    };
  }

  function sampleDiscoverPacket() {
    const packet = discoverPacketTemplate();
    packet.generated_at = new Date().toISOString();
    packet.mission_statement = "Help a healthcare team learn, improve and care for people without losing dignity, evidence or human accountability.";
    packet.core_values = ["human dignity", "psychological safety", "evidence", "accountability"];
    packet.current_priorities = ["Build one sustainable improvement rhythm", "Protect team capacity", "Learn responsible AI supervision"];
    packet.goals.short_term = ["Complete one bounded mission through Evaluate within 30 days"];
    packet.goals.medium_term = ["Create a reusable, human-reviewed improvement workflow within six months"];
    packet.goals.long_term = ["Develop responsible AI-agent orchestration capability without expanding professional authority"];
    packet.working_preferences = { communication_style: "clear, warm and concise", decision_style: "evidence-informed with visible uncertainty and human review", learning_preferences: ["worked examples", "reflection", "small experiments"] };
    packet.role_goals = [
      { role_id: "nurse-manager", goal: "Strengthen a learning culture", success_measure: "One evaluated improvement cycle with team feedback", priority: 90, default_edena: "yellow" },
      { role_id: "quality-safety", goal: "Make assumptions and measures visible", success_measure: "A reviewed measure and rollback plan", priority: 75, default_edena: "yellow" }
    ];
    packet.ai_boundaries = { default_autonomy: "prepare_only", may_support: ["research public sources", "compare options", "draft checklists"], requires_confirmation: ["finalize a plan", "share an artifact", "record external completion"], never_delegate: ["clinical judgment", "personnel decisions", "institutional approval", "external execution"] };
    packet.governance_preferences = { risk_tolerance: "conservative", default_edena: "yellow", default_retention: "session_only" };
    packet.recommended_workflow_ids = ["DSC-WF-01", "DSC-WF-03", "DSC-WF-20", "DSC-WF-22"];
    packet.recommended_capability_ids = ["structured-problem-solving", "edena-governance", "evaluation-qi", "agent-supervision"];
    packet.uncertainties = ["Synthetic example only; no real role, authority, organization or outcome is represented."];
    packet.source_provenance = ["Synthetic deidentified demonstration generated with Mission Control v2.0.0."];
    packet.demo = true;
    return packet;
  }

  function validateDiscoverPacket(value) {
    if (!isPlainObject(value) || value.schema !== DISCOVER_PACKET_SCHEMA) throw new Error("unknown Discover Packet adapter schema");
    assertExactKeys(value, ["schema", "packet_schema_version", "generated_at", "mission_statement", "core_values", "current_priorities", "goals", "working_preferences", "role_goals", "ai_boundaries", "governance_preferences", "recommended_workflow_ids", "recommended_capability_ids", "uncertainties", "source_provenance", "demo"], "Discover Packet");
    if (value.packet_schema_version !== "1.0-draft" || (value.generated_at !== null && !isIsoString(value.generated_at)) || typeof value.demo !== "boolean") throw new Error("unsupported packet version or date");
    if (typeof value.mission_statement !== "string" || value.mission_statement.length > 600) throw new Error("invalid mission statement");
    validateStringArray(value.core_values, "packet core values", 20, 120);
    validateStringArray(value.current_priorities, "packet priorities", 20, 240);
    if (!isPlainObject(value.goals)) throw new Error("invalid goals");
    assertExactKeys(value.goals, ["short_term", "medium_term", "long_term"], "packet goals");
    ["short_term", "medium_term", "long_term"].forEach((key) => validateStringArray(value.goals[key], `${key} goals`, 20, 300));
    if (!isPlainObject(value.working_preferences)) throw new Error("invalid packet working preferences");
    assertExactKeys(value.working_preferences, ["communication_style", "decision_style", "learning_preferences"], "packet working preferences");
    if (!safeShortString(value.working_preferences.communication_style, 200, true) || !safeShortString(value.working_preferences.decision_style, 200, true)) throw new Error("invalid packet working style");
    validateStringArray(value.working_preferences.learning_preferences, "packet learning preferences", 20, 160);
    if (!Array.isArray(value.role_goals) || value.role_goals.length > 30) throw new Error("invalid role goals");
    const roleGoals = value.role_goals.map((item) => {
      if (!isPlainObject(item)) throw new Error("invalid role goal");
      assertExactKeys(item, ["role_id", "goal", "success_measure", "priority", "default_edena"], "role goal");
      if (!ALLOWED_ROLE_IDS.has(item.role_id) || !safeShortString(item.goal, 300) || !safeShortString(item.success_measure, 300) || !Number.isInteger(item.priority) || item.priority < 0 || item.priority > 100 || !Object.hasOwn(EDENA_POLICY.tiers, item.default_edena)) throw new Error("invalid role goal value");
      return { ...item };
    });
    if (!isPlainObject(value.ai_boundaries)) throw new Error("invalid AI boundaries");
    assertExactKeys(value.ai_boundaries, ["default_autonomy", "may_support", "requires_confirmation", "never_delegate"], "AI boundaries");
    if (!["suggest_only", "prepare_only", "bounded_draft"].includes(value.ai_boundaries.default_autonomy)) throw new Error("invalid default autonomy");
    ["may_support", "requires_confirmation", "never_delegate"].forEach((key) => validateStringArray(value.ai_boundaries[key], key, 30, 240));
    if (!isPlainObject(value.governance_preferences)) throw new Error("invalid governance preferences");
    assertExactKeys(value.governance_preferences, ["risk_tolerance", "default_edena", "default_retention"], "governance preferences");
    if (!["conservative", "balanced", "exploratory_with_review"].includes(value.governance_preferences.risk_tolerance) || !Object.hasOwn(EDENA_POLICY.tiers, value.governance_preferences.default_edena) || !["session_only", "local_non_sensitive"].includes(value.governance_preferences.default_retention)) throw new Error("invalid governance preference value");
    if (!Array.isArray(value.recommended_workflow_ids) || value.recommended_workflow_ids.some((id) => !ALLOWED_WORKFLOW_IDS.has(id))) throw new Error("unknown recommended workflow");
    if (!Array.isArray(value.recommended_capability_ids) || value.recommended_capability_ids.some((id) => !ALLOWED_CAPABILITY_IDS.has(id))) throw new Error("unknown recommended capability");
    validateStringArray(value.uncertainties, "packet uncertainties", 30, 240);
    validateStringArray(value.source_provenance, "packet provenance", 30, 240);
    const detected = detectSensitiveText(JSON.stringify(value));
    if (detected.length) throw new Error(`possible prohibited or sensitive content: ${detected.join(", ")}`);
    return { ...value, role_goals: roleGoals, generated_at: value.generated_at ? safeIso(value.generated_at) : null };
  }

  function downloadDiscoverPacketTemplate() {
    downloadText("NAIO-Discover-Packet-Adapter-v1-Template.json", `${JSON.stringify(discoverPacketTemplate(), null, 2)}\n`, "application/json;charset=utf-8");
    setStatus(el.discoverPacketStatus, "Draft Discover Packet adapter downloaded. Add derived settings only—never raw interview notes or sensitive data.", true);
  }

  async function importDiscoverPacketFile(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_DISCOVER_IMPORT_BYTES) {
      setStatus(el.discoverPacketStatus, "Import rejected: Discover Packet exceeds the 100 KB limit.");
      return;
    }
    try {
      const parsed = JSON.parse(await file.text());
      rejectDangerousKeys(parsed);
      pendingDiscoverPacket = validateDiscoverPacket(parsed);
      renderDiscoverPacketState();
      setStatus(el.discoverPacketStatus, "Derived Discover Packet validated. Review every proposed setting before applying it.", true);
    } catch (error) {
      pendingDiscoverPacket = null;
      renderDiscoverPacketState();
      setStatus(el.discoverPacketStatus, `Import rejected: ${error.message}`);
    }
  }

  function previewSampleDiscoverPacket() {
    pendingDiscoverPacket = sampleDiscoverPacket();
    renderDiscoverPacketState();
    setStatus(el.discoverPacketStatus, "Synthetic Discover Packet loaded for preview. It is not your result or evidence.", true);
  }

  function renderDiscoverPacketState() {
    const packet = pendingDiscoverPacket || state.discoverPacket;
    if (!packet) {
      el.discoverPacketPreviewHeading.textContent = "No pending Discover Packet";
      el.discoverPacketPreview.replaceChildren(node("p", "muted-copy", "Mission Control is using neutral priorities and session-only retention."));
      el.discoverPacketPreviewActions.hidden = true;
      return;
    }
    el.discoverPacketPreviewHeading.textContent = pendingDiscoverPacket ? (packet.demo ? "Synthetic packet · not your profile" : "Validated packet preview") : (packet.demo ? "Synthetic packet applied" : "Applied Discover Packet");
    const dl = document.createElement("dl");
    const add = (label, value) => dl.append(node("dt", "", label), node("dd", "", value || "Not supplied"));
    add("Mission", packet.mission_statement);
    add("Priorities", packet.current_priorities.join("; "));
    add("Short-term goals", packet.goals.short_term.join("; "));
    add("Medium-term goals", packet.goals.medium_term.join("; "));
    add("Long-term goals", packet.goals.long_term.join("; "));
    add("Role goals", packet.role_goals.map((item) => `${getRole(item.role_id)?.name || item.role_id}: ${item.goal}`).join("; "));
    add("AI autonomy", packet.ai_boundaries.default_autonomy.replaceAll("_", " "));
    add("Never delegate", packet.ai_boundaries.never_delegate.join("; "));
    add("Governance", `${packet.governance_preferences.risk_tolerance}; default EDENA ${packet.governance_preferences.default_edena}; ${packet.governance_preferences.default_retention}`);
    add("Recommended workflows", packet.recommended_workflow_ids.join(", "));
    add("Uncertainties", packet.uncertainties.join("; "));
    el.discoverPacketPreview.replaceChildren(dl, node("p", "muted-copy", "Applying can tune mission language, priorities, safe defaults and workflow order. It cannot grant authority, enable an agent or approve an action."));
    el.discoverPacketPreviewActions.hidden = !pendingDiscoverPacket;
  }

  function applyPendingDiscoverPacket() {
    if (!pendingDiscoverPacket) return;
    state.discoverPacket = JSON.parse(JSON.stringify(pendingDiscoverPacket));
    state.discoverPacket.role_goals.forEach((item) => {
      if (!state.selectedRoleIds.includes(item.role_id)) state.selectedRoleIds.push(item.role_id);
      if (!ROLE_STATES.includes(state.roleStates[item.role_id])) state.roleStates[item.role_id] = "supporting";
    });
    ensureDashboardPartitions();
    pendingDiscoverPacket = null;
    const stored = saveState();
    renderAll();
    setStatus(el.discoverPacketStatus, stored ? `Discover Packet applied${state.discoverPacket.demo ? " as a synthetic demonstration" : ""}. Agents, permissions and authority were unchanged.` : "Discover Packet applied for this page, but browser storage failed. Agents, permissions and authority were unchanged.", stored);
    announce("Discover Packet settings applied. No agent or permission was enabled.");
  }

  function cancelDiscoverPacketPreview() {
    pendingDiscoverPacket = null;
    renderDiscoverPacketState();
    setStatus(el.discoverPacketStatus, "Discover Packet preview canceled. Nothing was applied.", true);
  }

  function clearAppliedDiscoverPacket() {
    if (!state.discoverPacket) return;
    if (!window.confirm("Clear the applied Discover Packet settings? Existing roles, missions and evidence will remain.")) return;
    state.discoverPacket = null;
    const stored = saveState();
    renderAll();
    setStatus(el.discoverPacketStatus, stored ? "Discover Packet settings cleared. Existing records remain." : "Packet cleared for this page, but browser storage could not be updated and it may return after reload.", stored);
  }

  function sampleSoulProfile() {
    const profile = soulProfileTemplate();
    profile.completed_at = new Date().toISOString();
    profile.role_constellation = [
      { role_id: "nurse-manager", label: "Nurse Leader or Healthcare Manager", state: "primary", priority: 100, authorization_status: "unverified" },
      { role_id: "nurse-educator", label: "Nurse Educator or Clinical Preceptor", state: "supporting", priority: 72, authorization_status: "unverified" },
      { role_id: "advanced-studies", label: "Advanced Studies Overlay", state: "emerging", priority: 64, authorization_status: "unverified" }
    ];
    profile.core_values = ["human dignity", "practical stewardship", "evidence before certainty", "shared growth"];
    profile.mission_and_purpose = { mission: "Help people and teams grow safer, wiser and more capable through governed learning and improvement.", populations: ["learners", "care teams"], guiding_principles: ["judgment first", "tools second", "make uncertainty visible"] };
    profile.learner_and_developmental_stage = ["experienced clinician", "emerging AI orchestrator"];
    profile.advanced_studies = [{ label: "Responsible AI leadership certificate", status: "active", target_date: null }];
    profile.working_and_learning_preferences = { communication_style: "concise, humane and direct", decision_style: "evidence-informed with explicit review gates", learning_preferences: ["worked examples", "reflection", "small experiments"] };
    profile.presentation_preferences = { theme_token: "connection", tone: "warm, direct and systems-aware" };
    profile.role_synergies = ["education strengthens leadership", "quality work creates learning opportunities"];
    profile.role_tensions = ["protected learning time competes with operational demand"];
    profile.wellness_limits = ["protect recovery time after demanding work"];
    profile.ai_relationship_preferences = ["thought partner", "research assistant", "workflow coordinator", "governance monitor"];
    profile.governance_boundaries = { may_support: ["learning plans", "scenario comparison", "drafting"], prepare_only: ["organizational recommendations"], requires_confirmation: ["sharing an artifact"], requires_supervision: ["clinical education decisions"], requires_accountable_human_judgment: ["clinical, employment and institutional decisions"], never_delegate: ["professional accountability", "final clinical judgment"], memory_allowed: ["non-sensitive preferences and goals"], memory_denied: ["PHI, secrets and confidential personnel data"], escalation_rules: ["pause when authority, data class or evidence is uncertain"] };
    profile.dashboard_recommendations = ["nurse-manager", "nurse-educator", "advanced-studies", "quality-safety"];
    profile.uncertainties = ["No competence, licensure or organizational authority was verified."];
    profile.source_provenance = ["Deidentified synthetic sample for interface demonstration."];
    profile.demo = true;
    return profile;
  }

  function downloadSoulProfileTemplate() {
    downloadText("NAIO-Soul-Profile-Adapter-v1-Template.json", `${JSON.stringify(soulProfileTemplate(), null, 2)}\n`, "application/json;charset=utf-8");
    setStatus(el.soulProfileStatus, "Draft adapter template downloaded. It is not the final Soul Quiz schema.", true);
  }

  async function importSoulProfileFile(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_SOUL_IMPORT_BYTES) {
      setStatus(el.soulProfileStatus, "Import rejected: Soul Profile exceeds the 100 KB limit.");
      return;
    }
    try {
      const parsed = JSON.parse(await file.text());
      rejectDangerousKeys(parsed);
      pendingSoulProfile = validateSoulProfile(parsed);
      renderSoulProfileState();
      setStatus(el.soulProfileStatus, "Derived profile validated. Review the preview before applying it.", true);
    } catch (error) {
      pendingSoulProfile = null;
      renderSoulProfileState();
      setStatus(el.soulProfileStatus, `Import rejected: ${error.message}`);
    }
  }

  function previewSampleSoulProfile() {
    pendingSoulProfile = sampleSoulProfile();
    renderSoulProfileState();
    setStatus(el.soulProfileStatus, "Deidentified synthetic profile loaded for preview. It is not your Soul Quiz result.", true);
  }

  function validateSoulProfile(value) {
    if (!isPlainObject(value) || value.schema !== SOUL_PROFILE_SCHEMA) throw new Error("unknown Soul Profile adapter schema");
    assertExactKeys(value, ["schema", "profile_schema_version", "quiz_definition_version", "scoring_model_version", "completed_at", "user_confirmed_at", "role_constellation", "core_values", "mission_and_purpose", "learner_and_developmental_stage", "advanced_studies", "working_and_learning_preferences", "presentation_preferences", "role_synergies", "role_tensions", "wellness_limits", "ai_relationship_preferences", "governance_boundaries", "dashboard_recommendations", "uncertainties", "source_provenance", "demo"], "Soul Profile");
    if (value.profile_schema_version !== "1.0-draft") throw new Error("unsupported profile schema version");
    if (typeof value.quiz_definition_version !== "string" || typeof value.scoring_model_version !== "string") throw new Error("missing quiz version metadata");
    if (value.completed_at !== null && !isIsoString(value.completed_at)) throw new Error("invalid completion date");
    if (value.user_confirmed_at !== null && !isIsoString(value.user_confirmed_at)) throw new Error("invalid confirmation date");
    if (!Array.isArray(value.role_constellation) || value.role_constellation.length < 1 || value.role_constellation.length > 20) throw new Error("role constellation must contain 1 to 20 roles");
    const roles = value.role_constellation.map((item) => {
      if (!isPlainObject(item)) throw new Error("invalid role constellation item");
      assertExactKeys(item, ["role_id", "label", "state", "priority", "authorization_status"], "role constellation item");
      if (!safeShortString(item.role_id, 64) || !safeShortString(item.label, 100) || !ROLE_STATES.includes(item.state) || !Number.isInteger(item.priority) || item.priority < 0 || item.priority > 100) throw new Error("invalid role constellation value");
      if (!["unverified", "user_asserted", "external_unverified"].includes(item.authorization_status)) throw new Error("invalid authorization status");
      return { ...item };
    });
    if (roles.filter((item) => item.state === "primary").length !== 1) throw new Error("role constellation must contain exactly one primary role");
    if (!isPlainObject(value.mission_and_purpose)) throw new Error("invalid mission and purpose");
    assertExactKeys(value.mission_and_purpose, ["mission", "populations", "guiding_principles"], "mission and purpose");
    if (typeof value.mission_and_purpose.mission !== "string" || value.mission_and_purpose.mission.length > 600) throw new Error("invalid mission statement");
    if (!isPlainObject(value.working_and_learning_preferences)) throw new Error("invalid working preferences");
    assertExactKeys(value.working_and_learning_preferences, ["communication_style", "decision_style", "learning_preferences"], "working preferences");
    if (!safeShortString(value.working_and_learning_preferences.communication_style, 200, true) || !safeShortString(value.working_and_learning_preferences.decision_style, 200, true)) throw new Error("invalid working preference");
    if (!isPlainObject(value.presentation_preferences)) throw new Error("invalid presentation preferences");
    assertExactKeys(value.presentation_preferences, ["theme_token", "tone"], "presentation preferences");
    if (!ALLOWED_DIMENSION_IDS.has(value.presentation_preferences.theme_token) || !safeShortString(value.presentation_preferences.tone, 160, true)) throw new Error("invalid presentation preference");
    const stringArrays = ["core_values", "learner_and_developmental_stage", "role_synergies", "role_tensions", "wellness_limits", "ai_relationship_preferences", "dashboard_recommendations", "uncertainties", "source_provenance"];
    stringArrays.forEach((key) => validateStringArray(value[key], key, 30, 240));
    validateStringArray(value.mission_and_purpose.populations, "populations", 20, 120);
    validateStringArray(value.mission_and_purpose.guiding_principles, "guiding principles", 20, 200);
    if (!Array.isArray(value.advanced_studies) || value.advanced_studies.length > 12) throw new Error("invalid Advanced Studies array");
    const studies = value.advanced_studies.map((item) => {
      if (!isPlainObject(item)) throw new Error("invalid Advanced Studies item");
      assertExactKeys(item, ["label", "status", "target_date"], "Advanced Studies item");
      if (!safeShortString(item.label, 160) || !["planned", "active", "paused", "completed"].includes(item.status) || (item.target_date !== null && !isIsoString(item.target_date))) throw new Error("invalid Advanced Studies value");
      return { ...item };
    });
    if (!isPlainObject(value.governance_boundaries)) throw new Error("invalid governance boundaries");
    const governanceKeys = ["may_support", "prepare_only", "requires_confirmation", "requires_supervision", "requires_accountable_human_judgment", "never_delegate", "memory_allowed", "memory_denied", "escalation_rules"];
    assertExactKeys(value.governance_boundaries, governanceKeys, "governance boundaries");
    governanceKeys.forEach((key) => validateStringArray(value.governance_boundaries[key], key, 30, 240));
    if (typeof value.demo !== "boolean") throw new Error("invalid demo flag");
    const sensitive = detectSensitiveText(JSON.stringify(value));
    if (sensitive.length) throw new Error(`possible prohibited or sensitive content: ${sensitive.join(", ")}`);
    return {
      ...value,
      role_constellation: roles,
      advanced_studies: studies,
      completed_at: value.completed_at ? safeIso(value.completed_at) : null,
      user_confirmed_at: value.user_confirmed_at ? safeIso(value.user_confirmed_at) : null
    };
  }

  function renderSoulProfileState() {
    const profile = pendingSoulProfile || state.soulProfile;
    el.restoreSoulProfile.disabled = !state.previousSoulProfile;
    if (!profile) {
      el.soulProfilePreviewHeading.textContent = "No pending profile";
      el.soulProfilePreview.replaceChildren(node("p", "muted-copy", "Your current dashboard is in the neutral Discover-first state."));
      el.soulPreviewActions.hidden = true;
      return;
    }
    el.soulProfilePreviewHeading.textContent = pendingSoulProfile ? (profile.demo ? "Synthetic preview · not your profile" : "Validated profile preview") : (profile.demo ? "Synthetic profile applied" : "Applied Soul Profile");
    const dl = document.createElement("dl");
    const add = (label, value) => { dl.append(node("dt", "", label), node("dd", "", value || "Not supplied")); };
    add("Mission", profile.mission_and_purpose.mission);
    add("Roles", profile.role_constellation.map((item) => `${item.label} (${item.state})`).join("; "));
    add("Core values", profile.core_values.join(", "));
    add("AI relationship", profile.ai_relationship_preferences.join(", "));
    add("Theme", profile.presentation_preferences.theme_token);
    add("Uncertainties", profile.uncertainties.join("; "));
    el.soulProfilePreview.replaceChildren(dl, node("p", "muted-copy", "Applying this profile can change presentation, role recommendations and workflow emphasis. It cannot grant authority or remove safeguards."));
    el.soulPreviewActions.hidden = !pendingSoulProfile;
  }

  function applyPendingSoulProfile() {
    if (!pendingSoulProfile) return;
    state.previousSoulProfile = state.soulProfile ? JSON.parse(JSON.stringify(state.soulProfile)) : null;
    const applied = JSON.parse(JSON.stringify(pendingSoulProfile));
    applied.user_confirmed_at = new Date().toISOString();
    state.soulProfile = applied;
    state.soul = null;
    const recommended = unique(applied.role_constellation.map((item) => item.role_id).concat(applied.dashboard_recommendations).filter((id) => ALLOWED_ROLE_IDS.has(id)));
    if (applied.advanced_studies.length && !recommended.includes("advanced-studies")) recommended.push("advanced-studies");
    if (recommended.length) {
      state.selectedRoleIds = unique(state.selectedRoleIds.concat(recommended));
      const primary = applied.role_constellation.find((item) => item.state === "primary" && ALLOWED_ROLE_IDS.has(item.role_id));
      if (primary) {
        Object.keys(state.roleStates).forEach((roleId) => {
          if (state.roleStates[roleId] === "primary") state.roleStates[roleId] = "supporting";
        });
        state.activeRoleId = primary.role_id;
      }
      applied.role_constellation.forEach((item) => { if (ALLOWED_ROLE_IDS.has(item.role_id)) state.roleStates[item.role_id] = item.state; });
      if (applied.advanced_studies.length) state.roleStates["advanced-studies"] = state.roleStates["advanced-studies"] || "emerging";
      state.selectedRoleIds.forEach((roleId) => { if (!ROLE_STATES.includes(state.roleStates[roleId])) state.roleStates[roleId] = "supporting"; });
      if (!Object.values(state.roleStates).includes("primary")) state.roleStates[state.selectedRoleIds[0]] = "primary";
    }
    ensureDashboardPartitions();
    pendingSoulProfile = null;
    const stored = saveState();
    renderAll();
    setStatus(el.soulProfileStatus, stored ? `Soul Profile applied${applied.demo ? " as a synthetic demonstration" : ""}. Permissions and safety gates were unchanged.` : "Soul Profile applied for this page, but browser storage failed. Permissions and safety gates were unchanged.", stored);
    announce("Soul Profile personalization applied. Authority remains unchanged.");
  }

  function cancelSoulPreview() {
    pendingSoulProfile = null;
    renderSoulProfileState();
    setStatus(el.soulProfileStatus, "Profile preview canceled. Nothing was applied.", true);
  }

  function restorePreviousSoulProfile() {
    if (!state.previousSoulProfile) {
      setStatus(el.soulProfileStatus, "No prior Soul Profile is available for rollback.");
      return;
    }
    const current = state.soulProfile;
    state.soulProfile = state.previousSoulProfile;
    state.previousSoulProfile = current;
    const stored = saveState();
    renderAll();
    setStatus(el.soulProfileStatus, stored ? "Prior Soul Profile restored. Role permissions and governance remained unchanged." : "Prior profile restored for this page, but browser storage failed.", stored);
  }

  function clearAppliedSoulProfile() {
    if (!state.soulProfile) return;
    if (!window.confirm("Clear the applied derived Soul Profile? Role dashboards and missions will remain.")) return;
    state.previousSoulProfile = state.soulProfile;
    state.soulProfile = null;
    const stored = saveState();
    renderAll();
    setStatus(el.soulProfileStatus, stored ? "Applied Soul Profile cleared. Neutral presentation restored." : "Profile cleared for this page, but browser storage could not be updated and may return after reload.", stored);
  }

  function openOnboarding(step) {
    onboardingStep = Math.max(0, Math.min(3, step));
    showOnboardingStep(onboardingStep);
    if (typeof el.onboardingDialog.showModal === "function" && !el.onboardingDialog.open) el.onboardingDialog.showModal();
    else el.onboardingDialog.setAttribute("open", "");
  }

  function showOnboardingStep(step) {
    onboardingStep = Math.max(0, Math.min(3, step));
    document.querySelectorAll("[data-onboarding-step]").forEach((panel) => {
      const active = Number(panel.dataset.onboardingStep) === onboardingStep;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    el.onboardingProgress.style.width = `${(onboardingStep + 1) * 25}%`;
    el.onboardingBack.hidden = onboardingStep === 0;
    el.onboardingNext.hidden = onboardingStep === 3;
    el.onboardingFinish.hidden = onboardingStep !== 3;
  }

  function advanceOnboarding() {
    if (onboardingStep === 1 && !el.onboardingSafetyAck.checked) {
      announce("Confirm the safety and local-storage boundary before continuing.");
      el.onboardingSafetyAck.focus();
      return;
    }
    showOnboardingStep(onboardingStep + 1);
  }

  function finishOnboarding() {
    state.onboardingComplete = true;
    const stored = saveState();
    if (typeof el.onboardingDialog.close === "function") el.onboardingDialog.close();
    else el.onboardingDialog.removeAttribute("open");
    announce(stored ? "Mission Control is ready in neutral, governed mode." : "Mission Control is ready for this open page, but browser storage failed; onboarding may return after reload.");
  }

  function closeOnboardingWithoutFinish() {
    if (!state.onboardingComplete) {
      showOnboardingStep(1);
      announce("Review and acknowledge the safety boundary before entering Mission Control.");
      return;
    }
    if (typeof el.onboardingDialog.close === "function") el.onboardingDialog.close();
    else el.onboardingDialog.removeAttribute("open");
  }

  async function copyText(textarea, successMessage) {
    const text = textarea.value;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      announce(successMessage);
    } catch (_error) {
      textarea.focus();
      textarea.select();
      const success = document.execCommand && document.execCommand("copy");
      announce(success ? successMessage : "Clipboard access is restricted. The text is selected for manual copy.");
    }
  }

  function openTrustedAddress(input, statusElement) {
    const raw = input.value.trim();
    if (!raw) {
      setStatus(statusElement, "Enter a trusted loopback HTTP or HTTPS Hermes address. The prompt is not sent.");
      input.focus();
      return;
    }
    try {
      const url = new URL(raw);
      if (!["http:", "https:"].includes(url.protocol)) throw new Error("only http or https is allowed");
      if (url.username || url.password) throw new Error("embedded credentials are not allowed");
      if (url.protocol === "http:" && !isLoopbackHostname(url.hostname)) throw new Error("plaintext http is allowed only for localhost/loopback; use https for remote Hermes addresses");
      window.open(url.href, "_blank", "noopener,noreferrer");
      setStatus(statusElement, "Hermes opened separately. No prompt or mission content was transmitted.", true);
    } catch (error) {
      setStatus(statusElement, `Address rejected: ${error.message}`);
    }
  }

  function validateStringArray(value, label, maximumCount, maximumLength) {
    if (!Array.isArray(value) || value.length > maximumCount || value.some((item) => !safeShortString(item, maximumLength, true))) throw new Error(`invalid ${label}`);
  }

  function safeShortString(value, maximumLength, allowEmpty = false) {
    return typeof value === "string" && value.length <= maximumLength && (allowEmpty || value.trim().length > 0);
  }

  function toggleFavorite(workflowId) {
    const dashboard = activeDashboard();
    const favorites = dashboard.favoriteWorkflowIds;
    const index = favorites.indexOf(workflowId);
    if (index >= 0) favorites.splice(index, 1);
    else favorites.push(workflowId);
    dashboard.favoriteWorkflowIds = unique(favorites).filter((id) => ALLOWED_WORKFLOW_IDS.has(id));
    saveState();
    renderDashboard();
    renderWorkflows();
  }

  function renderRoleDashboardLabel(roleId) {
    const roleItem = getRole(roleId);
    const dashboard = state.dashboards[roleId];
    return `${roleItem.name} (${dashboard.dashboardId.slice(0, 8)})`;
  }

  function openWorkflowDialog(workflowId) {
    const item = getWorkflow(workflowId);
    if (!item) return;
    activeWorkflow = item;
    clearTransientHandoff();
    const group = getGroup(item.groupId);
    el.workflowDialogMeta.textContent = `${item.id} · ${item.powerId} · Preview Only`;
    el.workflowDialogTitle.textContent = item.title;
    const card = node("div", "dialog-details-card");
    card.append(node("h3", "", `${item.templateId} · ${item.schema}`), node("p", "", item.description));
    const scope = item.id === "DSC-WF-24"
      ? "Owner-private exception: use only a separately approved encrypted owner-private store. This dashboard never saves private content."
      : "Allowed here: public, synthetic or approved aggregate D0/D1 metadata only.";
    card.append(node("p", "", scope), node("p", "", `Active role view: ${getActiveRole().name}. This view is not proof of authority.`));
    el.workflowDialogDetails.replaceChildren(card);
    if (typeof el.workflowDialog.showModal === "function") el.workflowDialog.showModal();
    else el.workflowDialog.setAttribute("open", "");
    setTimeout(() => el.workflowContext.focus(), 0);
  }

  function closeWorkflowDialog() {
    clearTransientHandoff();
    if (typeof el.workflowDialog.close === "function") el.workflowDialog.close();
    else el.workflowDialog.removeAttribute("open");
    activeWorkflow = null;
  }

  function clearTransientHandoff() {
    if (!el.workflowContext) return;
    el.workflowContext.value = "";
    el.handoffEdena.value = "unclassified";
    el.handoffEdenaReason.value = "";
    el.handoffConsent.checked = false;
    el.handoffOutput.value = "";
    el.hermesUrl.value = "";
    el.handoffOutputWrap.hidden = true;
    setStatus(el.handoffStatus, "");
  }

  function buildHandoff() {
    if (!activeWorkflow) return;
    if (!el.handoffConsent.checked) {
      setStatus(el.handoffStatus, "Confirm the data-boundary statement before building a prompt.");
      el.handoffConsent.focus();
      return;
    }
    const context = el.workflowContext.value.trim();
    const edena = el.handoffEdena.value;
    const edenaReason = el.handoffEdenaReason.value.trim();
    if (edena === "unclassified") {
      setStatus(el.handoffStatus, "Classify the handoff with EDENA before preparing it for Hermes.");
      el.handoffEdena.focus();
      return;
    }
    if (!edenaReason) {
      setStatus(el.handoffStatus, "Record a brief, non-sensitive reason for the EDENA classification.");
      el.handoffEdenaReason.focus();
      return;
    }
    const detected = detectSensitiveText(`${context}\n${edenaReason}`);
    if (detected.length) {
      setStatus(el.handoffStatus, `Remove possible sensitive content before continuing: ${detected.join(", ")}. The text was not saved.`);
      return;
    }
    el.handoffOutput.value = buildHandoffMarkdown(activeWorkflow, context, edena, edenaReason);
    el.handoffOutputWrap.hidden = false;
    setStatus(el.handoffStatus, "Safe Preview Only handoff created locally. Review every line before using it.", true);
    el.handoffOutput.focus();
  }

  function buildHandoffMarkdown(item, context, edena, edenaReason) {
    const roleItem = getActiveRole();
    const soul = getSoulPresentation();
    const privateRule = item.id === "DSC-WF-24"
      ? "This is WF-24. Do not place private content in the organizational tenant or this browser. Require an approved, owner-only encrypted store; otherwise keep the work question-only and discard it. Emit no institutional existence trace or control receipt for private content."
      : "Use only public, synthetic or explicitly approved aggregate D0/D1 metadata. Reject PHI, participant-level data, confidential research, personnel data, credentials and secrets before processing.";
    const packetBoundary = state.discoverPacket ? `Apply the reviewed Discover Packet boundary: autonomy ${state.discoverPacket.ai_boundaries.default_autonomy}; requires confirmation for ${state.discoverPacket.ai_boundaries.requires_confirmation.join(", ") || "all consequential use"}; never delegate ${state.discoverPacket.ai_boundaries.never_delegate.join(", ") || "professional judgment"}.` : "No Discover Packet boundary is active; default to prepare-only and require confirmation for every consequential use.";
    return [
      `# DISCOVER Hermes Preview Handoff — ${item.id}`,
      "",
      `**Workflow:** ${item.title}`,
      `**Power / template / schema:** ${item.powerId} / ${item.templateId} / ${item.schema}`,
      `**Role dashboard view:** ${roleItem.name} (presentation context only; not proof of identity, credentials, delegation or authority)`,
      `**Soul presentation cue:** ${soul.title} — use only to shape tone, question order and visual emphasis; never permissions, conclusions or evidence weighting.`,
      `**EDENA advisory:** ${EDENA_POLICY.tiers[edena].label}`,
      `**Classification reason:** ${edenaReason}`,
      "**Review rule:** Personal Edition advisory only. This classification does not approve use; Orange/Red requires qualified review and all outputs remain Preview Only.",
      "",
      "## Non-negotiable operating instruction",
      "",
      `Open ${item.id} inside the existing DISCOVER lane in **PREVIEW ONLY**. Do not enable an agent, connector, tool, network destination, background task or external action. Do not submit, publish, recruit, consent, enroll, deploy, purchase, send, contact, write to an official system or make a clinical, research, regulatory, safety, financial, employment or authority determination.`,
      "",
      privateRule,
      packetBoundary,
      "",
      "Treat the selected role as a dashboard recipe only. Re-verify the active organizational hat, named accountable human, delegated scope, jurisdiction, allowed data class, official destination and expiry before any persistent organizational artifact. If authority, boundary, evidence, approval or data status is missing, conflicting, stale or unresolved, keep the output blocked/unknown and route questions to the named qualified human.",
      "",
      "Run the DISCOVER FRAME and TRACE routines. Separate facts, operator-provided statements, interpretations, inferences, scenarios and unknowns. Preserve contradictions, limitations, dissent, equity, accessibility, dignity, burden and correction questions. Cite exact source/version/status where supplied; never invent a source, quote, result, approval, participant voice, credential or institutional position.",
      "",
      "Produce one clearly labeled, source-bounded preview using the stated template/schema. Show: allowed inputs used; excluded or unsupported inputs; assumptions and unknowns; human review gate; official route; expiry; correction/discard/rollback path; and the explicit statement **NO EXTERNAL ACTION TAKEN**. Stop after the preview and wait for human review.",
      "",
      "## User-provided non-sensitive context",
      "",
      context || "No context supplied. Ask only the minimum safe, non-sensitive questions needed to prepare this preview.",
      "",
      "---",
      `Generated locally by DISCOVER Personalized Mission Control v${APP_VERSION}. This handoff was not transmitted automatically.`
    ].join("\n");
  }

  async function copyHandoff() {
    const text = el.handoffOutput.value;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      announce("Prompt copied. Paste it only into the intended DISCOVER Hermes lane.");
    } catch (_error) {
      el.handoffOutput.focus();
      el.handoffOutput.select();
      const success = document.execCommand && document.execCommand("copy");
      announce(success ? "Prompt copied." : "Clipboard access is restricted. The prompt is selected for manual copy.");
    }
  }

  function downloadHandoff() {
    if (!activeWorkflow || !el.handoffOutput.value) return;
    downloadText(`DISCOVER-${activeWorkflow.short}-Hermes-Preview-Handoff.md`, el.handoffOutput.value, "text/markdown;charset=utf-8");
    announce("Markdown handoff downloaded.");
  }

  function openHermesSeparately() {
    const raw = el.hermesUrl.value.trim();
    if (!raw) {
      setStatus(el.handoffStatus, "Enter your trusted local or HTTPS Hermes address. It is used for this session only.");
      el.hermesUrl.focus();
      return;
    }
    try {
      const url = new URL(raw);
      if (!["http:", "https:"].includes(url.protocol)) throw new Error("only http or https is allowed");
      if (url.username || url.password) throw new Error("addresses containing embedded credentials are not allowed");
      if (url.protocol === "http:" && !isLoopbackHostname(url.hostname)) throw new Error("plaintext http is allowed only for localhost/loopback; use https for remote Hermes addresses");
      window.open(url.href, "_blank", "noopener,noreferrer");
      setStatus(el.handoffStatus, "Hermes opened separately. The prompt was not sent; copy and paste it yourself.", true);
    } catch (error) {
      setStatus(el.handoffStatus, `Hermes address rejected: ${error.message}`);
    }
  }

  function exportHermesHandoff() {
    const soul = getSoulPresentation();
    const lines = [
      "# DISCOVER Dashboard Profile Handoff for Hermes",
      "",
      `**Dashboard companion version:** ${APP_VERSION}`,
      `**Instance ID:** ${state.instanceId}`,
      `**EDENA advisory:** Yellow · verify local path, target workspace, lane scope and registration diff before acceptance.`,
      "**Review rule:** Manual human review required; this file requests link/configuration preparation only and grants no execution permission.",
      "**Authority statement:** Role selections are presentation recipes only. They do not verify identity, credentials, delegation or authority.",
      "**Data statement:** This export contains no raw Soul Quiz answers or mission records, but it may include derived personal presentation cues. Review before sharing.",
      "",
      "## Requested role dashboard links",
      "",
      ...state.selectedRoleIds.map((roleId) => {
        const roleItem = getRole(roleId);
        return `- ${roleItem.name} — dashboard partition ${state.dashboards[roleId].dashboardId}; recommended previews: ${roleItem.workflowIds.join(", ")}`;
      }),
      "",
      "## Presentation-only Soul signature",
      "",
      `- Primary presentation: ${soul.title}`,
      `- Coaching cue: ${soul.coaching}`,
      "- No raw answers or numeric quiz scores are included in this Hermes handoff.",
      "",
      "## Hermes integration request",
      "",
      "Register one local Nurse AI OS Mission Control entry plus separate view-only links for the selected role dashboards. Preserve each existing Nurse AI OS lane and keep role dashboards modular under the user’s shared identity. Do not copy raw browser storage into Hermes. Do not infer or grant authority. Keep every launcher Preview Only, agents and tools disabled until separately reviewed, and external actions Off. Add a local Guide link where supported. If local-file launch links are unsupported, report that limitation and retain manual copy/download handoffs. Return a visible before/after inventory and stop for human acceptance.",
      "",
      "The local dashboard path must be supplied and approved by the user at installation time. Never guess it."
    ];
    downloadText("DISCOVER-Dashboard-Profile-Handoff-for-Hermes.md", lines.join("\n"), "text/markdown;charset=utf-8");
    setStatus(el.roleStatus, "Hermes profile handoff downloaded. Review it before installation.", true);
  }

  function exportProfile() {
    const exportedMissions = state.missions.filter((mission) => !mission.sample).map((mission) => JSON.parse(JSON.stringify(mission)));
    const exportedMissionIds = new Set(exportedMissions.map((mission) => mission.id));
    const profile = {
      schema: PROFILE_SCHEMA,
      app_version: APP_VERSION,
      generated_at: new Date().toISOString(),
      instance_id: state.instanceId,
      role_ids: state.selectedRoleIds.slice(),
      active_role_id: state.activeRoleId,
      active_mission_id: exportedMissionIds.has(state.activeMissionId) ? state.activeMissionId : null,
      role_states: { ...state.roleStates },
      dashboards: Object.fromEntries(state.selectedRoleIds.map((roleId) => [roleId, {
        dashboard_id: state.dashboards[roleId].dashboardId,
        favorite_workflow_ids: state.dashboards[roleId].favoriteWorkflowIds.slice()
      }])),
      soul: state.soul ? {
        scores: { ...state.soul.scores },
        primary: state.soul.primary,
        secondary: state.soul.secondary,
        completed_at: state.soul.completedAt
      } : null,
      soul_profile: state.soulProfile ? JSON.parse(JSON.stringify(state.soulProfile)) : null,
      discover_packet: state.discoverPacket ? JSON.parse(JSON.stringify(state.discoverPacket)) : null,
      missions: exportedMissions,
      evidence: state.evidence.map((record) => JSON.parse(JSON.stringify(record))),
      guide_seen: Boolean(state.guideSeen),
      onboarding_complete: Boolean(state.onboardingComplete),
      edena_policy: `${EDENA_POLICY.id}@${EDENA_POLICY.version}`,
      backup_edena: "yellow",
      backup_review_required: "Review every field, storage location and destination before moving or sharing this unencrypted backup.",
      privacy_note: "This explicit backup may contain user-entered mission and evidence text. It is local but not encrypted. No raw Soul Quiz answers are included. Review before moving or sharing."
    };
    downloadText("DISCOVER-Mission-Control-Backup-v2.json", `${JSON.stringify(profile, null, 2)}\n`, "application/json;charset=utf-8");
    setStatus(el.profileStatus, "Backup exported. It is not encrypted and may contain mission text; review it before moving or sharing.", true);
  }

  async function importProfile(event) {
    const file = event.target.files && event.target.files[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_IMPORT_BYTES) {
      setStatus(el.profileStatus, "Import rejected: backup exceeds the 1 MB limit.");
      return;
    }
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      rejectDangerousKeys(parsed);
      state = validateImportedProfile(parsed);
      ensureDashboardPartitions();
      const stored = saveState();
      renderAll();
      setStatus(el.profileStatus, stored ? "Backup imported after atomic schema, governance and safety validation." : "Backup validated and loaded for this page, but browser storage failed; it will not survive reload.", stored);
      announce("DISCOVER Mission Control backup imported.");
    } catch (error) {
      setStatus(el.profileStatus, `Import rejected: ${error.message}`);
    }
  }

  function validateImportedProfile(value) {
    if (!isPlainObject(value) || value.schema !== PROFILE_SCHEMA) throw new Error("unknown profile schema");
    assertExactKeys(value, ["schema", "app_version", "generated_at", "instance_id", "role_ids", "active_role_id", "active_mission_id", "role_states", "dashboards", "soul", "soul_profile", "discover_packet", "missions", "evidence", "guide_seen", "onboarding_complete", "edena_policy", "backup_edena", "backup_review_required", "privacy_note"], "profile");
    if (value.app_version !== APP_VERSION || !isIsoString(value.generated_at) || typeof value.privacy_note !== "string" || value.edena_policy !== `${EDENA_POLICY.id}@${EDENA_POLICY.version}` || value.backup_edena !== "yellow" || typeof value.backup_review_required !== "string") throw new Error("incompatible app version or EDENA policy metadata");
    if (!Array.isArray(value.role_ids) || value.role_ids.length < 1 || value.role_ids.length > ROLES.length) throw new Error("invalid role list");
    const roleIds = unique(value.role_ids);
    if (roleIds.some((id) => typeof id !== "string" || !ALLOWED_ROLE_IDS.has(id))) throw new Error("unknown role ID");
    if (!roleIds.includes(value.active_role_id)) throw new Error("active role is not selected");
    if (!isPlainObject(value.role_states)) throw new Error("missing role states");
    assertExactKeys(value.role_states, roleIds, "role states");
    const roleStates = {};
    roleIds.forEach((roleId) => {
      if (!ROLE_STATES.includes(value.role_states[roleId])) throw new Error(`invalid role state for ${roleId}`);
      roleStates[roleId] = value.role_states[roleId];
    });
    if (Object.values(roleStates).filter((roleState) => roleState === "primary").length !== 1) throw new Error("exactly one role must be primary");
    if (!isPlainObject(value.dashboards)) throw new Error("missing dashboard partitions");
    assertExactKeys(value.dashboards, roleIds, "dashboard map");
    const dashboards = {};
    roleIds.forEach((roleId) => {
      const imported = value.dashboards[roleId];
      if (!isPlainObject(imported)) throw new Error(`missing ${roleId} dashboard`);
      assertExactKeys(imported, ["dashboard_id", "favorite_workflow_ids"], `${roleId} dashboard`);
      const dashboardId = validUuid(imported.dashboard_id) ? imported.dashboard_id : makeUuid();
      if (!Array.isArray(imported.favorite_workflow_ids) || imported.favorite_workflow_ids.length > WORKFLOWS.length) throw new Error(`invalid favorites for ${roleId}`);
      const favoriteWorkflowIds = unique(imported.favorite_workflow_ids);
      if (favoriteWorkflowIds.some((id) => typeof id !== "string" || !ALLOWED_WORKFLOW_IDS.has(id))) throw new Error(`unknown workflow favorite for ${roleId}`);
      dashboards[roleId] = { dashboardId, favoriteWorkflowIds };
    });
    const soul = validateLegacySoul(value.soul);
    const soulProfile = value.soul_profile === null ? null : validateSoulProfile(value.soul_profile);
    const discoverPacket = value.discover_packet === null ? null : validateDiscoverPacket(value.discover_packet);
    if (!Array.isArray(value.missions) || value.missions.length > 100) throw new Error("invalid mission collection");
    const missions = value.missions.map((mission) => validateMissionRecord(mission, roleIds));
    if (new Set(missions.map((mission) => mission.id)).size !== missions.length) throw new Error("duplicate mission ID");
    const missionIds = new Set(missions.map((mission) => mission.id));
    const missionMap = new Map(missions.map((mission) => [mission.id, mission]));
    if (value.active_mission_id !== null && !missionIds.has(value.active_mission_id)) throw new Error("active mission is unavailable");
    if (!Array.isArray(value.evidence) || value.evidence.length > 500) throw new Error("invalid evidence collection");
    const evidence = value.evidence.map((record) => validateEvidenceRecord(record, roleIds, missionIds, missionMap));
    if (new Set(evidence.map((record) => record.id)).size !== evidence.length) throw new Error("duplicate evidence ID");
    return {
      version: APP_VERSION,
      instanceId: validUuid(value.instance_id) ? value.instance_id : makeUuid(),
      selectedRoleIds: roleIds,
      activeRoleId: value.active_role_id,
      activeMissionId: value.active_mission_id,
      roleStates,
      dashboards,
      soul,
      soulProfile,
      discoverPacket,
      previousSoulProfile: null,
      missions,
      evidence,
      guideSeen: Boolean(value.guide_seen),
      onboardingComplete: Boolean(value.onboarding_complete)
    };
  }

  function validateLegacySoul(value) {
    if (value === null || value === undefined) return null;
    if (!isPlainObject(value) || !isPlainObject(value.scores)) throw new Error("invalid provisional Soul result");
    assertExactKeys(value, ["scores", "primary", "secondary", "completed_at"], "Soul result");
    assertExactKeys(value.scores, DIMENSIONS.map((dimension) => dimension.id), "Soul scores");
    const scores = {};
    DIMENSIONS.forEach((dimension) => {
      const score = value.scores[dimension.id];
      if (!Number.isInteger(score) || score < 0 || score > 100) throw new Error(`invalid ${dimension.id} score`);
      scores[dimension.id] = score;
    });
    const allowedPrimary = new Set([...ALLOWED_DIMENSION_IDS, "integrator"]);
    if (!allowedPrimary.has(value.primary) || !ALLOWED_DIMENSION_IDS.has(value.secondary) || !isIsoString(value.completed_at)) throw new Error("invalid Soul signature");
    return { scores, primary: value.primary, secondary: value.secondary, completedAt: safeIso(value.completed_at) };
  }

  function validateMissionRecord(value, roleIds, allowSample = false) {
    if (!isPlainObject(value)) throw new Error("invalid mission record");
    assertExactKeys(value, ["id", "schema", "title", "roleId", "edition", "edena", "edenaReason", "artifactState", "missionStatus", "retentionMode", "summary", "iteration", "parentMissionId", "sample", "riskAcknowledged", "approvalAttested", "approvalReference", "revision", "createdAt", "updatedAt", "stages", "history"], "mission record");
    if (!validUuid(value.id) || value.schema !== "NAIO-MISSION-1" || !safeShortString(value.title, 100) || !roleIds.includes(value.roleId)) throw new Error("invalid mission identity");
    if (!["personal", "institutional_preview"].includes(value.edition) || !Object.hasOwn(EDENA_POLICY.tiers, value.edena) || !safeShortString(value.edenaReason, 300) || !ARTIFACT_STATES.includes(value.artifactState)) throw new Error("invalid mission governance");
    if (!["active", "paused", "completed", "archived"].includes(value.missionStatus) || !["session_only", "local_non_sensitive"].includes(value.retentionMode)) throw new Error("invalid mission status");
    if (typeof value.summary !== "string" || value.summary.length > 1000 || !Number.isInteger(value.iteration) || value.iteration < 1 || value.iteration > 100 || (value.parentMissionId !== null && !validUuid(value.parentMissionId))) throw new Error("invalid mission content metadata");
    if (typeof value.sample !== "boolean" || (!allowSample && value.sample) || typeof value.riskAcknowledged !== "boolean" || typeof value.approvalAttested !== "boolean" || !safeShortString(value.approvalReference, 120, true) || !Number.isInteger(value.revision) || value.revision < 0 || !isIsoString(value.createdAt) || !isIsoString(value.updatedAt)) throw new Error("invalid mission flags");
    if (!isPlainObject(value.stages)) throw new Error("invalid mission stages");
    assertExactKeys(value.stages, MISSION_STAGES.map((stage) => stage.id), "mission stages");
    const stages = {};
    MISSION_STAGES.forEach((stage) => {
      const item = value.stages[stage.id];
      if (!isPlainObject(item)) throw new Error(`invalid ${stage.id} stage`);
      assertExactKeys(item, ["notes", "outcome", "complete", "needsReview", "revision"], `${stage.id} stage`);
      if (typeof item.notes !== "string" || item.notes.length > 5000 || typeof item.outcome !== "string" || item.outcome.length > 1500 || typeof item.complete !== "boolean" || typeof item.needsReview !== "boolean" || !Number.isInteger(item.revision) || item.revision < 0) throw new Error(`invalid ${stage.id} stage value`);
      stages[stage.id] = { ...item };
    });
    if (!Array.isArray(value.history) || value.history.length > 20) throw new Error("invalid mission history");
    const history = value.history.map((item) => {
      if (!isPlainObject(item)) throw new Error("invalid mission history entry");
      assertExactKeys(item, ["revision", "changedStages", "at"], "mission history entry");
      if (!Number.isInteger(item.revision) || !Array.isArray(item.changedStages) || item.changedStages.some((id) => !ALLOWED_STAGE_IDS.has(id)) || !isIsoString(item.at)) throw new Error("invalid mission history value");
      return { revision: item.revision, changedStages: unique(item.changedStages), at: safeIso(item.at) };
    });
    const detected = detectSensitiveText([value.title, value.summary, value.edenaReason, value.approvalReference, ...Object.values(stages).flatMap((item) => [item.notes, item.outcome])].join("\n"));
    if (detected.length) throw new Error(`mission contains possible prohibited or sensitive content: ${detected.join(", ")}`);
    const normalized = { ...value, stages, history, createdAt: safeIso(value.createdAt), updatedAt: safeIso(value.updatedAt) };
    const semanticError = validateMissionSemantic(normalized, Boolean(value.sample && allowSample));
    if (semanticError) throw new Error(`mission governance invariant failed: ${semanticError}`);
    return normalized;
  }

  function validateEvidenceRecord(value, roleIds, missionIds, missionMap = new Map()) {
    if (!isPlainObject(value)) throw new Error("invalid evidence record");
    assertExactKeys(value, ["id", "schema", "capabilityId", "missionId", "roleId", "type", "provenance", "edena", "summary", "createdAt"], "evidence record");
    const types = ["mission", "artifact_review", "assessment", "reflection", "outcome", "human_review", "safety_drill", "agent_run", "knowledge_transfer"];
    const provenance = ["app_observed", "user_attested", "human_reviewed_unverified"];
    if (!validUuid(value.id) || value.schema !== "NAIO-CAPABILITY-EVIDENCE-1" || !ALLOWED_CAPABILITY_IDS.has(value.capabilityId) || (value.missionId !== null && !missionIds.has(value.missionId)) || !roleIds.includes(value.roleId)) throw new Error("invalid evidence identity");
    if (!types.includes(value.type) || !provenance.includes(value.provenance) || !["green", "yellow", "orange", "red"].includes(value.edena) || !safeShortString(value.summary, 600) || !isIsoString(value.createdAt)) throw new Error("invalid evidence value");
    const mission = value.missionId === null ? null : missionMap.get(value.missionId);
    if (mission && (mission.sample || mission.roleId !== value.roleId || mission.edena !== value.edena)) throw new Error("evidence does not match the related mission role, EDENA tier or sample boundary");
    if (["artifact_review", "assessment", "human_review", "safety_drill", "agent_run", "knowledge_transfer"].includes(value.type) && !mission) throw new Error("evidence type requires a related mission");
    if (["mission", "outcome", "agent_run"].includes(value.type) && (!mission || !mission.stages.evaluate.complete)) throw new Error("evidence type requires an evaluated mission");
    if (value.provenance === "app_observed" && !(value.type === "mission" && mission && mission.stages.evaluate.complete)) throw new Error("app-observed provenance is unavailable for this evidence type");
    if (["human_review", "agent_run"].includes(value.type) && value.provenance !== "human_reviewed_unverified") throw new Error("evidence type requires human-reviewed provenance");
    if (!mission && value.edena !== "green") throw new Error("non-Green evidence requires a matching related mission");
    const detected = detectSensitiveText(value.summary);
    if (detected.length) throw new Error(`evidence contains possible sensitive content: ${detected.join(", ")}`);
    return { ...value, createdAt: safeIso(value.createdAt) };
  }

  function resetProfile() {
    if (!window.confirm("Erase all local DISCOVER roles, missions, evidence, favorites, Soul personalization and onboarding state in this browser?")) return;
    if (!removeStoredState()) {
      setStatus(el.profileStatus, "Local storage could not be erased. Nothing was reset; close private mode or check browser storage permissions, then retry.");
      return;
    }
    state = defaultState();
    ensureDashboardPartitions();
    const stored = saveState();
    renderAll();
    setStatus(el.profileStatus, stored ? "All local DISCOVER Mission Control data was erased and a fresh default state was created." : "All prior local data was erased, but the fresh default state could not be stored.", stored);
    openOnboarding(0);
  }

  function applySoulTheme() {
    const profileTheme = state.soulProfile && state.soulProfile.presentation_preferences && state.soulProfile.presentation_preferences.theme_token;
    document.documentElement.dataset.soul = ALLOWED_DIMENSION_IDS.has(profileTheme) ? profileTheme : (state.soul && ALLOWED_DIMENSION_IDS.has(state.soul.primary) ? state.soul.primary : "default");
  }

  function getSoulPresentation() {
    if (state.soulProfile) {
      const primary = state.soulProfile.role_constellation.find((roleItem) => roleItem.state === "primary") || state.soulProfile.role_constellation[0];
      const mission = (state.discoverPacket && state.discoverPacket.mission_statement) || state.soulProfile.mission_and_purpose.mission || "Pursue meaningful goals through disciplined learning and governed action.";
      const principle = state.soulProfile.core_values[0] || "human judgment";
      return {
        title: primary ? `${primary.label} · integrated Soul Profile` : "Integrated Soul Profile",
        tagline: `One shared foundation across ${state.soulProfile.role_constellation.length || 1} complementary role${state.soulProfile.role_constellation.length === 1 ? "" : "s"}.`,
        hero: mission,
        coaching: `Lead with ${principle}; preserve uncertainty, evidence, boundaries and accountable human review.`
      };
    }
    if (state.discoverPacket) {
      const priority = state.discoverPacket.current_priorities[0] || "one meaningful, bounded priority";
      return {
        title: "Discover Packet applied · Soul presentation neutral",
        tagline: `${state.discoverPacket.current_priorities.length} active priorit${state.discoverPacket.current_priorities.length === 1 ? "y" : "ies"} with reviewed AI boundaries.`,
        hero: state.discoverPacket.mission_statement || "Turn meaningful goals into governed missions that learn and improve.",
        coaching: `Begin with ${priority}. AI defaults to ${state.discoverPacket.ai_boundaries.default_autonomy.replaceAll("_", " ")}; human judgment and EDENA gates remain in control.`
      };
    }
    if (!state.soul) {
      return {
        title: "Unpersonalized DISCOVER view",
        tagline: "A balanced, role-aware starting canvas for responsible learning, practice, leadership and whole-life development.",
        hero: "Turn meaningful goals into governed missions that learn and improve.",
        coaching: "Begin with your situation, desired outcome, evidence, boundaries and a named human decision gate."
      };
    }
    if (state.soul.primary === "integrator") {
      return {
        title: "Balanced DISCOVER Integrator",
        tagline: "Your reflections are distributed across the six DISCOVER dimensions.",
        hero: "Connect the whole system without losing the human thread.",
        coaching: "Use your balance to link mission, evidence, rigor, people, translation and renewal."
      };
    }
    const dimension = DIMENSIONS.find((item) => item.id === state.soul.primary);
    const hero = {
      direction: "Find the truest question—and point the portfolio toward it.",
      evidence: "Protect the evidence trail that makes responsible progress possible.",
      rigor: "Give bold ideas a design strong enough to learn from.",
      connection: "Build innovation with people, not merely around them.",
      translation: "Move insight into bounded, useful and reversible action.",
      renewal: "Steward the future without spending the people who must build it."
    }[dimension.id];
    const coaching = {
      direction: "Lead with mission and unmet need; invite evidence and boundary challenge early.",
      evidence: "Lead with provenance and uncertainty; keep imagination visible rather than suppressed.",
      rigor: "Lead with testability and validity; keep burden, dignity and implementation in view.",
      connection: "Lead with reciprocity and voice; make decision rights and evidence thresholds explicit.",
      translation: "Lead with the smallest responsible experiment; protect stop, rollback and learning ownership.",
      renewal: "Lead with the long view; keep immediate decisions, accountable owners and evidence gates concrete."
    }[dimension.id];
    return { title: dimension.archetype, tagline: dimension.tagline, hero, coaching };
  }

  function getOrderedGroups() {
    if (state.discoverPacket && state.discoverPacket.recommended_workflow_ids.length) {
      const priority = new Map();
      state.discoverPacket.recommended_workflow_ids.forEach((workflowId, index) => {
        const workflow = getWorkflow(workflowId);
        if (workflow && !priority.has(workflow.groupId)) priority.set(workflow.groupId, index);
      });
      return GROUPS.slice().sort((a, b) => (priority.get(a.id) ?? 999) - (priority.get(b.id) ?? 999) || GROUPS.indexOf(a) - GROUPS.indexOf(b));
    }
    if (!state.soul || state.soul.primary === "integrator") return GROUPS.slice();
    return GROUPS.slice().sort((a, b) => {
      const aScore = state.soul.scores[a.id] || 0;
      const bScore = state.soul.scores[b.id] || 0;
      return bScore - aScore || GROUPS.indexOf(a) - GROUPS.indexOf(b);
    });
  }

  function loadState() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      const parsed = JSON.parse(raw);
      rejectDangerousKeys(parsed);
      return validateInternalState(parsed);
    } catch (_error) {
      return defaultState();
    }
  }

  function validateInternalState(value) {
    if (!isPlainObject(value)) return defaultState();
    const roleIds = Array.isArray(value.selectedRoleIds) ? unique(value.selectedRoleIds).filter((id) => ALLOWED_ROLE_IDS.has(id)) : [];
    if (!roleIds.length) roleIds.push("shared-identity");
    const activeRoleId = roleIds.includes(value.activeRoleId) ? value.activeRoleId : roleIds[0];
    const roleStates = {};
    let primaryAssigned = false;
    roleIds.forEach((roleId) => {
      const requested = isPlainObject(value.roleStates) && ROLE_STATES.includes(value.roleStates[roleId]) ? value.roleStates[roleId] : null;
      if (requested === "primary" && !primaryAssigned) {
        roleStates[roleId] = "primary";
        primaryAssigned = true;
      } else {
        roleStates[roleId] = requested && requested !== "primary" ? requested : "supporting";
      }
    });
    if (!primaryAssigned) roleStates[roleIds[0]] = "primary";
    const dashboards = {};
    roleIds.forEach((roleId) => {
      const item = isPlainObject(value.dashboards) && isPlainObject(value.dashboards[roleId]) ? value.dashboards[roleId] : {};
      dashboards[roleId] = {
        dashboardId: validUuid(item.dashboardId) ? item.dashboardId : makeUuid(),
        favoriteWorkflowIds: Array.isArray(item.favoriteWorkflowIds) ? unique(item.favoriteWorkflowIds).filter((id) => ALLOWED_WORKFLOW_IDS.has(id)).slice(0, WORKFLOWS.length) : []
      };
    });
    let soul = null;
    if (isPlainObject(value.soul) && isPlainObject(value.soul.scores)) {
      try {
        soul = validateLegacySoul({ scores: value.soul.scores, primary: value.soul.primary, secondary: value.soul.secondary, completed_at: value.soul.completedAt });
      } catch (_error) { soul = null; }
    }
    let soulProfile = null;
    let previousSoulProfile = null;
    let discoverPacket = null;
    try { soulProfile = value.soulProfile === null || value.soulProfile === undefined ? null : validateSoulProfile(value.soulProfile); } catch (_error) { soulProfile = null; }
    try { previousSoulProfile = value.previousSoulProfile === null || value.previousSoulProfile === undefined ? null : validateSoulProfile(value.previousSoulProfile); } catch (_error) { previousSoulProfile = null; }
    try { discoverPacket = value.discoverPacket === null || value.discoverPacket === undefined ? null : validateDiscoverPacket(value.discoverPacket); } catch (_error) { discoverPacket = null; }
    const missions = [];
    if (Array.isArray(value.missions)) {
      value.missions.slice(0, 100).forEach((mission) => {
        try { missions.push(validateMissionRecord(mission, roleIds, true)); } catch (_error) { /* discard invalid local record */ }
      });
    }
    const uniqueMissions = missions.filter((mission, index, list) => list.findIndex((item) => item.id === mission.id) === index);
    const missionIds = new Set(uniqueMissions.map((mission) => mission.id));
    const missionMap = new Map(uniqueMissions.map((mission) => [mission.id, mission]));
    const evidence = [];
    if (Array.isArray(value.evidence)) {
      value.evidence.slice(0, 500).forEach((record) => {
        try { evidence.push(validateEvidenceRecord(record, roleIds, missionIds, missionMap)); } catch (_error) { /* discard invalid local record */ }
      });
    }
    const uniqueEvidence = evidence.filter((record, index, list) => list.findIndex((item) => item.id === record.id) === index);
    return {
      version: APP_VERSION,
      instanceId: validUuid(value.instanceId) ? value.instanceId : makeUuid(),
      selectedRoleIds: roleIds,
      activeRoleId,
      activeMissionId: missionIds.has(value.activeMissionId) ? value.activeMissionId : (uniqueMissions[0] ? uniqueMissions[0].id : null),
      roleStates,
      dashboards,
      soul,
      soulProfile,
      previousSoulProfile,
      discoverPacket,
      missions: uniqueMissions,
      evidence: uniqueEvidence,
      guideSeen: Boolean(value.guideSeen),
      onboardingComplete: Boolean(value.onboardingComplete)
    };
  }

  function defaultState() {
    return {
      version: APP_VERSION,
      instanceId: makeUuid(),
      selectedRoleIds: ["shared-identity"],
      activeRoleId: "shared-identity",
      activeMissionId: null,
      roleStates: { "shared-identity": "primary" },
      dashboards: {},
      soul: null,
      soulProfile: null,
      previousSoulProfile: null,
      discoverPacket: null,
      missions: [],
      evidence: [],
      guideSeen: false,
      onboardingComplete: false
    };
  }

  function ensureDashboardPartitions() {
    if (!isPlainObject(state.dashboards)) state.dashboards = {};
    state.selectedRoleIds.forEach((roleId) => {
      if (!isPlainObject(state.dashboards[roleId])) state.dashboards[roleId] = { dashboardId: makeUuid(), favoriteWorkflowIds: [] };
      if (!validUuid(state.dashboards[roleId].dashboardId)) state.dashboards[roleId].dashboardId = makeUuid();
      if (!Array.isArray(state.dashboards[roleId].favoriteWorkflowIds)) state.dashboards[roleId].favoriteWorkflowIds = [];
    });
  }

  function saveState() {
    try {
      const persistentMissions = state.missions.filter((mission) => !mission.sample && mission.retentionMode === "local_non_sensitive");
      const persistentMissionIds = new Set(persistentMissions.map((mission) => mission.id));
      const persistent = {
        ...state,
        missions: persistentMissions,
        activeMissionId: persistentMissionIds.has(state.activeMissionId) ? state.activeMissionId : null,
        evidence: state.evidence.filter((record) => record.missionId === null || persistentMissionIds.has(record.missionId))
      };
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(persistent));
      return true;
    } catch (_error) {
      announce("Browser storage is unavailable. Personalization will last only for this open page.");
      return false;
    }
  }

  function removeStoredState() {
    try {
      window.localStorage.removeItem(STORAGE_KEY);
      return window.localStorage.getItem(STORAGE_KEY) === null;
    } catch (_error) {
      return false;
    }
  }

  function activeDashboard() {
    ensureDashboardPartitions();
    return state.dashboards[state.activeRoleId];
  }

  function currentFavorites() { return activeDashboard().favoriteWorkflowIds; }
  function getActiveRole() { return getRole(state.activeRoleId) || ROLES[0]; }
  function getRole(id) { return ROLES.find((item) => item.id === id); }
  function getWorkflow(id) { return WORKFLOWS.find((item) => item.id === id); }
  function getGroup(id) { return GROUPS.find((item) => item.id === id); }

  function setGroupVars(element, group) {
    element.style.setProperty("--group-color", group.color);
    element.style.setProperty("--group-soft", group.soft);
    element.style.setProperty("--card-color", group.color);
    element.style.setProperty("--card-soft", group.soft);
  }

  function detectSensitiveText(text) {
    if (!text) return [];
    const rules = [
      ["email address", /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i],
      ["phone number", /(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}/],
      ["SSN-like number", /\b\d{3}-\d{2}-\d{4}\b/],
      ["medical record identifier", /\b(?:MRN|medical record number|patient id|participant id)\b/i],
      ["date of birth", /\b(?:DOB|date of birth)\b/i],
      ["credential or secret", /\b(?:password|passcode|api[_ -]?key|access[_ -]?token|secret[_ -]?key)\b/i],
      ["direct patient/participant name field", /\b(?:patient name|participant name)\s*[:=]/i]
    ];
    return rules.filter(([, pattern]) => pattern.test(text)).map(([label]) => label);
  }

  function rejectDangerousKeys(value, depth = 0) {
    if (depth > 12) throw new Error("profile nesting is too deep");
    if (!value || typeof value !== "object") return;
    for (const key of Object.keys(value)) {
      if (["__proto__", "prototype", "constructor"].includes(key)) throw new Error("unsafe object key");
      rejectDangerousKeys(value[key], depth + 1);
    }
  }

  function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
  }

  function assertExactKeys(value, expected, label) {
    const actual = Object.keys(value).sort();
    const wanted = expected.slice().sort();
    if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) throw new Error(`${label} has unexpected or missing fields`);
  }

  function safeIso(value) {
    if (typeof value !== "string" || !Number.isFinite(Date.parse(value))) return new Date().toISOString();
    return new Date(value).toISOString();
  }

  function isIsoString(value) {
    return typeof value === "string" && Number.isFinite(Date.parse(value));
  }

  function isLoopbackHostname(value) {
    const hostname = String(value || "").toLowerCase();
    return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1" || hostname === "[::1]";
  }

  function validUuid(value) {
    return typeof value === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
  }

  function makeUuid() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") return window.crypto.randomUUID();
    const bytes = new Uint8Array(16);
    if (window.crypto && typeof window.crypto.getRandomValues === "function") window.crypto.getRandomValues(bytes);
    else for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }

  function unique(items) { return Array.from(new Set(items)); }

  function node(tag, className = "", text = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== "") element.textContent = text;
    return element;
  }

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") return window.CSS.escape(value);
    return String(value).replace(/[^a-zA-Z0-9_-]/g, "");
  }

  function setStatus(element, message, success = false) {
    element.textContent = message;
    element.classList.toggle("is-success", Boolean(success));
  }

  function announce(message) {
    window.clearTimeout(toastTimer);
    el.toast.textContent = message;
    el.toast.classList.add("is-visible");
    toastTimer = window.setTimeout(() => el.toast.classList.remove("is-visible"), 4200);
  }

  function downloadText(filename, text, mime) {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename.replace(/[^a-zA-Z0-9._-]/g, "-");
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
})();
