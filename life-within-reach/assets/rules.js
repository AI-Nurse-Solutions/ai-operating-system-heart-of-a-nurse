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
    version: "2026.11-verified.1",
    reviewed: "2026-11-07",
    note: "Screening estimates from published federal rules, each checked against its primary source on 2026-11-07. States add their own rules on top; always confirm with the program."
  };

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
  // Pregnancy Medicaid/CHIP limits below 200% FPL (KFF, Jan 2026). Median is 213%; all other states are 200% or higher.
  var PREGNANCY_LIMIT_BELOW_200 = { AZ: 161, FL: 196, HI: 196, ID: 138, KS: 171, MS: 199, MT: 162, ND: 175, OR: 190, SC: 199, SD: 138, UT: 144, WY: 159 };
  // Statewide rent caps. capByYear = published maximum for that calendar year; CA's varies by region (5% + regional CPI, never above 10%).
  var RENT_CAP_STATES = {
    CA: { law: "AB 1482 (Civil Code 1947.12): 5% + regional CPI, never more than 10%; most units over 15 years old", capByYear: {} },
    OR: { law: "ORS 90.323/90.324: 7% + CPI, never more than 10%; units under 15 years old are exempt", capByYear: { 2026: 9.5, 2027: 10 } },
    WA: { law: "RCW 59.18.700–.710 (HB 1217, effective May 7, 2025): 7% + CPI, never more than 10%; no increase in the first 12 months; units 12 years old or newer are exempt", capByYear: { 2026: 9.683, 2027: 10 } }
  };
  function rentCapFor(state, year) {
    var c = RENT_CAP_STATES[state];
    if (!c) return null;
    return { law: c.law, cap: c.capByYear[year] || 10, published: !!c.capByYear[year] };
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
    food:   { key: "food",   roman: "I",   app: "PantryPlan", name: "Groceries & essentials", accent: "var(--p-food)" },
    health: { key: "health", roman: "II",  app: "CareBridge", name: "Health care",            accent: "var(--p-health)" },
    housing: { key: "housing",   roman: "III", app: "HomeHold",   name: "Housing",                accent: "var(--p-home)" },
    energy: { key: "energy", roman: "IV",  app: "WattWise",   name: "Energy & utilities",     accent: "var(--p-energy)" },
    family: { key: "family", roman: "V",   app: "KinCare",    name: "Child care, elder care & leave", accent: "var(--p-family)" }
  };

  /* ---------- Links (official or long-standing nonprofit sources) ---------- */
  var L = {
    l211: { label: "211 — local help line", url: "https://www.211.org" },
    benefitFinder: { label: "USA.gov benefit finder", url: "https://www.usa.gov/benefit-finder" },
    snapState: { label: "SNAP office in your state", url: "https://www.fns.usda.gov/snap/state-directory" },
    wic: { label: "How to apply for WIC", url: "https://www.fns.usda.gov/wic/wic-how-apply" },
    foodbank: { label: "Find your local food bank", url: "https://www.feedingamerica.org/find-your-local-foodbank" },
    lifeline: { label: "Lifeline (USAC)", url: "https://www.lifelinesupport.org" },
    healthcare: { label: "HealthCare.gov", url: "https://www.healthcare.gov" },
    medicaid: { label: "Medicaid & CHIP help by state", url: "https://www.medicaid.gov/about-us/where-can-people-get-help-medicaid-chip" },
    hrsa: { label: "Find a community health center", url: "https://findahealthcenter.hrsa.gov" },
    needymeds: { label: "NeedyMeds patient-assistance programs", url: "https://www.needymeds.org" },
    cfpbMed: { label: "CFPB: medical bills & debt", url: "https://www.consumerfinance.gov/consumer-tools/medical-debt/" },
    lawhelp: { label: "LawHelp.org — free legal aid", url: "https://www.lawhelp.org" },
    hudRent: { label: "HUD rental help by state", url: "https://www.hud.gov/topics/rental_assistance" },
    liheap: { label: "LIHEAP energy help", url: "https://www.acf.hhs.gov/ocs/low-income-home-energy-assistance-program-liheap" },
    wap: { label: "Weatherization Assistance Program", url: "https://www.energy.gov/scep/wap/weatherization-assistance-program" },
    childcare: { label: "ChildCare.gov — find care & help paying", url: "https://childcare.gov" },
    headstart: { label: "Head Start locator", url: "https://eclkc.ohs.acf.hhs.gov/center-locator" },
    eldercare: { label: "Eldercare Locator", url: "https://eldercare.acl.gov" },
    respite: { label: "ARCH respite locator", url: "https://archrespite.org" },
    fmla: { label: "FMLA (U.S. Dept. of Labor)", url: "https://www.dol.gov/agencies/whd/fmla" },
    rep: { label: "Find your U.S. Representative", url: "https://www.house.gov/representatives/find-your-representative" },
    congress: { label: "Congress.gov bill tracker", url: "https://www.congress.gov" },
    lifeline988: { label: "988 Suicide & Crisis Lifeline", url: "https://988lifeline.org" }
  };

  /* ---------- Helpers ---------- */
  function num(v) { var n = parseFloat(v); return isFinite(n) && n > 0 ? n : 0; }
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
    var adjusted = Math.max(0, gross * (1 - SNAP.earnedIncomeDeduction) - stdDed);
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
    if (m === 11 || (m === 12 && d <= 15)) return { open: true, due: new Date(y, 11, 15), label: "Open Enrollment — enroll by Dec 15 for coverage starting Jan 1" };
    if (m === 12) return { open: true, due: new Date(y + 1, 0, 15), label: "Open Enrollment — final deadline Jan 15 (most states)" };
    if (m === 1 && d <= 15) return { open: true, due: new Date(y, 0, 15), label: "Open Enrollment — final deadline Jan 15 (most states)" };
    return { open: false, due: addDays(today, 60), label: "Outside Open Enrollment — you need a Special Enrollment Period (60 days from a qualifying event like losing coverage, moving, or a new baby)" };
  }

  /* ---------- Draft templates ("Do it with me") ---------- */
  function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }
  function today() { return new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }); }
  var SIG = "\n\n[Your name]\n[Your address]\n[Your phone or email]";

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
        "If you need help fast and have under $150 income this month, ask about EXPEDITED SNAP (7 days).";
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
      var cap = RENT_CAP_STATES[p.state];
      return today() + "\n\nDear [Landlord/Property manager],\n\nI received notice of a rent increase of " + num(p.rentIncreasePct) + "% for [address], effective [date].\n\n" +
        (cap ? "Under " + cap + ", annual increases for covered units are limited. My understanding is that this increase exceeds the allowed amount. Please confirm whether my unit is exempt, and if not, revise the increase to the lawful maximum.\n\n" :
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
    respite: "Family caregivers have higher rates of depression and chronic illness. Respite — even a few hours — is a health intervention, not a luxury."
  };

  /* ---------- Plan builder ---------- */
  function task(o) {
    o.monthly = Math.max(0, Math.round(o.monthly || 0));
    o.oneTime = Math.max(0, Math.round(o.oneTime || 0));
    o.effortMin = o.effortMin || 30;
    o.lesson = LESSONS[o.draft] || "";
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
        id: "snap", pillar: "food", draft: "snap", title: "Apply for SNAP today",
        why: pct <= SNAP.grossTestPct ? "Your income is under SNAP's gross-income limit." : "Your income is above 130% of poverty, but many states use a higher limit (up to 200%).",
        confidence: pct <= SNAP.grossTestPct ? "likely" : "possible", monthly: est, effortMin: 45, dueDays: 3,
        links: [L.snapState, L.l211], source: SNAP.source + " · effective " + SNAP.effective
      }));
    }
    if (!has(b, "wic") && (kidsU5 > 0 || p.pregnant) && (pct <= 185 || onSNAPorMedicaid)) {
      tasks.push(task({ id: "wic", pillar: "food", draft: "wic", title: "Schedule a WIC appointment",
        why: "You have a child under 5 or someone pregnant, and your income (or SNAP/Medicaid) qualifies.",
        confidence: "likely", monthly: 50 * (kidsU5 + (p.pregnant ? 1 : 0)), effortMin: 40, dueDays: 7, links: [L.wic], source: "USDA FNS WIC income guidelines (185% FPL; adjunctive eligibility via SNAP/Medicaid)" }));
    }
    if (kidsSchool > 0 && (pct <= 185 || has(b, "snap"))) {
      tasks.push(task({ id: "meals", pillar: "food", draft: "foodweek", title: "Confirm free or reduced-price school meals",
        why: has(b, "snap") ? "Children in SNAP households qualify automatically." : "Your income is within the school-meals limit (free ≤130%, reduced ≤185%). Some states now serve all students free.",
        confidence: "likely", monthly: 55 * kidsSchool, effortMin: 15, dueDays: 10, links: [L.l211], source: "USDA National School Lunch Program income eligibility" }));
    }
    if (!has(b, "lifeline") && num(p.internetBill) > 0 && (pct <= 135 || onSNAPorMedicaid || pct <= 200)) {
      var save = 9.25 + Math.max(0, num(p.internetBill) - 30);
      tasks.push(task({ id: "lifeline", pillar: "food", draft: "lifeline", title: "Cut the internet bill: Lifeline + low-income plan",
        why: (pct <= 135 || onSNAPorMedicaid) ? "You qualify for Lifeline, and providers' own low-income plans often cost $10–$30." : "Lifeline needs ≤135% of poverty, but many providers' low-income plans go higher.",
        confidence: (pct <= 135 || onSNAPorMedicaid) ? "likely" : "possible", monthly: Math.min(save, num(p.internetBill)), effortMin: 20, dueDays: 14, links: [L.lifeline], source: "FCC Lifeline program rules (47 CFR 54.409)" }));
    }
    if (p.foodRunsOut) {
      tasks.push(task({ id: "foodweek", pillar: "food", draft: "foodweek", title: "Build a two-week menu around a weekly pantry pickup",
        why: "You said food runs out before the month does. A pantry day plus a protein-first menu stretches every dollar.",
        confidence: "likely", monthly: 60, effortMin: 30, dueDays: 5, links: [L.foodbank, L.l211], source: "Community organizer guidance; local pantry hours vary — confirm before you go" }));
    }

    /* ----- II. Health ----- */
    var expansion = NON_EXPANSION.indexOf(p.state) === -1;
    if (p.renewalDue) {
      var rd = Math.max(1, num(p.renewalDays) || 14);
      tasks.push(task({ id: "renew", pillar: "health", draft: "renew", title: "Return your Medicaid/CHIP renewal packet",
        why: "Most people who lose Medicaid at renewal are still eligible — they lose it for paperwork.",
        confidence: "likely", valueLabel: "Keeps coverage", effortMin: 30, dueDays: Math.max(1, rd - 2), urgent: rd <= 14, links: [L.medicaid], source: "42 CFR 435.916 (annual renewals; 90-day reconsideration)" }));
    }
    if (p.uninsured) {
      var pregLimit = PREGNANCY_LIMIT_BELOW_200[p.state] || 200;
      // Medicaid counts the expected child in a pregnant person's household (42 CFR 435.603(b)); assume one.
      var pregPct = p.pregnant ? Math.round(income * 12 / fplAnnual(size + 1, p.state) * 100) : pct;
      var partialAdult = !expansion && PARTIAL_ADULT_COVERAGE[p.state] && pct <= 100;
      var medicaidLikely = (expansion && pct <= 138) || (p.pregnant && pregPct <= pregLimit) || partialAdult;
      var w = acaWindow(now);
      if (medicaidLikely) {
        tasks.push(task({ id: "coverage", pillar: "health", draft: "coverage", title: "Apply for Medicaid (any day of the year)",
          why: p.pregnant && pregPct <= pregLimit ? "Pregnancy coverage counts your baby in your household, and the limit in your state is about " + pregLimit + "% of poverty or more — you're at about " + pregPct + "%." :
            partialAdult ? PARTIAL_ADULT_COVERAGE[p.state] + "." : "Your state expanded Medicaid and your income is at or below 138% of poverty.",
          confidence: partialAdult && !(p.pregnant && pregPct <= pregLimit) && !(expansion && pct <= 138) ? "possible" : "likely", valueLabel: "Coverage", effortMin: 45, dueDays: 3, urgent: true, links: [L.medicaid, L.healthcare], meta: { route: "medicaid", pct: pct },
          source: "ACA §2001 expansion (138% FPL); expansion status per KFF/Medicaid.gov, Oct 2026; pregnancy limits per KFF, Jan 2026" }));
      } else if (pct >= ACA.minPct && pct <= ACA.maxPct) {
        var planYear = now.getMonth() >= 10 ? now.getFullYear() + 1 : now.getFullYear(); // Nov–Dec enrollment is for next year
        var maxPrem = income * (ACA.maxContributionPctByYear[planYear] || ACA.maxContributionPct) / 100;
        tasks.push(task({ id: "coverage", pillar: "health", draft: "coverage", title: w.open ? "Enroll in a Marketplace plan during Open Enrollment" : "Check for a Special Enrollment Period",
          why: "At about " + pct + "% of poverty you can get a premium tax credit. " + w.label + ".",
          confidence: "likely", valueLabel: "Subsidized coverage", effortMin: 60, dueDays: w.open ? Math.max(1, daysBetween(now, w.due)) : 60, absDue: w.open ? w.due : null, urgent: w.open && daysBetween(now, w.due) <= 45,
          links: [L.healthcare, L.hrsa], meta: { route: "aca", pct: pct, maxPremium: maxPrem }, source: ACA.source }));
      } else {
        tasks.push(task({ id: "coverage", pillar: "health", draft: "coverage", title: "Find low-cost care while you sort out coverage",
          why: (!expansion && pct < 100) ? "Your state hasn't expanded Medicaid, which leaves a coverage gap below 100% of poverty. Community health centers charge on a sliding scale." : "Community health centers serve everyone on a sliding scale.",
          confidence: "possible", valueLabel: "Lower-cost care", effortMin: 20, dueDays: 7, links: [L.hrsa, L.healthcare], meta: { route: "gap", pct: pct, maxPremium: 0 },
          source: "HRSA Health Center Program sliding-fee requirements" }));
        if (!expansion && pct < 100) flags.push("coverage-gap");
      }
    }
    if (p.uninsured && (num(p.kidsUnder5) + num(p.kids5to17)) > 0 && pct <= 200) {
      var cov = tasks.filter(function (t) { return t.id === "coverage"; })[0];
      if (cov) cov.why += " Children in your household likely qualify for Medicaid/CHIP in every state — apply for them any time of year.";
    }
    if (num(p.rxMonthly) > 0) {
      tasks.push(task({ id: "rx", pillar: "health", draft: "rx", title: "Lower prescription costs (cash price, generic, 90-day, assistance)",
        why: "You spend about $" + Math.round(num(p.rxMonthly)) + "/mo on prescriptions" + (p.rxTrouble ? " and cost is getting in the way of taking them." : "."),
        confidence: "possible", monthly: num(p.rxMonthly) * 0.3, effortMin: 25, dueDays: p.rxTrouble ? 3 : 10, urgent: !!p.rxTrouble, links: [L.needymeds], source: "Estimate: 30% average savings from price comparison/generic switch — your result will vary" }));
    }
    if (num(p.medBill) > 0 && pct <= 400) {
      tasks.push(task({ id: "charity", pillar: "health", draft: "charity", title: "Request hospital financial assistance (charity care)",
        why: pct <= 200 ? "Many nonprofit hospitals forgive bills in full below 200% of poverty." : "Many nonprofit hospitals discount bills up to 300–400% of poverty.",
        confidence: pct <= 200 ? "likely" : "possible", oneTime: pct <= 200 ? num(p.medBill) : num(p.medBill) * 0.5, effortMin: 60, dueDays: 14,
        links: [L.cfpbMed], meta: { pct: pct }, source: "IRS §501(r) financial assistance policy requirements; hospital policies vary" }));
    }
    if (p.paDenied) {
      tasks.push(task({ id: "pa", pillar: "health", draft: "pa", title: "Appeal the prior-authorization denial",
        why: "You have a right to an internal appeal and an independent external review. Many denials are overturned.",
        confidence: "possible", valueLabel: "Unlocks care", effortMin: 60, dueDays: 14, links: [L.healthcare], source: "45 CFR 147.136 (internal claims and appeals, external review)" }));
    }

    /* ----- III. Housing ----- */
    var rent = num(p.housingCost);
    var burden = income ? Math.round(rent / income * 100) : 0;
    if (p.evictionNotice) {
      tasks.push(task({ id: "eviction", pillar: "housing", draft: "eviction", title: "Get legal aid on the eviction notice — today",
        why: "Notice deadlines can be 3–5 days. Tenants with a lawyer are far more likely to stay housed.", confidence: "likely",
        valueLabel: "Keeps you housed", effortMin: 30, dueDays: 1, urgent: true, escalate: "legal", links: [L.lawhelp, L.l211], source: "Navigation only — not legal advice" }));
    }
    if (p.tenure === "rent" && num(p.rentIncreasePct) > 0) {
      var capInfo = rentCapFor(p.state, now.getFullYear());
      var capped = capInfo ? capInfo.law : null;
      var capPct = capInfo ? capInfo.cap : 10;
      var over = capped ? Math.max(0, num(p.rentIncreasePct) - capPct) : 0;
      tasks.push(task({ id: "rentIncrease", pillar: "housing", draft: "rentIncrease", title: capped && over > 0 ? "Challenge a rent increase that may exceed the state cap" : "Push back on the rent increase in writing",
        why: capped ? (over > 0 ? "Your increase (" + num(p.rentIncreasePct) + "%) is above the " + capPct + "% " + (capInfo.published ? now.getFullYear() + " cap" : "maximum") + " under " + capped + "." : "Your state caps increases on many units (" + capped + ") — confirm yours is covered.") : "Your state has no statewide cap, but a written request often lowers an increase.",
        confidence: capped && over > 0 ? "likely" : "possible", monthly: capped && over > 0 ? rent * over / (100 + num(p.rentIncreasePct)) : 0,
        valueLabel: capped && over > 0 ? null : "Negotiation", effortMin: 30, dueDays: 7, links: [L.lawhelp], source: capped ? capped : "Local rules vary — confirm with legal aid" }));
    }
    if (p.tenure === "rent" && (p.evictionNotice || p.behindRent || burden >= 50)) {
      tasks.push(task({ id: "erap", pillar: "housing", draft: "erap", title: "Apply for emergency rental assistance",
        why: p.evictionNotice || p.behindRent ? "You're behind or facing eviction — assistance can pay the landlord directly." : "Rent takes " + burden + "% of income (over 50% is 'severely cost-burdened').",
        confidence: "possible", oneTime: rent * 2, effortMin: 60, dueDays: p.evictionNotice ? 2 : 7, urgent: !!p.evictionNotice, links: [L.l211, L.hudRent], source: "County/city/charity programs; availability changes weekly" }));
    }
    if (p.tenure === "rent" && burden >= 40) {
      tasks.push(task({ id: "affordable", pillar: "housing", draft: "affordable", title: "Join affordable-housing lotteries and waitlists",
        why: "Rent is " + burden + "% of income. Below-market and LIHTC units are priced to income.",
        confidence: "possible", valueLabel: "Long-term rent cut", effortMin: 45, dueDays: 30, links: [L.hudRent], source: "HUD/LIHTC program rules; local lotteries vary" }));
    }
    if (p.tenure === "rent" && (num(p.rentIncreasePct) > 0 || p.evictionNotice || p.repairs)) {
      tasks.push(task({ id: "tenantOrg", pillar: "housing", draft: "tenantOrg", title: "Talk with neighbors: start a tenant association",
        why: "Rent and repair problems are usually building-wide. Collective requests carry weight.",
        confidence: "possible", valueLabel: "Collective power", effortMin: 60, dueDays: 45, organizer: true, links: [L.lawhelp], source: "Organizer layer" }));
    }

    /* ----- IV. Energy ----- */
    var bill = num(p.energyBill);
    if (p.shutoff) {
      var sd = Math.max(1, num(p.shutoffDays) || 5);
      tasks.push(task({ id: "shutoff", pillar: "energy", draft: "shutoff", title: p.medEquip ? "Stop the shutoff: medical certificate + payment plan" : "Stop the shutoff: call for a payment plan",
        why: p.medEquip ? "Someone relies on powered medical equipment — a clinician's certificate can delay disconnection." : "Utilities must offer options before disconnecting in most states — but you have to call first.",
        confidence: "likely", valueLabel: "Keeps power on", effortMin: 30, dueDays: Math.max(1, sd - 2), urgent: true, links: [L.liheap, L.l211], source: "State utility commission shutoff rules; protections vary by state and season" }));
    }
    if (!has(b, "utilDiscount") && bill > 0 && (pct <= 200 || (p.state === "CA" && pct <= 250))) {
      tasks.push(task({ id: "discount", pillar: "energy", draft: "discount", title: p.state === "CA" ? (pct > 200 ? "Enroll in FERA (18% off electric)" : "Enroll in CARE (30–35% off electric)") : "Enroll in your utility's low-income rate",
        why: "Discount rates lower every bill, not just one. Most utilities set the limit near 200% of poverty.",
        confidence: p.state === "CA" ? "likely" : "possible", monthly: bill * (p.state === "CA" && pct > 200 ? 0.1 : 0.2), effortMin: 15, dueDays: 7, links: [L.l211], source: p.state === "CA" ? "CPUC CARE (≤200% FPL) and FERA (200–250% FPL, electric only), income limits Jun 1, 2026–May 31, 2027" : "Utility-specific programs — confirm yours" }));
    }
    if (!has(b, "liheap") && bill > 0 && pct <= 150) {
      tasks.push(task({ id: "liheap", pillar: "energy", draft: "liheap", title: "Apply for LIHEAP energy assistance",
        why: "Your income is within LIHEAP's federal ceiling (150% of poverty). " + (p.shutoff ? "Ask for crisis assistance." : ""),
        confidence: "likely", oneTime: 400, effortMin: 45, dueDays: p.shutoff ? 2 : 14, urgent: !!p.shutoff, links: [L.liheap, L.l211], source: "42 U.S.C. 8624 (greater of 150% FPL or 60% of state median income); funded for FY2026, partly funded for FY2027 under a stopgap law; benefit amounts vary by state" }));
    }
    if (bill > 0) {
      tasks.push(task({ id: "rateplan", pillar: "energy", draft: "rateplan", title: "Decode the bill and check your rate plan",
        why: "The wrong rate plan for your routine can cost $10–$30 a month.", confidence: "possible", monthly: Math.min(30, bill * 0.08), effortMin: 20, dueDays: 21,
        links: [], source: "Estimate: 8% average from plan switching — run your utility's free comparison" }));
    }
    if (bill > 0 && pct <= 200) {
      tasks.push(task({ id: "weatherize", pillar: "energy", draft: "weatherize", title: "Request free weatherization + do the 20-minute DIY check",
        why: "Weatherization is free up to 200% of poverty in most states; renters can qualify too.", confidence: "possible", monthly: Math.min(35, bill * 0.12), effortMin: 30, dueDays: 30,
        links: [L.wap], source: "DOE Weatherization Assistance Program" }));
    }
    if (bill > 0 && income > 0 && bill / income >= 0.06) {
      tasks.push(task({ id: "ratepayer", pillar: "energy", draft: "ratepayer", title: "Add your voice to the next utility rate case",
        why: "Energy takes " + Math.round(bill / income * 100) + "% of your income (over 6% is considered unaffordable). Commissions hear from customers.",
        confidence: "possible", valueLabel: "Collective power", effortMin: 20, dueDays: 45, organizer: true, links: [], source: "Organizer layer" }));
    }

    /* ----- V. Family ----- */
    var cc = num(p.childcareCost);
    if (cc > 0 && !has(b, "childcareSubsidy") && pct <= 300) {
      tasks.push(task({ id: "childcare", pillar: "family", draft: "childcare", title: "Apply for child care assistance" + (kidsU5 && pct <= 100 ? " (and Head Start)" : ""),
        why: pct <= 200 ? "Your income is in range for most states' subsidy programs." : "Some states' limits reach 85% of state median income — worth checking.",
        confidence: pct <= 200 ? "likely" : "possible", monthly: cc * (pct <= 200 ? 0.6 : 0.3), effortMin: 60, dueDays: 7, links: [L.childcare, L.headstart], source: "CCDF (45 CFR 98.21; up to 85% SMI) — states set lower limits and co-pays" }));
    }
    if (cc > 0 && p.employerDCAP !== "no") {
      var dc = Math.min(cc * 12, DCAP_LIMIT.amount) * (pct > 250 ? 0.22 : 0.12) / 12;
      tasks.push(task({ id: "dcap", pillar: "family", draft: "dcap", title: "Use a Dependent Care FSA (pre-tax child care)",
        why: p.employerDCAP === "yes" ? "Your employer offers one." : "Ask HR — many employers offer one and enrollment is usually once a year.", confidence: p.employerDCAP === "yes" ? "likely" : "possible",
        monthly: dc, effortMin: 20, dueDays: 30, links: [], source: DCAP_LIMIT.source + " · effective " + DCAP_LIMIT.effective }));
    }
    if (p.needLeave) {
      var st = PAID_LEAVE_STATES[p.state];
      tasks.push(task({ id: "leave", pillar: "family", draft: "leave", title: st ? "Request leave and file for " + st : "Request job-protected leave (FMLA)",
        why: st ? "Your state pays partial wages during family or medical leave." : "FMLA protects your job for up to 12 weeks if you're eligible.",
        confidence: "possible", valueLabel: st ? "Paid, protected leave" : "Job protection", effortMin: 45, dueDays: 14, links: [L.fmla], source: "29 CFR Part 825 (FMLA)" + (st ? "; " + st : "") }));
    }
    if (p.caringAdult) {
      tasks.push(task({ id: "caregiverPay", pillar: "family", draft: "caregiverPay", title: p.state === "CA" ? "Ask about IHSS — get paid for care you give" : "Ask about paid family caregiver programs",
        why: "Many Medicaid programs pay family members for daily care they're already giving.", confidence: "possible", valueLabel: "Possible caregiver pay", effortMin: 45, dueDays: 14,
        links: [L.eldercare], source: "Medicaid HCBS / self-directed services (state-specific)" }));
      tasks.push(task({ id: "respite", pillar: "family", draft: "respite", title: "Schedule one break for yourself this week",
        why: "Caregiver strain is a health risk. Respite is care for the caregiver.", confidence: "likely", valueLabel: "Your health", effortMin: 20, dueDays: 7,
        links: [L.respite, L.lifeline988], source: "Community organizer guidance" }));
    }

    /* ----- Situation summary per pillar ----- */
    var dx = {};
    Object.keys(PILLARS).forEach(function (k) {
      var ts = tasks.filter(function (t) { return t.pillar === k; });
      var urgentT = ts.filter(function (t) { return t.urgent; });
      var enrollT = ts.filter(function (t) { return /snap|wic|meals|lifeline|coverage|discount|liheap|childcare|charity|erap/.test(t.id); });
      var status, words;
      if (urgentT.length) { status = "at-risk"; words = "Something has a deadline: " + urgentT[0].title.toLowerCase() + "."; }
      else if (enrollT.length) { status = "eligible"; words = "You likely qualify for help you're not getting yet."; }
      else if (ts.length) { status = "stretched"; words = "Stable, but there's money to save."; }
      else { status = "stable"; words = "Nothing urgent here based on what you told me."; }
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
    { pillar: "food", item: "Restore SNAP benefits and eligibility", ref: "I.2e", stake: function (p, r) { return has(p.benefits, "snap") || r.tasks.some(function (t) { return t.id === "snap"; }) ? "Your household uses or qualifies for SNAP — benefit and eligibility rules directly change your grocery budget." : "Indirect: SNAP spending supports local grocers and food banks you may rely on."; } },
    { pillar: "food", item: "Revive an Affordable Connectivity Program–style broadband discount", ref: "I.3", stake: function (p) { return num(p.internetBill) ? "A $30/mo discount would cut your $" + Math.round(num(p.internetBill)) + " internet bill to about $" + Math.max(0, Math.round(num(p.internetBill) - 30)) + "." : "Would lower home internet costs for low-income households."; } },
    { pillar: "food", item: "Roll back tariffs on household staples", ref: "I.1", stake: function () { return "Lower prices on groceries and essentials over time; effect depends on which goods are covered."; } },
    { pillar: "health", item: "Restore enhanced ACA premium tax credits", ref: "II.2a", stake: function (p, r) { return r.pct >= 100 && r.pct <= 600 ? "At " + r.pct + "% of poverty, enhanced credits would lower the most you pay for a benchmark plan (and remove the 400% cliff)." : "Mostly affects households between 100% and 600%+ of poverty buying their own insurance."; } },
    { pillar: "health", item: "Cap out-of-pocket drug costs and require PBM transparency", ref: "II.1a–b", stake: function (p) { return num(p.rxMonthly) ? "You pay about $" + Math.round(num(p.rxMonthly)) + "/mo for prescriptions — a cap or PBM reform could lower that." : "Would cap what insured people pay at the pharmacy counter."; } },
    { pillar: "health", item: "Reform prior authorization", ref: "II.2d", stake: function (p) { return p.paDenied ? "You're appealing a denial right now — faster, more transparent rules would help directly." : "Faster approvals and fewer care delays."; } },
    { pillar: "housing", item: "Expand the Low-Income Housing Tax Credit and build 4M homes", ref: "III.3, III.5", stake: function (p, r) { return r.burden >= 30 ? "Rent is " + r.burden + "% of your income. More affordable units means more lotteries you can win." : "Long-term pressure on rents in your area."; } },
    { pillar: "energy", item: "Invest in LIHEAP and protect ratepayers from data-center costs", ref: "IV.8–9", stake: function (p) { return num(p.energyBill) ? "Your $" + Math.round(num(p.energyBill)) + "/mo energy bill depends on how grid costs are split between homes and large new users." : "Keeps residential rates from absorbing large-load costs."; } },
    { pillar: "family", item: "National paid family and medical leave", ref: "V.1–2", stake: function (p) { return p.needLeave ? (PAID_LEAVE_STATES[p.state] ? "Your state already has paid leave; a national program would set a floor everywhere." : "Your state has no paid leave program — a national one would pay part of your wages during leave.") : "Would replace part of wages during family or medical leave."; } },
    { pillar: "family", item: "Expand the Child Tax Credit and Child & Dependent Care Credit", ref: "V.3", stake: function (p) { var k = num(p.kidsUnder5) + num(p.kids5to17); return k ? "With " + k + " child(ren), credit expansions would put more back in your tax refund." : "Mainly benefits families with children."; } },
    { pillar: "family", item: "Caregiver tax refund and senior care stipend", ref: "V.4–5", stake: function (p) { return p.caringAdult ? "You're caring for an adult — a caregiver credit or stipend would recognize that work." : "Supports families caring for older or disabled relatives."; } }
  ];

  global.LWR = {
    RULESET: RULESET, FPL: FPL, SNAP: SNAP, ACA: ACA, STATES: STATES, PILLARS: PILLARS, LINKS: L,
    PAID_LEAVE_STATES: PAID_LEAVE_STATES, RENT_CAP_STATES: RENT_CAP_STATES, NON_EXPANSION: NON_EXPANSION, PREGNANCY_LIMIT_BELOW_200: PREGNANCY_LIMIT_BELOW_200, rentCapFor: rentCapFor,
    DRAFTS: DRAFTS, LESSONS: LESSONS, POLICY: POLICY,
    fplPct: fplPct, fplAnnual: fplAnnual, snapEstimate: snapEstimate, buildPlan: buildPlan, acaWindow: acaWindow
  };
})(typeof window !== "undefined" ? window : globalThis);
