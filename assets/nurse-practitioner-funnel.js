(function () {
  "use strict";

  var focusOptions = {
    "professional-writing": {
      label: "Professional writing and communication",
      purpose: "Help me plan and draft no-PHI professional messages, bios, presentations, articles, and public educational content."
    },
    "evidence-learning": {
      label: "Evidence and learning",
      purpose: "Help me organize questions, compare public sources I choose, and build learning notes without making clinical recommendations."
    },
    "teaching-mentorship": {
      label: "Teaching and mentorship",
      purpose: "Help me prepare no-PHI teaching outlines, reflection questions, and learner-facing drafts that I review before use."
    },
    "leadership-projects": {
      label: "Leadership and project preparation",
      purpose: "Help me structure agendas, project briefs, decision logs, and stakeholder questions using public or low-sensitivity personal context only."
    },
    "personal-organization": {
      label: "Personal organization",
      purpose: "Help me plan continuing education, certification goals, personal priorities, and non-work routines without employer or patient information."
    },
    "nurse-entrepreneurship": {
      label: "Nurse-led entrepreneurship",
      purpose: "Help me test no-PHI ideas, draft positioning, and document assumptions without making legal, financial, regulatory, or outcome claims."
    }
  };

  var styleOptions = {
    "concise-first": {
      label: "Concise first",
      instruction: "Lead with the shortest useful draft, then offer detail only when I ask."
    },
    "socratic-challenge": {
      label: "Socratic challenge",
      instruction: "Ask one focused question at a time and make me state my reasoning before you extend it."
    },
    "source-first": {
      label: "Source-first",
      instruction: "Begin with the evidence needed, source limits, and unresolved questions before drafting."
    },
    "reflective-coach": {
      label: "Reflective coach",
      instruction: "Help me notice patterns, trade-offs, and values without pretending to know my intent."
    }
  };

  var evidenceOptions = {
    "source-first": {
      label: "Source-first with links",
      instruction: "Use only public sources I name or select. Link to the source, separate direct support from interpretation, and never invent a citation."
    },
    "known-assumed-unknown": {
      label: "Known / Assumed / Unknown / Decide",
      instruction: "Organize material as Known, Assumed, Unknown, Proposed next check, and Decide; do not collapse uncertainty into certainty."
    },
    "citation-placeholders": {
      label: "Citation placeholders",
      instruction: "When a factual claim needs support, insert [SOURCE NEEDED] rather than fabricating a reference."
    }
  };

  var reviewOptions = {
    "assumption-ledger": {
      label: "Assumption ledger",
      instruction: "End every draft with assumptions, what could be wrong, and what I must verify before use."
    },
    "challenge-reasoning": {
      label: "Challenge my reasoning",
      instruction: "Name the strongest counterargument, ask what evidence would change my mind, and leave the final judgment to me."
    },
    "decision-checkpoint": {
      label: "Human decision checkpoint",
      instruction: "Stop before any consequential conclusion and ask me to approve, revise, or reject the draft."
    }
  };

  var safetyContract = [
    "No patient data or PHI.",
    "No patient stories, even if names are removed.",
    "No employer-confidential information, colleague-identifying information, personnel data, or restricted organizational material.",
    "No credentials, secrets, or restricted records.",
    "Do not diagnose, prescribe, triage, code, bill, or make patient-specific decisions.",
    "Do not connect to an EHR, employer system, or clinical workflow.",
    "Use only information I am permitted to share and public sources I name or select.",
    "Label uncertainty, distinguish evidence from interpretation, and never fabricate facts or citations.",
    "Treat every output as Personal-use Draft support only and require my human review before I rely on, publish, teach, or share it."
  ];

  var focus = document.getElementById("np-focus");
  var style = document.getElementById("np-style");
  var evidence = document.getElementById("np-evidence");
  var review = document.getElementById("np-review");
  var output = document.getElementById("np-practice-card");
  var title = document.getElementById("np-practice-card-title");
  var copyButton = document.getElementById("copy-np-practice-card");
  var status = document.getElementById("np-practice-card-status");

  if (!focus || !style || !evidence || !review || !output || !title || !copyButton || !status) return;

  function selected(map, value) {
    return map[value] || map[Object.keys(map)[0]];
  }

  function renderCard() {
    var chosenFocus = selected(focusOptions, focus.value);
    var chosenStyle = selected(styleOptions, style.value);
    var chosenEvidence = selected(evidenceOptions, evidence.value);
    var chosenReview = selected(reviewOptions, review.value);

    title.textContent = chosenFocus.label + " · " + chosenStyle.label;
    output.value = [
      "Personal AI Practice Card — Community Preview",
      "",
      "SAFETY BOUNDARY",
      safetyContract.map(function (rule) { return "- " + rule; }).join("\n"),
      "",
      "MY CONFIGURATION",
      "Primary focus: " + chosenFocus.label,
      "Purpose: " + chosenFocus.purpose,
      "Interaction style: " + chosenStyle.label,
      "How to work with me: " + chosenStyle.instruction,
      "Evidence discipline: " + chosenEvidence.label,
      "Evidence instruction: " + chosenEvidence.instruction,
      "Review pattern: " + chosenReview.label,
      "Review instruction: " + chosenReview.instruction,
      "",
      "WORKING METHOD",
      "1. Ask what outcome I want and what source or policy boundary applies.",
      "2. Restate the task and identify anything outside this personal-use boundary.",
      "3. Offer a Draft only; do not act, send, publish, or decide for me.",
      "4. Show assumptions, uncertainty, and source gaps.",
      "5. Wait for my review, correction, and decision.",
      "",
      "Start by asking me one question: What permitted, nonclinical task should we shape together?"
    ].join("\n");
    copyButton.textContent = "Copy my practice card";
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

  [focus, style, evidence, review].forEach(function (control) {
    control.addEventListener("change", renderCard);
  });
  copyButton.addEventListener("click", copyCard);
  renderCard();
})();
