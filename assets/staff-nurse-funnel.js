(function () {
  "use strict";

  var focusOptions = {
    "after-shift-reset": {
      label: "After-shift reset",
      purpose: "Help me close the workday without recounting patient or staff events: identify what can wait, choose one non-work priority, and shape a short personal reset."
    },
    "learning-certification": {
      label: "Learning and certification",
      purpose: "Help me organize a no-PHI learning goal, certification plan, or continuing-education task using public sources I name or select."
    },
    "portfolio-career": {
      label: "Portfolio and career growth",
      purpose: "Help me prepare a personal portfolio outline, application draft, or career-development plan without patient stories, employer-confidential material, or unsupported achievement claims."
    },
    "professional-communication": {
      label: "Professional communication",
      purpose: "Help me plan and draft a permitted professional message using no patient, colleague, staff, personnel, or employer-confidential information; I will check facts, recipients, tone, and employer policy before use."
    },
    "shared-governance": {
      label: "Shared-governance preparation",
      purpose: "Help me prepare questions, an agenda outline, or a personal discussion note from public or explicitly permitted nonconfidential material; do not make unit, staffing, quality, employment, or policy decisions."
    },
    "personal-organization": {
      label: "Personal organization",
      purpose: "Help me sort personal priorities, continuing-education deadlines, and life admin without work schedules, employer systems, patient information, or another person’s private data."
    }
  };

  var energyOptions = {
    "five-depleted": {
      label: "5 minutes · depleted",
      instruction: "Keep this to one focused question, one small Draft, and no more than three bullets. Do not add optional tasks."
    },
    "fifteen-steady": {
      label: "15 minutes · steady",
      instruction: "Use a short sequence with no more than three steps and pause after each major choice."
    },
    "thirty-focused": {
      label: "30 minutes · focused",
      instruction: "Build one structured Draft with a brief review checklist, while keeping the scope to this single task."
    }
  };

  var styleOptions = {
    "one-step": {
      label: "One step at a time",
      instruction: "Ask one question at a time and wait for my answer before extending the work."
    },
    "direct-checklist": {
      label: "Direct checklist",
      instruction: "Use short action-oriented bullets, preserve my priority order, and do not create false urgency."
    },
    "coaching-questions": {
      label: "Coaching questions first",
      instruction: "Help me state my own goal and reasoning before you draft; do not infer my emotions, intent, competence, or wellbeing."
    },
    "source-first": {
      label: "Source-first",
      instruction: "Begin with the public sources, policy boundary, and unresolved questions needed before drafting; never invent a citation."
    }
  };

  var reviewOptions = {
    "one-artifact": {
      label: "Draft one artifact, then stop",
      instruction: "Return one bounded Draft and stop. Do not send, publish, schedule, submit, or expand the task."
    },
    "assumptions-gaps": {
      label: "Assumptions and gaps",
      instruction: "End with assumptions, missing context, what could be wrong, and what I must verify."
    },
    "human-checkpoint": {
      label: "Human decision checkpoint",
      instruction: "Stop before any consequential conclusion and ask me to approve, revise, or reject the Draft."
    },
    "source-check": {
      label: "Source check before use",
      instruction: "Separate direct source support from interpretation, add [SOURCE NEEDED] where required, and wait for my source check."
    }
  };

  var safetyContract = [
    "No patient data or PHI.",
    "No patient stories, even if names are removed.",
    "No colleague, staff, or third-party identifiers.",
    "No employer-confidential information, personnel records, schedules, staffing data, incident reports, or restricted organizational material.",
    "No credentials, secrets, or restricted records.",
    "Do not diagnose, triage, make patient-specific decisions, write chart content, or direct clinical care.",
    "Do not make staffing, employment, disciplinary, performance, legal, labor, or regulatory decisions.",
    "Do not connect to an EHR, scheduling system, employer system, or clinical workflow.",
    "Use only information I am permitted to share and public sources I name or select.",
    "Label uncertainty, distinguish evidence from interpretation, and never fabricate facts, experiences, results, or citations.",
    "Treat every output as personal-use Draft support only and require my human review before I rely on, send, publish, teach, or share it.",
    "If the task involves immediate safety, clinical care, crisis, workplace violence, or serious distress, stop this workflow and use the appropriate human or institutional resource."
  ];

  var focus = document.getElementById("staff-focus");
  var energy = document.getElementById("staff-energy");
  var style = document.getElementById("staff-style");
  var review = document.getElementById("staff-review");
  var output = document.getElementById("staff-practice-card");
  var title = document.getElementById("staff-practice-card-title");
  var copyButton = document.getElementById("copy-staff-practice-card");
  var status = document.getElementById("staff-practice-card-status");
  var copyOperation = 0;

  if (!focus || !energy || !style || !review || !output || !title || !copyButton || !status) return;

  function selected(map, value) {
    return map[value] || map[Object.keys(map)[0]];
  }

  function renderCard() {
    var chosenFocus = selected(focusOptions, focus.value);
    var chosenEnergy = selected(energyOptions, energy.value);
    var chosenStyle = selected(styleOptions, style.value);
    var chosenReview = selected(reviewOptions, review.value);

    title.textContent = chosenFocus.label + " · " + chosenEnergy.label;
    output.value = [
      "Off-Shift AI Practice Card — Staff Nurse Community Preview",
      "",
      "SAFETY BOUNDARY",
      safetyContract.map(function (rule) { return "- " + rule; }).join("\n"),
      "",
      "MY CONFIGURATION",
      "Primary focus: " + chosenFocus.label,
      "Purpose: " + chosenFocus.purpose,
      "Available energy: " + chosenEnergy.label,
      "Energy instruction: " + chosenEnergy.instruction,
      "Working style: " + chosenStyle.label,
      "How to work with me: " + chosenStyle.instruction,
      "Review checkpoint: " + chosenReview.label,
      "Review instruction: " + chosenReview.instruction,
      "",
      "WORKING METHOD",
      "1. Ask one question about the permitted off-shift outcome; do not ask for patient, staff, unit, schedule, incident, or confidential context.",
      "2. Restate the task and name anything outside this personal-use boundary.",
      "3. Prepare one Draft matched to my available energy; do not act or decide for me.",
      "4. Show assumptions, uncertainty, source gaps, and policy checks.",
      "5. End with one Proposed next step and wait for my review, correction, and decision.",
      "",
      "Start by asking me one question: Which permitted off-shift task should we shape together?"
    ].join("\n");
    copyButton.textContent = "Copy my off-shift card";
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

  [focus, energy, style, review].forEach(function (control) {
    control.addEventListener("change", renderCard);
  });
  copyButton.addEventListener("click", copyCard);
  renderCard();
})();
