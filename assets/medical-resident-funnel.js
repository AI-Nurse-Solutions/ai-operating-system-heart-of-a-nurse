(function () {
  "use strict";

  var focusOptions = {
    "rotation-learning": {
      label: "Rotation learning plan",
      purpose: "Help me turn a public rotation objective or a nonconfidential learning goal I write into one bounded learning plan without patient cases, clinical tasks, program records, or assumptions about my supervision or authority."
    },
    "board-review": {
      label: "Board and knowledge review",
      purpose: "Help me organize a knowledge-review session using public objectives, public sources, or my own nonconfidential notes; do not use protected exam questions, recalled test content, or answer a live assessment."
    },
    "journal-club": {
      label: "Journal club preparation",
      purpose: "Help me inspect a public article or source I am permitted to use, separate reported findings from interpretation, and prepare discussion questions without applying the article to a real patient or clinical decision."
    },
    "teaching-prep": {
      label: "Teaching preparation",
      purpose: "Help me outline a short teaching session using public topics and clearly labeled synthetic examples only; do not create a real case, disclose learner information, or present unverified claims as fact."
    },
    "feedback-reflection": {
      label: "Feedback reflection",
      purpose: "Help me turn my own nonconfidential reflection into questions for a human mentor or supervisor without pasting evaluations, naming people, inferring competence, or deciding what my program should do."
    },
    "career-portfolio": {
      label: "Career and portfolio",
      purpose: "Help me organize a personal portfolio outline, scholarship plan, or career Draft without confidential evaluations, program records, invented achievements, credentials, or promises about selection or advancement."
    }
  };

  var capacityOptions = {
    "ten-low": {
      label: "10 minutes · low capacity",
      instruction: "Keep this to one focused question, one small Draft, and no more than three bullets. Do not add optional tasks or create urgency."
    },
    "twenty-five-focused": {
      label: "25 minutes · focused",
      instruction: "Use a short sequence with no more than three steps and pause after each major choice."
    },
    "forty-five-deep": {
      label: "45 minutes · deep work",
      instruction: "Build one structured Draft with a brief verification checklist while keeping the scope to this single learning task."
    }
  };

  var styleOptions = {
    "socratic": {
      label: "Socratic questions",
      instruction: "Ask one question at a time so I state my own reasoning before you extend or challenge it."
    },
    "structured-outline": {
      label: "Structured outline",
      instruction: "Use concise headings and action-oriented bullets, preserve my priority order, and identify unresolved gaps."
    },
    "source-first": {
      label: "Source-first synthesis",
      instruction: "Begin with the public sources and source limits needed for the task, distinguish direct support from interpretation, and never invent a citation."
    },
    "challenge-assumptions": {
      label: "Challenge my assumptions",
      instruction: "Ask what evidence could change my view, name plausible alternatives, and do not infer my competence, intent, emotions, or wellbeing."
    }
  };

  var reviewOptions = {
    "one-artifact": {
      label: "Draft one artifact, then stop",
      instruction: "Return one bounded Draft and stop. Do not send, submit, publish, schedule, teach, or expand the task."
    },
    "source-verification": {
      label: "Source verification checkpoint",
      instruction: "End with source claims to verify, add [SOURCE NEEDED] where required, and wait for my source check."
    },
    "supervisor-policy": {
      label: "Supervisor or policy checkpoint",
      instruction: "Stop before anything governed by faculty supervision, program rules, institutional policy, training authority, or clinical responsibility and tell me which authorized human or source must control."
    },
    "human-review": {
      label: "Human review before use",
      instruction: "End with assumptions, uncertainty, possible errors, and what I must review, correct, approve, or reject."
    }
  };

  var safetyContract = [
    "No patient data or PHI.",
    "No patient cases, case narratives, or identifiable stories, even if names are removed.",
    "No EHR, sign-out, chart, consult, handoff, schedule, or incident content.",
    "No faculty, colleague, learner, or third-party identifiers.",
    "No evaluations, personnel records, or confidential program material.",
    "No protected exam questions, recalled test content, or restricted educational material.",
    "No credentials, secrets, institutional access details, or restricted records.",
    "Do not diagnose, triage, choose treatment, make patient-specific decisions, write chart content, or direct care.",
    "Do not determine competence, entrustment, supervision level, procedural authorization, duty-hour compliance, program standing, or credentialing.",
    "Do not replace faculty supervision, program policy, institutional policy, or resident reasoning.",
    "Do not connect to an EHR, hospital system, program system, assessment platform, or clinical workflow.",
    "Use only public, synthetic, or personally authored nonconfidential material that I am permitted to share.",
    "Label uncertainty, separate evidence from interpretation, and never fabricate facts, experiences, results, achievements, or citations.",
    "Treat every output as personal-use educational Draft support only and require my human review before I rely on, submit, present, teach, publish, or share it.",
    "If the task involves immediate patient safety, clinical care, fatigue-related safety, mistreatment, crisis, or serious distress, stop this workflow and use the appropriate human, supervisory, emergency, or institutional resource."
  ];

  var focus = document.getElementById("resident-focus");
  var capacity = document.getElementById("resident-capacity");
  var style = document.getElementById("resident-style");
  var review = document.getElementById("resident-review");
  var output = document.getElementById("resident-practice-card");
  var title = document.getElementById("resident-practice-card-title");
  var copyButton = document.getElementById("copy-resident-practice-card");
  var status = document.getElementById("resident-practice-card-status");
  var copyOperation = 0;

  if (!focus || !capacity || !style || !review || !output || !title || !copyButton || !status) return;

  function selected(map, value) {
    return map[value] || map[Object.keys(map)[0]];
  }

  function renderCard() {
    var chosenFocus = selected(focusOptions, focus.value);
    var chosenCapacity = selected(capacityOptions, capacity.value);
    var chosenStyle = selected(styleOptions, style.value);
    var chosenReview = selected(reviewOptions, review.value);

    title.textContent = chosenFocus.label + " · " + chosenCapacity.label;
    output.value = [
      "Resident Learning Practice Card — Medical Resident Community Preview",
      "",
      "SAFETY AND AUTHORITY BOUNDARY",
      safetyContract.map(function (rule) { return "- " + rule; }).join("\n"),
      "",
      "MY CONFIGURATION",
      "Primary focus: " + chosenFocus.label,
      "Purpose: " + chosenFocus.purpose,
      "Available capacity: " + chosenCapacity.label,
      "Capacity instruction: " + chosenCapacity.instruction,
      "Working style: " + chosenStyle.label,
      "How to work with me: " + chosenStyle.instruction,
      "Review checkpoint: " + chosenReview.label,
      "Review instruction: " + chosenReview.instruction,
      "",
      "WORKING METHOD",
      "1. Ask one question about the permitted public, synthetic, or personally authored learning goal; do not ask for patient, team, evaluation, program, schedule, incident, or confidential context.",
      "2. Restate the task, my learning responsibility, and anything outside this personal-use boundary.",
      "3. Help me show my own reasoning before preparing one Draft matched to my available capacity; do not act, decide, assess, or authorize for me.",
      "4. Show assumptions, uncertainty, source limits, possible errors, and any faculty, policy, or institutional checkpoint.",
      "5. End with one Proposed next step and wait for my review, correction, and decision.",
      "",
      "Start by asking me one question: Which public, synthetic, or personally authored nonconfidential learning goal should we shape together?"
    ].join("\n");
    copyButton.textContent = "Copy my learning card";
    status.textContent = "Card updated in this browser tab. Nothing has been sent anywhere.";
  }

  function selectForManualCopy() {
    output.focus();
    output.select();
  }

  function fallbackCopy() {
    selectForManualCopy();
    if (typeof document.execCommand !== "function") return false;
    try {
      return document.execCommand("copy");
    } catch (error) {
      return false;
    }
  }

  function copied() {
    copyButton.textContent = "Copied";
    status.textContent = "Copied. Before pasting, check the provider privacy boundary below.";
  }

  function manualCopy() {
    selectForManualCopy();
    copyButton.textContent = "Select card manually";
    status.textContent = "Automatic copy was blocked. The card is selected; use your device’s copy command.";
  }

  function staleCopy() {
    copyButton.textContent = "Copy updated card";
    status.textContent = "The card changed while copying. Copy the updated card again.";
  }

  async function copyCard() {
    var operation = ++copyOperation;
    var copiedWithClipboard = false;
    var cardToCopy = output.value;
    if (window.isSecureContext && navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      try {
        await navigator.clipboard.writeText(cardToCopy);
        copiedWithClipboard = true;
      } catch (error) {
        copiedWithClipboard = false;
      }
    }
    if (operation !== copyOperation) return;
    if (copiedWithClipboard && output.value !== cardToCopy) {
      staleCopy();
      return;
    }
    if (copiedWithClipboard || fallbackCopy()) {
      copied();
    } else {
      manualCopy();
    }
  }

  [focus, capacity, style, review].forEach(function (control) {
    control.addEventListener("change", renderCard);
  });
  copyButton.addEventListener("click", copyCard);
  renderCard();
})();
