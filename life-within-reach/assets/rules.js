/* ============================================================
   Life Within Reach — benefits rules engine (screening only)
   ------------------------------------------------------------
   Every number here is a published rule with an effective date
   and a source. Eligibility math comes from these rules, never
   from free-text generation. Results are SCREENING ESTIMATES —
   the agency that runs each program makes the real decision.
   ============================================================ */
(function (global) {
  "use strict";

  var RULESET = {
    version: "2026.11-verified.2",
    reviewed: "2026-11-07",
    note: "Screening estimates from published federal rules, each checked against its primary source on 2026-11-07. WorkBridge (work, income and training) added in .2 with its own cited sources. States add their own rules on top; always confirm with the program."
  };

  /* ---------- Language ---------- */
  // English is the source of truth; Spanish sits beside it. tr(en, es) picks by the current language.
  var LANG = "en";
  function setLang(l) { LANG = l === "es" ? "es" : "en"; return LANG; }
  function tr(en, es) { return LANG === "es" && es != null ? es : en; }

  /* ---------- Reference tables (each with effective date + source) ---------- */

  var FPL = {
    effective: "2026-01-13",
    source: "HHS Poverty Guidelines 2026 (91 FR 1797, Jan 15, 2026); used by SNAP FY2027, WIC and school meals 2026–27, Lifeline, and ACA plan year 2027",
    contiguous: { base: 15960, per: 5680 },
    AK: { base: 19950, per: 7100 },
    HI: { base: 18360, per: 6530 }
  };

  var SNAP = {
    effective: "2026-10-01", expires: "2027-09-30",
    source: "USDA FNS SNAP FY2027 cost-of-living adjustments, 48 states & DC (snap-fy27maximumAllotments-deductions.pdf; snap-fy27MinimumAllotments.pdf). Since P.L. 119-21 (2025), LIHEAP receipt triggers the heating/cooling utility allowance only for households with an elderly or disabled member, and internet costs don't count as shelter costs",
    maxAllotment: [0, 306, 562, 808, 1023, 1217, 1463, 1616, 1841], // by household size 1–8
    perAdditional: 225,
    standardDeduction: [0, 217, 217, 217, 229, 268, 308],          // 6+ = 308
    shelterCap: 769,
    minBenefit: 25,
    earnedIncomeDeduction: 0.20,
    grossTestPct: 130,
    bbceTestPct: 200 // broad-based categorical eligibility used by many states
  };

  var ACA = {
    effective: "2026-11-01",
    source: "IRS Rev. Proc. 2026-26 (plan year 2027: required contribution up to 10.22% of income) and Rev. Proc. 2025-25 (2026: 9.96%). Enhanced ARPA/IRA credits ended after 2025 and had not been restored as of Nov 7, 2026, so credits again stop at 400% FPL. HealthCare.gov Open Enrollment for 2027: Nov 1, 2026–Jan 15, 2027 (Dec 15 for Jan 1 coverage); state-run exchanges may differ",
    minPct: 100, maxPct: 400, maxContributionPct: 10.22, maxContributionPctByYear: { 2026: 9.96, 2027: 10.22 },
    openEnrollment: { start: [11, 1], endForJan1: [12, 15], end: [1, 15] }
  };

  // Not adopted as of Oct 2026 (KFF; Medicaid.gov). No state has ended expansion via a trigger law.
  var NON_EXPANSION = ["AL", "FL", "GA", "KS", "MS", "SC", "TN", "TX", "WI", "WY"];
  // Partial adult coverage in non-expansion states (up to 100% FPL)
  var PARTIAL_ADULT_COVERAGE = {
    WI: "Wisconsin BadgerCare Plus covers adults without dependent children up to 100% of poverty (waiver through 2029)",
    GA: "Georgia Pathways covers adults up to 100% of poverty with a work or activity requirement; its status after Dec 31, 2026 is pending federal approval"
  };
  var PARTIAL_ADULT_COVERAGE_ES = {
    WI: "BadgerCare Plus de Wisconsin cubre a adultos sin hijos dependientes con ingresos de hasta el 100% del nivel de pobreza (exención vigente hasta 2029)",
    GA: "Georgia Pathways cubre a adultos con ingresos de hasta el 100% del nivel de pobreza si cumplen un requisito de trabajo o actividades; su continuidad después del 31 de diciembre de 2026 está pendiente de aprobación federal"
  };
  function partialAdultText(state) { return tr(PARTIAL_ADULT_COVERAGE[state], PARTIAL_ADULT_COVERAGE_ES[state]); }
  // Pregnancy Medicaid/CHIP limits below 200% FPL (KFF, Jan 2026). Median is 213%; all other states are 200% or higher.
  var PREGNANCY_LIMIT_BELOW_200 = { AZ: 161, FL: 196, HI: 196, ID: 138, KS: 171, MS: 199, MT: 162, ND: 175, OR: 190, SC: 199, SD: 138, UT: 144, WY: 159 };
  // Statewide rent caps. capByYear = published maximum for that calendar year; CA's varies by region (5% + regional CPI, never above 10%).
  var RENT_CAP_STATES = {
    CA: { law: "AB 1482 (Civil Code 1947.12): 5% + regional CPI, never more than 10%; most units over 15 years old", lawEs: "AB 1482 (Código Civil 1947.12): 5% + inflación regional (CPI), nunca más del 10%; la mayoría de las viviendas con más de 15 años", capByYear: {} },
    OR: { law: "ORS 90.323/90.324: 7% + CPI, never more than 10%; units under 15 years old are exempt", lawEs: "ORS 90.323/90.324: 7% + inflación (CPI), nunca más del 10%; las viviendas con menos de 15 años están exentas", capByYear: { 2026: 9.5, 2027: 10 } },
    WA: { law: "RCW 59.18.700–.710 (HB 1217, effective May 7, 2025): 7% + CPI, never more than 10%; no increase in the first 12 months; units 12 years old or newer are exempt", lawEs: "RCW 59.18.700–.710 (HB 1217, vigente desde el 7 de mayo de 2025): 7% + inflación (CPI), nunca más del 10%; sin aumentos en los primeros 12 meses; las viviendas de 12 años o menos están exentas", capByYear: { 2026: 9.683, 2027: 10 } }
  };
  function rentCapFor(state, year) {
    var c = RENT_CAP_STATES[state];
    if (!c) return null;
    return { law: c.law, local: tr(c.law, c.lawEs), cap: c.capByYear[year] || 10, published: !!c.capByYear[year] };
  }
  // State paid family & medical leave programs paying benefits as of Nov 2026 (Maryland FAMLI: benefits from Jan 2028)
  var PAID_LEAVE_STATES = {
    CA: "California Paid Family Leave (EDD)", NJ: "New Jersey Family Leave Insurance", RI: "Rhode Island Temporary Caregiver Insurance", NY: "New York Paid Family Leave",
    WA: "Washington Paid Family & Medical Leave", DC: "DC Paid Family Leave", MA: "Massachusetts PFML", CT: "Connecticut Paid Leave", OR: "Paid Leave Oregon",
    CO: "Colorado FAMLI", MN: "Minnesota Paid Leave", DE: "Delaware Paid Leave", ME: "Maine Paid Family and Medical Leave"
  };
  var DCAP_LIMIT = { effective: "2026-01-01", amount: 7500, amountMFS: 3750, source: "IRC §129 as amended by P.L. 119-21 §70404 (tax years after Dec 31, 2025); the employer's plan must be amended to allow the higher limit" };

  var STATES = [
    ["AL","Alabama"],["AK","Alaska"],["AZ","Arizona"],["AR","Arkansas"],["CA","California"],["CO","Colorado"],["CT","Connecticut"],
    ["DE","Delaware"],["DC","District of Columbia"],["FL","Florida"],["GA","Georgia"],["HI","Hawaii"],["ID","Idaho"],["IL","Illinois"],
    ["IN","Indiana"],["IA","Iowa"],["KS","Kansas"],["KY","Kentucky"],["LA","Louisiana"],["ME","Maine"],["MD","Maryland"],
    ["MA","Massachusetts"],["MI","Michigan"],["MN","Minnesota"],["MS","Mississippi"],["MO","Missouri"],["MT","Montana"],
    ["NE","Nebraska"],["NV","Nevada"],["NH","New Hampshire"],["NJ","New Jersey"],["NM","New Mexico"],["NY","New York"],
    ["NC","North Carolina"],["ND","North Dakota"],["OH","Ohio"],["OK","Oklahoma"],["OR","Oregon"],["PA","Pennsylvania"],
    ["RI","Rhode Island"],["SC","South Carolina"],["SD","South Dakota"],["TN","Tennessee"],["TX","Texas"],["UT","Utah"],
    ["VT","Vermont"],["VA","Virginia"],["WA","Washington"],["WV","West Virginia"],["WI","Wisconsin"],["WY","Wyoming"]
  ];

  /* ---------- Pillars ---------- */
  var PILLARS = {
    food:   { key: "food",   roman: "I",   app: "PantryPlan", name: "Groceries & essentials", nameEs: "Comida y artículos esenciales", accent: "var(--p-food)" },
    health: { key: "health", roman: "II",  app: "CareBridge", name: "Health care", nameEs: "Salud",            accent: "var(--p-health)" },
    housing: { key: "housing",   roman: "III", app: "HomeHold",   name: "Housing", nameEs: "Vivienda",                accent: "var(--p-home)" },
    energy: { key: "energy", roman: "IV",  app: "WattWise",   name: "Energy & utilities", nameEs: "Energía y servicios",     accent: "var(--p-energy)" },
    family: { key: "family", roman: "V",   app: "KinCare",    name: "Child care, elder care & leave", nameEs: "Cuidado infantil, de mayores y licencias", accent: "var(--p-family)" },
    // WorkBridge is English-only for now: its drafts, lessons and pillar page have no Spanish twin yet.
    work:   { key: "work",   roman: "VI",  app: "WorkBridge", name: "Work, income & training", nameEs: "Trabajo, ingresos y capacitación", accent: "var(--p-work)", englishOnly: true }
  };

  /* ---------- Links (official or long-standing nonprofit sources) ---------- */
  var L = {
    l211: { label: "211 — local help line", url: "https://www.211.org", labelEs: "211: línea de ayuda local" },
    benefitFinder: { label: "USA.gov benefit finder", url: "https://www.usa.gov/benefit-finder", labelEs: "Buscador de beneficios de USA.gov" },
    snapState: { label: "SNAP office in your state", url: "https://www.fns.usda.gov/snap/state-directory", labelEs: "Oficina de SNAP de su estado" },
    wic: { label: "How to apply for WIC", url: "https://www.fns.usda.gov/wic/wic-how-apply", labelEs: "Cómo solicitar WIC", urlEs: "https://www.fns.usda.gov/es/wic" },
    foodbank: { label: "Find your local food bank", url: "https://www.feedingamerica.org/find-your-local-foodbank", labelEs: "Encuentre su banco de alimentos" },
    lifeline: { label: "Lifeline (USAC)", url: "https://www.lifelinesupport.org", labelEs: "Lifeline (USAC)" },
    healthcare: { label: "HealthCare.gov", url: "https://www.healthcare.gov", labelEs: "CuidadoDeSalud.gov", urlEs: "https://www.cuidadodesalud.gov/es/" },
    medicaid: { label: "Medicaid & CHIP help by state", url: "https://www.medicaid.gov/about-us/where-can-people-get-help-medicaid-chip", labelEs: "Ayuda de Medicaid y CHIP por estado" },
    hrsa: { label: "Find a community health center", url: "https://findahealthcenter.hrsa.gov", labelEs: "Encuentre un centro de salud comunitario" },
    needymeds: { label: "NeedyMeds patient-assistance programs", url: "https://www.needymeds.org", labelEs: "NeedyMeds: programas de ayuda para medicamentos" },
    cfpbMed: { label: "CFPB: medical bills & debt", url: "https://www.consumerfinance.gov/consumer-tools/medical-debt/", labelEs: "CFPB: cuentas y deudas médicas" },
    lawhelp: { label: "LawHelp.org — free legal aid", url: "https://www.lawhelp.org", labelEs: "LawHelp.org: ayuda legal gratis" },
    hudRent: { label: "HUD rental help by state", url: "https://www.hud.gov/topics/rental_assistance", labelEs: "HUD: ayuda con la renta por estado" },
    liheap: { label: "LIHEAP energy help", url: "https://www.acf.hhs.gov/ocs/low-income-home-energy-assistance-program-liheap", labelEs: "LIHEAP: ayuda con la energía" },
    wap: { label: "Weatherization Assistance Program", url: "https://www.energy.gov/scep/wap/weatherization-assistance-program", labelEs: "Programa de Climatización (WAP)" },
    childcare: { label: "ChildCare.gov — find care & help paying", url: "https://childcare.gov", labelEs: "ChildCare.gov: encuentre cuidado y ayuda para pagarlo", urlEs: "https://www.childcare.gov/es" },
    headstart: { label: "Head Start locator", url: "https://eclkc.ohs.acf.hhs.gov/center-locator", labelEs: "Buscador de Head Start" },
    eldercare: { label: "Eldercare Locator", url: "https://eldercare.acl.gov", labelEs: "Eldercare Locator (personas mayores)" },
    respite: { label: "ARCH respite locator", url: "https://archrespite.org", labelEs: "ARCH: buscador de servicios de respiro" },
    fmla: { label: "FMLA (U.S. Dept. of Labor)", url: "https://www.dol.gov/agencies/whd/fmla", labelEs: "FMLA (Departamento de Trabajo)" },
    rep: { label: "Find your U.S. Representative", url: "https://www.house.gov/representatives/find-your-representative", labelEs: "Encuentre a su representante en el Congreso" },
    congress: { label: "Congress.gov bill tracker", url: "https://www.congress.gov", labelEs: "Congress.gov: seguimiento de leyes" },
    lifeline988: { label: "988 Suicide & Crisis Lifeline", url: "https://988lifeline.org", labelEs: "988: línea de crisis y suicidio (oprima 2 para español)" },
    // WorkBridge (English-only). Government or long-standing nonprofit sources; every one is a place staffed by people.
    ui: { label: "Unemployment benefits — your state's office (USA.gov)", url: "https://www.usa.gov/unemployment-benefits" },
    ajc: { label: "Find an American Job Center (free, in person)", url: "https://www.careeronestop.org/LocalHelp/AmericanJobCenters/find-american-job-centers.aspx" },
    jobTraining: { label: "USA.gov — job training programs", url: "https://www.usa.gov/job-training" },
    apprenticeship: { label: "Apprenticeship.gov — find a paid apprenticeship", url: "https://www.apprenticeship.gov/apprenticeship-job-finder" },
    snapET: { label: "SNAP Employment & Training (free training for SNAP households)", url: "https://www.fns.usda.gov/snap/et" },
    pell: { label: "Federal Pell Grant, including short Workforce Pell programs", url: "https://studentaid.gov/understand-aid/types/grants/pell" },
    yearup: { label: "Year Up United (ages 18–29, no degree needed)", url: "https://www.yearup.org" },
    perscholas: { label: "Per Scholas (free tech training)", url: "https://perscholas.org" },
    jobcorps: { label: "Job Corps (ages 16–24, free training with housing)", url: "https://www.jobcorps.gov" },
    warn: { label: "WARN Act — 60-day layoff notice (U.S. Dept. of Labor)", url: "https://www.dol.gov/agencies/eta/layoffs/warn" },
    cobra: { label: "COBRA — keeping job-based insurance (U.S. Dept. of Labor)", url: "https://www.dol.gov/agencies/ebsa/laws-and-regulations/laws/cobra" },
    whd: { label: "Unpaid wages or final pay — Wage and Hour Division", url: "https://www.dol.gov/agencies/whd" },
    eeoc: { label: "EEOC — file a discrimination charge", url: "https://www.eeoc.gov/how-file-charge-employment-discrimination" },
    nlrb: { label: "NLRB — your right to act together at work", url: "https://www.nlrb.gov/about-nlrb/rights-we-protect/your-rights" },
    formUnion: { label: "AFL-CIO — how to form a union", url: "https://aflcio.org/formaunion" },
    nnuAI: { label: "National Nurses United on AI in patient care", url: "https://www.nationalnursesunited.org/artificial-intelligence" },
    nrp: { label: "Nurse residency programs (AACN)", url: "https://www.aacnnursing.org/nurse-residency-program" },
    vaJobs: { label: "VA careers & employment help for veterans", url: "https://www.va.gov/careers-employment/" }
  };

  /* ---------- Helpers ---------- */
  function linkFor(l) { return { label: tr(l.label, l.labelEs), url: (LANG === "es" && l.urlEs) || l.url }; }
  function pillarName(k) { return PILLARS[k] ? tr(PILLARS[k].name, PILLARS[k].nameEs) : k; }
  function num(v) { var n = parseFloat(v); return isFinite(n) && n > 0 ? n : 0; }
  // A day count the person may leave blank: blank keeps the fallback, 0 means "today".
  function daysOr(v, fallback) { var n = parseFloat(v); return (v === null || v === undefined || v === "" || !isFinite(n)) ? fallback : Math.max(0, n); }
  function has(arr, v) { return Array.isArray(arr) && arr.indexOf(v) !== -1; }
  function round5(n) { return Math.round(n / 5) * 5; }

  function fplAnnual(size, state) {
    var t = state === "AK" ? FPL.AK : state === "HI" ? FPL.HI : FPL.contiguous;
    size = Math.max(1, size | 0);
    return t.base + t.per * (size - 1);
  }
  function fplPct(p) {
    var annual = num(p.income) * 12;
    return Math.round((annual / fplAnnual(p.hhSize, p.state)) * 100);
  }

  function snapEstimate(p) {
    var size = Math.max(1, p.hhSize | 0);
    var max = size <= 8 ? SNAP.maxAllotment[size] : SNAP.maxAllotment[8] + (size - 8) * SNAP.perAdditional;
    var gross = num(p.income);
    var stdDed = SNAP.standardDeduction[Math.min(size, 6)];
    // The 20% deduction applies only to earnings (wages, self-employment), not Social Security, unemployment or child support.
    var earned = (p.earnedIncome === null || p.earnedIncome === undefined || p.earnedIncome === "") ? gross : Math.min(gross, num(p.earnedIncome));
    var adjusted = Math.max(0, gross - SNAP.earnedIncomeDeduction * earned - stdDed);
    var shelterCosts = num(p.housingCost) + num(p.energyBill);
    var excess = Math.max(0, shelterCosts - adjusted / 2);
    if (!(num(p.seniors) > 0 || p.disability)) excess = Math.min(excess, SNAP.shelterCap);
    var net = Math.max(0, adjusted - excess);
    var benefit = Math.round(max - 0.3 * net);
    if (size <= 2) benefit = Math.max(benefit, SNAP.minBenefit);
    return Math.max(0, Math.min(benefit, max));
  }

  function addDays(d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; }
  function daysBetween(a, b) { return Math.round((b - a) / 86400000); }
  function startOfDay(d) { var x = new Date(d.getTime()); x.setHours(0, 0, 0, 0); return x; }

  function acaWindow(today) {
    var y = today.getFullYear(), m = today.getMonth() + 1, d = today.getDate();
    if (m === 11 || (m === 12 && d <= 15)) return { open: true, due: new Date(y, 11, 15), label: tr("Open Enrollment — enroll by Dec 15 for coverage starting Jan 1", "Inscripción Abierta: inscríbase antes del 15 de diciembre para tener cobertura desde el 1 de enero") };
    if (m === 12) return { open: true, due: new Date(y + 1, 0, 15), label: tr("Open Enrollment — final deadline Jan 15 (most states)", "Inscripción Abierta: fecha límite final el 15 de enero (en la mayoría de los estados)") };
    if (m === 1 && d <= 15) return { open: true, due: new Date(y, 0, 15), label: tr("Open Enrollment — final deadline Jan 15 (most states)", "Inscripción Abierta: fecha límite final el 15 de enero (en la mayoría de los estados)") };
    return { open: false, due: addDays(today, 60), label: tr("Outside Open Enrollment — you need a Special Enrollment Period (60 days from a qualifying event like losing coverage, moving, or a new baby)", "Fuera de la Inscripción Abierta: necesita un Período de Inscripción Especial (60 días desde un cambio como perder la cobertura, mudarse o tener un bebé)") };
  }

  /* ---------- Draft templates ("Do it with me") ---------- */
  function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
  function today() { return new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }); }
  function todayEs() { return new Date().toLocaleDateString("es-US", { year: "numeric", month: "long", day: "numeric" }); }
  var SIG = "\n\n[Your name]\n[Your address]\n[Your phone or email]";
  var SIG_ES = "\n\n[Su nombre]\n[Su dirección]\n[Su teléfono o correo electrónico]";
  // Federally funded programs must offer free language help (Civil Rights Act Title VI; ACA §1557).
  var INTERPRETER_ES = "Puede pedir un intérprete gratis: diga \"Spanish, please\" o \"Necesito un intérprete en español\".";

  var DRAFTS = {
    snap: function (p, t) {
      return "SNAP APPLICATION — WHAT TO HAVE READY\n\n" +
        "Apply today: the date your application is received is the date benefits start counting from.\n" +
        "You can submit a form with just your name, address, and signature to lock in that date, then finish the rest.\n\n" +
        "Bring or upload:\n" +
        "[ ] ID for the person applying\n[ ] Pay stubs for the last 30 days (everyone who works)\n" +
        "[ ] Rent or mortgage statement (you said about " + money(num(p.housingCost)) + "/mo)\n" +
        "[ ] A utility bill (heat or electric) — this raises your deduction\n" +
        "[ ] Child care or dependent care costs you pay\n" +
        (num(p.seniors) > 0 || p.disability ? "[ ] Medical costs over $35/mo for anyone 60+ or with a disability — these count too\n" : "") +
        "\nTHE INTERVIEW (usually by phone, within ~30 days)\n" +
        "Say: \"I'm calling about my SNAP interview. My household has " + p.hhSize + " people.\n" +
        "Our gross income is about " + money(num(p.income)) + " a month. We pay " + money(num(p.housingCost)) + " for housing\n" +
        "and about " + money(num(p.energyBill)) + " for utilities. Please make sure the utility allowance is applied.\"\n\n" +
        "If you miss the call, call back the same day and ask to reschedule — do not let the case close.\n" +
        "If you need help fast and have under $150 income this month, ask about EXPEDITED SNAP (7 days)." +
        (p.jobLoss ? "\n\nYOU SAID A JOB ENDED OR HOURS WERE CUT: say so in the application and give this month's actual income, not last month's.\n" +
          "Ask for an EXPEDITED screening. You qualify for benefits within 7 days if EITHER (a) this month's gross income is under $150 AND you have $100 or less in cash and bank accounts, OR (b) your rent or mortgage plus utilities is more than this month's income plus what you have in cash and bank accounts. The office decides; ask them to check.\n" +
          "If you are an adult without children at home, ask whether work rules apply to you and whether signing up for free SNAP Employment & Training satisfies them." : "");
    },
    wic: function (p) {
      return "WIC — CALL SCRIPT\n\n\"Hi, I'd like to schedule a WIC appointment. " +
        (p.pregnant ? "I'm pregnant" : "") + (p.pregnant && num(p.kidsUnder5) ? " and " : "") +
        (num(p.kidsUnder5) ? "I have " + p.kidsUnder5 + " child(ren) under 5" : "") +
        ". " + (has(p.benefits, "snap") || has(p.benefits, "medicaid") ? "We're already on SNAP/Medicaid, so I understand we're income-eligible automatically." : "Our household of " + p.hhSize + " earns about " + money(num(p.income)) + " a month.") +
        "\nWhat should I bring, and can the appointment be by phone or video?\"\n\n" +
        "Bring: ID, proof of address, proof of income (or your SNAP/Medicaid card), each child's immunization record if you have it.";
    },
    lifeline: function (p) {
      return "INTERNET BILL — CALL SCRIPT\n\n1) Lifeline: apply at lifelinesupport.org (National Verifier). Qualify through SNAP, Medicaid, SSI, or income at or below 135% of poverty.\n\n" +
        "2) Call your internet provider and say:\n\"I'm calling to lower my bill. I currently pay about " + money(num(p.internetBill)) + " a month.\n" +
        "I " + (has(p.benefits, "snap") || has(p.benefits, "medicaid") ? "receive SNAP/Medicaid" : "have a low income") + ". What low-income plans do you offer?\n" +
        "Can you also remove any equipment rental fees and tell me if I'm paying for speed I don't need?\"\n\n" +
        "3) If they say no: \"Please transfer me to the retention department — I'm considering cancelling.\"\n\n" +
        "Write down: the plan name, new price, confirmation number, and the rep's first name.";
    },
    foodweek: function (p) {
      var n = Math.max(1, p.hhSize | 0);
      return "TWO-WEEK FOOD PLAN — HOUSEHOLD OF " + n + "\n(Built for health: protein at every meal, watch the sodium, fiber to stay full.)\n\n" +
        "PANTRY DAY: pick one food bank or pantry and put it on your calendar every week.\n\n" +
        "BUY ONCE, COOK TWICE\n" +
        "• Dry beans or lentils (cheapest protein per serving; rinse canned beans to cut sodium ~40%)\n" +
        "• Eggs, plain oats, brown rice, frozen vegetables (as nutritious as fresh, no waste)\n" +
        "• One whole chicken or family-pack thighs → roast, then soup from the bones\n" +
        "• Bananas, apples, carrots, cabbage — longest-lasting produce per dollar\n\n" +
        "WEEK 1: Mon bean chili · Tue chili over rice · Wed egg fried rice + frozen veg · Thu roast chicken + cabbage\n" +
        "        Fri chicken soup · Sat lentil curry · Sun leftovers + oatmeal pancakes\n" +
        "WEEK 2: repeat with swaps — black beans for kidney, sweet potato for rice.\n\n" +
        "IF SOMEONE HAS DIABETES: fill half the plate with non-starchy vegetables, keep rice/potato to a fist-size portion.\n" +
        "IF SOMEONE HAS HIGH BLOOD PRESSURE: choose 'no salt added' cans and season with garlic, lemon, vinegar, cumin.\n\n" +
        "SNAP/EBT DOUBLERS: ask your farmers market about EBT matching (e.g., Market Match in California).";
    },
    renew: function (p) {
      return "MEDICAID / CHIP RENEWAL — DON'T LET IT LAPSE\n\n" +
        "[ ] Find the renewal packet (envelope or online account). Note the due date: ______\n" +
        "[ ] Update your address and phone so you get every notice\n[ ] Upload last 30 days of pay stubs for everyone who works\n" +
        "[ ] Sign and submit — online is fastest; keep the confirmation number\n" +
        "[ ] If you were cut off for 'paperwork' reasons, you usually have 90 days to turn it in and be reinstated without reapplying\n\n" +
        "COMING JAN 1, 2027: adults covered through Medicaid expansion will renew every 6 months, and most will need to show work, school, volunteering or caregiving hours (with exemptions). Ask your Medicaid office which rules apply to you and when.\n\n" +
        "CALL SCRIPT: \"I'm calling to confirm you received my Medicaid renewal for case number ______.\n" +
        "Is anything missing? Can you note on my case that I submitted on " + today() + "?\"";
    },
    coverage: function (p, t) {
      var w = acaWindow(new Date());
      return "GETTING COVERED\n\n" + w.label + ".\n\n" +
        (t.meta && t.meta.route === "gap" ?
          "Based on your state and income, a subsidized plan or Medicaid may not be available to you right now.\n" +
          "You can still get care at lower cost:\n" +
          "• Community health centers (findahealthcenter.hrsa.gov) charge on a sliding scale by income — call and ask for a new-patient visit.\n" +
          (PARTIAL_ADULT_COVERAGE[p.state] && t.meta.pct <= 100 ? "• " + PARTIAL_ADULT_COVERAGE[p.state] + ". Ask your state Medicaid office.\n" : "") +
          "• Ask any nonprofit hospital for its financial assistance policy BEFORE a planned visit.\n" +
          "• Children and pregnant people often qualify for Medicaid/CHIP at higher incomes — apply for them separately.\n" +
          "• Recheck if your income, household, or state changes — eligibility can change mid-year.\n" :
        t.meta && t.meta.route === "medicaid" ?
          "Based on your income, Medicaid looks likely. You can apply ANY time of year — there's no enrollment window.\nApply through your state Medicaid agency or HealthCare.gov (it will route you).\n" :
          "Based on your income (about " + t.meta.pct + "% of the poverty line), you may get a premium tax credit.\n" +
          "Rough ceiling for a benchmark silver plan: about " + money(t.meta.maxPremium) + "/mo for your household.\n" +
          (t.meta.pct <= 250 ? "At your income, choose a SILVER plan — it comes with lower deductibles (cost-sharing reductions).\n" : "")) +
        "\nHave ready: income estimate for next year, Social Security numbers for people applying (not for others in the household), current coverage info.\n" +
        "Free local help: search 'navigator' at HealthCare.gov — navigators can't charge you or sell you anything.\n" +
        "Eligibility rules for some groups changed for 2027; a navigator can check your situation confidentially.";
    },
    rx: function (p) {
      return "PRESCRIPTION COST — QUESTIONS THAT SAVE MONEY\n\n" +
        "Ask the PHARMACIST:\n• \"What's the cash price vs. my insurance price? Is a discount card cheaper?\"\n" +
        "• \"Is this on a $4 or low-cost generic list here?\"\n• \"Would a 90-day supply or mail order be cheaper per month?\"\n\n" +
        "Ask the PRESCRIBER (by portal message is fine):\n• \"Cost is making it hard for me to take this as prescribed. Is there a generic or a\n" +
        "  lower-cost option in the same class that would work for me?\"\n• \"Can you check if the manufacturer has a patient-assistance program?\"\n\n" +
        "INSULIN: Medicare caps covered insulin at $35/month. Lilly, Novo Nordisk and Sanofi each run $35/month programs (Sanofi's includes Medicare);\n" +
        "  some programs must be renewed each January, so re-check terms for 2027.\n\n" +
        "SAFETY: never stop, split, or skip a medicine to save money without talking to your prescriber or pharmacist first.";
    },
    charity: function (p, t) {
      return today() + "\n\nFinancial Assistance Office\n[Hospital name and address]\n\nRe: Request for financial assistance — Account # ______\n\n" +
        "To whom it may concern,\n\nI am requesting financial assistance (charity care) under your hospital's Financial Assistance Policy for the bill above, " +
        "totaling " + money(num(p.medBill)) + ".\n\nMy household has " + p.hhSize + " people and our income is about " + money(num(p.income)) +
        " per month, which is roughly " + t.meta.pct + "% of the federal poverty guideline.\n\n" +
        "Please:\n1. Send me your financial assistance application and plain-language summary.\n" +
        "2. Place this account on hold from collections while my application is reviewed.\n" +
        "3. Confirm in writing that no extraordinary collection actions will be taken during review.\n\n" +
        "Thank you." + SIG + "\n\n— NOTE: Nonprofit hospitals can't use extraordinary collection actions (lawsuits, credit reporting) for at least 120 days after the first bill, and must pause them once you apply. Apply within 240 days of the first bill.\n— NOTE: Nonprofit hospitals must have a written financial assistance policy (IRS §501(r)). You generally have at least 240 days from the first bill to apply.";
    },
    pa: function (p) {
      return today() + "\n\n[Health plan name] — Appeals Department\n[Address or fax from the denial letter]\n\n" +
        "Re: Request for internal appeal — Member ID ______ — Claim/Reference # ______\n\n" +
        "I am appealing the denial of prior authorization for [service or medication] ordered by [prescriber name] on [date].\n\n" +
        "1. WHAT WAS DENIED AND WHY: The plan stated [copy the reason from the letter].\n" +
        "2. WHY IT IS MEDICALLY NECESSARY: [Ask your prescriber's office for a letter of medical necessity. Key points: diagnosis,\n" +
        "   symptoms and how they affect daily life, treatments already tried and why they failed or weren't tolerated.]\n" +
        "3. HOW IT MEETS THE PLAN'S OWN CRITERIA: [Request the plan's clinical criteria in writing — you have a right to it — and\n" +
        "   address each point.]\n4. REQUEST: Please overturn the denial. If my health could be seriously harmed by waiting, I request an EXPEDITED appeal.\n\n" +
        "Enclosed: denial letter, prescriber's letter, relevant records." + SIG +
        "\n\n— ALSO ASK the ordering office to request a PEER-TO-PEER review with the plan's medical director. It's often the fastest route.";
    },
    eviction: function (p) {
      return "EVICTION NOTICE — PREPARE FOR LEGAL AID (TODAY)\n\nThis is navigation, not legal advice. Deadlines can be very short — sometimes 3–5 days.\n\n" +
        "1. Do NOT ignore court papers. If you got a summons/complaint, there is a deadline to respond — missing it can mean losing automatically.\n" +
        "2. Call legal aid now (lawhelp.org or 211). Say: \"I received an eviction notice on [date]. It says [type: pay or quit / court summons].\n   I need help before [deadline on notice].\"\n" +
        "3. Gather: the notice (photo of every page), your lease, rent receipts or bank records, texts/emails with the landlord, photos of any repair problems.\n" +
        "4. Keep paying what you can and get a receipt — or ask legal aid whether to hold it.\n" +
        "5. Apply for emergency rental assistance at the same time (see next step).\n\nNever leave your home because of a notice alone — only a court order and a sheriff/marshal can remove you.";
    },
    rentIncrease: function (p, t) {
      var yr = new Date().getFullYear();
      var c = rentCapFor(p.state, yr);
      var cite = c ? c.law.split(":")[0] : null;
      var limit = c ? (c.published ? c.cap + "% for " + yr : c.law.split(":")[1].split(";")[0].trim()) : null;
      return today() + "\n\nDear [Landlord/Property manager],\n\nI received notice of a rent increase of " + num(p.rentIncreasePct) + "% for [address], effective [date].\n\n" +
        (c ? "Under " + cite + ", annual rent increases on covered units are limited (" + limit + "). My understanding is that this increase exceeds the allowed amount. Please confirm whether my unit is exempt, and if not, revise the increase to the lawful maximum.\n\n" :
          "I've been a reliable tenant and I'd like to stay. I'm asking you to reconsider and limit the increase to [X]% — turnover, vacancy and re-leasing usually cost more than a smaller raise.\n\n") +
        "I'm glad to discuss.\n" + SIG + "\n\n— Check local rules too: some cities have stricter rent control than the state. Legal aid or a tenant union can confirm.";
    },
    erap: function (p) {
      return "EMERGENCY RENTAL ASSISTANCE — CHECKLIST\n\nCall 211 and say: \"I need emergency rental assistance. I'm behind on rent" + (p.evictionNotice ? " and I've received an eviction notice" : "") + ".\nWhat programs are open in my county right now?\"\n\n" +
        "Also ask about: county/city programs · Salvation Army / Catholic Charities / St. Vincent de Paul · utility-inclusive help.\n\n" +
        "Have ready: ID, lease, the ledger or notice showing what's owed, proof of income, landlord's contact info (many programs pay the landlord directly).";
    },
    affordable: function (p) {
      return "AFFORDABLE HOUSING WATCH — SET UP ONCE\n\n[ ] Search your city/county housing department for 'below market rate' (BMR) or 'affordable housing lottery'\n" +
        "[ ] Sign up for alerts; most lotteries close in 2–4 weeks\n[ ] Ask your local housing authority if Housing Choice Voucher waitlists are open\n" +
        "[ ] Keep a folder ready: IDs, last 3 months of pay stubs, tax return, bank statements — lotteries move fast\n" +
        "[ ] LIHTC properties: call properties directly and ask for their waitlist";
    },
    tenantOrg: function (p) {
      return "TENANT ORGANIZING — FIRST MEETING\n\nYou are not the only one. Rent increases and repairs are building-wide problems.\n\n" +
        "1. Two-question survey for neighbors: \"Did your rent go up? What repairs are you waiting on?\"\n" +
        "2. Meet in a public place or someone's home. Agenda: introductions (10 min), what we're facing (15), one thing we'll ask for together (15), who does what (10).\n" +
        "3. Contact your local tenant union or legal aid — many help form tenant associations.\n" +
        "4. In most places, retaliating against tenants for organizing is illegal.";
    },
    shutoff: function (p) {
      return "SHUTOFF NOTICE — CALL THE UTILITY TODAY\n\n\"I'm calling about a disconnection notice on account # ______.\n" +
        (p.medEquip ? "Someone in my household uses medical equipment that needs power [CPAP / oxygen / refrigerated medication].\nI'm requesting a medical certificate / life-support hold on this account. What form does my clinician need to sign?\n" : "") +
        "I'd like to set up a payment arrangement I can actually keep. I can pay $____ now and $____ per month.\n" +
        "Please note on my account that I'm applying for LIHEAP and your low-income discount.\"\n\n" +
        "ASK: \"Are there any winter or heat-wave shutoff protections in effect?\" (Many states have them.)\n" +
        "Write down: name, date, confirmation #, new due date.\n\n" +
        (p.medEquip ? "TIP: most utilities accept a form signed by a physician, NP, or PA. Call the prescriber's office today and say it's to prevent a shutoff." : "");
    },
    liheap: function (p) {
      return "LIHEAP — ENERGY ASSISTANCE\n\nCall 211 or your local Community Action Agency: \"I'd like to apply for LIHEAP energy assistance. I have a" + (p.shutoff ? " shutoff notice — is crisis assistance available?" : "n energy bill I can't keep up with.") + "\"\n\n" +
        "Have ready: ID, Social Security numbers for household members who have them, last 30 days of income, your most recent utility bill.\n\n" +
        "ORDER MATTERS: apply for the utility discount rate first (it lowers every bill), then LIHEAP (one-time credit), then weatherization (lasting savings). Funding is first-come, first-served in many states — apply early.";
    },
    discount: function (p) {
      return "LOW-INCOME UTILITY RATE — CALL SCRIPT\n\n\"I'd like to enroll in your low-income discount program.\n" +
        (p.state === "CA" ? "In California that's CARE (30–35% off electric, 20% off gas, up to 200% of poverty), or FERA (18% off electric, 200–250% of poverty, for PG&E, SCE and SDG&E customers). " : "") +
        "Our household has " + p.hhSize + " people and earns about " + money(num(p.income)) + " a month.\n" +
        "Can you also check whether a different rate plan would cost me less based on my last 12 months of usage?\"\n\n" +
        "Many utilities let you enroll online in 5 minutes. Enrollment is often self-certified, with income verification later.";
    },
    rateplan: function (p) {
      return "READ YOUR BILL — 5 THINGS TO CHECK\n\n1. RATE PLAN NAME (e.g., time-of-use vs. tiered). If you're home during peak hours (often 4–9 pm), time-of-use can cost more.\n" +
        "2. USAGE vs. LAST YEAR — a jump with no lifestyle change can mean a meter error or a failing appliance (old fridge, space heater).\n" +
        "3. FIXED CHARGES — the part you pay no matter what.\n4. ESTIMATED READING? — if it says 'estimated', ask for an actual read.\n" +
        "5. DISCOUNT LINE — if you don't see a low-income discount, you're not enrolled.\n\n" +
        "Ask the utility: \"Can you run a rate comparison on my last 12 months?\" — most can, for free.";
    },
    weatherize: function (p) {
      return "WEATHERIZATION + 20-MINUTE DIY CHECK\n\nApply for free weatherization through the Weatherization Assistance Program (income up to 200% of poverty in most states; renters can qualify with landlord permission).\n\n" +
        "DIY, cheapest first:\n[ ] Weatherstrip and door sweeps (under $20)\n[ ] Window plastic film for winter\n[ ] Set water heater to 120°F\n[ ] LED bulbs in the 5 most-used lights\n" +
        "[ ] Unplug a second fridge or freezer if it's old\n[ ] Clean/replace furnace filter\n\nSkip expensive window replacements until the cheap fixes are done.";
    },
    ratepayer: function (p) {
      return "PUBLIC COMMENT TO YOUR UTILITY COMMISSION — TEMPLATE\n\nTo the [State] Public Utilities Commission, re: [Utility] rate case [docket #]:\n\n" +
        "My name is [first name] and I live in [city]. My household pays about " + money(num(p.energyBill)) + " a month for energy, which is about " +
        (num(p.income) ? Math.round(num(p.energyBill) / num(p.income) * 100) : "__") + "% of our income.\n\n" +
        "I ask the Commission to [protect residential customers from costs driven by large new loads such as data centers / expand low-income discounts / reject the proposed increase].\n\n" +
        "Thank you for considering households like mine." + "\n\n[First name, city]";
    },
    childcare: function (p) {
      return "CHILD CARE — SUBSIDY + FINDER CHECKLIST\n\n1. Apply for your state's child care assistance (CCDF-funded). Search '[your state] child care assistance' or use ChildCare.gov.\n" +
        (p.state === "CA" ? "   In California: CalWORKs Stages 1–3 or Alternative Payment Programs via your local Resource & Referral agency.\n" : "") +
        (num(p.kidsUnder5) && fplPct(p) <= 130 ? "2. Head Start / Early Head Start: free for families at or below poverty and for children in foster care or experiencing homelessness — apply now, waitlists are common.\n" : "2. Ask your local Resource & Referral agency for providers with REAL openings this month.\n") +
        "3. Have ready: proof of work/school schedule, pay stubs, child's birth certificate, immunization record.\n" +
        "4. Ask every provider: \"Do you accept subsidy? Is there a sibling discount? What's your waitlist?\"\n\n" +
        "Current cost you entered: " + money(num(p.childcareCost)) + "/mo.";
    },
    dcap: function (p) {
      return "DEPENDENT CARE FSA (DCAP) — EMAIL TO HR\n\nSubject: Dependent care FSA enrollment\n\nHi [HR],\nDoes our benefits plan include a Dependent Care Assistance Program (dependent care FSA)? If so, what are the open-enrollment dates and how do I enroll?\nI pay about " +
        money(num(p.childcareCost)) + " a month for child care.\n\nThanks,\n[Your name]\n\n— The household limit is $" + DCAP_LIMIT.amount.toLocaleString() + "/year starting 2026 ($" + DCAP_LIMIT.amountMFS.toLocaleString() + " if married filing separately), but only if your employer updated its plan. Money goes in pre-tax, so you save your tax rate on every dollar.\n" +
        "— You can't use the same dollars for both DCAP and the Child and Dependent Care Credit — a tax preparer (free VITA sites) can help pick the mix.";
    },
    leave: function (p) {
      var st = PAID_LEAVE_STATES[p.state];
      return today() + "\n\nDear [Manager/HR],\n\nI am requesting leave beginning [date] for approximately [number] weeks to [care for my family member with a serious health condition / bond with my new child / recover from my own serious health condition].\n\n" +
        "Please let me know whether this qualifies under the Family and Medical Leave Act" + (st ? " and " + st : "") + ", and send me any certification forms you need. I will return the completed certification within 15 days.\n\nThank you." + SIG +
        "\n\n— FMLA: job-protected, unpaid, up to 12 weeks if your employer has 50+ employees nearby and you've worked 1,250 hours in the past year.\n" +
        (st ? "— " + st + " can replace part of your wages; you usually apply to the STATE, not your employer.\n" :
          p.state === "MD" ? "— Maryland FAMLI starts paying benefits in January 2028; until then ask about employer short-term disability or paid time off.\n" :
          "— Your state doesn't have a statewide paid leave program as of this review; ask about employer short-term disability or paid time off.\n") +
        "— TIP for the certification form: ask the clinician to describe how often care is needed, for how long, and why — vague forms get rejected.";
    },
    caregiverPay: function (p) {
      return "GET PAID FOR CARE YOU ALREADY GIVE — CALL SCRIPT\n\nCall your Area Agency on Aging (Eldercare Locator: 1-800-677-1116) or your state Medicaid office:\n" +
        "\"I care for my [relationship], who needs help with [bathing, meals, medications, getting around]. Are there programs that pay family caregivers — like " +
        (p.state === "CA" ? "IHSS (In-Home Supportive Services)" : "consumer-directed home care under Medicaid") + "? Also, what respite care and adult day programs are available?\"\n\n" +
        "Also ask about: Medicaid home- and community-based services (HCBS) waivers · PACE · VA Aid & Attendance (if a veteran) · state caregiver tax credits.\n\n" +
        (p.state === "CA" ? "IHSS lets you hire a family member or friend. Spouses and parents of minor children can be paid only in certain circumstances.\n\n" : "") +
        "Write down every agency name, person, and date — these programs often take several calls.";
    },
    respite: function (p) {
      return "CAREGIVER CHECK-IN — FOR YOU\n\nCaregiving is skilled work, done unpaid at home. Your health counts too.\n\nThis week:\n[ ] One 2-hour break covered by someone else (family, friend, respite program)\n" +
        "[ ] Write the medication list in one place and share it with a backup person\n[ ] Find one caregiver support group (in person or online)\n[ ] Book your own overdue check-up\n\n" +
        "If you feel hopeless or think about harming yourself: call or text 988, any time.";
    },

    /* ----- VI. WorkBridge (English-only). Every draft points to an office with people in it. ----- */
    ui: function (p) {
      var since = p.jobEndDays === null || p.jobEndDays === undefined ? null : Math.round(num(p.jobEndDays));
      return "FILE FOR UNEMPLOYMENT — THIS WEEK\n\n" +
        "Why now: unemployment insurance pays from the week you FILE, not from the day the job ended. Every week you wait is a week you don't get back.\n" +
        (since !== null && since > 7 ? "You said the job ended about " + since + " days ago, so file today.\n" : "") +
        "You paid into this through every paycheck. It is insurance, not charity.\n\n" +
        "WHERE: your state's unemployment office (file in the state where you WORKED, even if you live elsewhere). Online, by phone, or in person at an American Job Center — a person can walk you through it for free.\n\n" +
        "HAVE READY:\n[ ] Social Security number (asked by the state office only — never by this app)\n[ ] Employer names, addresses and dates for the last 18 months\n" +
        "[ ] Last pay stubs; the reason the job ended, in your own words\n[ ] Bank account for direct deposit (or ask for a debit card)\n[ ] Alien registration number if you are not a U.S. citizen — the office asks; we never do\n\n" +
        "WHAT TO EXPECT:\n• Most states replace about half of your prior wages, up to a weekly cap, for up to 26 weeks (some states fewer).\n" +
        "• Hours cut, not lost? Ask about PARTIAL unemployment. You can often get a reduced check while working fewer hours.\n" +
        "• Quit or fired? File anyway. Many denials are overturned on appeal — \"good cause\" and \"misconduct\" are legal terms with narrow meanings.\n" +
        "• You must usually be looking for work and keep a simple log of it. Write every application down: date, employer, position, how you applied.\n" +
        "• Severance may delay benefits in some states. File anyway; let the office decide.\n\n" +
        "IF DENIED: appeal in writing before the deadline on the letter (often 10–30 days). Free legal aid handles these.\n\n" +
        "Unemployment benefits are taxable. Ask to have taxes withheld (usually 10% federal) so nothing surprises you in April.";
    },
    owed: function (p) {
      return "WHAT YOU'RE OWED WHEN A JOB ENDS — CHECKLIST\n\n" +
        "[ ] FINAL PAYCHECK: every hour worked, including overtime. Many states set a deadline (some the same day you're let go). If it's late or short, file a wage claim with your state labor department or the U.S. Wage and Hour Division — free, no lawyer needed.\n" +
        "[ ] UNUSED VACATION / PTO: paid out at separation in many states, or if the company's own policy says so. Ask for the policy in writing.\n" +
        "[ ] EXPENSE REIMBURSEMENTS and any commissions or bonuses already earned.\n" +
        "[ ] HEALTH INSURANCE END DATE: ask HR exactly which day coverage stops (often the end of the month). Write it down — it starts the 60-day clocks for COBRA and the Marketplace.\n" +
        "[ ] RETIREMENT: your 401(k)/403(b) money is yours. Don't cash it out in a panic (taxes plus a 10% penalty under 59½). Leaving it or rolling it to an IRA keeps it.\n" +
        "[ ] WRITTEN REASON for the separation, and a copy of your personnel file (your right in many states).\n" +
        "[ ] REFERENCES: ask a manager who respects you for a reference now, while the relationship is warm.\n\n" +
        "SEVERANCE — DON'T SIGN THE SAME DAY\n" +
        "A severance agreement usually asks you to give up the right to sue. Take it home.\n" +
        "• If you are 40 or older, federal law (OWBPA) gives you 21 days to consider it and 7 days to revoke after signing — 45 days in a group layoff.\n" +
        "• Everything is negotiable: more weeks of pay, paid health premiums, a neutral reference, dropping a non-compete.\n" +
        "• Free legal aid or a workers' center can read it with you.\n\n" +
        (p.warnLarge ? "WARN ACT — YOU MAY BE OWED 60 DAYS OF PAY\n" +
          "Employers with 100 or more workers generally must give 60 days' written notice before a plant closing or mass layoff. If you got little or no notice, you may be owed up to 60 days of wages and benefits. Several states (including CA, NY, NJ, IL) have stronger versions. Contact your state's Rapid Response team through an American Job Center, or legal aid. Keep every letter and email about the layoff.\n\n" : "") +
        "KEEP A FOLDER: pay stubs, the separation letter, insurance notices, every email. If anything goes wrong later, the person with the paper wins.";
    },
    coverageClock: function (p) {
      var covSince = p.coverageEndDays === null || p.coverageEndDays === undefined ? null : Math.round(num(p.coverageEndDays));
      var jobSince = p.jobEndDays === null || p.jobEndDays === undefined ? null : Math.round(num(p.jobEndDays));
      return "LOST HEALTH COVERAGE WITH THE JOB — THREE DOORS, ONE 60-DAY CLOCK\n\n" +
        "THE CLOCK STARTS THE DAY COVERAGE ENDS — not the day the job ended. Coverage often runs to the end of the month you left, and sometimes longer under a severance deal.\n" +
        (covSince !== null && covSince > 60 ? "You said coverage ended about " + covSince + " days ago, so the 60-day Marketplace window has likely closed. Medicaid is still open any day. Ask the Marketplace anyway (some states allow more time), and check the date on your COBRA election notice — COBRA's 60 days run from that notice if it came later.\n\n" :
          covSince !== null ? "You said coverage ended about " + covSince + " days ago, so about " + (60 - covSince) + " days remain on the 60-day windows. Confirm the exact end date with HR or the insurer's letter.\n\n" :
          "You haven't told me the exact day coverage ends" + (jobSince !== null ? " (the job ended about " + jobSince + " days ago)" : "") + ". FIRST STEP: call HR or the insurer and get that date in writing, then come back and enter it so I can set the real deadline.\n\n") +
        "DOOR 1 — MEDICAID (any day of the year, usually free)\n" +
        "Medicaid looks at your income NOW, not last year's. A household of " + p.hhSize + " earning about " + money(num(p.income)) + " a month" +
        (num(p.income) ? " is at roughly " + fplPct(p) + "% of the poverty line" : "") + ". " +
        (NON_EXPANSION.indexOf(p.state) !== -1 ? "Your state has not expanded Medicaid to most adults, so check the Marketplace too, and look for a community health center while you sort it out." : "If you are under about 138% of the poverty line, you likely qualify. Apply through your state Medicaid office or HealthCare.gov.") + "\n\n" +
        "DOOR 2 — MARKETPLACE SPECIAL ENROLLMENT (60 days before or after coverage ends)\n" +
        "Losing job-based coverage opens a window at HealthCare.gov (or your state's exchange) even outside Open Enrollment: you can apply up to 60 days BEFORE the end date so there's no gap, and up to 60 days after. Report your NEW lower income — the subsidy is based on what you expect to earn this year, and you can update it if you find work.\n\n" +
        "DOOR 3 — COBRA (60 days to decide; usually the most expensive)\n" +
        "You can keep the same plan for up to 18 months, but you pay the full premium plus 2% — often $600–$2,000 a month. It makes sense mainly if you're mid-treatment or have met a big deductible. You have 60 days to elect it, counted from the day coverage ended or the day you receive the COBRA election notice, whichever is later; if you elect, it covers you back to the day the old plan ended.\n\n" +
        "WHILE YOU DECIDE: a community health center sees you regardless of coverage and charges on a sliding scale. Don't skip medications — ask the pharmacy for the cash price and the manufacturer's assistance program.\n\n" +
        "WRITE DOWN: coverage end date ______  ·  60-day deadline ______  ·  Marketplace application date ______";
    },
    snapReport: function (p) {
      return "REPORT THE INCOME DROP TO SNAP — CALL SCRIPT\n\n" +
        "You are already on SNAP. A lower income usually means a HIGHER benefit — but only once you report it.\n\n" +
        "Call your caseworker or the state SNAP line and say:\n" +
        "\"I need to report a change. [My / my household member's] job ended / hours were cut on [date]. Our household income is now about " + money(num(p.income)) + " a month. Please recalculate our benefit from the date of the change, and tell me what proof you need.\"\n\n" +
        "SEND PROOF THE SAME WEEK: the separation letter, last pay stub, or a short signed statement from the employer. Keep a copy and note who you spoke to and when.\n\n" +
        "ALSO ASK:\n• \"Does this change my recertification date?\"\n• \"Are there work rules for me, and does SNAP Employment & Training count?\" (It's free and can include job search help, training and transportation money.)\n" +
        "• \"Can you add our utility allowance?\" — if you pay heat or electric separately and it isn't already counted.\n\n" +
        "If the office says the change doesn't matter, ask for that in writing. Reporting a DROP in income is always allowed, even between reports.";
    },
    ajc: function (p) {
      return "AMERICAN JOB CENTER — WHAT TO ASK FOR\n\n" +
        "There are about 2,300 of these across the country. They are run by people, paid for with taxes you already paid, and free. You do not need to use any app or AI to use them.\n\n" +
        "Find yours (CareerOneStop locator) and walk in or call. Say:\n" +
        "\"I'd like to meet with a career counselor. " + (p.jobLoss ? "I recently lost my job / had my hours cut" : p.newGrad ? "I'm looking for my first job after finishing school" : "I want training that leads to a better-paying job") + ". I'd like to know what I'm eligible for under WIOA.\"\n\n" +
        "WHAT THEY CAN DO:\n" +
        "[ ] Help you file for unemployment on the spot\n" +
        "[ ] Pay for training (an \"Individual Training Account\" — often several thousand dollars) at an approved school or program\n" +
        "[ ] Help with the costs of looking for work: transportation, work clothes, tools, sometimes child care\n" +
        "[ ] Résumé and interview help from a person; access to employers who hire through the center\n" +
        "[ ] \"Rapid Response\" services if your layoff was part of a larger one\n" +
        "[ ] Referrals to apprenticeships, SNAP Employment & Training, and veterans' employment staff\n\n" +
        "BRING: ID, your work history for the last few years, and the list of jobs you've applied to.\n\n" +
        "ASK BEFORE YOU LEAVE: \"What am I eligible for, what's the next step, and who is my point of contact?\" Write down the name.";
    },
    training: function (p) {
      return "TRAINING WITH A PAYCHECK AT THE END — HOW TO CHOOSE\n\n" +
        "The programs with the strongest evidence share three things: they're designed WITH the employers who hire from them, they pay you or cost you nothing, and they end in a real job. Here's how to tell them apart.\n\n" +
        "1. REGISTERED APPRENTICESHIP — you're hired on day one and paid while you learn (trades, health care, IT, manufacturing, and growing in office jobs). Search Apprenticeship.gov. Evidence: apprentices' earnings grew 43% vs. 16% for similar workers (Urban Institute).\n\n" +
        "2. SECTORAL PROGRAMS — free, several months, built with employers, with a coach. Year Up United (ages 18–29) and Per Scholas (tech) are the best-studied: in randomized trials, graduates earned 14–30% more for 7+ years. Seats are limited and they're not in every city — ask the job center what the local equivalent is.\n\n" +
        "3. SHORT PELL-FUNDED PROGRAMS — from July 2026, Pell Grants can pay for approved programs of 8 to 15 weeks (\"Workforce Pell\"). Each must show 70% completion and 70% job placement to stay approved. Ask the community college which of its short programs are approved and what graduates actually earn.\n\n" +
        "4. SNAP EMPLOYMENT & TRAINING — if you're on SNAP, free training plus help with transportation and books. Ask your caseworker.\n\n" +
        "QUESTIONS THAT PROTECT YOU (ask every program):\n" +
        "[ ] What share of people who START finish? What share have a job in the field 6 months later? What do they earn?\n" +
        "[ ] Who are the employers you work with — can I talk to a recent graduate?\n" +
        "[ ] What will it cost me, including fees, and is there any loan involved? (If a program pushes a private loan, walk away.)\n" +
        "[ ] Is the credential recognized by employers or a licensing board?\n\n" +
        "WHERE THE JOBS ARE HOLDING UP: the sharpest drops in entry-level hiring are in office work that software can do (routine coding, scripted customer service, basic marketing). Hands-on, in-person and licensed work — health care, the skilled trades, utilities, field service — has kept growing. Choose with your eyes open.";
    },
    firstJob: function (p) {
      return "FIRST JOB AFTER SCHOOL — THE MOVES WITH EVIDENCE BEHIND THEM\n\n" +
        "The market for new graduates is tighter than it was. That is not your fault, and it is measurable: recent graduates' unemployment is running about 1.3 points above everyone else's (NY Fed, 2026). Here is what actually moves the odds.\n\n" +
        "1. GET PAID EXPERIENCE ON THE RÉSUMÉ — EVEN NOW. An internship, co-op or apprenticeship cuts the odds of being stuck in a job that doesn't need your degree almost in half (Strada/Burning Glass). Many take recent graduates, not just students. Ask the career center (most serve alumni) and the American Job Center.\n\n" +
        "2. BE CAREFUL WITH A STOPGAP JOB. In a hiring experiment, graduates in jobs below their degree got 15–30% fewer interviews — but internship experience erased most of that penalty. If you need the stopgap for rent, take it, and keep one relevant thing going beside it.\n\n" +
        "3. APPLY WHERE A PERSON READS YOUR APPLICATION. Smaller employers, hospitals, public agencies, unions and apprenticeships are more likely to have a human on the other end. In Illinois, employers must now tell you when AI is used in a hiring decision; in New York City they must post notice and a bias audit. Anywhere, you can ask.\n\n" +
        "4. LEAN TOWARD WORK WHERE SOFTWARE HELPS RATHER THAN REPLACES. Entry-level jobs most exposed to AI fell about 11% for 22–25-year-olds since 2022; the least-exposed grew about 10% (Stanford, 2026). Care work, trades, field roles and anything licensed held up.\n\n" +
        "5. NEW NURSES: prioritize employers with an accredited nurse residency program (89% of residents are still there after a year, vs. 76% nationally). Look at rural and non-metro hospitals — shortages there run about three times deeper. Oregon and Washington now bar software from calling itself a \"nurse.\"\n\n" +
        "6. USE THE FREE PEOPLE: career center (alumni too), American Job Center, your professors' networks, your state's apprenticeship office, and a union hall in your field.\n\n" +
        "WEEKLY RHYTHM THAT WORKS: 5 tailored applications, 2 real conversations with people in the field, 1 skill hour. Log it — it also satisfies unemployment's work-search rule if you're collecting.";
    },
    aiRights: function (p) {
      return "WHEN SOFTWARE SCREENS, MONITORS OR REPLACES YOU — YOUR RIGHTS\n\n" +
        "Plain talk first: no federal law yet stops an employer from using AI to screen applications, set schedules, monitor work or decide layoffs. But the old laws still apply to whatever the software does, and a few states have added rules. Here's what you can use.\n\n" +
        "DISCRIMINATION LAWS APPLY TO THE TOOL. If an automated system screens out people by race, sex, age (40+), disability, national origin or pregnancy — even by accident — the EMPLOYER is responsible under Title VII, the ADA and the ADEA. You can file with the EEOC (free; 180–300 days from the event). An AI that can't handle a disability accommodation is an ADA problem.\n\n" +
        "ASK IN WRITING. Copy and send this:\n" +
        "\"Dear [HR / hiring manager], I'm writing about [my application for ___ / the decision on ___ dated ___]. Please tell me whether an automated or AI-based tool was used in this decision, what it evaluated, and how I can request a review by a person. If I need an accommodation for the process, please let me know how to request one. Thank you.\"\n" +
        "In ILLINOIS (since Jan. 1, 2026) employers must notify you when AI is used in hiring, promotion, discipline or firing, and may not use it in a way that discriminates. In NEW YORK CITY, automated hiring tools need a published bias audit and advance notice. Other states are moving — ask your state labor department.\n\n" +
        "LAYOFFS: if 100+ people work for the company, a mass layoff usually requires 60 days' written notice (WARN Act). \"AI efficiency\" is not an exemption.\n\n" +
        "MONITORING: your employer can generally monitor work accounts and devices. It cannot use monitoring to punish you for talking with coworkers about pay, safety, staffing or AI — that's protected under the National Labor Relations Act, union or not.\n\n" +
        "IN HEALTH CARE: AI cannot practice nursing or medicine. Oregon (2026) and Washington (2026) made it illegal for software to use the title \"nurse.\" If a tool's output conflicts with your clinical judgment, document it and follow your scope of practice — your license is yours, not the vendor's.\n\n" +
        "KEEP A RECORD: screenshots of any automated rejection, the job posting, dates, names. Patterns are what agencies and lawyers act on.";
    },
    organize: function (p) {
      return "TALK WITH COWORKERS — AI, STAFFING AND AUTOMATION ARE BARGAINABLE\n\n" +
        "One person objecting to a new system is a complaint. Ten people putting it in writing is a negotiation. The law protects the second one.\n\n" +
        "YOUR RIGHT: under Section 7 of the National Labor Relations Act, most private-sector workers can act together about working conditions — pay, schedules, safety, staffing, surveillance, and how new technology is introduced — whether or not there's a union. Firing or disciplining people for it is illegal, and the NLRB takes complaints for free.\n\n" +
        "FIRST CONVERSATIONS (off the clock, off company systems):\n" +
        "• \"What's changed in your job since [the new system / the layoffs]?\"\n" +
        "• \"What would make this safe and fair?\" — write down the three most common answers.\n" +
        "• \"Would you sign something that says that?\"\n\n" +
        "A GROUP LETTER THAT WORKS:\n" +
        "\"We, the undersigned employees of [department], ask management to meet with us about [the new scheduling/monitoring/AI system]. Specifically we ask for: (1) notice before any automated tool is used to evaluate, schedule or discipline us; (2) a person we can appeal to; (3) no reduction in staffing below [safe level] as a result. We'd like to meet by [date].\"\n" +
        "Signed by several people, delivered together.\n\n" +
        "IF YOU'RE IN A UNION: bring it to your steward — technology that changes working conditions usually must be bargained. Nurses: National Nurses United has model contract language on AI and patient safety.\n" +
        "IF YOU'RE NOT: a workers' center or the AFL-CIO's organizing line can walk you through it. Many first steps don't require forming a union.\n\n" +
        "Record who you talked to and when. Keep organizing conversations off employer email and chat.";
    },
    medicaidWork: function (p) {
      return "KEEP MEDICAID — THE 80-HOUR RULE STARTING IN 2027\n\n" +
        "Under the 2025 budget law (P.L. 119-21), states must start requiring many adults covered by Medicaid expansion to show 80 hours a month of work, job training, school, or volunteering — by January 2027 in most states (some may get extra time). People who can't show it, or who miss the paperwork, can lose coverage.\n\n" +
        "WHAT COUNTS TOWARD 80 HOURS: paid work (hours or earnings), a job-training program, half-time or more school, community service, or a mix.\n" +
        "LIKELY EXEMPT (confirm with your state): parents or caregivers of children 13 and under, people who are pregnant or recently gave birth, people with disabilities or serious health conditions, people in substance-use treatment, veterans with a total disability rating, and others.\n\n" +
        "WHY THIS IS ON YOUR PLAN: you told me a job ended or hours were cut while someone in the household has Medicaid. Starting now protects you:\n" +
        "[ ] Sign up for free SNAP Employment & Training or a job-center program — training hours count\n" +
        "[ ] Keep a simple monthly log: hours worked, class hours, volunteer hours\n" +
        "[ ] Make sure the Medicaid office has your current address, phone and email — most coverage losses are paperwork, not eligibility\n" +
        "[ ] Ask your state Medicaid office: \"When does the community engagement requirement start here, and am I exempt?\"\n\n" +
        "If you lose coverage, you can reapply — and Medicaid can be backdated up to 3 months for bills in that gap.";
    }
  };

  /* ---------- Lessons (60 seconds each) ---------- */
  var LESSONS = {
    snap: "SNAP doesn't just look at your paycheck. It subtracts 20% of earned income, a standard deduction, child care costs, and — the big one — housing and utility costs above half your remaining income. That's why reporting your rent and utility bill can raise your benefit by $100 or more.",
    wic: "WIC is separate from SNAP. It covers specific foods (milk, eggs, cereal, produce, formula) for pregnant and postpartum people and children under 5, plus breastfeeding support and nutrition check-ins. If you're on SNAP or Medicaid, you're usually income-eligible automatically.",
    lifeline: "Lifeline is a federal discount (about $9.25/month) on phone or internet. Separately, most large internet providers run their own low-income plans — often $10–$30 for usable home internet. You can often stack the two.",
    foodweek: "The cheapest calories are rarely the cheapest nutrition. Beans, eggs, oats, frozen vegetables and whole chickens give the most protein and fiber per dollar — which keeps people full and blood sugar steadier through the end of the month.",
    renew: "Medicaid must check eligibility at least once a year. Most people who lose coverage at renewal are still eligible — they lose it for paperwork. Returning the packet on time, with current income, is the single most protective thing you can do.",
    coverage: "Marketplace premium tax credits cap what you pay for a benchmark silver plan as a share of your income. Between 100% and 250% of poverty, silver plans also lower your deductible and copays. The enhanced credits from 2021–2025 ended, and as of November 2026 Congress hasn't restored them, so credits again stop at 400% of poverty and the most you pay for 2027 is 10.22% of income. Check your numbers on HealthCare.gov.",
    rx: "The price at the counter isn't fixed. Cash price, insurance price, discount-card price and mail-order price can differ several-fold for the same generic. Pharmacy benefit managers set many of these prices — that's what PBM-transparency bills are about.",
    charity: "Nonprofit hospitals get tax breaks and in return must publish a financial assistance policy. Many forgive bills entirely below 200% of poverty and discount them up to 300–400%. You can apply even after a bill goes to collections. Under the credit bureaus' own policy, medical debts under $500 and paid medical debts don't appear on credit reports (a 2025 federal rule that went further was struck down by a court).",
    pa: "Prior authorization means your plan must approve something before it pays. A denial is not the final word: you have a right to an internal appeal, and then an independent external review. Many denials are overturned — especially when the prescriber addresses the plan's own written criteria.",
    eviction: "An eviction notice starts a legal clock, but it isn't an eviction. Only a court can order you out. Tenants with a lawyer are far more likely to stay housed or get time to move — which is why getting legal aid on day one matters more than anything else.",
    rentIncrease: "A few states cap yearly increases on many older units — for 2026, Oregon at 9.5% and Washington at 9.683%, California at 5% plus regional inflation (never over 10%); dozens of cities have their own rules. Where there's no cap, landlords still weigh the cost of vacancy — a calm, written request often lands a smaller increase.",
    erap: "Emergency rental assistance is now mostly county, city and charity funded. Programs open and close quickly, so 211 is the best live source. Many pay the landlord directly, which also helps stop an eviction case.",
    affordable: "Below-market-rate and tax-credit (LIHTC) apartments rent at set prices tied to area income. They're won by lottery or waitlist, so the households who get them are the ones who apply to many and keep documents ready.",
    tenantOrg: "One tenant asking for repairs is a complaint; twenty tenants asking is a negotiation. Tenant associations are how renters win repairs, fair increases, and protection from retaliation.",
    shutoff: "A shutoff is a health event. Most states let a clinician certify that someone's health would be endangered without power, which can delay disconnection. Payment plans and seasonal protections exist in many states — but you have to ask before the shutoff date.",
    liheap: "LIHEAP is a federal block grant run by states. It gives one-time help with heating or cooling bills, plus crisis help when a shutoff is near. It's funded for 2026, and only partly funded for 2027 under a temporary spending law, so applying early matters.",
    discount: "Many utilities offer a permanent low-income rate — in California, CARE takes 30–35% off electric and 20% off gas. Unlike a one-time grant, a discount rate lowers every bill for as long as you qualify.",
    rateplan: "Your bill depends on the rate plan as much as your usage. Time-of-use plans reward shifting usage away from evening peaks; tiered plans charge more as total use rises. The wrong plan for your routine can quietly cost $10–$30 a month.",
    weatherize: "The Weatherization Assistance Program pays for insulation, air sealing and repairs in low-income homes — the Department of Energy estimates savings of several hundred dollars a year per home. Cheap DIY fixes come first; windows come last.",
    ratepayer: "Utility rates are set in public proceedings at your state's utility commission. Public comment from real customers becomes part of the record — and decisions about who pays for new power plants and data centers are being made right now.",
    childcare: "Child care subsidies are funded by the federal Child Care and Development Fund and run by states, with income limits up to 85% of state median income. Families usually pay a sliding co-pay. Head Start is free for eligible families.",
    dcap: "A Dependent Care FSA lets you pay for care with pre-tax dollars — up to $7,500 per household starting in 2026. If your combined tax rate is 22–30%, that's $1,600–$2,200 back on a full contribution — but only if your employer updated its plan to the new limit.",
    leave: "FMLA protects your job but doesn't pay. A growing number of states run paid family leave insurance funded by payroll deductions you've likely already been paying. The certification form is where most claims stall — a clear, specific clinician note prevents delays.",
    caregiverPay: "Many states' Medicaid programs let people hire a family member as their paid caregiver. California's IHSS is the largest. If your parent or partner already gets your help daily, you may be able to be paid for it.",
    respite: "Family caregivers have higher rates of depression and chronic illness. Respite — even a few hours — is a health intervention, not a luxury.",
    // WorkBridge (English-only)
    ui: "Unemployment insurance is paid for by a tax on your employer that's figured into your wages — you earned it. It pays from the week you file, not the day you lost the job, so delay costs you money. Most states replace about half of prior wages up to a cap, for up to 26 weeks. Partial benefits exist for cut hours, and many denials are won on appeal.",
    owed: "A final paycheck, unused vacation and earned commissions are debts the employer owes you, with state deadlines behind them. A severance agreement trades money for your right to sue; federal law gives workers 40 and over 21 days to think about it. And if 100 or more people work there, a mass layoff usually requires 60 days' notice — or 60 days of pay.",
    coverageClock: "Losing job-based insurance opens three doors. Medicaid is open any day and judges income now, not last year's. The Marketplace opens a 60-day special enrollment window with subsidies based on this year's expected income. COBRA keeps the old plan at full price for up to 18 months and can be elected retroactively within 60 days of losing coverage or getting the election notice, whichever is later. Both clocks run from the day coverage ends, not the day the job ended. Miss them and you may wait until November.",
    snapReport: "SNAP is recalculated when income changes — but a drop only raises your benefit once you report it, and the increase starts from the report, not the job loss. Expedited SNAP (benefits within 7 days) goes to households with under $150 in monthly income and $100 or less in cash and bank accounts, or whose rent plus utilities exceeds their income plus those resources — ask the office to screen you for it.",
    ajc: "American Job Centers are the public job-service system created by federal law (WIOA). They're free, in person, and can pay for training through Individual Training Accounts. They are the human front door to almost every program on this page — you don't need an app or an AI to use them.",
    training: "The only workforce programs proven in randomized trials — Year Up, Per Scholas, Project QUEST — share a design: built with employers, free to the participant, with a coach and a job at the end. Earnings gains of 14–30% lasted 7 to 14 years. Programs that charge you, push loans, or can't name their employer partners don't have that record.",
    firstJob: "Since 2023, recent college graduates have been unemployed at a higher rate than workers overall for the first time in decades, and 42% of those working are in jobs that don't need a degree. The best evidence says paid experience with an employer attached — internships, co-ops, apprenticeships, residencies — is what changes the odds, not another certificate.",
    aiRights: "No federal law yet limits AI in hiring or firing — but the discrimination laws apply to whatever the tool does, and the employer answers for it. Illinois requires notice when AI is used in employment decisions (2026); New York City requires bias audits. In health care, Oregon and Washington bar software from using the title \"nurse.\" Your record of what happened is what makes any of this enforceable.",
    organize: "The National Labor Relations Act protects most private-sector workers who act together over working conditions, union or not — including how new technology is introduced. Technology that changes jobs is a mandatory bargaining subject where there's a union. The research on AI and jobs finds the losses land where workers have the least say.",
    medicaidWork: "The 2025 budget law adds a work-or-activity requirement to Medicaid expansion starting by 2027: 80 hours a month of work, training, school or volunteering, with exemptions for parents of young children, people with disabilities and others. Where similar rules were tried before, most people who lost coverage were eligible — they lost it to paperwork. A log and an up-to-date address are the defense."
  };

  /* ---------- Spanish drafts and lessons ---------- */
    var DRAFTS_ES_IMPL = {
      snap: function (p, t) {
        var prog = p.state === "CA" ? "CalFresh" : "SNAP";
        return "SOLICITUD DE " + (p.state === "CA" ? "CALFRESH (SNAP)" : "SNAP (CUPONES DE ALIMENTOS)") + " — QUÉ DEBE TENER LISTO\n\n" +
          INTERPRETER_ES + "\n\n" +
          "Presente su solicitud hoy: los beneficios se cuentan a partir de la fecha en que reciben su solicitud.\n" +
          "Puede entregar un formulario con solo su nombre, dirección y firma para asegurar esa fecha, y después completar el resto.\n\n" +
          "Traiga o suba:\n" +
          "[ ] Identificación de la persona que presenta la solicitud\n[ ] Talones de pago de los últimos 30 días (de todas las personas que trabajan)\n" +
          "[ ] Comprobante de renta o hipoteca (usted dijo que paga unos " + money(num(p.housingCost)) + " al mes)\n" +
          "[ ] Una factura de servicios (calefacción o electricidad): esto aumenta su deducción\n" +
          "[ ] Lo que paga por el cuidado de niños o de otros dependientes\n" +
          (num(p.seniors) > 0 || p.disability ? "[ ] Gastos médicos de más de $35 al mes de cualquier persona de 60 años o más o con una discapacidad: también cuentan\n" : "") +
          "\nLA ENTREVISTA (por lo general por teléfono, en unos 30 días)\n" +
          "Diga: \"Llamo por mi entrevista de " + prog + ". En mi hogar somos " + p.hhSize + " personas.\n" +
          "Nuestro ingreso bruto es de unos " + money(num(p.income)) + " al mes. Pagamos " + money(num(p.housingCost)) + " de vivienda\n" +
          "y unos " + money(num(p.energyBill)) + " de servicios públicos. Por favor, asegúrese de que apliquen la deducción por servicios públicos (utility allowance).\"\n\n" +
          "Si pierde la llamada, llame de vuelta el mismo día y pida otra cita. No deje que cierren su caso.\n" +
          "Si necesita ayuda rápido y tiene menos de $150 de ingresos este mes, pregunte por " + prog + " ACELERADO (EXPEDITED, en 7 días).";
      },
      wic: function (p) {
        return "WIC — GUION PARA LLAMAR\n\n" + INTERPRETER_ES + "\n\n\"Hola, quisiera hacer una cita de WIC. " +
          (p.pregnant ? "Estoy embarazada" : "") + (p.pregnant && num(p.kidsUnder5) ? " y " : "") +
          (num(p.kidsUnder5) ? (p.pregnant ? "tengo " : "Tengo ") + p.kidsUnder5 + " hijo(s) menor(es) de 5 años" : "") +
          ". " + (has(p.benefits, "snap") || has(p.benefits, "medicaid") ? "Ya recibimos SNAP/Medicaid, así que entiendo que calificamos automáticamente por ingresos." : "En mi hogar somos " + p.hhSize + " personas y ganamos unos " + money(num(p.income)) + " al mes.") +
          "\n¿Qué debo traer? ¿Puede ser la cita por teléfono o por video?\"\n\n" +
          "Traiga: identificación, comprobante de domicilio, comprobante de ingresos (o su tarjeta de SNAP/Medicaid) y el registro de vacunas de cada niño si lo tiene.";
      },
      lifeline: function (p) {
        return "FACTURA DE INTERNET — GUION PARA LLAMAR\n\n" + INTERPRETER_ES + "\n\n" +
          "1) Lifeline: solicítelo en lifelinesupport.org (Verificador Nacional, National Verifier). Califica si recibe SNAP, Medicaid o SSI, o si su ingreso es igual o menor al 135% del nivel de pobreza.\n\n" +
          "2) Llame a su compañía de internet y diga:\n\"Llamo para bajar mi factura. Ahora pago unos " + money(num(p.internetBill)) + " al mes.\n" +
          (has(p.benefits, "snap") || has(p.benefits, "medicaid") ? "Recibo SNAP/Medicaid" : "Tengo ingresos bajos") + ". ¿Qué planes para personas de bajos ingresos ofrecen?\n" +
          "¿También me pueden quitar los cargos por alquiler de equipo y decirme si estoy pagando por más velocidad de la que necesito?\"\n\n" +
          "3) Si le dicen que no: \"Por favor, transfiérame al departamento de retención (retention department). Estoy pensando en cancelar.\"\n\n" +
          "Anote: el nombre del plan, el nuevo precio, el número de confirmación y el primer nombre del representante.";
      },
      foodweek: function (p) {
        var n = Math.max(1, p.hhSize | 0);
        return "PLAN DE COMIDAS PARA DOS SEMANAS — HOGAR DE " + n + (n === 1 ? " PERSONA" : " PERSONAS") + "\n(Pensado para la salud: proteína en cada comida, cuidado con el sodio y fibra para sentirse satisfecho.)\n\n" +
          "DÍA DE DESPENSA: elija un banco de alimentos o una despensa y apúntelo en su calendario cada semana.\n\n" +
          "COMPRE UNA VEZ, COCINE DOS VECES\n" +
          "• Frijoles o lentejas secos (la proteína más barata por porción; enjuague los frijoles de lata para bajar el sodio un ~40%)\n" +
          "• Huevos, avena natural, arroz integral, verduras congeladas (tan nutritivas como las frescas, y no se desperdician)\n" +
          "• Un pollo entero o un paquete familiar de muslos → áselo y después haga sopa con los huesos\n" +
          "• Plátanos (bananas), manzanas, zanahorias, repollo: las frutas y verduras que más duran por cada dólar\n\n" +
          "SEMANA 1: Lun chili de frijoles · Mar chili con arroz · Mié arroz frito con huevo + verduras congeladas · Jue pollo asado + repollo\n" +
          "          Vie sopa de pollo · Sáb curry de lentejas · Dom sobras + panqueques de avena\n" +
          "SEMANA 2: repita con algunos cambios: frijoles negros en vez de frijoles rojos, camote (batata) en vez de arroz.\n\n" +
          "SI ALGUIEN TIENE DIABETES: llene la mitad del plato con verduras sin almidón y limite el arroz o la papa a una porción del tamaño de un puño.\n" +
          "SI ALGUIEN TIENE PRESIÓN ALTA: elija latas 'sin sal añadida' (no salt added) y sazone con ajo, limón, vinagre y comino.\n\n" +
          "PARA DUPLICAR SU SNAP/EBT: pregunte en su mercado de agricultores (farmers market) si igualan las compras con EBT (por ejemplo, Market Match en California).";
      },
      renew: function (p) {
        var med = p.state === "CA" ? "Medi-Cal" : "Medicaid";
        return "RENOVACIÓN DE " + (p.state === "CA" ? "MEDI-CAL (MEDICAID)" : "MEDICAID") + " / CHIP — NO DEJE QUE SE VENZA\n\n" +
          INTERPRETER_ES + "\n\n" +
          "[ ] Busque el paquete de renovación (en un sobre o en su cuenta en línea). Anote la fecha límite: ______\n" +
          "[ ] Actualice su dirección y su teléfono para recibir todos los avisos\n[ ] Suba los talones de pago de los últimos 30 días de todas las personas que trabajan\n" +
          "[ ] Firme y envíelo (en línea es lo más rápido); guarde el número de confirmación\n" +
          "[ ] Si le cortaron la cobertura por razones de 'papeleo', por lo general tiene 90 días para entregarlo y recuperar la cobertura sin volver a presentar la solicitud\n\n" +
          "A PARTIR DEL 1 DE ENERO DE 2027: los adultos que tienen cobertura por la expansión de Medicaid tendrán que renovar cada 6 meses, y la mayoría tendrá que demostrar horas de trabajo, estudio, voluntariado o cuidado de otra persona (con excepciones). Pregunte en su oficina de " + med + " qué reglas le aplican y desde cuándo.\n\n" +
          "GUION PARA LLAMAR: \"Llamo para confirmar que recibieron mi renovación de " + med + " del caso número ______.\n" +
          "¿Falta algo? ¿Pueden anotar en mi caso que la entregué el " + todayEs() + "?\"";
      },
      coverage: function (p, t) {
        var w = acaWindow(new Date());
        return "CÓMO OBTENER COBERTURA MÉDICA\n\n" + w.label + ".\n\n" +
          (t.meta && t.meta.route === "gap" ?
            "Según su estado y sus ingresos, es posible que ahora no pueda obtener un plan con subsidio ni Medicaid.\n" +
            "Aun así, puede recibir atención a menor costo:\n" +
            "• Los centros de salud comunitarios (findahealthcenter.hrsa.gov) cobran según sus ingresos (escala móvil): llame y pida una cita como paciente nuevo.\n" +
            (PARTIAL_ADULT_COVERAGE[p.state] && t.meta.pct <= 100 ? "• " + partialAdultText(p.state) + ". Pregunte en la oficina de Medicaid de su estado.\n" : "") +
            "• Pida a cualquier hospital sin fines de lucro su política de asistencia financiera ANTES de una visita programada.\n" +
            "• Los niños y las personas embarazadas muchas veces califican para Medicaid/CHIP con ingresos más altos: presente una solicitud para ellos por separado.\n" +
            "• Vuelva a revisar si cambian sus ingresos, su hogar o su estado: la elegibilidad puede cambiar a mitad de año.\n" :
          t.meta && t.meta.route === "medicaid" ?
            "Según sus ingresos, es probable que califique para " + (p.state === "CA" ? "Medi-Cal (Medicaid)" : "Medicaid") + ". Puede presentar la solicitud en CUALQUIER momento del año: no hay período de inscripción.\nSolicítelo en la agencia de Medicaid de su estado o en CuidadoDeSalud.gov (HealthCare.gov), que lo dirigirá al lugar correcto.\n" :
            "Según sus ingresos (alrededor del " + t.meta.pct + "% del nivel de pobreza), podría recibir un crédito fiscal para la prima.\n" +
            "Límite aproximado para un plan plata de referencia: unos " + money(t.meta.maxPremium) + " al mes para su hogar.\n" +
            (t.meta.pct <= 250 ? "Con sus ingresos, elija un plan PLATA (silver): trae deducibles más bajos (reducciones de costos compartidos).\n" : "")) +
          "\nTenga listo: un cálculo de sus ingresos para el próximo año, los números de Seguro Social de las personas que solicitan (no de otras personas del hogar) e información sobre su cobertura actual.\n" +
          "Ayuda local gratis: busque 'navigator' (navegador) en CuidadoDeSalud.gov (HealthCare.gov). Los navegadores no le pueden cobrar ni venderle nada.\n" +
          "Las reglas de elegibilidad de algunos grupos cambiaron para 2027; un navegador puede revisar su situación de forma confidencial.";
      },
      rx: function (p) {
        return "COSTO DE LAS RECETAS — PREGUNTAS QUE AHORRAN DINERO\n\n" +
          "Pregúntele al FARMACÉUTICO:\n• \"¿Cuál es el precio pagando en efectivo y cuál es el precio con mi seguro? ¿Sale más barato con una tarjeta de descuento?\"\n" +
          "• \"¿Este medicamento está aquí en una lista de genéricos de $4 o de bajo costo?\"\n• \"¿Me saldría más barato al mes un suministro de 90 días o el pedido por correo?\"\n\n" +
          "Pregúntele a QUIEN LE RECETÓ (un mensaje por el portal está bien):\n• \"Por el costo, me cuesta tomar este medicamento como me lo recetaron. ¿Hay un genérico o una\n" +
          "  opción más barata de la misma clase que me funcione?\"\n• \"¿Puede averiguar si el fabricante tiene un programa de asistencia para pacientes?\"\n\n" +
          "INSULINA: Medicare limita el costo de la insulina cubierta a $35 al mes. Lilly, Novo Nordisk y Sanofi tienen cada uno programas de $35 al mes (el de Sanofi incluye a personas con Medicare);\n" +
          "  algunos programas se tienen que renovar cada enero, así que revise las condiciones para 2027.\n\n" +
          "SEGURIDAD: nunca deje de tomar, parta ni se salte un medicamento para ahorrar dinero sin hablar primero con quien se lo recetó o con su farmacéutico.";
      },
      charity: function (p, t) {
        var s = DRAFTS.charity(p, t);
        var i = s.indexOf("\n\n— ");
        var carta = i >= 0 ? s.slice(0, i) : s;
        return "CARTA AL HOSPITAL PARA PEDIR ASISTENCIA FINANCIERA (CHARITY CARE)\n\n" +
          "Qué es: una carta para pedir ayuda con su factura del hospital de " + money(num(p.medBill)) + " según la Política de Asistencia Financiera del hospital. Dice que su hogar tiene " + p.hhSize + " personas y que sus ingresos son de unos " + money(num(p.income)) + " al mes (alrededor del " + t.meta.pct + "% del nivel federal de pobreza). Pide la solicitud, que detengan los cobros mientras la revisan y que lo confirmen por escrito.\n" +
          "A quién se envía: a la Oficina de Asistencia Financiera (Financial Assistance Office) del hospital. La carta está en inglés porque el hospital la necesita en inglés.\n" +
          "Qué debe llenar: el nombre y la dirección del hospital, el número de cuenta (Account #) que aparece en la factura, y al final su nombre, su dirección y su teléfono o correo electrónico.\n" +
          "Consejo: los hospitales sin fines de lucro no pueden tomar acciones de cobro extraordinarias (demandas, reportes a las agencias de crédito) durante por lo menos 120 días después de la primera factura, y deben detenerlas cuando usted presenta la solicitud. Presente la solicitud dentro de los 240 días después de la primera factura.\n" +
          "Importante: los hospitales sin fines de lucro deben tener una política de asistencia financiera por escrito (IRS §501(r)). Por lo general, usted tiene por lo menos 240 días desde la primera factura para presentar la solicitud.\n\n" +
          "— CARTA EN INGLÉS PARA ENVIAR —\n\n" + carta;
      },
      pa: function (p) {
        var s = DRAFTS.pa(p);
        var i = s.indexOf("\n\n— ");
        var carta = i >= 0 ? s.slice(0, i) : s;
        return "CARTA DE APELACIÓN AL SEGURO MÉDICO (AUTORIZACIÓN PREVIA NEGADA)\n\n" +
          "Qué es: una carta para pedir una apelación interna cuando su plan de salud negó la autorización previa de un servicio o medicamento. La carta ya pide una apelación ACELERADA (expedited) si esperar podría dañar gravemente su salud.\n" +
          "A quién se envía: al Departamento de Apelaciones (Appeals Department) de su plan de salud, a la dirección o al fax que aparece en la carta de negación. La carta está en inglés porque el plan la necesita en inglés.\n" +
          "Qué debe llenar: todo lo que está entre [corchetes] y en las líneas ______: el nombre del plan, su número de miembro (Member ID), el número de reclamo o de referencia, el servicio o medicamento, el nombre de quien lo recetó y la fecha, la razón de la negación (cópiela de la carta), y al final su nombre, su dirección y su teléfono o correo electrónico. Pida a la oficina de quien le recetó una carta de necesidad médica (letter of medical necessity): diagnóstico, síntomas y cómo afectan su vida diaria, y tratamientos que ya probó y por qué no funcionaron o no los toleró. Pida al plan sus criterios clínicos por escrito (tiene derecho a recibirlos) y responda a cada punto.\n" +
          "Consejo: pida también a la oficina que ordenó el servicio que solicite una revisión entre médicos (peer-to-peer review) con el director médico del plan. Muchas veces es el camino más rápido.\n\n" +
          "— CARTA EN INGLÉS PARA ENVIAR —\n\n" + carta;
      },
      eviction: function (p) {
        return "AVISO DE DESALOJO — PREPÁRESE PARA HABLAR CON ASISTENCIA LEGAL (HOY)\n\n" + INTERPRETER_ES + "\n\n" +
          "Esto es orientación, no asesoría legal. Los plazos pueden ser muy cortos, a veces de 3 a 5 días.\n\n" +
          "1. NO ignore los papeles de la corte. Si recibió una citación o una demanda (summons/complaint), hay una fecha límite para responder; si no responde a tiempo, puede perder el caso automáticamente.\n" +
          "2. Llame ahora a asistencia legal (lawhelp.org o 211). Diga: \"Recibí un aviso de desalojo el [fecha]. Dice [tipo: pague o desocupe (pay or quit) / citación de la corte].\n   Necesito ayuda antes del [fecha límite del aviso].\"\n" +
          "3. Reúna: el aviso (una foto de cada página), su contrato de renta, recibos de renta o estados de cuenta del banco, mensajes de texto o correos con el arrendador, y fotos de cualquier problema de reparaciones.\n" +
          "4. Siga pagando lo que pueda y pida un recibo, o pregunte a asistencia legal si debe guardar ese dinero.\n" +
          "5. Al mismo tiempo, solicite asistencia de emergencia para la renta (vea el siguiente paso).\n\n" +
          "Nunca deje su casa solo por un aviso: únicamente una orden de la corte y un alguacil (sheriff/marshal) lo pueden sacar.";
      },
      rentIncrease: function (p, t) {
        var yr = new Date().getFullYear();
        var c = rentCapFor(p.state, yr);
        var cite = c ? c.law.split(":")[0] : null;
        var s = DRAFTS.rentIncrease(p, t);
        var i = s.indexOf("\n\n— ");
        var carta = i >= 0 ? s.slice(0, i) : s;
        return "CARTA AL ARRENDADOR SOBRE UN AUMENTO DE RENTA\n\n" +
          "Qué es: una carta para responder a un aumento de renta del " + num(p.rentIncreasePct) + "%. " +
          (c ? "La carta cita la ley de su estado, " + cite + ", que limita los aumentos anuales de renta en las viviendas cubiertas" + (c.published ? " (límite de " + c.cap + "% para " + yr + ")" : "") + ", y pide al arrendador que confirme si su vivienda está exenta y, si no lo está, que baje el aumento al máximo que permite la ley." :
            "La carta dice que usted ha sido un buen inquilino, que quiere quedarse, y pide al arrendador que lo reconsidere y limite el aumento, porque tener la vivienda vacía y volver a rentarla normalmente le cuesta más que un aumento menor.") + "\n" +
          "A quién se envía: a su arrendador o al administrador de la propiedad (landlord / property manager). La carta está en inglés porque el arrendador la necesita en inglés.\n" +
          "Qué debe llenar: " + (c ? "" : "el porcentaje que quiere pedir ([X]%), ") + "la dirección de la vivienda, la fecha en que empieza el aumento, el nombre del arrendador, y al final su nombre, su dirección y su teléfono o correo electrónico.\n" +
          "Consejo: revise también las reglas locales: algunas ciudades tienen un control de rentas más estricto que el del estado. Una organización de asistencia legal o un sindicato de inquilinos se lo puede confirmar.\n\n" +
          "— CARTA EN INGLÉS PARA ENVIAR —\n\n" + carta;
      },
      erap: function (p) {
        return "ASISTENCIA DE EMERGENCIA PARA LA RENTA — LISTA DE PASOS\n\n" + INTERPRETER_ES + "\n\n" +
          "Llame al 211 y diga: \"Necesito asistencia de emergencia para la renta. Me atrasé con la renta" + (p.evictionNotice ? " y recibí un aviso de desalojo" : "") + ".\n¿Qué programas están abiertos ahora mismo en mi condado?\"\n\n" +
          "Pregunte también por: programas del condado o de la ciudad · Ejército de Salvación (Salvation Army) / Caridades Católicas (Catholic Charities) / San Vicente de Paúl (St. Vincent de Paul) · ayuda que también cubra los servicios públicos.\n\n" +
          "Tenga listo: identificación, contrato de renta, el estado de cuenta o el aviso que muestra lo que debe, comprobante de ingresos y los datos de contacto del arrendador (muchos programas le pagan directamente al arrendador).";
      },
      affordable: function (p) {
        return "ALERTAS DE VIVIENDA ASEQUIBLE — PREPÁRELAS UNA VEZ\n\n" +
          "[ ] Busque en el departamento de vivienda de su ciudad o condado 'below market rate' (BMR, renta por debajo del mercado) o 'affordable housing lottery' (lotería de vivienda asequible)\n" +
          "[ ] Inscríbase para recibir alertas; la mayoría de las loterías cierran en 2 a 4 semanas\n" +
          "[ ] Pregunte en la autoridad de vivienda local (housing authority) si están abiertas las listas de espera de vales de vivienda (Housing Choice Voucher)\n" +
          "[ ] Tenga lista una carpeta: identificaciones, talones de pago de los últimos 3 meses, declaración de impuestos y estados de cuenta del banco; las loterías avanzan rápido\n" +
          "[ ] Propiedades LIHTC (crédito fiscal para vivienda de bajos ingresos): llame directamente a cada propiedad y pida entrar en su lista de espera";
      },
      tenantOrg: function (p) {
        return "ORGANIZACIÓN DE INQUILINOS — PRIMERA REUNIÓN\n\n" +
          "Usted no es la única persona. Los aumentos de renta y las reparaciones son problemas de todo el edificio.\n\n" +
          "1. Encuesta de dos preguntas para sus vecinos: \"¿Le subieron la renta? ¿Qué reparaciones está esperando?\"\n" +
          "2. Reúnanse en un lugar público o en la casa de alguien. Orden del día: presentaciones (10 min), qué problemas tenemos (15), una cosa que vamos a pedir juntos (15), quién hace qué (10).\n" +
          "3. Comuníquese con el sindicato de inquilinos (tenant union) o con asistencia legal de su zona; muchos ayudan a formar asociaciones de inquilinos.\n" +
          "4. En la mayoría de los lugares es ilegal tomar represalias contra los inquilinos por organizarse.";
      },
      shutoff: function (p) {
        return "AVISO DE CORTE — LLAME HOY A LA COMPAÑÍA DE SERVICIOS\n\n" + INTERPRETER_ES + "\n\n" +
          "\"Llamo por un aviso de desconexión en la cuenta número ______.\n" +
          (p.medEquip ? "Alguien en mi hogar usa equipo médico que necesita electricidad [CPAP / oxígeno / medicamento que se guarda en el refrigerador].\nQuiero pedir un certificado médico / una protección por equipo de soporte vital (life-support hold) en esta cuenta. ¿Qué formulario tiene que firmar el profesional de salud?\n" : "") +
          "Quiero hacer un plan de pagos que de verdad pueda cumplir. Puedo pagar $____ ahora y $____ al mes.\n" +
          "Por favor, anoten en mi cuenta que estoy solicitando LIHEAP y su descuento para personas de bajos ingresos.\"\n\n" +
          "PREGUNTE: \"¿Hay alguna protección contra cortes por invierno o por olas de calor vigente ahora?\" (Muchos estados las tienen.)\n" +
          "Anote: el nombre, la fecha, el número de confirmación y la nueva fecha de pago.\n\n" +
          (p.medEquip ? "CONSEJO: la mayoría de las compañías aceptan un formulario firmado por un médico, NP (enfermero practicante) o PA (asistente médico). Llame hoy a la oficina de quien le receta y diga que es para evitar un corte del servicio." : "");
      },
      liheap: function (p) {
        return "LIHEAP — AYUDA PARA PAGAR LA ENERGÍA\n\n" + INTERPRETER_ES + "\n\n" +
          "Llame al 211 o a su Agencia de Acción Comunitaria (Community Action Agency): \"Quiero solicitar la ayuda de energía de LIHEAP. " + (p.shutoff ? "Tengo un aviso de corte. ¿Hay ayuda de crisis disponible?" : "Tengo una factura de energía que no puedo pagar al día.") + "\"\n\n" +
          "Tenga listo: identificación, los números de Seguro Social de las personas del hogar que los tengan, sus ingresos de los últimos 30 días y su factura de servicios más reciente.\n\n" +
          "EL ORDEN IMPORTA: primero solicite la tarifa de descuento de la compañía (baja todas sus facturas), después LIHEAP (un crédito de una sola vez) y después la climatización (weatherization, ahorros duraderos). En muchos estados los fondos se reparten por orden de llegada: solicite temprano.";
      },
      discount: function (p) {
        return "TARIFA PARA PERSONAS DE BAJOS INGRESOS — GUION PARA LLAMAR\n\n" + INTERPRETER_ES + "\n\n" +
          "\"Quiero inscribirme en su programa de descuento para personas de bajos ingresos.\n" +
          (p.state === "CA" ? "En California se llama CARE (30–35% de descuento en electricidad y 20% en gas, con ingresos de hasta el 200% del nivel de pobreza), o FERA (18% de descuento en electricidad, con ingresos entre el 200% y el 250% del nivel de pobreza, para clientes de PG&E, SCE y SDG&E). " : "") +
          "En mi hogar somos " + p.hhSize + " personas y ganamos unos " + money(num(p.income)) + " al mes.\n" +
          "¿También puede revisar si otro plan de tarifas me costaría menos según mi consumo de los últimos 12 meses?\"\n\n" +
          "Muchas compañías le permiten inscribirse en línea en 5 minutos. Muchas veces usted mismo declara sus ingresos y la verificación viene después.";
      },
      rateplan: function (p) {
        return "LEA SU FACTURA — 5 COSAS QUE DEBE REVISAR\n\n" +
          "1. NOMBRE DEL PLAN DE TARIFAS (por ejemplo, por horario de uso [time-of-use] o por niveles [tiered]). Si está en casa en las horas pico (muchas veces de 4 a 9 pm), el plan por horario de uso le puede costar más.\n" +
          "2. CONSUMO COMPARADO CON EL AÑO PASADO: un aumento grande sin cambios en su rutina puede ser un error del medidor o un aparato que está fallando (un refrigerador viejo, un calentador portátil).\n" +
          "3. CARGOS FIJOS: la parte que paga sin importar cuánto use.\n4. ¿LECTURA ESTIMADA? Si dice 'estimated' (estimada), pida una lectura real del medidor.\n" +
          "5. LÍNEA DE DESCUENTO: si no ve un descuento para personas de bajos ingresos, no está inscrito.\n\n" +
          "Pregúntele a la compañía: \"¿Pueden hacer una comparación de tarifas con mis últimos 12 meses?\" La mayoría lo hace gratis.";
      },
      weatherize: function (p) {
        return "CLIMATIZACIÓN + REVISIÓN DE 20 MINUTOS QUE PUEDE HACER USTED MISMO\n\n" +
          "Solicite la climatización gratis por medio del Programa de Asistencia para la Climatización (Weatherization Assistance Program): ingresos de hasta el 200% del nivel de pobreza en la mayoría de los estados; los inquilinos pueden calificar con permiso del dueño.\n\n" +
          "Hágalo usted mismo, primero lo más barato:\n[ ] Burletes y barredores para puertas (menos de $20)\n[ ] Película plástica para las ventanas en invierno\n[ ] Ponga el calentador de agua a 120°F\n[ ] Focos LED en las 5 luces que más usa\n" +
          "[ ] Desconecte un segundo refrigerador o congelador si es viejo\n[ ] Limpie o cambie el filtro de la calefacción\n\n" +
          "Deje para después el costoso cambio de ventanas hasta terminar los arreglos baratos.";
      },
      ratepayer: function (p) {
        var carta = DRAFTS.ratepayer(p);
        return "COMENTARIO PÚBLICO PARA LA COMISIÓN DE SERVICIOS PÚBLICOS DE SU ESTADO\n\n" +
          "Qué es: un modelo de comentario público sobre un caso de tarifas (rate case) de su compañía de servicios. Dice que su hogar paga unos " + money(num(p.energyBill)) + " al mes de energía, alrededor del " +
          (num(p.income) ? Math.round(num(p.energyBill) / num(p.income) * 100) : "__") + "% de sus ingresos.\n" +
          "A quién se envía: a la Comisión de Servicios Públicos (Public Utilities Commission) de su estado. El comentario está en inglés porque la comisión lo necesita en inglés.\n" +
          "Qué debe llenar: el nombre de su estado, el nombre de la compañía, el número del caso (docket #), su primer nombre y su ciudad. Dentro de los [corchetes], deje solo lo que quiere pedir: proteger a los clientes residenciales de los costos causados por nuevas cargas grandes, como los centros de datos (data centers) / ampliar los descuentos para personas de bajos ingresos / rechazar el aumento propuesto.\n" +
          "Consejo: los comentarios públicos de clientes reales pasan a formar parte del expediente oficial del caso.\n\n" +
          "— COMENTARIO EN INGLÉS PARA ENVIAR —\n\n" + carta;
      },
      childcare: function (p) {
        return "CUIDADO INFANTIL — LISTA PARA PEDIR AYUDA DE PAGO Y ENCONTRAR PROVEEDOR\n\n" +
          "1. Solicite la ayuda de su estado para pagar el cuidado infantil (con fondos de CCDF). Busque '[su estado] child care assistance' o use ChildCare.gov.\n" +
          (p.state === "CA" ? "   En California: CalWORKs Etapas 1 a 3 (Stages 1–3) o los Programas de Pago Alternativo (Alternative Payment Programs) por medio de su agencia local de Recursos y Referencias (Resource & Referral).\n" : "") +
          (num(p.kidsUnder5) && fplPct(p) <= 130 ? "2. Head Start / Early Head Start: es gratis para familias con ingresos iguales o menores al nivel de pobreza y para niños en cuidado de crianza temporal (foster care) o sin hogar. Solicite ahora: es común que haya listas de espera.\n" : "2. Pida a su agencia local de Recursos y Referencias (Resource & Referral) proveedores con lugares REALMENTE disponibles este mes.\n") +
          "3. Tenga listo: comprobante de su horario de trabajo o estudio, talones de pago, el acta de nacimiento del niño y su registro de vacunas.\n" +
          "4. Pregunte a cada proveedor: \"¿Aceptan la ayuda de pago del gobierno (subsidy)? ¿Tienen descuento para hermanos? ¿Cómo es su lista de espera?\"\n\n" +
          "Costo actual que usted anotó: " + money(num(p.childcareCost)) + " al mes.";
      },
      dcap: function (p) {
        var s = DRAFTS.dcap(p);
        var i = s.indexOf("\n\n— ");
        var carta = i >= 0 ? s.slice(0, i) : s;
        return "CORREO A RECURSOS HUMANOS: CUENTA FSA PARA EL CUIDADO DE DEPENDIENTES (DCAP)\n\n" +
          "Qué es: un correo electrónico corto para preguntar a Recursos Humanos (HR) si su plan de beneficios incluye una cuenta de gastos flexibles para el cuidado de dependientes (Dependent Care FSA o DCAP), cuáles son las fechas de inscripción y cómo inscribirse. Menciona que usted paga unos " + money(num(p.childcareCost)) + " al mes por el cuidado de niños.\n" +
          "A quién se envía: a Recursos Humanos o al departamento de beneficios de su trabajo. El correo está en inglés porque su empleador lo necesita en inglés.\n" +
          "Qué debe llenar: el nombre de la persona de Recursos Humanos ([HR]) y su nombre ([Your name]).\n" +
          "Consejo: el límite por hogar es de $" + DCAP_LIMIT.amount.toLocaleString() + " al año a partir de 2026 ($" + DCAP_LIMIT.amountMFS.toLocaleString() + " si es casado y presenta la declaración por separado), pero solo si su empleador actualizó su plan. El dinero se aparta antes de impuestos, así que ahorra su tasa de impuestos en cada dólar.\n" +
          "Importante: no puede usar el mismo dinero para la DCAP y para el Crédito por Gastos del Cuidado de Hijos y Dependientes (Child and Dependent Care Credit). Un preparador de impuestos (los sitios VITA son gratis) le puede ayudar a escoger la mejor combinación.\n\n" +
          "— CORREO EN INGLÉS PARA ENVIAR —\n\n" + carta;
      },
      leave: function (p) {
        var st = PAID_LEAVE_STATES[p.state];
        var s = DRAFTS.leave(p);
        var i = s.indexOf("\n\n— ");
        var carta = i >= 0 ? s.slice(0, i) : s;
        return "CARTA PARA PEDIR UNA LICENCIA EN SU TRABAJO\n\n" +
          "Qué es: una carta para pedir una licencia (leave) para cuidar a un familiar con una condición de salud grave, para crear un vínculo con su nuevo hijo o para recuperarse de su propia condición de salud grave. Pregunta si la licencia califica bajo la Ley de Licencia Familiar y Médica (FMLA)" + (st ? " y bajo " + st : "") + ", pide los formularios de certificación y promete devolver la certificación completa en un plazo de 15 días.\n" +
          "A quién se envía: a su supervisor o a Recursos Humanos (HR). La carta está en inglés porque su empleador la necesita en inglés.\n" +
          "Qué debe llenar: la fecha de inicio, el número aproximado de semanas, el nombre de su supervisor o de Recursos Humanos, y al final su nombre, su dirección y su teléfono o correo electrónico. Dentro de los [corchetes], deje solo la razón que le corresponde y borre las otras.\n" +
          "FMLA: protege su empleo, no es pagada, y da hasta 12 semanas si su empleador tiene 50 o más empleados cerca y usted trabajó 1,250 horas en el último año.\n" +
          (st ? st + " puede reemplazar parte de su sueldo; por lo general usted lo solicita al ESTADO, no a su empleador.\n" :
            p.state === "MD" ? "Maryland FAMLI empieza a pagar beneficios en enero de 2028; mientras tanto, pregunte por el seguro de discapacidad a corto plazo de su empleador o por tiempo libre pagado.\n" :
            "Su estado no tiene un programa estatal de licencia pagada a la fecha de esta revisión; pregunte por el seguro de discapacidad a corto plazo de su empleador o por tiempo libre pagado.\n") +
          "Consejo para el formulario de certificación: pida al profesional de salud que describa con qué frecuencia se necesita el cuidado, por cuánto tiempo y por qué. Los formularios poco claros se rechazan.\n\n" +
          "— CARTA EN INGLÉS PARA ENVIAR —\n\n" + carta;
      },
      caregiverPay: function (p) {
        return "RECIBA PAGO POR EL CUIDADO QUE YA DA — GUION PARA LLAMAR\n\n" + INTERPRETER_ES + "\n\n" +
          "Llame a su Agencia Local para Personas Mayores (Area Agency on Aging; Eldercare Locator: 1-800-677-1116) o a la oficina de Medicaid de su estado:\n" +
          "\"Yo cuido a mi [parentesco], que necesita ayuda para [bañarse, comer, tomar sus medicamentos, moverse]. ¿Hay programas que les paguen a los familiares que cuidan, como " +
          (p.state === "CA" ? "IHSS (Servicios de Apoyo en el Hogar, In-Home Supportive Services)" : "el cuidado en el hogar dirigido por el consumidor bajo Medicaid (consumer-directed home care)") + "? ¿Y qué servicios de relevo (respite care) y programas de día para adultos hay?\"\n\n" +
          "Pregunte también por: exenciones de Medicaid para servicios en el hogar y la comunidad (HCBS waivers) · PACE · VA Aid & Attendance (si la persona es veterana) · créditos fiscales estatales para cuidadores.\n\n" +
          (p.state === "CA" ? "Con IHSS puede contratar a un familiar o a un amigo. Los cónyuges y los padres de hijos menores de edad solo pueden recibir pago en ciertas circunstancias.\n\n" : "") +
          "Anote el nombre de cada agencia, la persona con quien habló y la fecha: muchas veces estos programas requieren varias llamadas.";
      },
      respite: function (p) {
        return "REVISIÓN PARA QUIEN CUIDA — PARA USTED\n\n" +
          "Cuidar a otra persona es un trabajo especializado que se hace en casa y sin pago. Su salud también importa.\n\n" +
          "Esta semana:\n[ ] Un descanso de 2 horas mientras otra persona cuida (familia, amistades, un programa de relevo)\n" +
          "[ ] Escriba la lista de medicamentos en un solo lugar y compártala con una persona de respaldo\n[ ] Busque un grupo de apoyo para cuidadores (en persona o en línea)\n[ ] Haga la cita para su propio chequeo médico pendiente\n\n" +
          "Si se siente sin esperanza o piensa en hacerse daño: llame o envíe un mensaje de texto al 988, a cualquier hora (para español, oprima 2).";
      }
    };
    var LESSONS_ES_IMPL = {
      snap: "SNAP (cupones de alimentos) no solo mira su sueldo. Resta el 20% de los ingresos por trabajo, una deducción estándar, los gastos de cuidado de niños y, lo más importante, los gastos de vivienda y servicios que pasen de la mitad de los ingresos que le quedan. Por eso, reportar su renta y su factura de servicios puede subir su beneficio en $100 o más.",
      wic: "WIC es aparte de SNAP. Cubre alimentos específicos (leche, huevos, cereal, frutas y verduras, fórmula) para personas embarazadas o que acaban de dar a luz y para niños menores de 5 años, además de apoyo para la lactancia y consultas de nutrición. Si recibe SNAP o Medicaid, por lo general califica automáticamente por ingresos.",
      lifeline: "Lifeline es un descuento federal (de unos $9.25 al mes) en el teléfono o el internet. Aparte, la mayoría de las grandes compañías de internet tienen sus propios planes para personas de bajos ingresos, muchas veces de $10 a $30 por un internet en casa que sirve bien. Muchas veces puede usar los dos a la vez.",
      foodweek: "Las calorías más baratas casi nunca son la nutrición más barata. Los frijoles, los huevos, la avena, las verduras congeladas y el pollo entero dan más proteína y fibra por cada dólar, y eso ayuda a sentirse satisfecho y a mantener el azúcar en la sangre más estable hasta fin de mes.",
      renew: "Medicaid tiene que revisar si usted sigue calificando por lo menos una vez al año. La mayoría de las personas que pierden la cobertura al renovar todavía califican: la pierden por el papeleo. Devolver el paquete a tiempo, con sus ingresos actuales, es lo que más le protege.",
      coverage: "Los créditos fiscales para la prima del Mercado de Seguros Médicos limitan lo que usted paga por un plan plata de referencia a una parte de sus ingresos. Entre el 100% y el 250% del nivel de pobreza, los planes plata también bajan su deducible y sus copagos. Los créditos ampliados de 2021 a 2025 terminaron y, a noviembre de 2026, el Congreso no los ha restablecido, así que los créditos otra vez se acaban en el 400% del nivel de pobreza y lo máximo que pagará en 2027 es el 10.22% de sus ingresos. Revise sus números en CuidadoDeSalud.gov (HealthCare.gov).",
      rx: "El precio en el mostrador no es fijo. El precio en efectivo, con seguro, con tarjeta de descuento y por correo puede variar varias veces para el mismo genérico. Los administradores de beneficios de farmacia (PBM) fijan muchos de estos precios; de eso tratan los proyectos de ley de transparencia de los PBM.",
      charity: "Los hospitales sin fines de lucro reciben beneficios fiscales y, a cambio, deben publicar una política de asistencia financiera. Muchos perdonan toda la factura por debajo del 200% del nivel de pobreza y dan descuentos hasta el 300–400%. Puede presentar la solicitud aunque la factura ya esté en cobranza. Según la política de las propias agencias de crédito, las deudas médicas de menos de $500 y las deudas médicas pagadas no aparecen en los reportes de crédito (una corte anuló una regla federal de 2025 que iba más lejos).",
      pa: "La autorización previa significa que su plan tiene que aprobar algo antes de pagarlo. Una negación no es la última palabra: usted tiene derecho a una apelación interna y después a una revisión externa independiente. Muchas negaciones se revierten, sobre todo cuando quien receta responde a los criterios escritos del propio plan.",
      eviction: "Un aviso de desalojo pone en marcha un plazo legal, pero no es un desalojo. Solo una corte puede ordenar que usted se vaya. Los inquilinos que tienen abogado tienen muchas más probabilidades de quedarse en su vivienda o de conseguir tiempo para mudarse; por eso, conseguir asistencia legal desde el primer día importa más que cualquier otra cosa.",
      rentIncrease: "Algunos estados limitan los aumentos anuales en muchas viviendas más antiguas: para 2026, Oregon al 9.5%, Washington al 9.683% y California al 5% más la inflación regional (nunca más del 10%); docenas de ciudades tienen sus propias reglas. Donde no hay límite, los arrendadores igual toman en cuenta lo que les cuesta tener la vivienda vacía; una petición calmada y por escrito muchas veces logra un aumento menor.",
      erap: "La asistencia de emergencia para la renta ahora viene sobre todo de condados, ciudades y organizaciones benéficas. Los programas abren y cierran rápido, así que el 211 es la mejor fuente de información al día. Muchos le pagan directamente al arrendador, lo que también ayuda a detener un caso de desalojo.",
      affordable: "Los apartamentos con renta por debajo del mercado (BMR) y con crédito fiscal (LIHTC) se rentan a precios fijos según los ingresos de la zona. Se consiguen por lotería o lista de espera, así que los hogares que los obtienen son los que solicitan en muchos lugares y tienen sus documentos listos.",
      tenantOrg: "Un inquilino que pide reparaciones es una queja; veinte inquilinos que piden lo mismo son una negociación. Las asociaciones de inquilinos son la forma en que los inquilinos logran reparaciones, aumentos justos y protección contra represalias.",
      shutoff: "Un corte de servicio es un asunto de salud. En la mayoría de los estados, un profesional de salud puede certificar que la salud de alguien correría peligro sin electricidad, y eso puede retrasar la desconexión. En muchos estados hay planes de pago y protecciones por temporada, pero tiene que pedirlos antes de la fecha del corte.",
      liheap: "LIHEAP es un fondo federal en bloque (block grant) que manejan los estados. Da ayuda de una sola vez con las facturas de calefacción o de aire acondicionado, además de ayuda de crisis cuando se acerca un corte. Tiene fondos para 2026 y solo fondos parciales para 2027 bajo una ley temporal de gastos, así que es importante solicitar temprano.",
      discount: "Muchas compañías de servicios ofrecen una tarifa permanente para personas de bajos ingresos; en California, CARE descuenta del 30 al 35% de la electricidad y el 20% del gas. A diferencia de una ayuda de una sola vez, una tarifa de descuento baja todas sus facturas mientras usted califique.",
      rateplan: "Su factura depende tanto del plan de tarifas como de cuánto usa. Los planes por horario de uso premian usar menos energía en las horas pico de la tarde y la noche; los planes por niveles cobran más a medida que sube el consumo total. Un plan que no va con su rutina le puede costar de $10 a $30 más al mes sin que se dé cuenta.",
      weatherize: "El Programa de Asistencia para la Climatización paga el aislamiento, el sellado de fugas de aire y reparaciones en hogares de bajos ingresos; el Departamento de Energía calcula ahorros de varios cientos de dólares al año por hogar. Primero van los arreglos baratos que puede hacer usted mismo; las ventanas van al final.",
      ratepayer: "Las tarifas de los servicios se fijan en procesos públicos ante la comisión de servicios públicos de su estado. Los comentarios públicos de clientes reales pasan a formar parte del expediente, y ahora mismo se están tomando decisiones sobre quién paga las nuevas plantas de energía y los centros de datos.",
      childcare: "La ayuda para pagar el cuidado infantil viene del Fondo Federal para el Cuidado y Desarrollo Infantil (CCDF) y la manejan los estados, con límites de ingresos de hasta el 85% del ingreso medio del estado. Las familias por lo general pagan un copago según sus ingresos. Head Start es gratis para las familias que califican.",
      dcap: "Una cuenta FSA para el cuidado de dependientes le permite pagar el cuidado con dinero antes de impuestos: hasta $7,500 por hogar a partir de 2026. Si su tasa combinada de impuestos es del 22 al 30%, eso es un ahorro de $1,600 a $2,200 con una contribución completa, pero solo si su empleador actualizó su plan al nuevo límite.",
      leave: "La FMLA (Ley de Licencia Familiar y Médica) protege su empleo, pero no le paga. Cada vez más estados tienen un seguro de licencia familiar pagada que se financia con descuentos de nómina que probablemente usted ya ha estado pagando. La mayoría de las solicitudes se atrasan en el formulario de certificación; una nota clara y específica del profesional de salud evita retrasos.",
      caregiverPay: "Los programas de Medicaid de muchos estados permiten contratar a un familiar como cuidador pagado. IHSS de California es el más grande. Si su padre, su madre o su pareja ya recibe su ayuda todos los días, es posible que le puedan pagar a usted por ella.",
      respite: "Las personas que cuidan a sus familiares tienen más depresión y enfermedades crónicas. El relevo (respite), aunque sea de unas pocas horas, es una medida para su salud, no un lujo."
    };
  var DRAFTS_ES = typeof DRAFTS_ES_IMPL !== "undefined" ? DRAFTS_ES_IMPL : {};
  var LESSONS_ES = typeof LESSONS_ES_IMPL !== "undefined" ? LESSONS_ES_IMPL : {};
  function draftFor(key, p, t) {
    var f = (LANG === "es" && DRAFTS_ES[key]) || DRAFTS[key];
    return f ? f(p, t) : "";
  }
  function lessonFor(key) { return (LANG === "es" && LESSONS_ES[key]) || LESSONS[key] || ""; }

  /* ---------- Plan builder ---------- */
  function task(o) {
    o.monthly = Math.max(0, Math.round(o.monthly || 0));
    o.oneTime = Math.max(0, Math.round(o.oneTime || 0));
    o.effortMin = o.effortMin || 30;
    o.lesson = lessonFor(o.draft);
    return o;
  }

  function buildPlan(p, now) {
    now = now || new Date();
    var pct = fplPct(p);
    var b = p.benefits || [];
    var tasks = [];
    var flags = [];
    var size = Math.max(1, p.hhSize | 0);
    var income = num(p.income);
    var kidsU5 = num(p.kidsUnder5), kidsSchool = num(p.kids5to17);
    var onSNAPorMedicaid = has(b, "snap") || has(b, "medicaid") || has(b, "ssi");

    /* ----- I. Food ----- */
    if (!has(b, "snap") && pct <= SNAP.bbceTestPct) {
      var est = snapEstimate(p);
      if (est > 0) tasks.push(task({
        id: "snap", pillar: "food", draft: "snap", title: tr("Apply for SNAP today", "Solicite SNAP (cupones de alimentos) hoy"),
        why: pct <= SNAP.grossTestPct ? tr("Your income is under SNAP's gross-income limit.", "Sus ingresos están por debajo del límite de ingresos brutos de SNAP.") : tr("Your income is above 130% of poverty, but many states use a higher limit (up to 200%).", "Sus ingresos superan el 130% del nivel de pobreza, pero muchos estados usan un límite más alto (hasta el 200%)."),
        confidence: pct <= SNAP.grossTestPct ? "likely" : "possible", monthly: est, effortMin: 45, dueDays: 3,
        links: [L.snapState, L.l211], source: SNAP.source + " · effective " + SNAP.effective
      }));
    }
    if (!has(b, "wic") && (kidsU5 > 0 || p.pregnant) && (pct <= 185 || onSNAPorMedicaid)) {
      tasks.push(task({ id: "wic", pillar: "food", draft: "wic", title: tr("Schedule a WIC appointment", "Pida una cita de WIC"),
        why: tr("You have a child under 5 or someone pregnant, and your income (or SNAP/Medicaid) qualifies.", "Tiene un hijo menor de 5 años o alguien embarazada, y sus ingresos (o SNAP/Medicaid) califican."),
        confidence: "likely", monthly: 50 * (kidsU5 + (p.pregnant ? 1 : 0)), effortMin: 40, dueDays: 7, links: [L.wic], source: "USDA FNS WIC income guidelines (185% FPL; adjunctive eligibility via SNAP/Medicaid)" }));
    }
    if (kidsSchool > 0 && (pct <= 185 || has(b, "snap"))) {
      tasks.push(task({ id: "meals", pillar: "food", draft: "foodweek", title: tr("Confirm free or reduced-price school meals", "Confirme las comidas escolares gratis o a precio reducido"),
        why: has(b, "snap") ? tr("Children in SNAP households qualify automatically.", "Los niños de hogares con SNAP califican automáticamente.") : tr("Your income is within the school-meals limit (free ≤130%, reduced ≤185%). Some states now serve all students free.", "Sus ingresos están dentro del límite para comidas escolares (gratis ≤130%, precio reducido ≤185%). Algunos estados ya sirven comida gratis a todos los estudiantes."),
        confidence: "likely", monthly: 55 * kidsSchool, effortMin: 15, dueDays: 10, links: [L.l211], source: "USDA National School Lunch Program income eligibility" }));
    }
    if (!has(b, "lifeline") && num(p.internetBill) > 0 && (pct <= 135 || onSNAPorMedicaid || pct <= 200)) {
      var save = 9.25 + Math.max(0, num(p.internetBill) - 30);
      tasks.push(task({ id: "lifeline", pillar: "food", draft: "lifeline", title: tr("Cut the internet bill: Lifeline + low-income plan", "Baje la factura de internet: Lifeline + plan para bajos ingresos"),
        why: (pct <= 135 || onSNAPorMedicaid) ? tr("You qualify for Lifeline, and providers' own low-income plans often cost $10–$30.", "Usted califica para Lifeline, y los planes para bajos ingresos de las compañías suelen costar $10–$30.") : tr("Lifeline needs ≤135% of poverty, but many providers' low-income plans go higher.", "Lifeline exige ingresos de hasta el 135% del nivel de pobreza, pero los planes para bajos ingresos de muchas compañías aceptan ingresos más altos."),
        confidence: (pct <= 135 || onSNAPorMedicaid) ? "likely" : "possible", monthly: Math.min(save, num(p.internetBill)), effortMin: 20, dueDays: 14, links: [L.lifeline], source: "FCC Lifeline program rules (47 CFR 54.409)" }));
    }
    if (p.foodRunsOut) {
      tasks.push(task({ id: "foodweek", pillar: "food", draft: "foodweek", title: tr("Build a two-week menu around a weekly pantry pickup", "Arme un menú de dos semanas con una visita semanal a la despensa de alimentos"),
        why: tr("You said food runs out before the month does. A pantry day plus a protein-first menu stretches every dollar.", "Usted dijo que la comida se acaba antes de fin de mes. Un día fijo de despensa y un menú con proteína en cada comida hacen rendir cada dólar."),
        confidence: "likely", monthly: 60, effortMin: 30, dueDays: 5, links: [L.foodbank, L.l211], source: "Community organizer guidance; local pantry hours vary — confirm before you go" }));
    }

    /* ----- II. Health ----- */
    var expansion = NON_EXPANSION.indexOf(p.state) === -1;
    if (p.renewalDue) {
      var rd = daysOr(p.renewalDays, 14);
      tasks.push(task({ id: "renew", pillar: "health", draft: "renew", title: tr("Return your Medicaid/CHIP renewal packet", "Entregue su paquete de renovación de Medicaid/CHIP"),
        why: tr("Most people who lose Medicaid at renewal are still eligible — they lose it for paperwork.", "Muchas personas que pierden Medicaid al renovar todavía califican: lo pierden por el papeleo."),
        confidence: "likely", valueLabel: tr("Keeps coverage", "Mantiene su cobertura"), effortMin: 30, dueDays: Math.max(0, rd - 2), urgent: rd <= 14, links: [L.medicaid], source: "42 CFR 435.916 (annual renewals; 90-day reconsideration)" }));
    }
    if (p.uninsured) {
      var pregLimit = PREGNANCY_LIMIT_BELOW_200[p.state] || 200;
      // Medicaid counts the expected child in a pregnant person's household (42 CFR 435.603(b)); assume one.
      var pregPct = p.pregnant ? Math.round(income * 12 / fplAnnual(size + 1, p.state) * 100) : pct;
      var partialAdult = !expansion && PARTIAL_ADULT_COVERAGE[p.state] && pct <= 100;
      var medicaidLikely = (expansion && pct <= 138) || (p.pregnant && pregPct <= pregLimit) || partialAdult;
      var w = acaWindow(now);
      if (medicaidLikely) {
        tasks.push(task({ id: "coverage", pillar: "health", draft: "coverage", title: tr("Apply for Medicaid (any day of the year)", "Solicite Medicaid (cualquier día del año)"),
          why: p.pregnant && pregPct <= pregLimit ? tr("Pregnancy coverage counts your baby in your household, and the limit in your state is about " + pregLimit + "% of poverty or more — you're at about " + pregPct + "%.", "La cobertura por embarazo cuenta a su bebé como parte de su hogar, y el límite en su estado es de alrededor del " + pregLimit + "% del nivel de pobreza o más; usted está en alrededor del " + pregPct + "%.") :
            partialAdult ? partialAdultText(p.state) + "." : tr("Your state expanded Medicaid and your income is at or below 138% of poverty.", "Su estado amplió Medicaid y sus ingresos están en o por debajo del 138% del nivel de pobreza."),
          confidence: partialAdult && !(p.pregnant && pregPct <= pregLimit) && !(expansion && pct <= 138) ? "possible" : "likely", valueLabel: tr("Coverage", "Cobertura"), effortMin: 45, dueDays: 3, urgent: true, links: [L.medicaid, L.healthcare], meta: { route: "medicaid", pct: pct },
          source: "ACA §2001 expansion (138% FPL); expansion status per KFF/Medicaid.gov, Oct 2026; pregnancy limits per KFF, Jan 2026" }));
      } else if (pct >= ACA.minPct && pct <= ACA.maxPct) {
        var planYear = now.getMonth() >= 10 ? now.getFullYear() + 1 : now.getFullYear(); // Nov–Dec enrollment is for next year
        var maxPrem = income * (ACA.maxContributionPctByYear[planYear] || ACA.maxContributionPct) / 100;
        tasks.push(task({ id: "coverage", pillar: "health", draft: "coverage", title: w.open ? tr("Enroll in a Marketplace plan during Open Enrollment", "Inscríbase en un plan del Mercado de Seguros Médicos durante la Inscripción Abierta") : tr("Check for a Special Enrollment Period", "Vea si califica para un Período de Inscripción Especial"),
          why: tr("At about " + pct + "% of poverty you can get a premium tax credit. ", "Con alrededor del " + pct + "% del nivel de pobreza, puede recibir un crédito fiscal para la prima. ") + w.label + ".",
          confidence: "likely", valueLabel: tr("Subsidized coverage", "Cobertura con ayuda"), effortMin: 60, dueDays: w.open ? Math.max(1, daysBetween(now, w.due)) : 60, absDue: w.open ? w.due : null, urgent: w.open && daysBetween(now, w.due) <= 45,
          links: [L.healthcare, L.hrsa], meta: { route: "aca", pct: pct, maxPremium: maxPrem }, source: ACA.source }));
      } else {
        tasks.push(task({ id: "coverage", pillar: "health", draft: "coverage", title: tr("Find low-cost care while you sort out coverage", "Busque atención de bajo costo mientras resuelve su cobertura"),
          why: (!expansion && pct < 100) ? tr("Your state hasn't expanded Medicaid, which leaves a coverage gap below 100% of poverty. Community health centers charge on a sliding scale.", "Su estado no ha ampliado Medicaid, lo que deja una brecha de cobertura por debajo del 100% del nivel de pobreza. Los centros de salud comunitarios cobran según sus ingresos.") : tr("Community health centers serve everyone on a sliding scale.", "Los centros de salud comunitarios atienden a todos y cobran según sus ingresos."),
          confidence: "possible", valueLabel: tr("Lower-cost care", "Atención más barata"), effortMin: 20, dueDays: 7, links: [L.hrsa, L.healthcare], meta: { route: "gap", pct: pct, maxPremium: 0 },
          source: "HRSA Health Center Program sliding-fee requirements" }));
        if (!expansion && pct < 100) flags.push("coverage-gap");
      }
    }
    if (p.uninsured && (num(p.kidsUnder5) + num(p.kids5to17)) > 0 && pct <= 200) {
      var cov = tasks.filter(function (t) { return t.id === "coverage"; })[0];
      if (cov) cov.why += tr(" Children in your household likely qualify for Medicaid/CHIP in every state — apply for them any time of year.", " Es probable que los niños de su hogar califiquen para Medicaid/CHIP en cualquier estado; puede solicitarlo para ellos en cualquier momento del año.");
    }
    if (num(p.rxMonthly) > 0) {
      tasks.push(task({ id: "rx", pillar: "health", draft: "rx", title: tr("Lower prescription costs (cash price, generic, 90-day, assistance)", "Baje el costo de sus recetas (precio en efectivo, genéricos, 90 días, ayuda)"),
        why: tr("You spend about $" + Math.round(num(p.rxMonthly)) + "/mo on prescriptions" + (p.rxTrouble ? " and cost is getting in the way of taking them." : "."), "Usted gasta unos $" + Math.round(num(p.rxMonthly)) + " al mes en recetas" + (p.rxTrouble ? " y el costo le impide tomarlas como le indicaron." : ".")),
        confidence: "possible", monthly: num(p.rxMonthly) * 0.3, effortMin: 25, dueDays: p.rxTrouble ? 3 : 10, urgent: !!p.rxTrouble, links: [L.needymeds], source: "Estimate: 30% average savings from price comparison/generic switch — your result will vary" }));
    }
    if (num(p.medBill) > 0 && pct <= 400) {
      tasks.push(task({ id: "charity", pillar: "health", draft: "charity", title: tr("Request hospital financial assistance (charity care)", "Pida ayuda financiera al hospital (atención de caridad)"),
        why: pct <= 200 ? tr("Many nonprofit hospitals forgive bills in full below 200% of poverty.", "Muchos hospitales sin fines de lucro perdonan la cuenta completa por debajo del 200% del nivel de pobreza.") : tr("Many nonprofit hospitals discount bills up to 300–400% of poverty.", "Muchos hospitales sin fines de lucro dan descuentos hasta el 300–400% del nivel de pobreza."),
        confidence: pct <= 200 ? "likely" : "possible", oneTime: pct <= 200 ? num(p.medBill) : num(p.medBill) * 0.5, effortMin: 60, dueDays: 14,
        links: [L.cfpbMed], meta: { pct: pct }, source: "IRS §501(r) financial assistance policy requirements; hospital policies vary" }));
    }
    if (p.paDenied) {
      tasks.push(task({ id: "pa", pillar: "health", draft: "pa", title: tr("Appeal the prior-authorization denial", "Apele la negación de la autorización previa"),
        why: tr("You have a right to an internal appeal and an independent external review. Many denials are overturned.", "Tiene derecho a una apelación interna y a una revisión externa independiente. Muchas negaciones se revierten."),
        confidence: "possible", valueLabel: tr("Unlocks care", "Desbloquea la atención"), effortMin: 60, dueDays: 14, links: [L.healthcare], source: "45 CFR 147.136 (internal claims and appeals, external review)" }));
    }

    /* ----- III. Housing ----- */
    var rent = num(p.housingCost);
    var burden = income ? Math.round(rent / income * 100) : 0;
    if (p.evictionNotice) {
      tasks.push(task({ id: "eviction", pillar: "housing", draft: "eviction", title: tr("Get legal aid on the eviction notice — today", "Busque ayuda legal por el aviso de desalojo hoy mismo"),
        why: tr("Notice deadlines can be 3–5 days. Tenants with a lawyer are far more likely to stay housed.", "Los plazos de un aviso pueden ser de 3 a 5 días. Los inquilinos con abogado tienen muchas más probabilidades de conservar su vivienda."), confidence: "likely",
        valueLabel: tr("Keeps you housed", "Conserva su vivienda"), effortMin: 30, dueDays: 1, urgent: true, escalate: "legal", links: [L.lawhelp, L.l211], source: "Navigation only — not legal advice" }));
    }
    if (p.tenure === "rent" && num(p.rentIncreasePct) > 0) {
      var capInfo = rentCapFor(p.state, now.getFullYear());
      var capped = capInfo ? capInfo.law : null;
      var capPct = capInfo ? capInfo.cap : 10;
      var over = capped ? Math.max(0, num(p.rentIncreasePct) - capPct) : 0;
      tasks.push(task({ id: "rentIncrease", pillar: "housing", draft: "rentIncrease", title: capped && over > 0 ? tr("Challenge a rent increase that may exceed the state cap", "Impugne un aumento de renta que puede superar el límite estatal") : tr("Push back on the rent increase in writing", "Responda por escrito al aumento de renta"),
        why: capped ? (over > 0 ? tr("Your increase (" + num(p.rentIncreasePct) + "%) is above the " + capPct + "% " + (capInfo.published ? now.getFullYear() + " cap" : "maximum") + " under " + capped + ".", "Su aumento (" + num(p.rentIncreasePct) + "%) supera el " + (capInfo.published ? "límite de " + now.getFullYear() + " del " + capPct + "%" : "máximo del " + capPct + "%") + " según " + capInfo.local + ".") : tr("Your state caps increases on many units (" + capped + ") — confirm yours is covered.", "Su estado limita los aumentos en muchas viviendas (" + capInfo.local + "); confirme si la suya está cubierta.")) : tr("Your state has no statewide cap, but a written request often lowers an increase.", "Su estado no tiene un límite estatal, pero una solicitud por escrito suele bajar el aumento."),
        confidence: capped && over > 0 ? "likely" : "possible", monthly: capped && over > 0 ? rent * over / (100 + num(p.rentIncreasePct)) : 0,
        valueLabel: capped && over > 0 ? null : tr("Negotiation", "Negociación"), effortMin: 30, dueDays: 7, links: [L.lawhelp], source: capped ? capped : "Local rules vary — confirm with legal aid" }));
    }
    if (p.tenure === "rent" && (p.evictionNotice || p.behindRent || burden >= 50)) {
      tasks.push(task({ id: "erap", pillar: "housing", draft: "erap", title: tr("Apply for emergency rental assistance", "Solicite ayuda de emergencia para la renta"),
        why: p.evictionNotice || p.behindRent ? tr("You're behind or facing eviction — assistance can pay the landlord directly.", "Está atrasado o enfrenta un desalojo: la ayuda puede pagarle directamente al dueño.") : tr("Rent takes " + burden + "% of income (over 50% is 'severely cost-burdened').", "La renta se lleva el " + burden + "% de sus ingresos (más del 50% se considera una carga severa)."),
        confidence: "possible", oneTime: rent * 2, effortMin: 60, dueDays: p.evictionNotice ? 2 : 7, urgent: !!p.evictionNotice, links: [L.l211, L.hudRent], source: "County/city/charity programs; availability changes weekly" }));
    }
    if (p.tenure === "rent" && burden >= 40) {
      tasks.push(task({ id: "affordable", pillar: "housing", draft: "affordable", title: tr("Join affordable-housing lotteries and waitlists", "Inscríbase en sorteos y listas de espera de vivienda asequible"),
        why: tr("Rent is " + burden + "% of income. Below-market and LIHTC units are priced to income.", "La renta es el " + burden + "% de sus ingresos. Las viviendas a precio por debajo del mercado y las de LIHTC tienen precios según los ingresos."),
        confidence: "possible", valueLabel: tr("Long-term rent cut", "Renta más baja a largo plazo"), effortMin: 45, dueDays: 30, links: [L.hudRent], source: "HUD/LIHTC program rules; local lotteries vary" }));
    }
    if (p.tenure === "rent" && (num(p.rentIncreasePct) > 0 || p.evictionNotice || p.repairs)) {
      tasks.push(task({ id: "tenantOrg", pillar: "housing", draft: "tenantOrg", title: tr("Talk with neighbors: start a tenant association", "Hable con sus vecinos: formen una asociación de inquilinos"),
        why: tr("Rent and repair problems are usually building-wide. Collective requests carry weight.", "Los problemas de renta y reparaciones suelen afectar a todo el edificio. Las peticiones colectivas tienen peso."),
        confidence: "possible", valueLabel: tr("Collective power", "Fuerza colectiva"), effortMin: 60, dueDays: 45, organizer: true, links: [L.lawhelp], source: "Organizer layer" }));
    }

    /* ----- IV. Energy ----- */
    var bill = num(p.energyBill);
    if (p.shutoff) {
      var sd = daysOr(p.shutoffDays, 5);
      tasks.push(task({ id: "shutoff", pillar: "energy", draft: "shutoff", title: p.medEquip ? tr("Stop the shutoff: medical certificate + payment plan", "Detenga el corte: certificado médico + plan de pagos") : tr("Stop the shutoff: call for a payment plan", "Detenga el corte: llame para pedir un plan de pagos"),
        why: p.medEquip ? tr("Someone relies on powered medical equipment — a clinician's certificate can delay disconnection.", "Alguien depende de equipo médico que necesita electricidad: un certificado de un profesional de salud puede retrasar el corte.") : tr("Utilities must offer options before disconnecting in most states — but you have to call first.", "En la mayoría de los estados, la compañía debe ofrecer opciones antes de cortar el servicio, pero usted tiene que llamar primero."),
        confidence: "likely", valueLabel: tr("Keeps power on", "Mantiene la luz"), effortMin: 30, dueDays: Math.max(0, sd - 2), urgent: true, links: [L.liheap, L.l211], source: "State utility commission shutoff rules; protections vary by state and season" }));
    }
    if (!has(b, "utilDiscount") && bill > 0 && (pct <= 200 || (p.state === "CA" && pct <= 250))) {
      tasks.push(task({ id: "discount", pillar: "energy", draft: "discount", title: p.state === "CA" ? (pct > 200 ? tr("Enroll in FERA (18% off electric)", "Inscríbase en FERA (18% de descuento en electricidad)") : tr("Enroll in CARE (30–35% off electric)", "Inscríbase en CARE (30–35% de descuento en electricidad)")) : tr("Enroll in your utility's low-income rate", "Inscríbase en la tarifa para bajos ingresos de su compañía de servicios"),
        why: tr("Discount rates lower every bill, not just one. Most utilities set the limit near 200% of poverty.", "Las tarifas con descuento bajan cada factura, no solo una. La mayoría de las compañías fija el límite cerca del 200% del nivel de pobreza."),
        confidence: p.state === "CA" ? "likely" : "possible", monthly: bill * (p.state === "CA" && pct > 200 ? 0.1 : 0.2), effortMin: 15, dueDays: 7, links: [L.l211], source: p.state === "CA" ? "CPUC CARE (≤200% FPL) and FERA (200–250% FPL, electric only), income limits Jun 1, 2026–May 31, 2027" : "Utility-specific programs — confirm yours" }));
    }
    if (!has(b, "liheap") && bill > 0 && pct <= 150) {
      tasks.push(task({ id: "liheap", pillar: "energy", draft: "liheap", title: tr("Apply for LIHEAP energy assistance", "Solicite ayuda de energía de LIHEAP"),
        why: tr("Your income is within LIHEAP's federal ceiling (150% of poverty). ", "Sus ingresos están dentro del límite federal de LIHEAP (150% del nivel de pobreza). ") + (p.shutoff ? tr("Ask for crisis assistance.", "Pida asistencia de crisis.") : ""),
        confidence: "likely", oneTime: 400, effortMin: 45, dueDays: p.shutoff ? 2 : 14, urgent: !!p.shutoff, links: [L.liheap, L.l211], source: "42 U.S.C. 8624 (greater of 150% FPL or 60% of state median income); funded for FY2026, partly funded for FY2027 under a stopgap law; benefit amounts vary by state" }));
    }
    if (bill > 0) {
      tasks.push(task({ id: "rateplan", pillar: "energy", draft: "rateplan", title: tr("Decode the bill and check your rate plan", "Entienda su factura y revise su plan de tarifas"),
        why: tr("The wrong rate plan for your routine can cost $10–$30 a month.", "Un plan de tarifas que no va con su rutina puede costarle $10–$30 al mes."), confidence: "possible", monthly: Math.min(30, bill * 0.08), effortMin: 20, dueDays: 21,
        links: [], source: "Estimate: 8% average from plan switching — run your utility's free comparison" }));
    }
    if (bill > 0 && pct <= 200) {
      tasks.push(task({ id: "weatherize", pillar: "energy", draft: "weatherize", title: tr("Request free weatherization + do the 20-minute DIY check", "Pida la climatización gratuita (weatherization) y haga la revisión casera de 20 minutos"),
        why: tr("Weatherization is free up to 200% of poverty in most states; renters can qualify too.", "La climatización es gratis hasta el 200% del nivel de pobreza en la mayoría de los estados; los inquilinos también pueden calificar."), confidence: "possible", monthly: Math.min(35, bill * 0.12), effortMin: 30, dueDays: 30,
        links: [L.wap], source: "DOE Weatherization Assistance Program" }));
    }
    if (bill > 0 && income > 0 && bill / income >= 0.06) {
      tasks.push(task({ id: "ratepayer", pillar: "energy", draft: "ratepayer", title: tr("Add your voice to the next utility rate case", "Haga oír su voz en el próximo caso de tarifas de servicios públicos"),
        why: tr("Energy takes " + Math.round(bill / income * 100) + "% of your income (over 6% is considered unaffordable). Commissions hear from customers.", "La energía se lleva el " + Math.round(bill / income * 100) + "% de sus ingresos (más del 6% se considera inasequible). Las comisiones escuchan a los clientes."),
        confidence: "possible", valueLabel: tr("Collective power", "Fuerza colectiva"), effortMin: 20, dueDays: 45, organizer: true, links: [], source: "Organizer layer" }));
    }

    /* ----- V. Family ----- */
    var cc = num(p.childcareCost);
    if (cc > 0 && !has(b, "childcareSubsidy") && pct <= 300) {
      tasks.push(task({ id: "childcare", pillar: "family", draft: "childcare", title: tr("Apply for child care assistance", "Solicite ayuda para el cuidado infantil") + (kidsU5 && pct <= 100 ? tr(" (and Head Start)", " (y Head Start)") : ""),
        why: pct <= 200 ? tr("Your income is in range for most states' subsidy programs.", "Sus ingresos están en el rango de los programas de subsidio de la mayoría de los estados.") : tr("Some states' limits reach 85% of state median income — worth checking.", "Los límites de algunos estados llegan al 85% del ingreso medio estatal; vale la pena revisarlo."),
        confidence: pct <= 200 ? "likely" : "possible", monthly: cc * (pct <= 200 ? 0.6 : 0.3), effortMin: 60, dueDays: 7, links: [L.childcare, L.headstart], source: "CCDF (45 CFR 98.21; up to 85% SMI) — states set lower limits and co-pays" }));
    }
    if (cc > 0 && p.employerDCAP !== "no") {
      var dc = Math.min(cc * 12, DCAP_LIMIT.amount) * (pct > 250 ? 0.22 : 0.12) / 12;
      tasks.push(task({ id: "dcap", pillar: "family", draft: "dcap", title: tr("Use a Dependent Care FSA (pre-tax child care)", "Use una cuenta FSA para el cuidado de dependientes (cuidado infantil antes de impuestos)"),
        why: p.employerDCAP === "yes" ? tr("Your employer offers one.", "Su empleador ofrece una.") : tr("Ask HR — many employers offer one and enrollment is usually once a year.", "Pregunte a Recursos Humanos: muchos empleadores la ofrecen y la inscripción suele ser una vez al año."), confidence: p.employerDCAP === "yes" ? "likely" : "possible",
        monthly: dc, effortMin: 20, dueDays: 30, links: [], source: DCAP_LIMIT.source + " · effective " + DCAP_LIMIT.effective }));
    }
    if (p.needLeave) {
      var st = PAID_LEAVE_STATES[p.state];
      tasks.push(task({ id: "leave", pillar: "family", draft: "leave", title: st ? tr("Request leave and file for ", "Pida licencia y solicite ") + st : tr("Request job-protected leave (FMLA)", "Pida licencia con protección de empleo (FMLA)"),
        why: st ? tr("Your state pays partial wages during family or medical leave.", "Su estado paga parte del salario durante una licencia familiar o médica.") : tr("FMLA protects your job for up to 12 weeks if you're eligible.", "La FMLA protege su empleo hasta por 12 semanas si usted califica."),
        confidence: "possible", valueLabel: st ? tr("Paid, protected leave", "Licencia pagada y protegida") : tr("Job protection", "Protección del empleo"), effortMin: 45, dueDays: 14, links: [L.fmla], source: "29 CFR Part 825 (FMLA)" + (st ? "; " + st : "") }));
    }
    if (p.caringAdult) {
      tasks.push(task({ id: "caregiverPay", pillar: "family", draft: "caregiverPay", title: p.state === "CA" ? tr("Ask about IHSS — get paid for care you give", "Pregunte por IHSS: reciba pago por el cuidado que ya da") : tr("Ask about paid family caregiver programs", "Pregunte por programas que pagan a familiares cuidadores"),
        why: tr("Many Medicaid programs pay family members for daily care they're already giving.", "Muchos programas de Medicaid pagan a familiares por el cuidado diario que ya dan."), confidence: "possible", valueLabel: tr("Possible caregiver pay", "Posible pago como cuidador"), effortMin: 45, dueDays: 14,
        links: [L.eldercare], source: "Medicaid HCBS / self-directed services (state-specific)" }));
      tasks.push(task({ id: "respite", pillar: "family", draft: "respite", title: tr("Schedule one break for yourself this week", "Programe un descanso para usted esta semana"),
        why: tr("Caregiver strain is a health risk. Respite is care for the caregiver.", "El desgaste del cuidador es un riesgo para la salud. El respiro es cuidado para quien cuida."), confidence: "likely", valueLabel: tr("Your health", "Su salud"), effortMin: 20, dueDays: 7,
        links: [L.respite, L.lifeline988], source: "Community organizer guidance" }));
    }

    /* ----- VI. Work, income & training (WorkBridge; English-only) -----
       A job loss sets off deadlines in the other pillars, so some of these steps
       land there (health, food) while WorkBridge holds the work itself. */
    var jobEnd = daysOr(p.jobEndDays, null);
    var covEnd = daysOr(p.coverageEndDays, null); // days since job-based coverage ended; the 60-day windows run from this, not from the job's end
    if (p.jobLoss) {
      // UI pays from the week you file; if the job ended more than a week ago the deadline is today.
      tasks.push(task({ id: "ui", pillar: "work", draft: "ui", title: tr("File for unemployment this week — it pays from the week you file", "Solicite el seguro de desempleo esta semana"),
        why: "You paid into unemployment insurance with every paycheck. Benefits start the week you file, not the day the job ended, so each week of delay is money you don't get back. Hours cut, not lost? Partial benefits exist.",
        confidence: "likely", valueLabel: "Partial wage replacement", effortMin: 45, urgent: true, dueDays: jobEnd === null ? 7 : Math.max(0, 7 - jobEnd),
        links: [L.ui, L.ajc], source: "State unemployment insurance laws (file in the state where you worked); USA.gov unemployment benefits. Most states replace about half of prior wages up to a weekly cap for up to 26 weeks" }));
      tasks.push(task({ id: "owed", pillar: "work", draft: "owed", title: p.warnLarge ? "Collect what you're owed — and check whether the WARN Act's 60-day notice applied" : "Collect what you're owed: final pay, unused PTO, severance terms, your file",
        why: "Final wages and earned leave are debts the employer owes you. A severance release should never be signed the same day" + (p.warnLarge ? ", and a large employer that gave little notice may owe up to 60 days of pay" : "") + ".",
        confidence: "likely", valueLabel: "Money already yours", effortMin: 40, dueDays: 7,
        links: p.warnLarge ? [L.warn, L.whd, L.lawhelp] : [L.whd, L.lawhelp], source: "FLSA and state final-pay laws; OWBPA, 29 U.S.C. 626(f) (workers 40+: 21 days to consider a release, 7 to revoke; 45 days in a group layoff); WARN Act, 29 U.S.C. 2101–2109 (employers of 100+, 60 days' notice)" }));
    }
    if (p.lostCoverage) {
      // The Marketplace and COBRA windows run 60 days from the day coverage ends. Without that date, the step is to pin it down within a week.
      tasks.push(task({ id: "coverageClock", pillar: "health", draft: "coverageClock",
        title: covEnd === null ? "Find out the exact day job-based coverage ends — the 60-day clocks start from it" : "Beat the 60-day clock on health coverage: Medicaid, Marketplace, or COBRA",
        why: covEnd === null ? "Losing job-based insurance opens a 60-day Marketplace Special Enrollment Period and a 60-day COBRA election window, both counted from the day coverage ends — not the day the job ended. Get that date in writing, then enter it here for the real deadline. Medicaid is open any day."
          : "Losing job-based insurance opens a 60-day Special Enrollment Period and a 60-day COBRA election window, counted from the day coverage ended. Medicaid is open any day and judges income now. Miss the 60 days and you may wait until Open Enrollment.",
        confidence: "likely", valueLabel: "Keeps coverage", effortMin: 60, urgent: true, dueDays: covEnd === null ? 7 : Math.max(0, 60 - covEnd),
        links: [L.healthcare, L.medicaid, L.cobra, L.hrsa], source: "45 CFR 155.420(c)(2) and (d)(1) (loss of coverage SEP: 60 days before or after the loss); COBRA, 29 U.S.C. 1165(a)(1) (election period ends 60 days after the later of coverage loss or the election notice; coverage retroactive); Medicaid enrollment is year-round" }));
    }
    if (p.jobLoss && has(b, "snap")) {
      tasks.push(task({ id: "snapReport", pillar: "food", draft: "snapReport", title: "Report the income drop to SNAP — your benefit should go up",
        why: "SNAP is figured on current income, but a drop only raises the benefit once it's reported, and the increase starts from the report. Ten minutes on the phone.",
        confidence: "likely", valueLabel: "Higher SNAP benefit", effortMin: 15, dueDays: 10,
        links: [L.snapState, L.snapET], source: "7 CFR 273.12 (reporting changes; reported decreases in income take effect for the next issuance) and 7 CFR 273.2(i) (expedited service within 7 days)" }));
    }
    if (p.jobLoss || p.newGrad || p.wantsTraining) {
      tasks.push(task({ id: "ajc", pillar: "work", draft: "ajc", title: "Visit an American Job Center — free help from a person, and money for training",
        why: "About 2,300 public job centers offer free career counseling, help filing for unemployment, and Individual Training Accounts that can pay for training. No app or AI required — you talk to a person.",
        confidence: "likely", valueLabel: "Free help; training funds", effortMin: 90, dueDays: 14,
        links: [L.ajc, L.jobTraining, L.vaJobs], source: "Workforce Innovation and Opportunity Act (P.L. 113-128), Title I adult and dislocated worker programs; Individual Training Accounts under 20 CFR 680.300" }));
    }
    if (p.wantsTraining || p.newGrad) {
      tasks.push(task({ id: "training", pillar: "work", draft: "training", title: "Pick training with a paycheck at the end: apprenticeship, a sectoral program, or a short Pell-funded course",
        why: "The programs proven in randomized trials are free, built with employers, and end in a job — earnings 14–30% higher for 7 to 14 years. Programs that charge you or push loans don't have that record.",
        confidence: "possible", valueLabel: "Earnings +14–30% in trials", effortMin: 90, dueDays: 30,
        links: [L.apprenticeship, L.snapET, L.pell, L.yearup, L.perscholas], source: "Year Up PACE randomized trial (ACF/OPRE, 2021); MDRC WorkAdvance 7-year follow-up (Per Scholas); Urban Institute, American Apprenticeship Initiative earnings brief; Workforce Pell final rule, 91 FR (May 19, 2026), effective July 1, 2026" }));
    }
    if (p.newGrad) {
      tasks.push(task({ id: "firstJob", pillar: "work", draft: "firstJob", title: "First job after school: the moves with evidence behind them",
        why: "Recent graduates' unemployment now runs about 1.3 points above everyone else's. Paid experience with an employer attached — internships, co-ops, apprenticeships, residencies — is what changes the odds, not another certificate.",
        confidence: "likely", valueLabel: "A first job that uses your training", effortMin: 60, dueDays: 14,
        links: [L.ajc, L.apprenticeship, L.nrp], source: "Federal Reserve Bank of New York, Labor Market for Recent College Graduates (Nov. 2, 2026); Strada/Burning Glass, Talent Disrupted (2024); Nunley et al., résumé field experiment (Auburn, 2014); Vizient/AACN Nurse Residency Program fact sheet; Stanford Digital Economy Lab, Canaries in the Coal Mine (Aug. 2026)" }));
    }
    if (p.aiAffected) {
      tasks.push(task({ id: "aiRights", pillar: "work", draft: "aiRights", title: "Know your rights when software screens, monitors, or replaces you",
        why: "No federal law yet limits AI in hiring or layoffs, but discrimination law applies to whatever the tool does, Illinois and New York City require notice, and large layoffs still require 60 days' notice. A written record is what makes any of it enforceable.",
        confidence: "likely", valueLabel: "Your rights, in writing", effortMin: 45, dueDays: 14,
        links: [L.eeoc, L.nlrb, L.warn, L.nnuAI], source: "Title VII, ADA and ADEA as applied to automated tools (EEOC); Illinois HB 3773, 775 ILCS 5/2-102(L) (effective Jan. 1, 2026); NYC Local Law 144 of 2021 (automated employment decision tools); WARN Act; Oregon 2025 Or. Laws ch. 378 and Washington HB 2155 (2026) on the title \"nurse\"" }));
    }
    if (p.aiAffected || p.jobLoss) {
      tasks.push(task({ id: "organize", pillar: "work", draft: "organize", title: "Talk with coworkers: AI, staffing and automation are things you can bargain over",
        why: "The National Labor Relations Act protects most private-sector workers who act together over working conditions, union or not. The research on AI and jobs finds the losses land where workers have the least say.",
        confidence: "possible", valueLabel: "Collective leverage", effortMin: 60, dueDays: 45, organizer: true,
        links: [L.nlrb, L.formUnion, L.nnuAI], source: "National Labor Relations Act §7, 29 U.S.C. 157 (protected concerted activity); NLRB, Your Rights" }));
    }
    if (p.jobLoss && has(b, "medicaid") && NON_EXPANSION.indexOf(p.state) === -1) {
      tasks.push(task({ id: "medicaidWork", pillar: "health", draft: "medicaidWork", title: "Keep Medicaid in 2027: the 80-hours-a-month rule and what counts",
        why: "Starting by January 2027, most states must require many adults on Medicaid expansion to show 80 hours a month of work, training, school or volunteering. Training and job-center programs count, and a log protects you.",
        confidence: "possible", valueLabel: "Keeps coverage", effortMin: 20, dueDays: 60,
        links: [L.medicaid, L.snapET, L.ajc], source: "P.L. 119-21 (2025) §71119, adding Social Security Act §1902(xx): community engagement requirement, 80 hours/month, states to implement no later than Jan. 1, 2027 (extensions possible); exemptions include parents of dependent children 13 and under, pregnant and postpartum people, people with disabilities, and others. Confirm your state's start date" }));
    }

    /* ----- Situation summary per pillar ----- */
    var dx = {};
    Object.keys(PILLARS).forEach(function (k) {
      var ts = tasks.filter(function (t) { return t.pillar === k; });
      var urgentT = ts.filter(function (t) { return t.urgent; });
      var enrollT = ts.filter(function (t) { return /^(snap|wic|meals|lifeline|coverage|coverageClock|discount|liheap|childcare|charity|erap|ui|ajc|snapReport)$/.test(t.id); });
      var status, words;
      if (urgentT.length) { status = "at-risk"; words = tr("Something has a deadline: ", "Hay una fecha límite: ") + urgentT[0].title.toLowerCase() + "."; }
      else if (enrollT.length) { status = "eligible"; words = tr("You likely qualify for help you're not getting yet.", "Es probable que califique para ayuda que todavía no recibe."); }
      else if (ts.length) { status = "stretched"; words = tr("Stable, but there's money to save.", "Estable, pero hay dinero que ahorrar."); }
      else { status = "stable"; words = tr("Nothing urgent here based on what you told me.", "Nada urgente aquí según lo que me contó."); }
      dx[k] = { status: status, words: words, count: ts.length };
    });

    /* ----- Rank: urgent first, then dollars per hour of effort ----- */
    // Due dates are anchored to the day of intake (countdowns like "shutoff in 5 days"
    // were true on that day), so returning later shows the real time left — or overdue.
    var anchor = startOfDay(p.intakeDate ? new Date(p.intakeDate) : now);
    var today0 = startOfDay(now);
    tasks.forEach(function (t) {
      t.dueDate = t.absDue ? startOfDay(t.absDue) : addDays(anchor, t.dueDays);
      t.daysLeft = daysBetween(today0, t.dueDate);
      t.overdue = t.daysLeft < 0;
      var value = t.monthly + t.oneTime / 12;
      t.score = (t.urgent ? 100000 - t.daysLeft * 500 + (t.escalate ? 400 : 0) : 0) + (t.overdue ? 5000 : 0) + (value / (t.effortMin / 60)) + (t.valueLabel && !value ? 40 : 0) - (t.organizer ? 30 : 0);
      t.horizon = t.daysLeft <= 30 ? 30 : t.daysLeft <= 60 ? 60 : 90;
    });
    tasks.sort(function (a, c) { return c.score - a.score; });

    var potMonthly = tasks.reduce(function (s, t) { return s + t.monthly; }, 0);
    var potOnce = tasks.reduce(function (s, t) { return s + t.oneTime; }, 0);

    return { pct: pct, fplAnnual: fplAnnual(size, p.state), burden: burden, tasks: tasks, dx: dx, flags: flags, potential: { monthly: potMonthly, oneTime: potOnce }, ruleset: RULESET };
  }

  /* ---------- Policy Watch (Affordability Agenda items) ---------- */
  var POLICY = [
    { pillar: "food", item: "Restore SNAP benefits and eligibility", itemEs: "Restaurar los beneficios y la elegibilidad de SNAP", ref: "I.2e", stake: function (p, r) { return has(p.benefits, "snap") || r.tasks.some(function (t) { return t.id === "snap"; }) ? tr("Your household uses or qualifies for SNAP — benefit and eligibility rules directly change your grocery budget.", "Su hogar usa SNAP o califica para él: las reglas de beneficios y elegibilidad cambian directamente su presupuesto de comida.") : tr("Indirect: SNAP spending supports local grocers and food banks you may rely on.", "Indirecto: el gasto de SNAP sostiene a los comercios locales y bancos de alimentos en los que usted puede apoyarse."); } },
    { pillar: "food", item: "Revive an Affordable Connectivity Program–style broadband discount", itemEs: "Revivir un descuento de internet como el Programa de Conectividad Asequible", ref: "I.3", stake: function (p) { return num(p.internetBill) ? tr("A $30/mo discount would cut your $" + Math.round(num(p.internetBill)) + " internet bill to about $" + Math.max(0, Math.round(num(p.internetBill) - 30)) + ".", "Un descuento de $30 al mes bajaría su factura de internet de $" + Math.round(num(p.internetBill)) + " a unos $" + Math.max(0, Math.round(num(p.internetBill) - 30)) + ".") : tr("Would lower home internet costs for low-income households.", "Bajaría el costo de internet en casa para hogares de bajos ingresos."); } },
    { pillar: "food", item: "Roll back tariffs on household staples", itemEs: "Reducir los aranceles a los productos básicos del hogar", ref: "I.1", stake: function () { return tr("Lower prices on groceries and essentials over time; effect depends on which goods are covered.", "Precios más bajos en comestibles y artículos esenciales con el tiempo; el efecto depende de qué productos se incluyan."); } },
    { pillar: "health", item: "Restore enhanced ACA premium tax credits", itemEs: "Restaurar los créditos fiscales ampliados para las primas de la ACA", ref: "II.2a", stake: function (p, r) { return r.pct >= 100 && r.pct <= 600 ? tr("At " + r.pct + "% of poverty, enhanced credits would lower the most you pay for a benchmark plan (and remove the 400% cliff).", "Con el " + r.pct + "% del nivel de pobreza, los créditos ampliados bajarían lo máximo que usted paga por un plan de referencia (y quitarían el límite del 400%).") : tr("Mostly affects households between 100% and 600%+ of poverty buying their own insurance.", "Afecta sobre todo a hogares entre el 100% y más del 600% del nivel de pobreza que compran su propio seguro."); } },
    { pillar: "health", item: "Cap out-of-pocket drug costs and require PBM transparency", itemEs: "Limitar el costo de los medicamentos y exigir transparencia a los PBM", ref: "II.1a–b", stake: function (p) { return num(p.rxMonthly) ? tr("You pay about $" + Math.round(num(p.rxMonthly)) + "/mo for prescriptions — a cap or PBM reform could lower that.", "Usted paga unos $" + Math.round(num(p.rxMonthly)) + " al mes en recetas: un límite o una reforma de los PBM podría bajarlo.") : tr("Would cap what insured people pay at the pharmacy counter.", "Limitaría lo que pagan en la farmacia las personas aseguradas."); } },
    { pillar: "health", item: "Reform prior authorization", itemEs: "Reformar la autorización previa", ref: "II.2d", stake: function (p) { return p.paDenied ? tr("You're appealing a denial right now — faster, more transparent rules would help directly.", "Usted está apelando una negación ahora mismo: reglas más rápidas y transparentes le ayudarían directamente.") : tr("Faster approvals and fewer care delays.", "Aprobaciones más rápidas y menos retrasos en la atención."); } },
    { pillar: "housing", item: "Expand the Low-Income Housing Tax Credit and build 4M homes", itemEs: "Ampliar el Crédito Fiscal para Viviendas de Bajos Ingresos y construir 4 millones de viviendas", ref: "III.3, III.5", stake: function (p, r) { return r.burden >= 30 ? tr("Rent is " + r.burden + "% of your income. More affordable units means more lotteries you can win.", "La renta es el " + r.burden + "% de sus ingresos. Más viviendas asequibles significan más sorteos que puede ganar.") : tr("Long-term pressure on rents in your area.", "Presión a largo plazo sobre las rentas en su área."); } },
    { pillar: "energy", item: "Invest in LIHEAP and protect ratepayers from data-center costs", itemEs: "Invertir en LIHEAP y proteger a los clientes de los costos de los centros de datos", ref: "IV.8–9", stake: function (p) { return num(p.energyBill) ? tr("Your $" + Math.round(num(p.energyBill)) + "/mo energy bill depends on how grid costs are split between homes and large new users.", "Su factura de energía de $" + Math.round(num(p.energyBill)) + " al mes depende de cómo se reparten los costos de la red entre hogares y grandes usuarios nuevos.") : tr("Keeps residential rates from absorbing large-load costs.", "Evita que las tarifas residenciales absorban los costos de grandes consumidores."); } },
    { pillar: "family", item: "National paid family and medical leave", itemEs: "Licencia familiar y médica pagada a nivel nacional", ref: "V.1–2", stake: function (p) { return p.needLeave ? (PAID_LEAVE_STATES[p.state] ? tr("Your state already has paid leave; a national program would set a floor everywhere.", "Su estado ya tiene licencia pagada; un programa nacional fijaría un mínimo en todo el país.") : tr("Your state has no paid leave program — a national one would pay part of your wages during leave.", "Su estado no tiene un programa de licencia pagada: uno nacional pagaría parte de su salario durante la licencia.")) : tr("Would replace part of wages during family or medical leave.", "Reemplazaría parte del salario durante una licencia familiar o médica."); } },
    { pillar: "family", item: "Expand the Child Tax Credit and Child & Dependent Care Credit", itemEs: "Ampliar el Crédito Tributario por Hijos y el Crédito por Cuidado de Hijos y Dependientes", ref: "V.3", stake: function (p) { var k = num(p.kidsUnder5) + num(p.kids5to17); return k ? tr("With " + k + " child(ren), credit expansions would put more back in your tax refund.", "Con " + k + " hijo(s), ampliar los créditos le devolvería más en su reembolso de impuestos.") : tr("Mainly benefits families with children.", "Beneficia sobre todo a familias con hijos."); } },
    { pillar: "family", item: "Caregiver tax refund and senior care stipend", itemEs: "Reembolso de impuestos para cuidadores y apoyo para el cuidado de personas mayores", ref: "V.4–5", stake: function (p) { return p.caringAdult ? tr("You're caring for an adult — a caregiver credit or stipend would recognize that work.", "Usted cuida a un adulto: un crédito o un apoyo para cuidadores reconocería ese trabajo.") : tr("Supports families caring for older or disabled relatives.", "Apoya a familias que cuidan a parientes mayores o con discapacidad."); } }
  ];

  global.LWR = {
    RULESET: RULESET, FPL: FPL, SNAP: SNAP, ACA: ACA, STATES: STATES, PILLARS: PILLARS, LINKS: L,
    PAID_LEAVE_STATES: PAID_LEAVE_STATES, RENT_CAP_STATES: RENT_CAP_STATES, NON_EXPANSION: NON_EXPANSION, PREGNANCY_LIMIT_BELOW_200: PREGNANCY_LIMIT_BELOW_200, rentCapFor: rentCapFor, setLang: setLang, getLang: function () { return LANG; }, tr: tr, linkFor: linkFor, pillarName: pillarName, draftFor: draftFor, lessonFor: lessonFor,
    DRAFTS: DRAFTS, LESSONS: LESSONS, POLICY: POLICY,
    fplPct: fplPct, fplAnnual: fplAnnual, snapEstimate: snapEstimate, buildPlan: buildPlan, acaWindow: acaWindow
  };
})(typeof window !== "undefined" ? window : globalThis);
