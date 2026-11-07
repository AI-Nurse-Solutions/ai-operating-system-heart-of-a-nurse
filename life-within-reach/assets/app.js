/* ============================================================
   Life Within Reach — Household Command Center (browser app)
   Five-step loop: Assess → Understand → Plan → Act → Check in
   All data stays in localStorage on this device.
   ============================================================ */
(function () {
  "use strict";
  var R = window.LWR;
  var KEY = "lwr.household.v1";
  var view = document.getElementById("view");
  var tablist = document.getElementById("tablist");
  var dlg = document.getElementById("taskDialog");

  /* ---------- State ---------- */
  var state = load() || fresh();
  var plan = null;
  var currentTab = "home";
  var intakeStep = 0;

  function fresh() { return { profile: null, draft: {}, done: {}, checkins: [], created: new Date().toISOString(), updated: null }; }
  function load() { try { var s = JSON.parse(localStorage.getItem(KEY)); return s && typeof s === "object" ? s : null; } catch (e) { return null; } }
  function save() { state.updated = new Date().toISOString(); try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode: keep in memory */ } }

  /* ---------- Utils ---------- */
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function usd(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
  function fmtDate(d) { return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" }); }
  function toast(msg) { var t = document.getElementById("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(toast._t); toast._t = setTimeout(function () { t.classList.remove("show"); }, 2400); }
  function num(v) { var n = parseFloat(v); return isFinite(n) && n > 0 ? n : 0; }
  function has(a, v) { return Array.isArray(a) && a.indexOf(v) !== -1; }
  function setHeaderVar() { var h = document.getElementById("siteHeader"); if (h) document.documentElement.style.setProperty("--header-h", h.offsetHeight + "px"); }
  window.addEventListener("resize", setHeaderVar); setHeaderVar();
  document.getElementById("rulesetVersion").textContent = R.RULESET.version;

  /* ============================================================
     ASSESS — conversational intake, one question at a time
     ============================================================ */
  function choice(name, value, label, checked, sub, type) {
    return '<label class="choice"><input type="' + (type || "checkbox") + '" name="' + name + '" value="' + esc(value) + '"' + (checked ? " checked" : "") + '><span>' + label + (sub ? '<span class="sub">' + sub + "</span>" : "") + "</span></label>";
  }
  function moneyField(name, label, val, hint) {
    return '<div class="field"><label for="f-' + name + '">' + label + '</label><div class="money"><input id="f-' + name + '" name="' + name + '" type="number" inputmode="decimal" min="0" step="1" value="' + (val ? esc(val) : "") + '" placeholder="0"></div>' + (hint ? '<span class="hint">' + hint + "</span>" : "") + "</div>";
  }
  function numField(name, label, val, min, hint) {
    return '<div class="field"><label for="f-' + name + '">' + label + '</label><input id="f-' + name + '" name="' + name + '" type="number" inputmode="numeric" min="' + (min || 0) + '" step="1" value="' + (val !== undefined && val !== null && val !== "" ? esc(val) : "") + '">' + (hint ? '<span class="hint">' + hint + "</span>" : "") + "</div>";
  }
  function yes(name, label, checked, sub) { return choice(name, "1", label, checked, sub); }

  var REASONS = [
    ["bill", "A bill I can't pay", "medical, utility, or other"],
    ["coverage", "Health coverage or a renewal deadline", ""],
    ["housing", "Rent, a rent increase, or an eviction notice", ""],
    ["shutoff", "A shutoff notice or a high energy bill", ""],
    ["childcare", "Child care costs or a waitlist", ""],
    ["caregiving", "Caring for a parent or family member", ""],
    ["food", "Food runs out before the month does", ""],
    ["general", "I just want to lower costs", ""]
  ];
  var BENEFITS = [
    ["snap", "SNAP / food stamps", "CalFresh in CA"], ["wic", "WIC", ""], ["medicaid", "Medicaid or CHIP", "Medi-Cal in CA"],
    ["marketplace", "Marketplace (ACA) plan", ""], ["employer", "Insurance through a job", ""], ["medicare", "Medicare", ""],
    ["ssi", "SSI or SSDI", ""], ["utilDiscount", "Utility low-income discount", "e.g. CARE"], ["liheap", "LIHEAP this year", ""],
    ["lifeline", "Lifeline phone/internet", ""], ["childcareSubsidy", "Child care subsidy", ""], ["voucher", "Housing voucher / public housing", ""]
  ];

  var STEPS = [
    {
      id: "reasons", q: "What brought you here today?",
      why: "So I can start with what's most urgent for you. Pick as many as fit.",
      html: function (p) { return '<div class="choices">' + REASONS.map(function (r) { return choice("reasons", r[0], r[1], has(p.reasons, r[0]), r[2]); }).join("") + "</div>"; },
      read: function (f, p) { p.reasons = f.getAll("reasons"); }
    },
    {
      id: "place", q: "Where do you live?",
      why: "Benefit rules change by state — Medicaid limits, rent caps, paid leave, utility programs. Your ZIP code only helps point you to local resources; it is never shared.",
      html: function (p) {
        return '<div class="row"><div class="field"><label for="f-state">State</label><select id="f-state" name="state" required><option value="">Choose your state…</option>' +
          R.STATES.map(function (s) { return '<option value="' + s[0] + '"' + (p.state === s[0] ? " selected" : "") + ">" + s[1] + "</option>"; }).join("") +
          '</select></div><div class="field"><label for="f-zip">ZIP code <span class="muted">(optional)</span></label><input id="f-zip" name="zip" type="text" inputmode="numeric" pattern="[0-9]{5}" maxlength="5" autocomplete="postal-code" value="' + esc(p.zip || "") + '"></div></div>';
      },
      read: function (f, p) { p.state = f.get("state") || ""; p.zip = (f.get("zip") || "").replace(/\D/g, "").slice(0, 5); },
      valid: function (p) { return p.state ? "" : "Please choose your state so I use the right rules."; }
    },
    {
      id: "household", q: "Who lives in your household?",
      why: "Most programs use household size to set income limits. Children's ages matter for WIC, school meals, and child care help.",
      html: function (p) {
        return '<div class="row">' + numField("hhSize", "People in your household (including you)", p.hhSize || 1, 1) +
          numField("kidsUnder5", "Children under 5", p.kidsUnder5 || 0) + numField("kids5to17", "Children 5–17", p.kids5to17 || 0) + numField("seniors", "Adults 60 or older", p.seniors || 0) + "</div>" +
          '<div class="choices">' + yes("pregnant", "Someone is pregnant", p.pregnant) + yes("disability", "Someone has a disability", p.disability) + "</div>";
      },
      read: function (f, p) {
        p.hhSize = Math.max(1, parseInt(f.get("hhSize"), 10) || 1); p.kidsUnder5 = parseInt(f.get("kidsUnder5"), 10) || 0; p.kids5to17 = parseInt(f.get("kids5to17"), 10) || 0;
        p.seniors = parseInt(f.get("seniors"), 10) || 0; p.pregnant = !!f.get("pregnant"); p.disability = !!f.get("disability");
        var counted = 1 + p.kidsUnder5 + p.kids5to17; if (p.hhSize < counted) p.hhSize = counted;
      }
    },
    {
      id: "income", q: "About how much does your household earn in a month, before taxes?",
      why: "Nearly every program compares income to the federal poverty guideline. A close estimate is fine — I'll show the math, and the program checks the real numbers.",
      html: function (p) { return moneyField("income", "Monthly household income before taxes", p.income, "Include wages, self-employment, unemployment, Social Security, and child support received.") + '<div class="choices">' + yes("incomeDropped", "Our income dropped recently", p.incomeDropped) + "</div>"; },
      read: function (f, p) { p.income = num(f.get("income")); p.incomeDropped = !!f.get("incomeDropped"); }
    },
    {
      id: "benefits", q: "Which of these do you already have?",
      why: "So I don't send you after things you already have — and because some (like SNAP or Medicaid) automatically qualify you for others.",
      html: function (p) { return '<div class="choices">' + BENEFITS.map(function (b) { return choice("benefits", b[0], b[1], has(p.benefits, b[0]), b[2]); }).join("") + "</div>"; },
      read: function (f, p) { p.benefits = f.getAll("benefits"); }
    },
    {
      id: "housing", q: "Tell me about your housing.",
      why: "Housing is the cost that drives everything else. If there's a notice, the clock matters more than anything — I'll put it first.",
      html: function (p) {
        return '<div class="field"><span class="label">Do you…</span><div class="choices">' +
          choice("tenure", "rent", "Rent", p.tenure === "rent", "", "radio") + choice("tenure", "own", "Own (mortgage or paid off)", p.tenure === "own", "", "radio") + choice("tenure", "other", "Stay with others / other", p.tenure === "other", "", "radio") + "</div></div>" +
          moneyField("housingCost", "Monthly rent or mortgage", p.housingCost) +
          '<div class="choices">' + yes("behindRent", "We're behind on rent or mortgage", p.behindRent) + yes("evictionNotice", "I received an eviction notice or court papers", p.evictionNotice, "I'll move this to the top") + yes("repairs", "Repairs aren't being made", p.repairs) + "</div>" +
          '<div class="row" style="margin-top:1rem">' + numField("rentIncreasePct", "Rent increase in the last notice (%)", p.rentIncreasePct || "", 0, "Leave blank if none") + "</div>";
      },
      read: function (f, p) {
        p.tenure = f.get("tenure") || "rent"; p.housingCost = num(f.get("housingCost")); p.behindRent = !!f.get("behindRent"); p.evictionNotice = !!f.get("evictionNotice"); p.repairs = !!f.get("repairs");
        p.rentIncreasePct = num(f.get("rentIncreasePct"));
      }
    },
    {
      id: "energy", q: "What about energy and utility bills?",
      why: "A shutoff is a health event — especially with medical equipment, insulin that needs a fridge, or extreme heat or cold. Some protections only work if you ask before the shutoff date.",
      html: function (p) {
        return moneyField("energyBill", "Typical monthly energy bill (electric + gas)", p.energyBill) +
          '<div class="choices">' + yes("shutoff", "I have a shutoff / disconnection notice", p.shutoff) + yes("medEquip", "Someone uses medical equipment that needs power", p.medEquip, "CPAP, oxygen, refrigerated medicine, power wheelchair…") + "</div>" +
          '<div class="row" style="margin-top:1rem">' + numField("shutoffDays", "Days until the shutoff date", p.shutoffDays || "", 0, "If you have a notice") + "</div>";
      },
      read: function (f, p) { p.energyBill = num(f.get("energyBill")); p.shutoff = !!f.get("shutoff"); p.medEquip = !!f.get("medEquip"); p.shutoffDays = num(f.get("shutoffDays")); }
    },
    {
      id: "health", q: "How is health coverage and health spending going?",
      why: "Losing coverage and paying list price are the two things that most often bankrupt families. I'm asking about costs and paperwork — not symptoms or diagnoses.",
      html: function (p) {
        var b = p.benefits || [];
        return '<div class="choices">' +
          yes("uninsured", "Someone in the household has no health insurance", p.uninsured, "Even if others in the household are covered") +
          (has(b, "medicaid") ? yes("renewalDue", "A Medicaid/CHIP renewal is due", p.renewalDue) : "") +
          yes("rxTrouble", "Cost makes it hard to take a prescription as prescribed", p.rxTrouble) +
          yes("paDenied", "Insurance denied a prior authorization", p.paDenied) + "</div>" +
          '<div class="row" style="margin-top:1rem">' +
          (has(b, "medicaid") ? numField("renewalDays", "Days until the renewal is due", p.renewalDays || "", 0) : "") +
          moneyField("medBill", "Unpaid medical bills (total)", p.medBill) + moneyField("rxMonthly", "Prescriptions per month (out of pocket)", p.rxMonthly) + "</div>";
      },
      read: function (f, p) {
        p.uninsured = !!f.get("uninsured"); p.renewalDue = !!f.get("renewalDue"); p.rxTrouble = !!f.get("rxTrouble"); p.paDenied = !!f.get("paDenied");
        p.renewalDays = num(f.get("renewalDays")); p.medBill = num(f.get("medBill")); p.rxMonthly = num(f.get("rxMonthly"));
      }
    },
    {
      id: "family", q: "Who are you caring for?",
      why: "Child care and caregiving are where household math breaks hardest — and where help is most scattered. I'm also checking whether your job can be protected while you give care.",
      html: function (p) {
        var kids = (p.kidsUnder5 || 0) + (p.kids5to17 || 0);
        return (kids ? moneyField("childcareCost", "Monthly child care cost", p.childcareCost) +
          '<div class="field"><span class="label">Does your employer offer a dependent care FSA (DCAP)?</span><div class="choices">' +
          choice("employerDCAP", "yes", "Yes", p.employerDCAP === "yes", "", "radio") + choice("employerDCAP", "no", "No / not working", p.employerDCAP === "no", "", "radio") + choice("employerDCAP", "unsure", "Not sure", !p.employerDCAP || p.employerDCAP === "unsure", "", "radio") + "</div></div>" : "") +
          '<div class="choices">' + yes("caringAdult", "I help care for a parent, partner, or adult family member", p.caringAdult) + yes("needLeave", "I need time off work for family or medical reasons", p.needLeave) + "</div>";
      },
      read: function (f, p) { p.childcareCost = num(f.get("childcareCost")); p.employerDCAP = f.get("employerDCAP") || "unsure"; p.caringAdult = !!f.get("caringAdult"); p.needLeave = !!f.get("needLeave"); }
    },
    {
      id: "food", q: "Last one: food and internet.",
      why: "Food is often the first thing that breaks each month, and internet is a bill most people overpay. Both usually have quick fixes.",
      html: function (p) { return '<div class="choices">' + yes("foodRunsOut", "Food often runs out before the end of the month", p.foodRunsOut) + "</div>" + '<div class="row" style="margin-top:1rem">' + moneyField("internetBill", "Monthly internet bill", p.internetBill) + "</div>"; },
      read: function (f, p) { p.foodRunsOut = !!f.get("foodRunsOut"); p.internetBill = num(f.get("internetBill")); }
    }
  ];

  function renderIntake() {
    var p = state.draft || {};
    var step = STEPS[intakeStep];
    var pct = Math.round((intakeStep) / STEPS.length * 100);
    view.innerHTML =
      '<div class="intake">' +
      '<div class="persona"><div class="persona-avatar" aria-hidden="true">🤝</div><div class="bubble"><div class="who">Your community organizer · AI</div>' +
      (intakeStep === 0 ? "<p>Hi — I'm an AI community organizer, not a nurse, doctor, or lawyer. I'll look at your actual situation with you and build a plan you can start today. Plain questions, one at a time, about 5–8 minutes. Skip anything you'd rather not answer.</p>" :
        "<p>" + ["Thank you.", "Got it.", "That helps.", "Okay.", "Good to know.", "Thanks — almost there."][intakeStep % 6] + "</p>") +
      "</div></div>" +
      '<div class="progress" role="progressbar" aria-label="Intake progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct + '"><span style="width:' + Math.max(4, pct) + '%"></span></div>' +
      '<form class="q-card" id="qForm" novalidate>' +
      '<p class="eyebrow dark">Question ' + (intakeStep + 1) + " of " + STEPS.length + "</p>" +
      '<h2 id="qTitle" tabindex="-1">' + step.q + "</h2>" +
      '<details class="why"><summary>Why I\'m asking</summary><p>' + step.why + "</p></details>" +
      step.html(p) +
      '<p class="urgent" id="qError" role="alert" hidden></p>' +
      '<div class="q-actions">' + (intakeStep > 0 ? '<button type="button" class="btn btn-ghost btn-small" id="qBack">← Back</button>' : '<button type="button" class="btn-link" id="qSample">Explore with a sample household instead</button>') +
      '<div class="right">' + (step.valid ? "" : '<button type="button" class="btn btn-ghost btn-small" id="qSkip">Skip</button>') +
      '<button type="submit" class="btn btn-teal">' + (intakeStep === STEPS.length - 1 ? "Build my plan →" : "Next →") + "</button></div></div>" +
      '<p class="never-ask">I will never ask your immigration status, Social Security number, or anything about symptoms or diagnoses. Answers stay on this device.</p>' +
      "</form></div>";

    var form = $("#qForm");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var fd = new FormData(form); step.read(fd, p); state.draft = p;
      var err = step.valid && step.valid(p);
      if (err) { var el = $("#qError"); el.textContent = err; el.hidden = false; return; }
      save(); next();
    });
    var back = $("#qBack"); if (back) back.onclick = function () { var fd = new FormData(form); step.read(fd, p); state.draft = p; save(); intakeStep--; renderIntake(); focusQ(); };
    var skip = $("#qSkip"); if (skip) skip.onclick = function () { next(); };
    var sample = $("#qSample"); if (sample) sample.onclick = loadSample;
  }
  function focusQ() { var h = $("#qTitle"); if (h) h.focus({ preventScroll: false }); }
  function next() {
    if (intakeStep < STEPS.length - 1) { intakeStep++; renderIntake(); focusQ(); window.scrollTo(0, 0); return; }
    state.profile = JSON.parse(JSON.stringify(state.draft)); state.profile.intakeDate = new Date().toISOString(); save(); intakeStep = 0; refresh(); setTab("home"); window.scrollTo(0, 0);
  }

  function loadSample() {
    state.draft = {
      reasons: ["bill", "coverage", "shutoff", "childcare", "caregiving"], state: "CA", zip: "94109", hhSize: 3, kidsUnder5: 1, kids5to17: 0, seniors: 0, pregnant: false, disability: false,
      income: 3400, benefits: ["medicaid"], tenure: "rent", housingCost: 2100, behindRent: false, evictionNotice: false, repairs: true, rentIncreasePct: 14,
      energyBill: 210, shutoff: true, medEquip: true, shutoffDays: 5, uninsured: false, renewalDue: true, renewalDays: 12, rxTrouble: true, paDenied: true, medBill: 2400, rxMonthly: 42,
      childcareCost: 1900, employerDCAP: "unsure", caringAdult: true, needLeave: true, foodRunsOut: true, internetBill: 75, sample: true
    };
    state.profile = JSON.parse(JSON.stringify(state.draft)); state.profile.intakeDate = new Date().toISOString(); state.done = {}; save(); refresh(); setTab("home");
    toast("Loaded a sample household — replace it with your own any time.");
  }

  /* ============================================================
     UNDERSTAND + PLAN
     ============================================================ */
  function refresh() {
    if (state.profile && !state.profile.intakeDate) { state.profile.intakeDate = state.updated || new Date().toISOString(); save(); }
    plan = state.profile ? R.buildPlan(state.profile, new Date()) : null; renderTabs();
  }

  var STATUS = { "at-risk": ["rose", "At risk"], eligible: ["gold", "Eligible, not enrolled"], stretched: ["", "Stable but stretched"], stable: ["green", "Stable"] };

  function summarySentence(p) {
    var parts = [];
    parts.push("You're a household of " + p.hhSize + " in " + stateName(p.state) + (p.income ? ", bringing in about " + usd(p.income) + " a month — roughly " + plan.pct + "% of the federal poverty guideline" : "") + ".");
    var urgent = plan.tasks.filter(function (t) { return t.urgent; });
    if (urgent.length) parts.push("<strong>" + urgent.length + " thing" + (urgent.length > 1 ? "s have" : " has") + " a deadline</strong> — I've put " + (urgent.length > 1 ? "them" : "it") + " at the top.");
    var eligible = plan.tasks.filter(function (t) { return t.confidence === "likely" && (t.monthly || t.oneTime); });
    if (eligible.length) parts.push("You likely qualify for " + eligible.length + " kind" + (eligible.length > 1 ? "s" : "") + " of help you aren't getting yet.");
    if (plan.burden >= 30 && p.tenure === "rent") parts.push("Rent takes " + plan.burden + "% of income" + (plan.burden >= 50 ? " — that's severe cost burden." : "."));
    if (plan.flags.indexOf("coverage-gap") !== -1) parts.push("Your state hasn't expanded Medicaid, which can leave a coverage gap — I've added low-cost care options.");
    if (!plan.tasks.length) parts.push("Based on what you told me, nothing urgent stands out. Check in weekly — things change.");
    return parts.join(" ");
  }
  function stateName(code) { var s = R.STATES.filter(function (x) { return x[0] === code; })[0]; return s ? s[1] : "your state"; }

  function valueHtml(t) {
    if (t.monthly) return usd(t.monthly) + "/mo<small>est. " + (t.confidence === "likely" ? "likely" : "possible") + "</small>";
    if (t.oneTime) return usd(t.oneTime) + "<small>one-time est.</small>";
    return esc(t.valueLabel || "") + "<small>&nbsp;</small>";
  }
  function dueHtml(t) {
    var d = t.daysLeft;
    var txt = d < 0 ? "Overdue since " + fmtDate(t.dueDate) + " — call today and ask what you can still do" :
      "Due " + fmtDate(t.dueDate) + " · " + (d === 0 ? "today" : d === 1 ? "tomorrow" : "in " + d + " days");
    var hot = t.urgent || d < 0;
    return '<span class="' + (hot ? "urgent" : "") + '">' + (hot ? "⚑ " : "") + txt + "</span>";
  }
  function taskHtml(t) {
    var P = R.PILLARS[t.pillar];
    var done = !!state.done[t.id];
    return '<li class="task' + (done ? " done" : "") + '" style="--accent:' + P.accent + '">' +
      '<input class="check" type="checkbox" data-done="' + t.id + '" aria-label="Mark done: ' + esc(t.title) + '"' + (done ? " checked" : "") + ">" +
      '<div><div class="task-title">' + esc(t.title) + "</div>" +
      '<div class="task-meta"><span class="chip" style="background:color-mix(in srgb,' + P.accent + ' 14%, white);color:var(--navy-900)">' + P.app + "</span>" + dueHtml(t) + '<span class="muted">· ~' + t.effortMin + " min</span>" +
      (t.confidence === "likely" ? '<span class="chip green">Likely eligible</span>' : '<span class="chip">Worth checking</span>') + (t.organizer ? '<span class="chip navy">Organizer step</span>' : "") + "</div>" +
      '<p class="task-why">' + esc(t.why) + "</p></div>" +
      '<div class="task-value">' + valueHtml(t) + "</div>" +
      '<div class="task-actions"><button type="button" class="btn btn-teal btn-small" data-open="' + t.id + '">Do it with me</button>' +
      '<button type="button" class="btn btn-ghost btn-small" data-learn="' + t.id + '">60-second lesson</button>' +
      '<a class="btn btn-ghost btn-small" href="https://www.211.org" target="_blank" rel="noopener">Talk to a person ↗</a></div>' +
      "</li>";
  }

  function horizonBlocks(tasks) {
    var out = "";
    [[30, "Next 30 days", "Deadlines and the fastest dollars"], [60, "Days 31–60", "Follow-through"], [90, "Days 61–90", "Longer-term moves and organizing"]].forEach(function (h) {
      var ts = tasks.filter(function (t) { return t.horizon === h[0]; });
      if (!ts.length) return;
      out += '<section class="horizon"><h3>' + h[1] + ' <span class="muted">' + h[2] + '</span></h3><ol class="task-list">' + ts.map(taskHtml).join("") + "</ol></section>";
    });
    return out || '<div class="empty">No steps here right now.</div>';
  }

  /* ---------- Sidebar (Evaluate) ---------- */
  function sidebarHtml() {
    var savedM = 0, savedO = 0;
    plan.tasks.forEach(function (t) { if (state.done[t.id]) { savedM += t.monthly; savedO += t.oneTime; } });
    var potential = plan.potential.monthly + plan.potential.oneTime / 12;
    var savedEq = savedM + savedO / 12;
    var pctBar = potential ? Math.min(100, Math.round(savedEq / potential * 100)) : 0;
    var last = state.checkins[state.checkins.length - 1];
    var daysSince = last ? Math.floor((Date.now() - new Date(last.date)) / 86400000) : null;
    var due = daysSince === null || daysSince >= 7;
    return '<aside class="sidebar" aria-label="Progress and settings">' +
      '<div class="card tally"><p class="eyebrow dark">Saved so far</p><div class="big">' + usd(savedM) + '<span class="small muted">/mo</span></div>' +
      (savedO ? '<div class="pot">+ ' + usd(savedO) + " one-time</div>" : "") +
      '<div class="meter" aria-hidden="true"><span style="width:' + pctBar + '%"></span></div>' +
      '<div class="pot">Plan potential: ' + usd(plan.potential.monthly) + "/mo" + (plan.potential.oneTime ? " + " + usd(plan.potential.oneTime) + " one-time" : "") + "</div>" +
      '<p class="small muted" style="margin:.5rem 0 0">Estimates. Check a step off when it\'s done.</p></div>' +
      '<div class="card side-card"><h3>Weekly check-in</h3>' +
      (due ? '<p class="small">Two questions, one minute. ' + (last ? "Last check-in " + daysSince + " days ago." : "Your first one is due in a week — or do it now.") + '</p><button class="btn btn-gold btn-small" type="button" id="checkinBtn">Check in</button>' :
        '<p class="small">Last check-in ' + (daysSince === 0 ? "today" : daysSince + " day" + (daysSince > 1 ? "s" : "") + " ago") + '. Next one in ' + (7 - daysSince) + ' days.</p><button class="btn-link small" type="button" id="checkinBtn">Check in early</button>') +
      "</div>" +
      '<div class="card side-card"><h3>Need a person?</h3><ul><li><a href="https://www.211.org" target="_blank" rel="noopener">Call 211</a> — local help, 24/7</li><li><a href="https://www.lawhelp.org" target="_blank" rel="noopener">Free legal aid</a></li><li>Trained community volunteers — <span class="muted">joining in the pilot</span></li></ul></div>' +
      '<div class="card side-card"><h3>Your data</h3><p class="small muted">Stored only in this browser. Export it, change it, or erase it.</p><div class="data-actions">' +
      '<button class="btn btn-ghost btn-small" type="button" id="editBtn">Edit answers</button><button class="btn btn-ghost btn-small" type="button" id="printBtn">Print plan</button>' +
      '<button class="btn btn-ghost btn-small" type="button" id="exportBtn">Export</button><button class="btn btn-ghost btn-small" type="button" id="storyBtn">Share my story</button>' +
      '<button class="btn btn-ghost btn-small" type="button" id="wipeBtn" style="border-color:var(--rose-600);color:var(--rose-700)">Erase everything</button></div></div>' +
      "</aside>";
  }

  /* ---------- Views ---------- */
  function renderHome() {
    if (!state.profile) { renderIntake(); return; }
    var p = state.profile;
    view.innerHTML = '<div class="layout"><div>' +
      (p.sample ? '<div class="boundary" style="margin-bottom:1rem"><p><strong>You\'re viewing a sample household.</strong> <button class="btn-link" type="button" id="startOwn">Start my own plan</button></p></div>' : "") +
      '<div class="persona"><div class="persona-avatar" aria-hidden="true">🤝</div><div class="bubble"><div class="who">Here\'s what\'s going on</div><p>' + summarySentence(p) + "</p>" +
      '<p class="small muted">Ranked by deadline first, then by dollars saved per hour of your effort.</p></div></div>' +
      '<div class="dx-grid" aria-label="Summary by area">' + Object.keys(R.PILLARS).map(function (k) {
        var P = R.PILLARS[k], d = plan.dx[k], s = STATUS[d.status];
        return '<button type="button" class="dx" style="--accent:' + P.accent + ';text-align:left;font:inherit;cursor:pointer" data-tab="' + k + '"><div class="name">' + P.app + '</div><div class="status"><span class="chip ' + s[0] + '">' + s[1] + "</span></div><p>" + esc(d.words) + "</p></button>";
      }).join("") + "</div>" +
      '<h2 style="margin-top:1.8rem">Your 30 / 60 / 90-day plan</h2>' + horizonBlocks(plan.tasks) +
      "</div>" + sidebarHtml() + "</div>";
    var so = $("#startOwn"); if (so) so.onclick = startOver;
  }

  var PILLAR_INFO = {
    food: { who: "Households whose food or internet bill is the first thing to break each month; SNAP/WIC-eligible families not enrolled; anyone whose SNAP was cut.", job: "Treat food security as a priority: understand the shortfall, plan a food budget that survives the month, connect to the local food system.",
      tools: [["Benefits screener", "SNAP, WIC, school meals, Lifeline — with an estimated monthly amount", true], ["Food-dollar planner", "Two-week menu with a basic nutrition check", true], ["Internet-bill clinic", "Lifeline, ISP low-income plans, downgrade script", true], ["Local food map", "Pantries, EBT match, community fridges with verified hours", false], ["Price-shift alerts", "Staples that moved most this month in your ZIP", false], ["Essentials exchange", "Diaper banks, buy-nothing groups, tool libraries", false]],
      links: ["foodbank", "snapState", "wic", "lifeline", "l211"] },
    health: { who: "Anyone facing a coverage lapse, a medical bill they can't pay, a prescription they're rationing, or a denied prior authorization.", job: "Stop the two things that bankrupt families — losing coverage and paying list price — and teach you to read your own bills.",
      tools: [["Coverage triage", "Medicaid renewal, Marketplace subsidy estimate, enrollment windows", true], ["Prescription cost cutter", "Cash price, generic, 90-day, assistance programs", true], ["Bill reader + charity care", "Financial-assistance request letter", true], ["Prior-auth appeal builder", "Appeal letter built around your plan's own criteria", true], ["Care-access map", "Community health centers and sliding-scale clinics", true], ["Upload a bill to decode it", "Line-by-line explanation and No Surprises Act check", false]],
      guard: "Navigation, not medical advice. No diagnosis, no dosing. If anyone has chest pain, trouble breathing, stroke signs, or thoughts of self-harm: call 911 or 988 now.",
      links: ["healthcare", "medicaid", "hrsa", "needymeds", "cfpbMed"] },
    housing: { who: "Renters facing an increase or eviction notice, households paying over 40% of income on housing, and would-be owners who need a guide.", job: "Stabilize first (keep you housed), then reduce cost, then build toward ownership. Tenant power is collective.",
      tools: [["Eviction prep for legal aid", "Legal-clock basics and what to gather today", true], ["Rent-increase checker", "Statewide caps in CA, OR, WA + pushback letter", true], ["Emergency rental assistance finder", "County, city, and charity programs", true], ["Affordable-unit watch", "BMR and LIHTC lotteries", true], ["Tenant organizing kit", "Survey, first-meeting agenda", true], ["ADU & first-home pathfinder", "Down-payment help, ADU feasibility", false]],
      guard: "Navigation, not legal advice. For any notice or court paper, contact legal aid right away.",
      links: ["lawhelp", "hudRent", "l211"] },
    energy: { who: "Households with a bill they can't cover, a shutoff notice, or a bill that jumped without explanation — including renters.", job: "A shutoff is a health event. Prevent it, then lower the bill, then organize ratepayers.",
      tools: [["Shutoff shield", "Medical certificate + payment-plan script", true], ["Assistance stack", "Discount rate → LIHEAP → weatherization, in the right order", true], ["Bill decoder", "Five things to check on your bill", true], ["DIY energy check", "Cheapest fixes first", true], ["Ratepayer organizer", "Public-comment template for rate cases", true], ["Rebate & credit finder", "Heat pumps, insulation, community solar", false]],
      links: ["liheap", "wap", "l211"] },
    family: { who: "Working parents priced out of child care, the sandwich generation, anyone who needs leave, and seniors facing care costs.", job: "Caregiving is skilled work, done unpaid at home. Find and fund care, protect your job and health, and connect you with other caregivers.",
      tools: [["Child care subsidy stacker", "State subsidy, Head Start, DCAP", true], ["Leave navigator", "FMLA + state paid leave + request letter", true], ["Paid family caregiver finder", "IHSS and consumer-directed programs", true], ["Caregiver check-in", "Respite and support", true], ["Elder care cost map", "In-home vs. adult day vs. assisted living, with Medicaid waivers", false], ["Care co-op builder", "Shared nannies and babysitting swaps", false]],
      links: ["childcare", "headstart", "eldercare", "respite", "fmla"] }
  };

  function renderPillar(k) {
    var P = R.PILLARS[k], I = PILLAR_INFO[k];
    var ts = plan ? plan.tasks.filter(function (t) { return t.pillar === k; }) : [];
    var d = plan && plan.dx[k];
    view.innerHTML = '<div class="layout"><div>' +
      '<div class="pillar-hero" style="--accent:' + P.accent + '"><p class="eyebrow dark">Pillar ' + P.roman + " · " + P.name + "</p><h2>" + P.app + "</h2>" +
      (d ? '<p><span class="chip ' + STATUS[d.status][0] + '">' + STATUS[d.status][1] + "</span> " + esc(d.words) + "</p>" : "") +
      '<p class="small"><strong>Who it\'s for:</strong> ' + I.who + "</p><p class=\"small\"><strong>Your community organizer's job here:</strong> " + I.job + "</p>" +
      (I.guard ? '<div class="escalate"><strong>Guardrail:</strong> ' + I.guard + "</div>" : "") + "</div>" +
      (state.profile ? "<h3>Your steps</h3>" + (ts.length ? '<ol class="task-list">' + ts.map(taskHtml).join("") + "</ol>" : '<div class="empty">Nothing urgent here based on your answers. <button class="btn-link" type="button" id="editBtn2">Update answers</button></div>') :
        '<div class="empty"><p>Answer a few questions to see your steps.</p><button class="btn btn-teal" type="button" data-tab="home">Start my plan</button></div>') +
      '<h3 style="margin-top:1.6rem">Tools in ' + P.app + "</h3><ul class=\"tool-list\">" + I.tools.map(function (t) {
        return '<li><span class="t">' + t[0] + "</span>" + (t[2] ? '<span class="chip green">In this preview</span>' : '<span class="chip">Planned</span>') + '<span class="d">' + t[1] + "</span></li>";
      }).join("") + "</ul>" +
      '<h3 style="margin-top:1.6rem">Trusted sources</h3><div class="links">' + I.links.map(function (l) { var x = R.LINKS[l]; return '<a href="' + x.url + '" target="_blank" rel="noopener">' + x.label + "</a>"; }).join("") + "</div>" +
      "</div>" + (plan ? sidebarHtml() : "") + "</div>";
    var e2 = $("#editBtn2"); if (e2) e2.onclick = editAnswers;
  }

  function renderPolicy() {
    var p = state.profile || {};
    var pl = plan || { pct: 0, burden: 0, tasks: [] };
    view.innerHTML = '<div class="layout"><div>' +
      '<div class="pillar-hero" style="--accent:var(--gold-500)"><p class="eyebrow dark">Policy Watch · preview</p><h2>What the Affordability Agenda would mean for you</h2>' +
      "<p>Your plan works on the next 30 days. These proposals work on the next 30 years. Here is each one translated into your household's stake" + (state.profile ? "" : " — answer the intake to personalize this") + ".</p>" +
      '<p class="small muted">Source: New Democrat Coalition, <em>Affordability Agenda: Restoring the American Dream</em>. Items are proposals, not law. Live bill tracking is planned; for current status, use Congress.gov.</p></div>' +
      '<div class="grid">' + R.POLICY.map(function (it) {
        var P = R.PILLARS[it.pillar];
        return '<article class="card policy-item" style="--accent:' + P.accent + '"><p class="eyebrow dark">' + P.app + " · Agenda " + it.ref + "</p><h3>" + it.item + '</h3><div class="stake"><strong>Your stake:</strong> ' + esc(it.stake(p, pl)) + "</div></article>";
      }).join("") + "</div>" +
      '<div class="card" style="margin-top:1rem"><h3>Make your numbers count</h3><p>Representatives hear abstractions all day. A real household budget is harder to ignore. Use "Share my story" to create a de-identified summary of your situation, then send it to your representative.</p><div class="links"><a href="' + R.LINKS.rep.url + '" target="_blank" rel="noopener">' + R.LINKS.rep.label + '</a><a href="' + R.LINKS.congress.url + '" target="_blank" rel="noopener">' + R.LINKS.congress.label + "</a></div>" +
      (state.profile ? '<p style="margin-top:1rem"><button class="btn btn-gold" type="button" id="storyBtn2">Create my de-identified story</button></p>' : "") + "</div>" +
      "</div>" + (plan ? sidebarHtml() : "") + "</div>";
    var s2 = $("#storyBtn2"); if (s2) s2.onclick = openStory;
  }

  /* ---------- Tabs ---------- */
  function renderTabs() {
    var tabs = [["home", "Household plan", "var(--gold-500)"]];
    Object.keys(R.PILLARS).forEach(function (k) { tabs.push([k, R.PILLARS[k].app, R.PILLARS[k].accent]); });
    tabs.push(["policy", "Policy Watch", "var(--navy-700)"]);
    tablist.innerHTML = tabs.map(function (t) {
      var c = plan && R.PILLARS[t[0]] ? plan.dx[t[0]].count : 0;
      var openC = plan && R.PILLARS[t[0]] ? plan.tasks.filter(function (x) { return x.pillar === t[0] && !state.done[x.id]; }).length : 0;
      return '<button role="tab" type="button" id="tab-' + t[0] + '" aria-controls="view" aria-selected="' + (currentTab === t[0]) + '" tabindex="' + (currentTab === t[0] ? 0 : -1) + '" data-tab="' + t[0] + '" style="--tab-accent:' + t[2] + '"><span class="dot"></span>' + t[1] + (c ? '<span class="count" aria-label="' + openC + ' open steps">' + openC + "</span>" : "") + "</button>";
    }).join("");
  }
  function setTab(t, focus) {
    currentTab = t; renderTabs();
    if (t === "home") renderHome(); else if (t === "policy") renderPolicy(); else renderPillar(t);
    if (location.hash !== "#" + t) history.replaceState(null, "", "#" + t);
    if (focus) { var b = $("#tab-" + t); if (b) b.focus(); }
  }
  tablist.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    var btns = $all("[role=tab]", tablist), i = btns.findIndex(function (b) { return b.getAttribute("aria-selected") === "true"; });
    i = (i + (e.key === "ArrowRight" ? 1 : -1) + btns.length) % btns.length; setTab(btns[i].dataset.tab, true);
  });

  /* ============================================================
     IMPLEMENT — "Do it with me" dialog
     ============================================================ */
  function findTask(id) { return plan && plan.tasks.filter(function (t) { return t.id === id; })[0]; }
  function openDialog(eyebrow, title, body) {
    $("#dlgEyebrow").textContent = eyebrow; $("#dlgTitle").textContent = title; $("#dlgBody").innerHTML = body;
    if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
  }
  function closeDialog() { if (dlg.open) { if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); } }
  dlg.addEventListener("click", function (e) { if (e.target === dlg || e.target.hasAttribute("data-close")) closeDialog(); });

  function openTask(id, lessonOnly) {
    var t = findTask(id); if (!t) return;
    var P = R.PILLARS[t.pillar];
    var draft = R.DRAFTS[t.draft] ? R.DRAFTS[t.draft](state.profile, t) : "";
    var escal = t.escalate === "legal" ? '<div class="escalate"><strong>Out of scope for an app:</strong> legal deadlines. This prepares you for legal aid — please contact them today. <a href="https://www.lawhelp.org" target="_blank" rel="noopener">Find free legal aid ↗</a></div>' :
      t.pillar === "health" ? '<div class="escalate"><strong>Navigation, not medical advice.</strong> Never change how you take a medicine without your prescriber or pharmacist. Emergencies: 911 · Crisis: 988.</div>' : "";
    var body = escal +
      '<div class="lesson"><h3>The 60-second lesson</h3><p>' + esc(t.lesson) + "</p></div>" +
      (lessonOnly ? "" :
        '<label for="draftText" class="label" style="font-weight:700;display:block;margin-bottom:.3rem">Your draft — edit anything, then copy, download, or print</label>' +
        '<textarea id="draftText" class="draft">' + esc(draft) + "</textarea>" +
        '<div class="dlg-actions"><button class="btn btn-teal btn-small" type="button" id="copyDraft">Copy</button><button class="btn btn-ghost btn-small" type="button" id="dlDraft">Download .txt</button>' +
        '<button class="btn btn-ghost btn-small" type="button" id="doneDraft">' + (state.done[t.id] ? "Mark not done" : "Mark this step done") + "</button></div>") +
      (t.links && t.links.length ? '<h3 style="margin-top:1rem;font-size:1rem">Where to go</h3><div class="links">' + t.links.map(function (l) { return '<a href="' + l.url + '" target="_blank" rel="noopener">' + l.label + "</a>"; }).join("") + "</div>" : "") +
      '<p class="source"><strong>Why this step:</strong> ' + esc(t.why) + "<br><strong>Rule source:</strong> " + esc(t.source || "") + " · ruleset " + R.RULESET.version + "</p>" +
      (lessonOnly ? '<div class="dlg-actions"><button class="btn btn-teal btn-small" type="button" id="toDraft">Do it with me →</button></div>' : "");
    openDialog(P.app + (lessonOnly ? " · Learn" : " · Do it with me"), t.title, body);
    var c = $("#copyDraft"); if (c) c.onclick = function () { copyText($("#draftText").value); };
    var dl = $("#dlDraft"); if (dl) dl.onclick = function () { download(t.id + ".txt", $("#draftText").value, "text/plain"); };
    var dn = $("#doneDraft"); if (dn) dn.onclick = function () { toggleDone(t.id); closeDialog(); };
    var td = $("#toDraft"); if (td) td.onclick = function () { openTask(id, false); };
  }

  function copyText(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function () { toast("Copied."); }, fallback); else fallback();
    function fallback() { var ta = $("#draftText") || $("#storyText"); if (ta) { ta.select(); try { document.execCommand("copy"); toast("Copied."); } catch (e) { toast("Select the text and copy it."); } } }
  }
  function download(name, text, type) {
    var blob = new Blob([text], { type: type }); var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function toggleDone(id) {
    if (state.done[id]) delete state.done[id]; else state.done[id] = new Date().toISOString();
    save(); var y = window.scrollY; setTab(currentTab); window.scrollTo(0, y);
    toast(state.done[id] ? "Nice work. Saved to your tally." : "Marked not done.");
  }

  /* ============================================================
     EVALUATE — weekly check-in + story bank (opt-in, local)
     ============================================================ */
  function openCheckin() {
    var open = plan.tasks.filter(function (t) { return !state.done[t.id]; });
    var body = '<form id="ciForm"><div class="field"><span class="label">1. Did the plan hold this week? Check anything that got done.</span><div class="choices">' +
      (open.length ? open.slice(0, 8).map(function (t) { return choice("did", t.id, esc(t.title), false); }).join("") : "<p>Everything is checked off. 🎉</p>") +
      choice("did", "_denied", "Something was <strong>denied</strong> or we were waitlisted", false) + "</div></div>" +
      '<div class="field"><span class="label">2. What changed?</span><div class="choices">' +
      choice("changed", "none", "Nothing big", true, "", "radio") + choice("changed", "income", "Income or work changed", false, "", "radio") + choice("changed", "notice", "A new bill, notice, or deadline", false, "", "radio") + choice("changed", "household", "Someone moved in or out", false, "", "radio") +
      '</div></div><button class="btn btn-teal" type="submit">Save check-in</button></form>';
    openDialog("Evaluate", "Weekly check-in", body);
    $("#ciForm").onsubmit = function (e) {
      e.preventDefault(); var f = new FormData(e.target); var did = f.getAll("did"); var changed = f.get("changed");
      did.forEach(function (id) { if (id[0] !== "_") state.done[id] = new Date().toISOString(); });
      state.checkins.push({ date: new Date().toISOString(), did: did, changed: changed }); save(); closeDialog();
      if (changed && changed !== "none") { toast("Let's update your answers and re-plan."); editAnswers(changed === "income" ? 3 : changed === "household" ? 2 : 5); return; }
      setTab(currentTab);
      if (did.indexOf("_denied") !== -1) openDialog("Evaluate", "A denial isn't the end", '<p>Denials and waitlists are exactly where programs fail households — and where a person helps most.</p><ul><li>Ask for the reason <strong>in writing</strong> and the deadline to appeal.</li><li>Most benefit denials can be appealed through a "fair hearing" — legal aid can help for free.</li><li>Call <a href="https://www.211.org" target="_blank" rel="noopener">211</a> for other programs while you wait.</li></ul><p class="small muted">With your permission, stories like yours show lawmakers where programs break. Use "Share my story" to create a de-identified summary.</p>');
      else toast("Check-in saved.");
    };
  }

  function storyText() {
    var p = state.profile; var pl = plan;
    var band = pl.pct <= 100 ? "below the poverty line" : pl.pct <= 200 ? "between 100% and 200% of the poverty line" : pl.pct <= 400 ? "between 200% and 400% of the poverty line" : "above 400% of the poverty line";
    var lines = [];
    lines.push("A household of " + p.hhSize + " in " + stateName(p.state) + ", with income " + band + ".");
    var pressures = [];
    if (p.tenure === "rent" && pl.burden) pressures.push("rent that takes " + pl.burden + "% of income");
    if (p.rentIncreasePct) pressures.push("a " + p.rentIncreasePct + "% rent increase");
    if (p.evictionNotice) pressures.push("an eviction notice");
    if (p.shutoff) pressures.push("a utility shutoff notice" + (p.medEquip ? " while relying on powered medical equipment" : ""));
    if (p.renewalDue) pressures.push("a Medicaid renewal deadline");
    if (p.uninsured) pressures.push("someone without health insurance");
    if (num(p.medBill)) pressures.push("about " + usd(Math.round(num(p.medBill) / 100) * 100) + " in medical bills");
    if (p.rxTrouble) pressures.push("prescriptions they struggle to afford");
    if (p.paDenied) pressures.push("a denied prior authorization");
    if (num(p.childcareCost)) pressures.push("child care costing about " + usd(Math.round(num(p.childcareCost) / 100) * 100) + "/month");
    if (p.caringAdult) pressures.push("unpaid care for an adult family member");
    if (p.foodRunsOut) pressures.push("food that runs out before the end of the month");
    if (pressures.length) lines.push("This month they faced " + pressures.join(", ") + ".");
    var denied = state.checkins.some(function (c) { return c.did.indexOf("_denied") !== -1; });
    lines.push("Their plan found about " + usd(pl.potential.monthly) + "/month in help they may qualify for but weren't receiving" + (denied ? ", and at least one application was denied or waitlisted" : "") + ".");
    lines.push("Policies on the Affordability Agenda that would change this household's budget: " + R.POLICY.filter(function (x) { return /Your|You're|With \d|At \d|Rent is/.test(x.stake(p, pl)); }).map(function (x) { return x.item.toLowerCase(); }).slice(0, 4).join("; ") + ".");
    lines.push("\n(De-identified: no name, ZIP code, or contact details. Shared only if the household chooses to send it.)");
    return lines.join(" ");
  }
  function openStory() {
    openDialog("Story bank · opt-in", "Share my story (de-identified)", '<p>This summary leaves out your name, ZIP code, exact income, and contact details. Nothing is sent anywhere — you choose whether to copy it to a representative, an organizer, or a reporter.</p>' +
      '<textarea id="storyText" class="draft" style="min-height:200px">' + esc(storyText()) + '</textarea><div class="dlg-actions"><button class="btn btn-teal btn-small" type="button" id="copyStory">Copy</button><a class="btn btn-ghost btn-small" href="' + R.LINKS.rep.url + '" target="_blank" rel="noopener">Find my representative ↗</a></div>');
    $("#copyStory").onclick = function () { copyText($("#storyText").value); };
  }

  /* ---------- Data controls ---------- */
  function editAnswers(step) {
    state.draft = JSON.parse(JSON.stringify(state.profile || state.draft || {})); delete state.draft.sample;
    if (state.draft.intakeDate) {
      var elapsed = Math.max(0, Math.floor((Date.now() - new Date(state.draft.intakeDate)) / 86400000));
      ["renewalDays", "shutoffDays"].forEach(function (k) { if (num(state.draft[k])) state.draft[k] = Math.max(0, num(state.draft[k]) - elapsed); });
      delete state.draft.intakeDate;
    }
    state.profile = null; intakeStep = typeof step === "number" ? step : 0; save(); plan = null; setTab("home"); focusQ();
  }
  function startOver() { state = fresh(); save(); plan = null; intakeStep = 0; setTab("home"); }
  function wipe() {
    if (!confirm("Erase all your answers and progress from this browser? This can't be undone.")) return;
    try { localStorage.removeItem(KEY); } catch (e) {}
    state = fresh(); plan = null; intakeStep = 0; setTab("home"); toast("Erased. Nothing remains on this device.");
  }
  function exportData() { download("life-within-reach-household.json", JSON.stringify({ exported: new Date().toISOString(), ruleset: R.RULESET.version, data: state }, null, 2), "application/json"); }

  /* ---------- Global click delegation ---------- */
  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-open],[data-learn],[data-tab],#checkinBtn,#editBtn,#printBtn,#exportBtn,#storyBtn,#wipeBtn");
    if (!el) return;
    if (el.dataset.open) return openTask(el.dataset.open, false);
    if (el.dataset.learn) return openTask(el.dataset.learn, true);
    if (el.dataset.tab) { setTab(el.dataset.tab); window.scrollTo(0, 0); return; }
    switch (el.id) {
      case "checkinBtn": return openCheckin();
      case "editBtn": return editAnswers();
      case "printBtn": return window.print();
      case "exportBtn": return exportData();
      case "storyBtn": return openStory();
      case "wipeBtn": return wipe();
    }
  });
  document.addEventListener("change", function (e) { if (e.target.matches("[data-done]")) toggleDone(e.target.dataset.done); });

  /* ---------- Boot ---------- */
  var params = new URLSearchParams(location.search);
  if (params.get("sample") === "1" && !state.profile) loadSample();
  refresh();
  var h = location.hash.replace("#", "");
  setTab(["home", "food", "health", "housing", "energy", "family", "policy"].indexOf(h) !== -1 && h ? h : "home");
})();
