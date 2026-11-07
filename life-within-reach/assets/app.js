/* ============================================================
   Life Within Reach — Household Command Center (browser app)
   Five-step loop: Assess → Understand → Plan → Act → Check in
   All data stays in localStorage on this device.
   English and Spanish sit side by side: T("English", "Español").
   ============================================================ */
(function () {
  "use strict";
  var R = window.LWR;
  var KEY = "lwr.household.v1";
  var LANG_KEY = "lwr.lang";
  var view = document.getElementById("view");
  var tablist = document.getElementById("tablist");
  var dlg = document.getElementById("taskDialog");

  /* ---------- Language (?lang=es, else saved choice, else the page's lang) ---------- */
  var LANG = (function () {
    var q = new URLSearchParams(location.search).get("lang"), saved = null;
    try { saved = localStorage.getItem(LANG_KEY); } catch (e) {}
    var l = (q || saved || document.documentElement.lang || "en").slice(0, 2).toLowerCase() === "es" ? "es" : "en";
    try { localStorage.setItem(LANG_KEY, l); } catch (e) {}
    return l;
  })();
  var ES = LANG === "es";
  R.setLang(LANG);
  document.documentElement.lang = LANG;
  function T(en, es) { return ES ? es : en; }
  var LOCALE = ES ? "es-US" : "en-US";

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
  function fmtDate(d) { return new Date(d).toLocaleDateString(LOCALE, { month: "short", day: "numeric" }); }
  function toast(msg) { var t = document.getElementById("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(toast._t); toast._t = setTimeout(function () { t.classList.remove("show"); }, 2400); }
  function num(v) { var n = parseFloat(v); return isFinite(n) && n > 0 ? n : 0; }
  // Optional numeric answer: blank stays null (unknown); 0 is a real answer.
  function optNum(v) { if (v === null || v === undefined || String(v).trim() === "") return null; var n = parseFloat(v); return isFinite(n) ? Math.max(0, n) : null; }
  function shown(v) { return v === null || v === undefined ? "" : v; }
  function has(a, v) { return Array.isArray(a) && a.indexOf(v) !== -1; }
  function setHeaderVar() { var h = document.getElementById("siteHeader"); if (h) document.documentElement.style.setProperty("--header-h", h.offsetHeight + "px"); }
  function linkHtml(l) { var x = R.linkFor(l); return '<a href="' + x.url + '" target="_blank" rel="noopener">' + esc(x.label) + "</a>"; }

  /* ---------- Static page text + language toggle ---------- */
  if (ES) {
    $all("[data-es]").forEach(function (el) { el.innerHTML = el.getAttribute("data-es"); });
    $all("[data-es-aria]").forEach(function (el) { el.setAttribute("aria-label", el.getAttribute("data-es-aria")); });
    document.title = "Plan del hogar — Life Within Reach | Nurse AI OS";
  }
  var toggle = document.getElementById("langToggle");
  if (toggle) {
    toggle.textContent = ES ? "English" : "Español";
    toggle.setAttribute("href", "?lang=" + (ES ? "en" : "es"));
    toggle.setAttribute("lang", ES ? "en" : "es");
    toggle.setAttribute("hreflang", ES ? "en" : "es");
    toggle.addEventListener("click", function (e) {
      e.preventDefault();
      try { localStorage.setItem(LANG_KEY, ES ? "en" : "es"); } catch (err) {}
      location.href = "?lang=" + (ES ? "en" : "es") + location.hash;
    });
  }
  // In Spanish, links back to the landing page go to the Spanish one.
  if (ES) $all('#siteHeader a[href^="../"]').forEach(function (a) { a.setAttribute("href", a.getAttribute("href").replace(/^\.\.\//, "../es/")); });
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
    ["bill", T("A bill I can't pay", "Una cuenta que no puedo pagar"), T("medical, utility, or other", "médica, de servicios u otra")],
    ["coverage", T("Health coverage or a renewal deadline", "Seguro médico o una fecha límite de renovación"), ""],
    ["housing", T("Rent, a rent increase, or an eviction notice", "La renta, un aumento de renta o un aviso de desalojo"), ""],
    ["shutoff", T("A shutoff notice or a high energy bill", "Un aviso de corte o una factura de energía alta"), ""],
    ["childcare", T("Child care costs or a waitlist", "El costo del cuidado infantil o una lista de espera"), ""],
    ["caregiving", T("Caring for a parent or family member", "Cuidar a un padre, madre u otro familiar"), ""],
    ["food", T("Food runs out before the month does", "La comida se acaba antes de fin de mes"), ""],
    ["work", T("A lost job, cut hours, or a job search", "Un trabajo perdido, menos horas o una búsqueda de empleo"), T("including a first job after school", "incluida una primera búsqueda después de la escuela")],
    ["general", T("I just want to lower costs", "Solo quiero bajar mis gastos"), ""]
  ];
  var BENEFITS = [
    ["snap", T("SNAP / food stamps", "SNAP / cupones de alimentos"), T("CalFresh in CA", "CalFresh en CA")], ["wic", "WIC", ""], ["medicaid", T("Medicaid or CHIP", "Medicaid o CHIP"), T("Medi-Cal in CA", "Medi-Cal en CA")],
    ["marketplace", T("Marketplace (ACA) plan", "Plan del Mercado de Seguros Médicos (ACA)"), ""], ["employer", T("Insurance through a job", "Seguro por medio del trabajo"), ""], ["medicare", "Medicare", ""],
    ["ssi", T("SSI or SSDI", "SSI o SSDI"), ""], ["utilDiscount", T("Utility low-income discount", "Descuento de servicios para bajos ingresos"), T("e.g. CARE", "p. ej., CARE")], ["liheap", T("LIHEAP this year", "LIHEAP este año"), ""],
    ["lifeline", T("Lifeline phone/internet", "Lifeline (teléfono/internet)"), ""], ["childcareSubsidy", T("Child care subsidy", "Subsidio para cuidado infantil"), ""], ["voucher", T("Housing voucher / public housing", "Vale de vivienda / vivienda pública"), ""]
  ];

  var STEPS = [
    {
      id: "reasons", q: T("What brought you here today?", "¿Qué le trae por aquí hoy?"),
      why: T("So I can start with what's most urgent for you. Pick as many as fit.", "Para empezar por lo más urgente para usted. Marque todas las que apliquen."),
      html: function (p) { return '<div class="choices">' + REASONS.map(function (r) { return choice("reasons", r[0], r[1], has(p.reasons, r[0]), r[2]); }).join("") + "</div>"; },
      read: function (f, p) { p.reasons = f.getAll("reasons"); }
    },
    {
      id: "place", q: T("Where do you live?", "¿Dónde vive?"),
      why: T("Benefit rules change by state — Medicaid limits, rent caps, paid leave, utility programs. Your ZIP code only helps point you to local resources; it is never shared.",
        "Las reglas de los beneficios cambian según el estado: límites de Medicaid, límites de renta, licencias pagadas, programas de servicios. Su código postal solo sirve para indicarle recursos locales; nunca se comparte."),
      html: function (p) {
        return '<div class="row"><div class="field"><label for="f-state">' + T("State", "Estado") + '</label><select id="f-state" name="state" required><option value="">' + T("Choose your state…", "Elija su estado…") + "</option>" +
          R.STATES.map(function (s) { return '<option value="' + s[0] + '"' + (p.state === s[0] ? " selected" : "") + ">" + s[1] + "</option>"; }).join("") +
          '</select></div><div class="field"><label for="f-zip">' + T("ZIP code", "Código postal") + ' <span class="muted">' + T("(optional)", "(opcional)") + '</span></label><input id="f-zip" name="zip" type="text" inputmode="numeric" pattern="[0-9]{5}" maxlength="5" autocomplete="postal-code" value="' + esc(p.zip || "") + '"></div></div>';
      },
      read: function (f, p) { p.state = f.get("state") || ""; p.zip = (f.get("zip") || "").replace(/\D/g, "").slice(0, 5); },
      valid: function (p) { return p.state ? "" : T("Please choose your state so I use the right rules.", "Por favor, elija su estado para usar las reglas correctas."); }
    },
    {
      id: "household", q: T("Who lives in your household?", "¿Quiénes viven en su hogar?"),
      why: T("Most programs use household size to set income limits. Children's ages matter for WIC, school meals, and child care help.",
        "La mayoría de los programas usan el tamaño del hogar para fijar los límites de ingresos. La edad de los niños importa para WIC, las comidas escolares y la ayuda con el cuidado infantil."),
      html: function (p) {
        return '<div class="row">' + numField("hhSize", T("People in your household (including you)", "Personas en su hogar (incluyéndose usted)"), p.hhSize || 1, 1) +
          numField("kidsUnder5", T("Children under 5", "Niños menores de 5 años"), p.kidsUnder5 || 0) + numField("kids5to17", T("Children 5–17", "Niños de 5 a 17 años"), p.kids5to17 || 0) + numField("seniors", T("Adults 60 or older", "Adultos de 60 años o más"), p.seniors || 0) + "</div>" +
          '<div class="choices">' + yes("pregnant", T("Someone is pregnant", "Alguien está embarazada"), p.pregnant) + yes("disability", T("Someone has a disability", "Alguien tiene una discapacidad"), p.disability) + "</div>";
      },
      read: function (f, p) {
        p.hhSize = Math.max(1, parseInt(f.get("hhSize"), 10) || 1); p.kidsUnder5 = parseInt(f.get("kidsUnder5"), 10) || 0; p.kids5to17 = parseInt(f.get("kids5to17"), 10) || 0;
        p.seniors = parseInt(f.get("seniors"), 10) || 0; p.pregnant = !!f.get("pregnant"); p.disability = !!f.get("disability");
        var counted = 1 + p.kidsUnder5 + p.kids5to17; if (p.hhSize < counted) p.hhSize = counted;
      }
    },
    {
      id: "income", q: T("About how much does your household earn in a month, before taxes?", "¿Cuánto gana su hogar al mes, más o menos, antes de impuestos?"),
      why: T("Nearly every program compares income to the federal poverty guideline. A close estimate is fine — I'll show the math, and the program checks the real numbers.",
        "Casi todos los programas comparan los ingresos con la guía federal de pobreza. Un cálculo aproximado está bien: le mostraré las cuentas, y el programa revisa las cifras reales."),
      html: function (p) {
        return moneyField("income", T("Monthly household income before taxes", "Ingresos mensuales del hogar antes de impuestos"), p.income, T("Include wages, self-employment, unemployment, Social Security, and child support received.", "Incluya salarios, trabajo por cuenta propia, desempleo, Seguro Social y manutención de hijos que reciba.")) +
          '<div class="field"><label for="f-earnedIncome">' + T("How much of that comes from a job or self-employment?", "¿Cuánto de eso viene de un trabajo o de trabajo por cuenta propia?") + '</label><div class="money"><input id="f-earnedIncome" name="earnedIncome" type="number" inputmode="decimal" min="0" step="1" value="' + esc(shown(p.earnedIncome)) + '" placeholder="' + T("Leave blank if all of it", "Déjelo en blanco si es todo") + '"></div>' +
          '<span class="hint">' + T("SNAP gives a 20% deduction on earnings only — not on Social Security, unemployment, or child support. Enter 0 if none of it is from work.", "SNAP da una deducción del 20% solo sobre lo que gana trabajando, no sobre el Seguro Social, el desempleo ni la manutención. Escriba 0 si nada viene del trabajo.") + "</span></div>" +
          '<div class="choices">' + yes("incomeDropped", T("Our income dropped recently", "Nuestros ingresos bajaron hace poco"), p.incomeDropped) + "</div>";
      },
      read: function (f, p) { p.income = num(f.get("income")); p.earnedIncome = optNum(f.get("earnedIncome")); p.incomeDropped = !!f.get("incomeDropped"); }
    },
    {
      // WorkBridge intake.
      id: "work", q: T("Has work changed for anyone in the household?", "¿Cambió el trabajo de alguien en el hogar?"),
      why: T("A job ending sets off deadlines everywhere else: unemployment pays from the week you file, health coverage has a 60-day window, and SNAP can go up. I'm asking so those land on your plan with dates. Every step this unlocks leads to an office with people in it — you can do all of it without using any AI.",
        "Cuando termina un trabajo, se activan plazos en todo lo demás: el desempleo paga desde la semana en que lo solicita, el seguro médico tiene un plazo de 60 días y SNAP puede subir. Le pregunto para que esos plazos queden en su plan con fechas. Cada paso que esto activa lleva a una oficina con personas: puede hacerlo todo sin usar ninguna IA."),
      html: function (p) {
        return '<div class="choices">' +
          yes("jobLoss", T("Someone lost a job or had hours cut", "Alguien perdió su trabajo o le redujeron las horas"), p.jobLoss, T("Includes being laid off, let go, or quitting for a good reason", "Incluye despidos, recortes y renunciar por una buena razón")) +
          yes("lostCoverage", T("Health insurance ended, or will end, with that job", "El seguro médico terminó, o va a terminar, con ese trabajo"), p.lostCoverage, T("Starts a 60-day clock", "Empieza un plazo de 60 días")) +
          yes("warnLarge", T("The employer has 100 or more workers and gave little or no notice", "El empleador tiene 100 trabajadores o más y avisó con poco tiempo o sin aviso"), p.warnLarge, T("The WARN Act may apply", "Puede aplicar la ley WARN")) +
          yes("newGrad", T("Someone is looking for a first job after finishing school or training", "Alguien busca su primer empleo después de terminar los estudios o una capacitación"), p.newGrad, T("Including new nurses", "Incluye enfermeras y enfermeros nuevos")) +
          yes("wantsTraining", T("Someone wants training that leads to a better-paying job", "Alguien quiere una capacitación que lleve a un trabajo mejor pagado"), p.wantsTraining, T("Apprenticeships and free programs", "Aprendizajes y programas gratuitos")) +
          yes("aiAffected", T("Software or AI screened someone out, cut their hours, or took over their work", "Un programa de computadora o IA descartó a alguien, le redujo las horas o se quedó con su trabajo"), p.aiAffected, T("Unlocks your rights and ways to push back", "Activa sus derechos y formas de responder")) +
          "</div>" +
          '<div class="row" style="margin-top:1rem">' + numField("jobEndDays", T("Days since the job ended or hours were cut", "Días desde que terminó el trabajo o redujeron las horas"), shown(p.jobEndDays), 0, T("Leave blank if it hasn't happened or you're not sure. Enter 0 if it's today.", "Déjelo en blanco si no ha pasado o no está seguro. Escriba 0 si es hoy.")) +
          numField("coverageEndDays", T("Days since the job-based health coverage ended", "Días desde que terminó el seguro médico del trabajo"), shown(p.coverageEndDays), 0, T("Often later than the last day of work. Enter 0 if it ends today; leave blank if it hasn't ended yet or you're not sure.", "Suele ser después del último día de trabajo. Escriba 0 si termina hoy; déjelo en blanco si todavía no ha terminado o no está seguro.")) + "</div>";
      },
      read: function (f, p) {
        p.jobLoss = !!f.get("jobLoss"); p.lostCoverage = !!f.get("lostCoverage"); p.warnLarge = !!f.get("warnLarge"); p.newGrad = !!f.get("newGrad"); p.wantsTraining = !!f.get("wantsTraining"); p.aiAffected = !!f.get("aiAffected");
        p.jobEndDays = optNum(f.get("jobEndDays")); p.coverageEndDays = optNum(f.get("coverageEndDays"));
      }
    },
    {
      id: "benefits", q: T("Which of these do you already have?", "¿Cuáles de estos ya tiene?"),
      why: T("So I don't send you after things you already have — and because some (like SNAP or Medicaid) automatically qualify you for others.",
        "Para no mandarle a buscar lo que ya tiene, y porque algunos (como SNAP o Medicaid) le hacen calificar automáticamente para otros."),
      html: function (p) { return '<div class="choices">' + BENEFITS.map(function (b) { return choice("benefits", b[0], b[1], has(p.benefits, b[0]), b[2]); }).join("") + "</div>"; },
      read: function (f, p) { p.benefits = f.getAll("benefits"); }
    },
    {
      id: "housing", q: T("Tell me about your housing.", "Hábleme de su vivienda."),
      why: T("Housing is the cost that drives everything else. If there's a notice, the clock matters more than anything — I'll put it first.",
        "La vivienda es el gasto que mueve todo lo demás. Si recibió un aviso, el tiempo importa más que nada: lo pondré primero."),
      html: function (p) {
        return '<div class="field"><span class="label">' + T("Do you…", "Usted…") + '</span><div class="choices">' +
          choice("tenure", "rent", T("Rent", "Renta"), p.tenure === "rent", "", "radio") + choice("tenure", "own", T("Own (mortgage or paid off)", "Es dueño (con hipoteca o pagada)"), p.tenure === "own", "", "radio") + choice("tenure", "other", T("Stay with others / other", "Vive con otras personas / otro"), p.tenure === "other", "", "radio") + "</div></div>" +
          moneyField("housingCost", T("Monthly rent or mortgage", "Renta o hipoteca mensual"), p.housingCost) +
          '<div class="choices">' + yes("behindRent", T("We're behind on rent or mortgage", "Estamos atrasados con la renta o la hipoteca"), p.behindRent) + yes("evictionNotice", T("I received an eviction notice or court papers", "Recibí un aviso de desalojo o papeles de la corte"), p.evictionNotice, T("I'll move this to the top", "Lo pondré primero")) + yes("repairs", T("Repairs aren't being made", "No hacen las reparaciones"), p.repairs) + "</div>" +
          '<div class="row" style="margin-top:1rem">' + numField("rentIncreasePct", T("Rent increase in the last notice (%)", "Aumento de renta en el último aviso (%)"), p.rentIncreasePct || "", 0, T("Leave blank if none", "Déjelo en blanco si no hubo")) + "</div>";
      },
      read: function (f, p) {
        p.tenure = f.get("tenure") || "rent"; p.housingCost = num(f.get("housingCost")); p.behindRent = !!f.get("behindRent"); p.evictionNotice = !!f.get("evictionNotice"); p.repairs = !!f.get("repairs");
        p.rentIncreasePct = num(f.get("rentIncreasePct"));
      }
    },
    {
      id: "energy", q: T("What about energy and utility bills?", "¿Y las facturas de energía y servicios?"),
      why: T("A shutoff is a health event — especially with medical equipment, insulin that needs a fridge, or extreme heat or cold. Some protections only work if you ask before the shutoff date.",
        "Un corte de servicio afecta la salud, sobre todo si hay equipo médico, insulina que necesita refrigerador, o calor o frío extremos. Algunas protecciones solo funcionan si las pide antes de la fecha del corte."),
      html: function (p) {
        return moneyField("energyBill", T("Typical monthly energy bill (electric + gas)", "Factura de energía de un mes normal (luz + gas)"), p.energyBill) +
          '<div class="choices">' + yes("shutoff", T("I have a shutoff / disconnection notice", "Tengo un aviso de corte o desconexión"), p.shutoff) + yes("medEquip", T("Someone uses medical equipment that needs power", "Alguien usa equipo médico que necesita electricidad"), p.medEquip, T("CPAP, oxygen, refrigerated medicine, power wheelchair…", "CPAP, oxígeno, medicina refrigerada, silla de ruedas eléctrica…")) + "</div>" +
          '<div class="row" style="margin-top:1rem">' + numField("shutoffDays", T("Days until the shutoff date", "Días que faltan para el corte"), shown(p.shutoffDays), 0, T("If you have a notice. Enter 0 if it's today.", "Si tiene un aviso. Escriba 0 si es hoy.")) + "</div>";
      },
      read: function (f, p) { p.energyBill = num(f.get("energyBill")); p.shutoff = !!f.get("shutoff"); p.medEquip = !!f.get("medEquip"); p.shutoffDays = optNum(f.get("shutoffDays")); }
    },
    {
      id: "health", q: T("How is health coverage and health spending going?", "¿Cómo va su seguro médico y sus gastos de salud?"),
      why: T("Losing coverage and paying list price are the two things that most often bankrupt families. I'm asking about costs and paperwork — not symptoms or diagnoses.",
        "Perder el seguro y pagar precio completo son las dos cosas que más llevan a las familias a la quiebra. Pregunto por costos y papeleo, no por síntomas ni diagnósticos."),
      html: function (p) {
        var b = p.benefits || [];
        return '<div class="choices">' +
          yes("uninsured", T("Someone in the household has no health insurance", "Alguien en el hogar no tiene seguro médico"), p.uninsured, T("Even if others in the household are covered", "Aunque otros en el hogar sí tengan")) +
          (has(b, "medicaid") ? yes("renewalDue", T("A Medicaid/CHIP renewal is due", "Hay que renovar Medicaid/CHIP"), p.renewalDue) : "") +
          yes("rxTrouble", T("Cost makes it hard to take a prescription as prescribed", "El costo me impide tomar una receta como me indicaron"), p.rxTrouble) +
          yes("paDenied", T("Insurance denied a prior authorization", "El seguro negó una autorización previa"), p.paDenied) + "</div>" +
          '<div class="row" style="margin-top:1rem">' +
          (has(b, "medicaid") ? numField("renewalDays", T("Days until the renewal is due", "Días que faltan para la fecha de renovación"), shown(p.renewalDays), 0, T("Enter 0 if it's due today.", "Escriba 0 si vence hoy.")) : "") +
          moneyField("medBill", T("Unpaid medical bills (total)", "Cuentas médicas sin pagar (total)"), p.medBill) + moneyField("rxMonthly", T("Prescriptions per month (out of pocket)", "Recetas al mes (lo que usted paga)"), p.rxMonthly) + "</div>";
      },
      read: function (f, p) {
        p.uninsured = !!f.get("uninsured"); p.renewalDue = !!f.get("renewalDue"); p.rxTrouble = !!f.get("rxTrouble"); p.paDenied = !!f.get("paDenied");
        p.renewalDays = optNum(f.get("renewalDays")); p.medBill = num(f.get("medBill")); p.rxMonthly = num(f.get("rxMonthly"));
      }
    },
    {
      id: "family", q: T("Who are you caring for?", "¿A quién cuida usted?"),
      why: T("Child care and caregiving are where household math breaks hardest — and where help is most scattered. I'm also checking whether your job can be protected while you give care.",
        "El cuidado de niños y de familiares es donde más se rompen las cuentas del hogar, y donde la ayuda está más dispersa. También reviso si su empleo puede estar protegido mientras cuida a alguien."),
      html: function (p) {
        var kids = (p.kidsUnder5 || 0) + (p.kids5to17 || 0);
        return (kids ? moneyField("childcareCost", T("Monthly child care cost", "Costo mensual del cuidado infantil"), p.childcareCost) +
          '<div class="field"><span class="label">' + T("Does your employer offer a dependent care FSA (DCAP)?", "¿Su empleador ofrece una cuenta FSA para el cuidado de dependientes (DCAP)?") + '</span><div class="choices">' +
          choice("employerDCAP", "yes", T("Yes", "Sí"), p.employerDCAP === "yes", "", "radio") + choice("employerDCAP", "no", T("No / not working", "No / no trabajo"), p.employerDCAP === "no", "", "radio") + choice("employerDCAP", "unsure", T("Not sure", "No sé"), !p.employerDCAP || p.employerDCAP === "unsure", "", "radio") + "</div></div>" : "") +
          '<div class="choices">' + yes("caringAdult", T("I help care for a parent, partner, or adult family member", "Ayudo a cuidar a mi padre, madre, pareja u otro familiar adulto"), p.caringAdult) + yes("needLeave", T("I need time off work for family or medical reasons", "Necesito tiempo libre del trabajo por razones familiares o médicas"), p.needLeave) + "</div>";
      },
      read: function (f, p) { p.childcareCost = num(f.get("childcareCost")); p.employerDCAP = f.get("employerDCAP") || "unsure"; p.caringAdult = !!f.get("caringAdult"); p.needLeave = !!f.get("needLeave"); }
    },
    {
      id: "food", q: T("Last one: food and internet.", "La última: comida e internet."),
      why: T("Food is often the first thing that breaks each month, and internet is a bill most people overpay. Both usually have quick fixes.",
        "La comida suele ser lo primero que falta cada mes, y la mayoría paga de más por internet. Las dos cosas suelen tener soluciones rápidas."),
      html: function (p) { return '<div class="choices">' + yes("foodRunsOut", T("Food often runs out before the end of the month", "La comida suele acabarse antes de fin de mes"), p.foodRunsOut) + "</div>" + '<div class="row" style="margin-top:1rem">' + moneyField("internetBill", T("Monthly internet bill", "Factura mensual de internet"), p.internetBill) + "</div>"; },
      read: function (f, p) { p.foodRunsOut = !!f.get("foodRunsOut"); p.internetBill = num(f.get("internetBill")); }
    }
  ];

  function renderIntake() {
    var p = state.draft || {};
    var step = STEPS[intakeStep];
    var pct = Math.round((intakeStep) / STEPS.length * 100);
    var nods = ES ? ["Gracias.", "Entendido.", "Eso ayuda.", "Muy bien.", "Bueno saberlo.", "Gracias, ya casi terminamos."] : ["Thank you.", "Got it.", "That helps.", "Okay.", "Good to know.", "Thanks — almost there."];
    view.innerHTML =
      '<div class="intake">' +
      '<div class="persona"><div class="persona-avatar" aria-hidden="true">🤝</div><div class="bubble"><div class="who">' + T("Your community organizer · AI", "Su organizador comunitario · IA") + "</div>" +
      (intakeStep === 0 ? "<p>" + T("Hi — I'm an AI community organizer, not a nurse, doctor, or lawyer. I'll look at your actual situation with you and build a plan you can start today. Plain questions, one at a time, about 5–8 minutes. Skip anything you'd rather not answer.",
        "Hola. Soy un organizador comunitario hecho con inteligencia artificial (IA): no soy profesional de enfermería, ni médico, ni abogado. Vamos a ver juntos su situación real y a armar un plan que puede empezar hoy. Preguntas sencillas, una a la vez, unos 5 a 8 minutos. Puede saltarse lo que prefiera no contestar.") + "</p>" :
        "<p>" + nods[intakeStep % 6] + "</p>") +
      "</div></div>" +
      '<div class="progress" role="progressbar" aria-label="' + T("Intake progress", "Avance de las preguntas") + '" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct + '"><span style="width:' + Math.max(4, pct) + '%"></span></div>' +
      '<form class="q-card" id="qForm" novalidate>' +
      '<p class="eyebrow dark">' + T("Question ", "Pregunta ") + (intakeStep + 1) + T(" of ", " de ") + STEPS.length + "</p>" +
      '<h2 id="qTitle" tabindex="-1">' + step.q + "</h2>" +
      '<details class="why"><summary>' + T("Why I'm asking", "Por qué le pregunto") + "</summary><p>" + step.why + "</p></details>" +
      step.html(p) +
      '<p class="urgent" id="qError" role="alert" hidden></p>' +
      '<div class="q-actions">' + (intakeStep > 0 ? '<button type="button" class="btn btn-ghost btn-small" id="qBack">' + T("← Back", "← Atrás") + "</button>" : '<button type="button" class="btn-link" id="qSample">' + T("Explore with a sample household instead", "Mejor ver un hogar de ejemplo") + "</button>") +
      '<div class="right">' + (step.valid ? "" : '<button type="button" class="btn btn-ghost btn-small" id="qSkip">' + T("Skip", "Saltar") + "</button>") +
      '<button type="submit" class="btn btn-teal">' + (intakeStep === STEPS.length - 1 ? T("Build my plan →", "Armar mi plan →") : T("Next →", "Siguiente →")) + "</button></div></div>" +
      '<p class="never-ask">' + T("I will never ask your immigration status, Social Security number, or anything about symptoms or diagnoses. Answers stay on this device.",
        "Nunca le preguntaré su situación migratoria, su número de Seguro Social, ni nada sobre síntomas o diagnósticos. Sus respuestas se quedan en este aparato.") + "</p>" +
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
      childcareCost: 1900, employerDCAP: "unsure", caringAdult: true, needLeave: true, foodRunsOut: true, internetBill: 75,
      jobLoss: true, jobEndDays: 10, coverageEndDays: null, lostCoverage: false, warnLarge: false, newGrad: false, wantsTraining: true, aiAffected: true, sample: true
    };
    state.profile = JSON.parse(JSON.stringify(state.draft)); state.profile.intakeDate = new Date().toISOString(); state.done = {}; save(); refresh(); setTab("home");
    toast(T("Loaded a sample household — replace it with your own any time.", "Se cargó un hogar de ejemplo: cámbielo por el suyo cuando quiera."));
  }

  /* ============================================================
     UNDERSTAND + PLAN
     ============================================================ */
  function refresh() {
    if (state.profile && !state.profile.intakeDate) { state.profile.intakeDate = state.updated || new Date().toISOString(); save(); }
    plan = state.profile ? R.buildPlan(state.profile, new Date()) : null; renderTabs();
  }

  var STATUS = { "at-risk": ["rose", T("At risk", "En riesgo")], eligible: ["gold", T("Eligible, not enrolled", "Califica, sin inscribirse")], stretched: ["", T("Stable but stretched", "Estable, pero justo")], stable: ["green", T("Stable", "Estable")] };

  function summarySentence(p) {
    var parts = [];
    var urgent = plan.tasks.filter(function (t) { return t.urgent; });
    var eligible = plan.tasks.filter(function (t) { return t.confidence === "likely" && (t.monthly || t.oneTime); });
    if (ES) {
      parts.push("Su hogar es de " + p.hhSize + (p.hhSize === 1 ? " persona" : " personas") + " en " + stateName(p.state) + (p.income ? ", con ingresos de unos " + usd(p.income) + " al mes, más o menos el " + plan.pct + "% de la guía federal de pobreza" : "") + ".");
      if (urgent.length) parts.push("<strong>" + (urgent.length > 1 ? urgent.length + " cosas tienen" : "1 cosa tiene") + " fecha límite</strong>: " + (urgent.length > 1 ? "las puse" : "la puse") + " primero.");
      if (eligible.length) parts.push("Es probable que califique para " + eligible.length + (eligible.length > 1 ? " tipos" : " tipo") + " de ayuda que todavía no recibe.");
      if (plan.burden >= 30 && p.tenure === "rent") parts.push("La renta se lleva el " + plan.burden + "% de sus ingresos" + (plan.burden >= 50 ? ": eso es una carga severa." : "."));
      if (plan.flags.indexOf("coverage-gap") !== -1) parts.push("Su estado no ha ampliado Medicaid, lo que puede dejar una brecha de cobertura; agregué opciones de atención de bajo costo.");
      if (p.jobLoss) parts.push("Un trabajo terminó o redujeron las horas, así que puse en orden los pasos que traen dinero más rápido y protegen su cobertura; cada uno lleva a una persona, no a un programa.");
      else if (p.newGrad || p.wantsTraining) parts.push("Usted busca trabajo o capacitación, así que agregué las opciones con la evidencia más fuerte.");
      if (!plan.tasks.length) parts.push("Según lo que me contó, no hay nada urgente. Revise cada semana: las cosas cambian.");
      return parts.join(" ");
    }
    parts.push("You're a household of " + p.hhSize + " in " + stateName(p.state) + (p.income ? ", bringing in about " + usd(p.income) + " a month — roughly " + plan.pct + "% of the federal poverty guideline" : "") + ".");
    if (urgent.length) parts.push("<strong>" + urgent.length + " thing" + (urgent.length > 1 ? "s have" : " has") + " a deadline</strong> — I've put " + (urgent.length > 1 ? "them" : "it") + " at the top.");
    if (eligible.length) parts.push("You likely qualify for " + eligible.length + " kind" + (eligible.length > 1 ? "s" : "") + " of help you aren't getting yet.");
    if (plan.burden >= 30 && p.tenure === "rent") parts.push("Rent takes " + plan.burden + "% of income" + (plan.burden >= 50 ? " — that's severe cost burden." : "."));
    if (plan.flags.indexOf("coverage-gap") !== -1) parts.push("Your state hasn't expanded Medicaid, which can leave a coverage gap — I've added low-cost care options.");
    if (p.jobLoss) parts.push("A job ended or hours were cut, so I've lined up the steps that bring money back fastest and protect your coverage — each one leads to a person, not a program.");
    else if (p.newGrad || p.wantsTraining) parts.push("You're looking for work or training, so I've added the options with the strongest evidence behind them.");
    if (!plan.tasks.length) parts.push("Based on what you told me, nothing urgent stands out. Check in weekly — things change.");
    return parts.join(" ");
  }
  function stateName(code) { var s = R.STATES.filter(function (x) { return x[0] === code; })[0]; return s ? s[1] : T("your state", "su estado"); }

  function valueHtml(t) {
    if (t.monthly) return usd(t.monthly) + T("/mo", "/mes") + "<small>" + (t.confidence === "likely" ? T("est. likely", "aprox. probable") : T("est. possible", "aprox. posible")) + "</small>";
    if (t.oneTime) return usd(t.oneTime) + "<small>" + T("one-time est.", "aprox., una vez") + "</small>";
    return esc(t.valueLabel || "") + "<small>&nbsp;</small>";
  }
  function dueHtml(t) {
    var d = t.daysLeft;
    var txt = d < 0 ? T("Overdue since ", "Vencido desde el ") + fmtDate(t.dueDate) + T(" — call today and ask what you can still do", ": llame hoy y pregunte qué puede hacer todavía") :
      T("Due ", "Vence ") + fmtDate(t.dueDate) + " · " + (d === 0 ? T("today", "hoy") : d === 1 ? T("tomorrow", "mañana") : T("in " + d + " days", "en " + d + " días"));
    var hot = t.urgent || d < 0;
    return '<span class="' + (hot ? "urgent" : "") + '">' + (hot ? "⚑ " : "") + txt + "</span>";
  }
  function taskHtml(t) {
    var P = R.PILLARS[t.pillar];
    var done = !!state.done[t.id];
    return '<li class="task' + (done ? " done" : "") + '" style="--accent:' + P.accent + '">' +
      '<input class="check" type="checkbox" data-done="' + t.id + '" aria-label="' + T("Mark done: ", "Marcar como hecho: ") + esc(t.title) + '"' + (done ? " checked" : "") + ">" +
      '<div><div class="task-title">' + esc(t.title) + "</div>" +
      '<div class="task-meta"><span class="chip" style="background:color-mix(in srgb,' + P.accent + ' 14%, white);color:var(--navy-900)">' + P.app + "</span>" + dueHtml(t) + '<span class="muted">· ~' + t.effortMin + " min</span>" +
      (t.confidence === "likely" ? '<span class="chip green">' + T("Likely eligible", "Probablemente califica") + "</span>" : '<span class="chip">' + T("Worth checking", "Vale la pena revisar") + "</span>") + (t.organizer ? '<span class="chip navy">' + T("Organizer step", "Paso de organización") + "</span>" : "") + "</div>" +
      '<p class="task-why">' + esc(t.why) + "</p></div>" +
      '<div class="task-value">' + valueHtml(t) + "</div>" +
      '<div class="task-actions"><button type="button" class="btn btn-teal btn-small" data-open="' + t.id + '">' + T("Do it with me", "Hágalo conmigo") + "</button>" +
      '<button type="button" class="btn btn-ghost btn-small" data-learn="' + t.id + '">' + T("60-second lesson", "Lección de 60 segundos") + "</button>" +
      '<a class="btn btn-ghost btn-small" href="https://www.211.org" target="_blank" rel="noopener">' + T("Talk to a person ↗", "Hablar con una persona ↗") + "</a></div>" +
      "</li>";
  }

  function horizonBlocks(tasks) {
    var out = "";
    [[30, T("Next 30 days", "Próximos 30 días"), T("Deadlines and the fastest dollars", "Fechas límite y el dinero más rápido")], [60, T("Days 31–60", "Días 31 a 60"), T("Follow-through", "Seguimiento")], [90, T("Days 61–90", "Días 61 a 90"), T("Longer-term moves and organizing", "Pasos a largo plazo y organización")]].forEach(function (h) {
      var ts = tasks.filter(function (t) { return t.horizon === h[0]; });
      if (!ts.length) return;
      out += '<section class="horizon"><h3>' + h[1] + ' <span class="muted">' + h[2] + '</span></h3><ol class="task-list">' + ts.map(taskHtml).join("") + "</ol></section>";
    });
    return out || '<div class="empty">' + T("No steps here right now.", "No hay pasos aquí por ahora.") + "</div>";
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
    var oneTime = T(" one-time", " una vez");
    return '<aside class="sidebar" aria-label="' + T("Progress and settings", "Avance y ajustes") + '">' +
      '<div class="card tally"><p class="eyebrow dark">' + T("Saved so far", "Ahorrado hasta ahora") + '</p><div class="big">' + usd(savedM) + '<span class="small muted">' + T("/mo", "/mes") + "</span></div>" +
      (savedO ? '<div class="pot">+ ' + usd(savedO) + oneTime + "</div>" : "") +
      '<div class="meter" aria-hidden="true"><span style="width:' + pctBar + '%"></span></div>' +
      '<div class="pot">' + T("Plan potential: ", "Potencial del plan: ") + usd(plan.potential.monthly) + T("/mo", "/mes") + (plan.potential.oneTime ? " + " + usd(plan.potential.oneTime) + oneTime : "") + "</div>" +
      '<p class="small muted" style="margin:.5rem 0 0">' + T("Estimates. Check a step off when it's done.", "Son cálculos aproximados. Marque cada paso cuando lo termine.") + "</p></div>" +
      '<div class="card side-card"><h3>' + T("Weekly check-in", "Revisión semanal") + "</h3>" +
      (due ? '<p class="small">' + T("Two questions, one minute. ", "Dos preguntas, un minuto. ") + (last ? T("Last check-in " + daysSince + " days ago.", "Última revisión hace " + daysSince + " días.") : T("Your first one is due in a week — or do it now.", "La primera toca en una semana, o hágala ahora.")) + '</p><button class="btn btn-gold btn-small" type="button" id="checkinBtn">' + T("Check in", "Revisar") + "</button>" :
        '<p class="small">' + (ES ? "Última revisión " + (daysSince === 0 ? "hoy" : "hace " + daysSince + (daysSince > 1 ? " días" : " día")) + ". La próxima en " + (7 - daysSince) + " días." : "Last check-in " + (daysSince === 0 ? "today" : daysSince + " day" + (daysSince > 1 ? "s" : "") + " ago") + ". Next one in " + (7 - daysSince) + " days.") + '</p><button class="btn-link small" type="button" id="checkinBtn">' + T("Check in early", "Revisar antes") + "</button>") +
      "</div>" +
      '<div class="card side-card"><h3>' + T("Need a person?", "¿Necesita a una persona?") + '</h3><ul><li><a href="https://www.211.org" target="_blank" rel="noopener">' + T("Call 211", "Llame al 211") + "</a>" + T(" — local help, 24/7", ": ayuda local, a toda hora") + '</li><li><a href="https://www.lawhelp.org" target="_blank" rel="noopener">' + T("Free legal aid", "Ayuda legal gratis") + "</a></li><li>" + T("Trained community volunteers — ", "Voluntarios comunitarios capacitados: ") + '<span class="muted">' + T("joining in the pilot", "se suman en el piloto") + "</span></li></ul></div>" +
      '<div class="card side-card"><h3>' + T("Your data", "Sus datos") + '</h3><p class="small muted">' + T("Stored only in this browser. Export it, change it, or erase it.", "Se guardan solo en este navegador. Puede exportarlos, cambiarlos o borrarlos.") + '</p><div class="data-actions">' +
      '<button class="btn btn-ghost btn-small" type="button" id="editBtn">' + T("Edit answers", "Cambiar respuestas") + '</button><button class="btn btn-ghost btn-small" type="button" id="printBtn">' + T("Print plan", "Imprimir plan") + "</button>" +
      '<button class="btn btn-ghost btn-small" type="button" id="exportBtn">' + T("Export", "Exportar") + '</button><button class="btn btn-ghost btn-small" type="button" id="storyBtn">' + T("Share my story", "Compartir mi historia") + "</button>" +
      '<button class="btn btn-ghost btn-small" type="button" id="wipeBtn" style="border-color:var(--rose-600);color:var(--rose-700)">' + T("Erase everything", "Borrar todo") + "</button></div></div>" +
      "</aside>";
  }

  /* ---------- Views ---------- */
  function renderHome() {
    if (!state.profile) { renderIntake(); return; }
    var p = state.profile;
    view.innerHTML = '<div class="layout"><div>' +
      (p.sample ? '<div class="boundary" style="margin-bottom:1rem"><p><strong>' + T("You're viewing a sample household.", "Está viendo un hogar de ejemplo.") + '</strong> <button class="btn-link" type="button" id="startOwn">' + T("Start my own plan", "Empezar mi propio plan") + "</button></p></div>" : "") +
      '<div class="persona"><div class="persona-avatar" aria-hidden="true">🤝</div><div class="bubble"><div class="who">' + T("Here's what's going on", "Esto es lo que está pasando") + "</div><p>" + summarySentence(p) + "</p>" +
      '<p class="small muted">' + T("Ranked by deadline first, then by dollars saved per hour of your effort.", "Ordenado primero por fecha límite y después por el dinero que ahorra por cada hora de su esfuerzo.") + "</p></div></div>" +
      '<div class="dx-grid" aria-label="' + T("Summary by area", "Resumen por área") + '">' + Object.keys(R.PILLARS).map(function (k) {
        var P = R.PILLARS[k], d = plan.dx[k], s = STATUS[d.status];
        return '<button type="button" class="dx" style="--accent:' + P.accent + ';text-align:left;font:inherit;cursor:pointer" data-tab="' + k + '"><div class="name">' + P.app + '</div><div class="status"><span class="chip ' + s[0] + '">' + s[1] + "</span></div><p>" + esc(d.words) + "</p></button>";
      }).join("") + "</div>" +
      '<h2 style="margin-top:1.8rem">' + T("Your 30 / 60 / 90-day plan", "Su plan de 30 / 60 / 90 días") + "</h2>" + horizonBlocks(plan.tasks) +
      "</div>" + sidebarHtml() + "</div>";
    var so = $("#startOwn"); if (so) so.onclick = startOver;
  }

  var PILLAR_INFO = {
    food: { who: T("Households whose food or internet bill is the first thing to break each month; SNAP/WIC-eligible families not enrolled; anyone whose SNAP was cut.", "Hogares donde la comida o el internet es lo primero que falla cada mes; familias que califican para SNAP/WIC sin estar inscritas; quien haya perdido o visto reducido su SNAP."),
      job: T("Treat food security as a priority: understand the shortfall, plan a food budget that survives the month, connect to the local food system.", "Tomar la comida como prioridad: entender lo que falta, planear un presupuesto que dure el mes y conectarle con la red de comida local."),
      tools: [[T("Benefits screener", "Revisión de beneficios"), T("SNAP, WIC, school meals, Lifeline — with an estimated monthly amount", "SNAP, WIC, comidas escolares, Lifeline, con un monto mensual aproximado"), true], [T("Food-dollar planner", "Planificador del dinero para comida"), T("Two-week menu with a basic nutrition check", "Menú de dos semanas con una revisión básica de nutrición"), true], [T("Internet-bill clinic", "Ayuda con la factura de internet"), T("Lifeline, ISP low-income plans, downgrade script", "Lifeline, planes para bajos ingresos y guion para bajar de plan"), true], [T("Local food map", "Mapa local de comida"), T("Pantries, EBT match, community fridges with verified hours", "Despensas, EBT doble, refrigeradores comunitarios con horarios verificados"), false], [T("Price-shift alerts", "Alertas de precios"), T("Staples that moved most this month in your ZIP", "Productos básicos que más cambiaron este mes en su código postal"), false], [T("Essentials exchange", "Intercambio de artículos esenciales"), T("Diaper banks, buy-nothing groups, tool libraries", "Bancos de pañales, grupos de regalo, bibliotecas de herramientas"), false]],
      links: ["foodbank", "snapState", "wic", "lifeline", "l211"] },
    health: { who: T("Anyone facing a coverage lapse, a medical bill they can't pay, a prescription they're rationing, or a denied prior authorization.", "Quien esté por perder su seguro, tenga una cuenta médica que no puede pagar, esté racionando una receta o tenga una autorización previa negada."),
      job: T("Stop the two things that bankrupt families — losing coverage and paying list price — and teach you to read your own bills.", "Evitar las dos cosas que llevan a las familias a la quiebra (perder el seguro y pagar precio completo) y enseñarle a leer sus propias cuentas."),
      tools: [[T("Coverage triage", "Revisión de cobertura"), T("Medicaid renewal, Marketplace subsidy estimate, enrollment windows", "Renovación de Medicaid, ayuda aproximada del Mercado de Seguros y fechas de inscripción"), true], [T("Prescription cost cutter", "Reductor del costo de recetas"), T("Cash price, generic, 90-day, assistance programs", "Precio en efectivo, genéricos, 90 días y programas de ayuda"), true], [T("Bill reader + charity care", "Lector de cuentas + atención de caridad"), T("Financial-assistance request letter", "Carta para pedir ayuda financiera"), true], [T("Prior-auth appeal builder", "Apelación de autorización previa"), T("Appeal letter built around your plan's own criteria", "Carta de apelación basada en los criterios de su propio plan"), true], [T("Care-access map", "Mapa de acceso a atención"), T("Community health centers and sliding-scale clinics", "Centros de salud comunitarios y clínicas que cobran según ingresos"), true], [T("Upload a bill to decode it", "Suba una cuenta para entenderla"), T("Line-by-line explanation and No Surprises Act check", "Explicación línea por línea y revisión según la Ley Sin Sorpresas"), false]],
      guard: T("Navigation, not medical advice. No diagnosis, no dosing. If anyone has chest pain, trouble breathing, stroke signs, or thoughts of self-harm: call 911 or 988 now.", "Orientación, no consejo médico. Sin diagnósticos ni dosis. Si alguien tiene dolor de pecho, dificultad para respirar, señales de derrame cerebral o pensamientos de hacerse daño: llame ahora al 911 o al 988."),
      links: ["healthcare", "medicaid", "hrsa", "needymeds", "cfpbMed"] },
    housing: { who: T("Renters facing an increase or eviction notice, households paying over 40% of income on housing, and would-be owners who need a guide.", "Inquilinos con un aumento o un aviso de desalojo, hogares que pagan más del 40% de sus ingresos en vivienda, y quienes quieren comprar casa y necesitan una guía."),
      job: T("Stabilize first (keep you housed), then reduce cost, then build toward ownership. Tenant power is collective.", "Primero estabilizar (que conserve su vivienda), luego bajar el costo y después avanzar hacia ser dueño. La fuerza de los inquilinos es colectiva."),
      tools: [[T("Eviction prep for legal aid", "Preparación para la ayuda legal en un desalojo"), T("Legal-clock basics and what to gather today", "Lo básico de los plazos legales y qué reunir hoy"), true], [T("Rent-increase checker", "Revisión de aumentos de renta"), T("Statewide caps in CA, OR, WA + pushback letter", "Límites estatales en CA, OR y WA + carta de respuesta"), true], [T("Emergency rental assistance finder", "Buscador de ayuda de emergencia para la renta"), T("County, city, and charity programs", "Programas del condado, la ciudad y organizaciones benéficas"), true], [T("Affordable-unit watch", "Alertas de vivienda asequible"), T("BMR and LIHTC lotteries", "Sorteos de viviendas BMR y LIHTC"), true], [T("Tenant organizing kit", "Guía para organizar a inquilinos"), T("Survey, first-meeting agenda", "Encuesta y agenda para la primera reunión"), true], [T("ADU & first-home pathfinder", "Guía para ADU y primera vivienda"), T("Down-payment help, ADU feasibility", "Ayuda para el pago inicial y viabilidad de un ADU"), false]],
      guard: T("Navigation, not legal advice. For any notice or court paper, contact legal aid right away.", "Orientación, no consejo legal. Ante cualquier aviso o papel de la corte, comuníquese de inmediato con ayuda legal."),
      links: ["lawhelp", "hudRent", "l211"] },
    energy: { who: T("Households with a bill they can't cover, a shutoff notice, or a bill that jumped without explanation — including renters.", "Hogares con una factura que no pueden pagar, un aviso de corte o una factura que subió sin explicación, incluidos los inquilinos."),
      job: T("A shutoff is a health event. Prevent it, then lower the bill, then organize ratepayers.", "Un corte de servicio afecta la salud. Primero evitarlo, luego bajar la factura y después organizar a los clientes."),
      tools: [[T("Shutoff shield", "Protección contra cortes"), T("Medical certificate + payment-plan script", "Certificado médico + guion para pedir un plan de pagos"), true], [T("Assistance stack", "Orden de las ayudas"), T("Discount rate → LIHEAP → weatherization, in the right order", "Tarifa con descuento → LIHEAP → climatización, en el orden correcto"), true], [T("Bill decoder", "Lector de facturas"), T("Five things to check on your bill", "Cinco cosas que revisar en su factura"), true], [T("DIY energy check", "Revisión casera de energía"), T("Cheapest fixes first", "Primero los arreglos más baratos"), true], [T("Ratepayer organizer", "Organización de clientes"), T("Public-comment template for rate cases", "Modelo de comentario público para casos de tarifas"), true], [T("Rebate & credit finder", "Buscador de reembolsos y créditos"), T("Heat pumps, insulation, community solar", "Bombas de calor, aislamiento y energía solar comunitaria"), false]],
      links: ["liheap", "wap", "l211"] },
    family: { who: T("Working parents priced out of child care, the sandwich generation, anyone who needs leave, and seniors facing care costs.", "Padres que trabajan y no pueden pagar el cuidado infantil, quienes cuidan a hijos y a padres a la vez, quien necesite una licencia, y personas mayores con gastos de cuidado."),
      job: T("Caregiving is skilled work, done unpaid at home. Find and fund care, protect your job and health, and connect you with other caregivers.", "Cuidar es un trabajo con mucha habilidad, hecho sin pago en casa. Encontrar y pagar el cuidado, proteger su empleo y su salud, y conectarle con otros cuidadores."),
      tools: [[T("Child care subsidy stacker", "Combinador de subsidios para cuidado infantil"), T("State subsidy, Head Start, DCAP", "Subsidio estatal, Head Start y DCAP"), true], [T("Leave navigator", "Guía de licencias"), T("FMLA + state paid leave + request letter", "FMLA + licencia pagada del estado + carta de solicitud"), true], [T("Paid family caregiver finder", "Buscador de pago para familiares cuidadores"), T("IHSS and consumer-directed programs", "IHSS y programas dirigidos por el consumidor"), true], [T("Caregiver check-in", "Revisión para cuidadores"), T("Respite and support", "Respiro y apoyo"), true], [T("Elder care cost map", "Mapa de costos del cuidado de mayores"), T("In-home vs. adult day vs. assisted living, with Medicaid waivers", "En casa, centro de día o vivienda asistida, con exenciones de Medicaid"), false], [T("Care co-op builder", "Cooperativas de cuidado"), T("Shared nannies and babysitting swaps", "Niñeras compartidas e intercambio de cuidado"), false]],
      links: ["childcare", "headstart", "eldercare", "respite", "fmla"] },
    work: { who: T("Anyone who lost a job or had hours cut, is looking for a first job after school or training, wants training that leads to a raise, or was screened out, scheduled, or replaced by software.", "Quien perdió su trabajo o le redujeron las horas, busca su primer empleo después de los estudios o una capacitación, quiere una capacitación que lleve a un aumento, o fue descartado, programado o reemplazado por un programa de computadora."),
      job: T("Replace the paycheck fast, collect what you're owed, protect your coverage, and connect you to people — not bots — who can help: job centers, unions, legal aid, and training with a real employer at the end.", "Reemplazar el sueldo rápido, cobrar lo que le deben, proteger su cobertura y conectarle con personas, no con robots, que pueden ayudar: centros de empleo, sindicatos, asistencia legal y capacitación con un empleador real al final."),
      guard: T("Plain talk about AI. This tool is software with fixed rules and published sources: it doesn't hire, screen, rank, or monitor anyone, and nothing you type here is sent anywhere or used to train an AI. Every step below ends at a human office you can walk into. If you'd rather not use AI at all, print this page and start with the American Job Center and 211.", "Hablemos claro sobre la IA. Esta herramienta es un programa con reglas fijas y fuentes publicadas: no contrata, ni filtra, ni clasifica, ni vigila a nadie, y nada de lo que escribe aquí se envía a ningún lado ni se usa para entrenar una IA. Cada paso de abajo termina en una oficina con personas a la que puede ir. Si prefiere no usar IA para nada, imprima esta página y empiece por el American Job Center y el 211."),
      tools: [[T("Job-loss cascade", "Cadena de pasos tras perder el trabajo"), T("Unemployment, final pay, the 60-day coverage clock, and SNAP — with dates", "Desempleo, último cheque, el plazo de 60 días del seguro y SNAP, con fechas"), true], [T("What you're owed checklist", "Lista de lo que le deben"), T("Final paycheck, PTO, severance timing, WARN Act notice", "Último cheque, vacaciones, plazos del finiquito, aviso de la ley WARN"), true], [T("Free training finder", "Buscador de capacitación gratuita"), T("Apprenticeships, sectoral programs, SNAP E&T, Workforce Pell — with the evidence behind each", "Aprendizajes, programas sectoriales, SNAP E&T, Workforce Pell, con la evidencia de cada uno"), true], [T("First-job playbook", "Guía para el primer empleo"), T("For new graduates, including new nurses", "Para recién graduados, incluidas enfermeras y enfermeros nuevos"), true], [T("Rights letter: AI in hiring and firing", "Carta de derechos: IA en contrataciones y despidos"), T("Ask in writing whether a tool was used; where notice is required", "Pregunte por escrito si se usó una herramienta; dónde se exige aviso"), true], [T("Coworker organizing kit", "Guía para organizarse con compañeros"), T("Group letter and first conversations on AI, staffing and automation", "Carta en grupo y primeras conversaciones sobre IA, personal y automatización"), true], [T("Local hiring map", "Mapa local de contratación"), T("Employers near you hiring through job centers and apprenticeships", "Empleadores cerca de usted que contratan a través de centros de empleo y aprendizajes"), false], [T("Union and workers' center finder", "Buscador de sindicatos y centros de trabajadores"), T("By industry and ZIP, with contract language on AI", "Por industria y código postal, con lenguaje de contrato sobre la IA"), false]],
      links: ["ajc", "ui", "apprenticeship", "snapET", "eeoc", "nlrb", "lawhelp", "l211"] }
  };

  function renderPillar(k) {
    var P = R.PILLARS[k], I = PILLAR_INFO[k];
    var ts = plan ? plan.tasks.filter(function (t) { return t.pillar === k; }) : [];
    var d = plan && plan.dx[k];
    view.innerHTML = '<div class="layout"><div>' +
      '<div class="pillar-hero" style="--accent:' + P.accent + '"><p class="eyebrow dark">' + T("Pillar ", "Pilar ") + P.roman + " · " + R.pillarName(k) + "</p><h2>" + P.app + "</h2>" +
      (d ? '<p><span class="chip ' + STATUS[d.status][0] + '">' + STATUS[d.status][1] + "</span> " + esc(d.words) + "</p>" : "") +
      '<p class="small"><strong>' + T("Who it's for:", "Para quién es:") + "</strong> " + I.who + '</p><p class="small"><strong>' + T("Your community organizer's job here:", "Lo que hace aquí su organizador comunitario:") + "</strong> " + I.job + "</p>" +
      (I.guard ? '<div class="escalate"><strong>' + T("Guardrail:", "Límite:") + "</strong> " + I.guard + "</div>" : "") + "</div>" +
      (state.profile ? "<h3>" + T("Your steps", "Sus pasos") + "</h3>" + (ts.length ? '<ol class="task-list">' + ts.map(taskHtml).join("") + "</ol>" : '<div class="empty">' + T("Nothing urgent here based on your answers. ", "Nada urgente aquí según sus respuestas. ") + '<button class="btn-link" type="button" id="editBtn2">' + T("Update answers", "Actualizar respuestas") + "</button></div>") :
        '<div class="empty"><p>' + T("Answer a few questions to see your steps.", "Conteste unas preguntas para ver sus pasos.") + '</p><button class="btn btn-teal" type="button" data-tab="home">' + T("Start my plan", "Empezar mi plan") + "</button></div>") +
      '<h3 style="margin-top:1.6rem">' + T("Tools in ", "Herramientas de ") + P.app + '</h3><ul class="tool-list">' + I.tools.map(function (t) {
        return '<li><span class="t">' + t[0] + "</span>" + (t[2] ? '<span class="chip green">' + T("In this preview", "En esta versión") + "</span>" : '<span class="chip">' + T("Planned", "Planeado") + "</span>") + '<span class="d">' + t[1] + "</span></li>";
      }).join("") + "</ul>" +
      '<h3 style="margin-top:1.6rem">' + T("Trusted sources", "Fuentes confiables") + '</h3><div class="links">' + I.links.map(function (l) { return linkHtml(R.LINKS[l]); }).join("") + "</div>" +
      "</div>" + (plan ? sidebarHtml() : "") + "</div>";
    var e2 = $("#editBtn2"); if (e2) e2.onclick = editAnswers;
  }

  function renderPolicy() {
    var p = state.profile || {};
    var pl = plan || { pct: 0, burden: 0, tasks: [] };
    view.innerHTML = '<div class="layout"><div>' +
      '<div class="pillar-hero" style="--accent:var(--gold-500)"><p class="eyebrow dark">' + T("Policy Watch · preview", "Policy Watch · versión preliminar") + "</p><h2>" + T("What the Affordability Agenda would mean for you", "Lo que la Agenda de Asequibilidad significaría para usted") + "</h2>" +
      "<p>" + T("Your plan works on the next 30 days. These proposals work on the next 30 years. Here is each one translated into your household's stake", "Su plan trabaja en los próximos 30 días. Estas propuestas trabajan en los próximos 30 años. Aquí está lo que cada una significa para su hogar") + (state.profile ? "" : T(" — answer the intake to personalize this", ": conteste las preguntas para personalizarlo")) + ".</p>" +
      '<p class="small muted">' + T("Source: New Democrat Coalition, <em>Affordability Agenda: Restoring the American Dream</em>. Items are proposals, not law. Live bill tracking is planned; for current status, use Congress.gov.", "Fuente: New Democrat Coalition (Coalición Nuevos Demócratas, un grupo del Congreso), <em>Affordability Agenda: Restoring the American Dream</em>. Son propuestas, no leyes. Planeamos seguir las leyes en vivo; por ahora, consulte Congress.gov.") + "</p></div>" +
      '<div class="grid">' + R.POLICY.map(function (it) {
        var P = R.PILLARS[it.pillar];
        return '<article class="card policy-item" style="--accent:' + P.accent + '"><p class="eyebrow dark">' + P.app + T(" · Agenda ", " · Agenda ") + it.ref + "</p><h3>" + (ES ? it.itemEs : it.item) + '</h3><div class="stake"><strong>' + T("Your stake:", "Lo que significa para usted:") + "</strong> " + esc(it.stake(p, pl)) + "</div></article>";
      }).join("") + "</div>" +
      '<div class="card" style="margin-top:1rem"><h3>' + T("Make your numbers count", "Que sus números cuenten") + "</h3><p>" + T("Representatives hear abstractions all day. A real household budget is harder to ignore. Use \"Share my story\" to create a de-identified summary of your situation, then send it to your representative.", "Los representantes escuchan generalidades todo el día. El presupuesto real de un hogar es más difícil de ignorar. Use \"Compartir mi historia\" para crear un resumen anónimo de su situación y envíelo a su representante.") + '</p><div class="links">' + linkHtml(R.LINKS.rep) + linkHtml(R.LINKS.congress) + "</div>" +
      (state.profile ? '<p style="margin-top:1rem"><button class="btn btn-gold" type="button" id="storyBtn2">' + T("Create my de-identified story", "Crear mi historia anónima") + "</button></p>" : "") + "</div>" +
      "</div>" + (plan ? sidebarHtml() : "") + "</div>";
    var s2 = $("#storyBtn2"); if (s2) s2.onclick = openStory;
  }

  /* ---------- Tabs ---------- */
  function renderTabs() {
    var tabs = [["home", T("Household plan", "Plan del hogar"), "var(--gold-500)"]];
    Object.keys(R.PILLARS).forEach(function (k) { tabs.push([k, R.PILLARS[k].app, R.PILLARS[k].accent]); });
    tabs.push(["policy", "Policy Watch", "var(--navy-700)"]);
    tablist.innerHTML = tabs.map(function (t) {
      var c = plan && R.PILLARS[t[0]] ? plan.dx[t[0]].count : 0;
      var openC = plan && R.PILLARS[t[0]] ? plan.tasks.filter(function (x) { return x.pillar === t[0] && !state.done[x.id]; }).length : 0;
      return '<button role="tab" type="button" id="tab-' + t[0] + '" aria-controls="view" aria-selected="' + (currentTab === t[0]) + '" tabindex="' + (currentTab === t[0] ? 0 : -1) + '" data-tab="' + t[0] + '" style="--tab-accent:' + t[2] + '"><span class="dot"></span>' + t[1] + (c ? '<span class="count" aria-label="' + openC + T(" open steps", " pasos pendientes") + '">' + openC + "</span>" : "") + "</button>";
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
    var draft = R.draftFor(t.draft, state.profile, t);
    var escal = t.escalate === "legal" ? '<div class="escalate"><strong>' + T("Out of scope for an app:", "Fuera del alcance de una app:") + "</strong> " + T("legal deadlines. This prepares you for legal aid — please contact them today.", "los plazos legales. Esto le prepara para la ayuda legal: comuníquese con ellos hoy.") + ' <a href="https://www.lawhelp.org" target="_blank" rel="noopener">' + T("Find free legal aid ↗", "Buscar ayuda legal gratis ↗") + "</a></div>" :
      t.pillar === "health" ? '<div class="escalate"><strong>' + T("Navigation, not medical advice.", "Orientación, no consejo médico.") + "</strong> " + T("Never change how you take a medicine without your prescriber or pharmacist. Emergencies: 911 · Crisis: 988.", "Nunca cambie cómo toma un medicamento sin hablar con quien se lo recetó o con su farmacéutico. Emergencias: 911 · Crisis: 988.") + "</div>" : "";
    var body = escal +
      '<div class="lesson"><h3>' + T("The 60-second lesson", "La lección de 60 segundos") + "</h3><p>" + esc(t.lesson) + "</p></div>" +
      (lessonOnly ? "" :
        '<label for="draftText" class="label" style="font-weight:700;display:block;margin-bottom:.3rem">' + T("Your draft — edit anything, then copy, download, or print", "Su borrador: cambie lo que quiera y luego cópielo, descárguelo o imprímalo") + "</label>" +
        '<textarea id="draftText" class="draft">' + esc(draft) + "</textarea>" +
        '<div class="dlg-actions"><button class="btn btn-teal btn-small" type="button" id="copyDraft">' + T("Copy", "Copiar") + '</button><button class="btn btn-ghost btn-small" type="button" id="dlDraft">' + T("Download .txt", "Descargar .txt") + "</button>" +
        '<button class="btn btn-ghost btn-small" type="button" id="doneDraft">' + (state.done[t.id] ? T("Mark not done", "Marcar como pendiente") : T("Mark this step done", "Marcar este paso como hecho")) + "</button></div>") +
      (t.links && t.links.length ? '<h3 style="margin-top:1rem;font-size:1rem">' + T("Where to go", "Adónde ir") + '</h3><div class="links">' + t.links.map(linkHtml).join("") + "</div>" : "") +
      '<p class="source"><strong>' + T("Why this step:", "Por qué este paso:") + "</strong> " + esc(t.why) + "<br><strong>" + T("Rule source:", "Fuente de la regla:") + "</strong> " + esc(t.source || "") + T("", " (fuente oficial, en inglés)") + T(" · ruleset ", " · reglas ") + R.RULESET.version + "</p>" +
      (lessonOnly ? '<div class="dlg-actions"><button class="btn btn-teal btn-small" type="button" id="toDraft">' + T("Do it with me →", "Hágalo conmigo →") + "</button></div>" : "");
    openDialog(P.app + (lessonOnly ? T(" · Learn", " · Aprenda") : T(" · Do it with me", " · Hágalo conmigo")), t.title, body);
    var c = $("#copyDraft"); if (c) c.onclick = function () { copyText($("#draftText").value); };
    var dl = $("#dlDraft"); if (dl) dl.onclick = function () { download(t.id + ".txt", $("#draftText").value, "text/plain"); };
    var dn = $("#doneDraft"); if (dn) dn.onclick = function () { toggleDone(t.id); closeDialog(); };
    var td = $("#toDraft"); if (td) td.onclick = function () { openTask(id, false); };
  }

  function copyText(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function () { toast(T("Copied.", "Copiado.")); }, fallback); else fallback();
    function fallback() { var ta = $("#draftText") || $("#storyText"); if (ta) { ta.select(); try { document.execCommand("copy"); toast(T("Copied.", "Copiado.")); } catch (e) { toast(T("Select the text and copy it.", "Seleccione el texto y cópielo.")); } } }
  }
  function download(name, text, type) {
    var blob = new Blob([text], { type: type }); var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function toggleDone(id) {
    if (state.done[id]) delete state.done[id]; else state.done[id] = new Date().toISOString();
    save(); var y = window.scrollY; setTab(currentTab); window.scrollTo(0, y);
    toast(state.done[id] ? T("Nice work. Saved to your tally.", "¡Bien hecho! Se sumó a su total.") : T("Marked not done.", "Marcado como pendiente."));
  }

  /* ============================================================
     EVALUATE — weekly check-in + story bank (opt-in, local)
     ============================================================ */
  function openCheckin() {
    var open = plan.tasks.filter(function (t) { return !state.done[t.id]; });
    var body = '<form id="ciForm"><div class="field"><span class="label">' + T("1. Did the plan hold this week? Check anything that got done.", "1. ¿Funcionó el plan esta semana? Marque lo que ya hizo.") + '</span><div class="choices">' +
      (open.length ? open.slice(0, 8).map(function (t) { return choice("did", t.id, esc(t.title), false); }).join("") : "<p>" + T("Everything is checked off. 🎉", "Todo está marcado. 🎉") + "</p>") +
      choice("did", "_denied", T("Something was <strong>denied</strong> or we were waitlisted", "Algo fue <strong>negado</strong> o nos pusieron en lista de espera"), false) + "</div></div>" +
      '<div class="field"><span class="label">' + T("2. What changed?", "2. ¿Qué cambió?") + '</span><div class="choices">' +
      choice("changed", "none", T("Nothing big", "Nada importante"), true, "", "radio") + choice("changed", "income", T("Income or work changed", "Cambiaron los ingresos o el trabajo"), false, "", "radio") + choice("changed", "notice", T("A new bill, notice, or deadline", "Una nueva cuenta, aviso o fecha límite"), false, "", "radio") + choice("changed", "household", T("Someone moved in or out", "Alguien llegó o se fue del hogar"), false, "", "radio") +
      '</div></div><button class="btn btn-teal" type="submit">' + T("Save check-in", "Guardar revisión") + "</button></form>";
    openDialog(T("Evaluate", "Evaluar"), T("Weekly check-in", "Revisión semanal"), body);
    $("#ciForm").onsubmit = function (e) {
      e.preventDefault(); var f = new FormData(e.target); var did = f.getAll("did"); var changed = f.get("changed");
      did.forEach(function (id) { if (id[0] !== "_") state.done[id] = new Date().toISOString(); });
      state.checkins.push({ date: new Date().toISOString(), did: did, changed: changed }); save(); closeDialog();
      if (changed && changed !== "none") { toast(T("Let's update your answers and re-plan.", "Vamos a actualizar sus respuestas y rehacer el plan.")); editAnswers(changed === "income" ? 3 : changed === "household" ? 2 : 6); return; }
      setTab(currentTab);
      if (did.indexOf("_denied") !== -1) openDialog(T("Evaluate", "Evaluar"), T("A denial isn't the end", "Una negación no es el final"), T('<p>Denials and waitlists are exactly where programs fail households — and where a person helps most.</p><ul><li>Ask for the reason <strong>in writing</strong> and the deadline to appeal.</li><li>Most benefit denials can be appealed through a "fair hearing" — legal aid can help for free.</li><li>Call <a href="https://www.211.org" target="_blank" rel="noopener">211</a> for other programs while you wait.</li></ul><p class="small muted">With your permission, stories like yours show lawmakers where programs break. Use "Share my story" to create a de-identified summary.</p>',
        '<p>Las negaciones y las listas de espera son justo donde los programas les fallan a los hogares, y donde una persona ayuda más.</p><ul><li>Pida el motivo <strong>por escrito</strong> y la fecha límite para apelar.</li><li>La mayoría de las negaciones de beneficios se pueden apelar en una "audiencia imparcial" (fair hearing); la ayuda legal puede ayudarle gratis.</li><li>Llame al <a href="https://www.211.org" target="_blank" rel="noopener">211</a> para buscar otros programas mientras espera.</li></ul><p class="small muted">Con su permiso, historias como la suya les muestran a los legisladores dónde fallan los programas. Use "Compartir mi historia" para crear un resumen anónimo.</p>'));
      else toast(T("Check-in saved.", "Revisión guardada."));
    };
  }

  // The story is built in English always (it goes to representatives); in Spanish mode a Spanish copy comes first.
  function storyText(es) {
    var S = function (en, sp) { return es ? sp : en; };
    var p = state.profile; var pl = plan;
    var band = pl.pct <= 100 ? S("below the poverty line", "por debajo del nivel de pobreza") : pl.pct <= 200 ? S("between 100% and 200% of the poverty line", "entre el 100% y el 200% del nivel de pobreza") : pl.pct <= 400 ? S("between 200% and 400% of the poverty line", "entre el 200% y el 400% del nivel de pobreza") : S("above 400% of the poverty line", "por encima del 400% del nivel de pobreza");
    var lines = [];
    lines.push(S("A household of " + p.hhSize + " in " + stateName(p.state) + ", with income " + band + ".", "Un hogar de " + p.hhSize + (p.hhSize === 1 ? " persona" : " personas") + " en " + stateName(p.state) + ", con ingresos " + band + "."));
    var pressures = [];
    if (p.tenure === "rent" && pl.burden) pressures.push(S("rent that takes " + pl.burden + "% of income", "una renta que se lleva el " + pl.burden + "% de sus ingresos"));
    if (p.rentIncreasePct) pressures.push(S("a " + p.rentIncreasePct + "% rent increase", "un aumento de renta del " + p.rentIncreasePct + "%"));
    if (p.evictionNotice) pressures.push(S("an eviction notice", "un aviso de desalojo"));
    if (p.shutoff) pressures.push(S("a utility shutoff notice" + (p.medEquip ? " while relying on powered medical equipment" : ""), "un aviso de corte de servicio" + (p.medEquip ? " mientras dependen de equipo médico eléctrico" : "")));
    if (p.renewalDue) pressures.push(S("a Medicaid renewal deadline", "una fecha límite para renovar Medicaid"));
    if (p.uninsured) pressures.push(S("someone without health insurance", "alguien sin seguro médico"));
    if (num(p.medBill)) pressures.push(S("about ", "unos ") + usd(Math.round(num(p.medBill) / 100) * 100) + S(" in medical bills", " en cuentas médicas"));
    if (p.rxTrouble) pressures.push(S("prescriptions they struggle to afford", "recetas que les cuesta pagar"));
    if (p.paDenied) pressures.push(S("a denied prior authorization", "una autorización previa negada"));
    if (num(p.childcareCost)) pressures.push(S("child care costing about ", "cuidado infantil que cuesta unos ") + usd(Math.round(num(p.childcareCost) / 100) * 100) + S("/month", " al mes"));
    if (p.caringAdult) pressures.push(S("unpaid care for an adult family member", "el cuidado sin pago de un familiar adulto"));
    if (p.foodRunsOut) pressures.push(S("food that runs out before the end of the month", "comida que se acaba antes de fin de mes"));
    if (p.jobLoss) pressures.push(S("a lost job or cut hours" + (p.aiAffected ? ", with software or AI involved in the decision" : ""), "un trabajo perdido o menos horas" + (p.aiAffected ? ", con programas de computadora o IA de por medio" : "")));
    else if (p.aiAffected) pressures.push(S("being screened out or replaced by software or AI", "haber sido descartado o reemplazado por programas de computadora o IA"));
    if (p.newGrad) pressures.push(S("a new graduate still looking for a first job", "un recién graduado que todavía busca su primer empleo"));
    if (pressures.length) lines.push(S("This month they faced ", "Este mes enfrentaron ") + pressures.join(", ") + ".");
    var denied = state.checkins.some(function (c) { return c.did.indexOf("_denied") !== -1; });
    lines.push(S("Their plan found about " + usd(pl.potential.monthly) + "/month in help they may qualify for but weren't receiving", "Su plan encontró unos " + usd(pl.potential.monthly) + " al mes en ayuda para la que podrían calificar y que no recibían") + (denied ? S(", and at least one application was denied or waitlisted", ", y al menos una solicitud fue negada o quedó en lista de espera") : "") + ".");
    // Which agenda items touch this household: decided on the English stakes so the filter is language-independent.
    var lang = R.getLang(); R.setLang("en");
    var personal = R.POLICY.filter(function (x) { return /Your|You're|With \d|At \d|Rent is/.test(x.stake(p, pl)); });
    R.setLang(lang);
    lines.push(S("Policies on the Affordability Agenda that would change this household's budget: ", "Propuestas de la Agenda de Asequibilidad que cambiarían el presupuesto de este hogar: ") + personal.map(function (x) { return (es ? x.itemEs : x.item).toLowerCase(); }).slice(0, 4).join("; ") + ".");
    lines.push(S("\n(De-identified: no name, ZIP code, or contact details. Shared only if the household chooses to send it.)", "\n(Anónimo: sin nombre, código postal ni datos de contacto. Solo se comparte si el hogar decide enviarlo.)"));
    return lines.join(" ");
  }
  function openStory() {
    var text = ES ? storyText(true) + "\n\n— In English, to send to an English-speaking office —\n" + storyText(false) : storyText(false);
    openDialog(T("Story bank · opt-in", "Banco de historias · solo si usted quiere"), T("Share my story (de-identified)", "Compartir mi historia (anónima)"), "<p>" + T("This summary leaves out your name, ZIP code, exact income, and contact details. Nothing is sent anywhere — you choose whether to copy it to a representative, an organizer, or a reporter.", "Este resumen no incluye su nombre, código postal, ingresos exactos ni datos de contacto. No se envía a ningún lado: usted decide si lo copia para un representante, un organizador o un periodista. Abajo va también en inglés.") + "</p>" +
      '<textarea id="storyText" class="draft" style="min-height:200px">' + esc(text) + '</textarea><div class="dlg-actions"><button class="btn btn-teal btn-small" type="button" id="copyStory">' + T("Copy", "Copiar") + '</button><a class="btn btn-ghost btn-small" href="' + R.LINKS.rep.url + '" target="_blank" rel="noopener">' + T("Find my representative ↗", "Encontrar a mi representante ↗") + "</a></div>");
    $("#copyStory").onclick = function () { copyText($("#storyText").value); };
  }

  /* ---------- Data controls ---------- */
  function editAnswers(step) {
    state.draft = JSON.parse(JSON.stringify(state.profile || state.draft || {})); delete state.draft.sample;
    if (state.draft.intakeDate) {
      var elapsed = Math.max(0, Math.floor((Date.now() - new Date(state.draft.intakeDate)) / 86400000));
      ["renewalDays", "shutoffDays"].forEach(function (k) { var v = optNum(state.draft[k]); if (v !== null) state.draft[k] = Math.max(0, v - elapsed); });
      // "Days since the job ended" grows with time, unlike the countdowns above.
      ["jobEndDays", "coverageEndDays"].forEach(function (k) { var v = optNum(state.draft[k]); if (v !== null) state.draft[k] = v + elapsed; });
      delete state.draft.intakeDate;
    }
    state.profile = null; intakeStep = typeof step === "number" ? step : 0; save(); plan = null; setTab("home"); focusQ();
  }
  function startOver() { state = fresh(); save(); plan = null; intakeStep = 0; setTab("home"); }
  function wipe() {
    if (!confirm(T("Erase all your answers and progress from this browser? This can't be undone.", "¿Borrar todas sus respuestas y su avance de este navegador? No se puede deshacer."))) return;
    try { localStorage.removeItem(KEY); } catch (e) {}
    state = fresh(); plan = null; intakeStep = 0; setTab("home"); toast(T("Erased. Nothing remains on this device.", "Borrado. No queda nada en este aparato."));
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
  setTab(["home", "food", "health", "housing", "energy", "family", "work", "policy"].indexOf(h) !== -1 && h ? h : "home");
})();
