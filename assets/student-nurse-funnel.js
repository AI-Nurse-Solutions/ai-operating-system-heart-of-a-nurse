(function () {
  "use strict";

  var safetyContract = "Safety contract: No patient data. No student-identifying data. Do not answer graded work or invent facts or citations. Do not make clinical decisions. Do not replace faculty, preceptors, approved sources, or school policy. This is Draft-only learning support. If the activity is graded, restricted, or permission is unclear, stop and ask faculty before using AI. Mark claims that need verification, disclose AI use when required, and require my human review. ";

  var workflows = {
    "student-study-map": {
      label: "lecture topic → study-map prompt",
      prompt: safetyContract + "Task: Act as my nursing learning coach, not an answer generator. Ask for only a topic name, my own recall, learning objectives, and approved course sources. Then draft a study-map structure with: Core Idea, Key Connections, What I Can Already Explain, Gaps or Misconceptions to Check, Five Teach-Back Questions, and a Source-Verification Checklist. End by asking me to correct the map in my own words."
    },
    "student-socratic": {
      label: "Socratic self-test prompt",
      prompt: safetyContract + "Task: Act as a Socratic nursing tutor, not an answer key. First ask whether the activity is graded, restricted, or unclear under school policy. If yes or unclear, stop and help me draft a question for faculty instead. Otherwise, ask for the topic, learning objectives, learner level, and approved sources. Ask one reasoning question at a time and wait for my answer. Identify what my answer supports, ask me to explain one unclear connection, mark claims to verify, and invite revision. Never provide submit-ready prose, full worked assignment answers, or a polished response intended for submission. End with three gaps I identified and a source-check plan."
    },
    "student-week-plan": {
      label: "weekly study-plan prompt",
      prompt: safetyContract + "Task: Help me draft a one-week nursing study schedule. Ask for my approved deadlines, available study blocks, fixed responsibilities stated without identifying anyone, rest needs, and the topic priority order I choose. Preserve my priority order; do not rank topics or recommend priorities for me. Arrange my choices into a draft schedule with retrieval practice, spaced review, teach-back, source checking, breaks, and one smallest next action. Label what is Known, Assumed, and Still to Decide. End by asking me to approve or change every time block."
    },
    "student-exam-review": {
      label: "exam-review prompt",
      prompt: safetyContract + "Task: Help me organize an exam-review map from official learning objectives and approved study sources. I will not provide protected test questions, recalled exam content, answer keys, or confidential course material. Ask for the approved objectives, exam date, topics I can teach back, topics I cannot explain, time available, and the priority order I assign. Preserve my order; do not predict questions, rank topics, or recommend what will appear on the exam. Draft a review table with retrieval practice, spaced checkpoints, source fields left for me to fill, and confidence ratings I assign myself. End with questions I can take to faculty about unresolved gaps."
    },
    "student-clinical-reflection": {
      label: "de-identified learning-reflection prompt",
      prompt: safetyContract + "Task: Help me organize a learning reflection without discussing a patient or requesting clinical direction. Ask only for the general skill or concept, what faculty or a preceptor expected, what I understood before, what confused me, non-identifying feedback, and the approved source I will check. Draft headings for: Context Without Identifiers, What I Noticed About My Learning, What I Need to Verify, Questions for Faculty or Preceptor, and My Next Learning Step. Do not evaluate staff, infer competence, reconstruct a case, or suggest patient care. End with a privacy check for details that could identify any person or encounter."
    },
    "student-integrity-check": {
      label: "faculty-question prompt for AI-use rules",
      prompt: safetyContract + "Task: Help me draft questions for faculty about whether a planned AI use fits assignment and school rules. I may summarize or quote only policy text my school permits me to share. Do not ask for the assignment, graded questions, answer key, confidential rubric, or another person’s work. Never decide or label the use as allowed, approved, compliant, or prohibited. Return only: Policy Points I Reported—Not Independently Verified, What Remains Unknown, Questions for Faculty, Possible Disclosure Questions, and How I Will Keep the Thinking Mine. If the actual policy or assignment-specific permission has not been confirmed by the accountable instructor, state: Stop and ask faculty before using AI."
    }
  };

  var taskSelect = document.getElementById("student-task");
  var promptField = document.getElementById("student-prompt");
  var promptTitle = document.getElementById("student-prompt-title");
  var copyButton = document.getElementById("copy-student-workflow");
  var status = document.getElementById("student-workflow-status");

  if (!taskSelect || !promptField || !promptTitle || !copyButton || !status) return;

  function renderPrompt() {
    var workflow = workflows[taskSelect.value] || workflows["student-study-map"];
    promptTitle.textContent = workflow.label;
    promptField.value = workflow.prompt;
    status.textContent = "Your prompt is ready. Read it before copying.";
    copyButton.textContent = "Copy this study prompt";
  }

  function fallbackCopy() {
    try {
      promptField.focus();
      promptField.select();
      if (typeof document.execCommand !== "function") return false;
      return Boolean(document.execCommand("copy"));
    } catch (error) {
      return false;
    }
  }

  async function copyPrompt() {
    var copied = false;
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(promptField.value);
        copied = true;
      } catch (error) {
        copied = fallbackCopy();
      }
    } else {
      copied = fallbackCopy();
    }

    if (copied) {
      copyButton.textContent = "Copied";
      status.textContent = "Copied. Before pasting, confirm your school permits this use and review the provider privacy boundary below.";
      copyButton.focus();
    } else {
      promptField.focus();
      promptField.select();
      status.textContent = "Automatic copy was blocked. The prompt is selected; use your device’s copy command, or select it manually.";
    }
  }

  taskSelect.addEventListener("change", renderPrompt);
  copyButton.addEventListener("click", copyPrompt);
  renderPrompt();
})();
