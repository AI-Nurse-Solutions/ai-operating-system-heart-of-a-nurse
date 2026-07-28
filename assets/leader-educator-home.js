(function () {
  "use strict";

  var workflows = {
    "leader-huddle": {
      label: "15-minute staff huddle",
      prompt: "You are my drafting assistant for a 15-minute staff huddle. I will provide only de-identified, non-patient, non-confidential goals or themes. Ask me for: (1) the huddle goal, (2) the three messages staff must leave with, and (3) one question I need the team to answer. Then draft a timed outline with an opening, three concise talking points, one participation question, and a close. Mark assumptions clearly. Do not make clinical decisions, write patient-specific guidance, or invent policy. End with a human review checklist. No patient data. Human review is required before use."
    },
    "leader-meeting": {
      label: "decision-ready meeting brief",
      prompt: "Help me prepare a decision-ready brief for a non-clinical nursing leadership meeting. Ask me for the objective, audience, known facts, unresolved questions, constraints, and the decision I need from the group. Use only de-identified, non-patient, non-confidential information. Draft: purpose, known facts, assumptions, options with trade-offs, questions for the meeting, and next-step owners left blank for humans to assign. Do not recommend a clinical action, invent evidence, or speak for my organization. End with a human review checklist. No patient data. Human review is required before use."
    },
    "leader-improvement": {
      label: "improvement-project update",
      prompt: "Turn my de-identified, non-patient improvement-project notes into a concise leadership update. First ask for the aim, current state, evidence available, barriers, what has not been validated, and the decision or support needed. Draft five sections: Aim, Known, Assumed or Unknown, Risks and Equity Considerations, and Smallest Next Step. Do not infer outcomes, claim validation, make clinical recommendations, or identify staff or patients. End with a human review checklist. No patient data. Human review is required before use."
    },
    "educator-lesson": {
      label: "lesson-plan first draft",
      prompt: "Help me draft a lesson plan for a nursing education topic using only public, de-identified, non-patient material. Ask me for the learner level, topic, time available, learning objectives, required source material, and assessment format. Draft an opening question, timed learning sequence, active-learning exercise, checks for understanding, and a closing reflection. Flag every claim that needs source verification. Do not invent citations, create patient-specific advice, or replace faculty judgment. End with a human review checklist. No patient data or student-identifying data. Human review is required before use."
    },
    "educator-discussion": {
      label: "Socratic discussion guide",
      prompt: "Create a Socratic discussion guide for a nursing education topic. Ask me for the learner level, topic, approved reading or public source, and the reasoning skill I want learners to practice. Draft eight questions that progress from observation to interpretation, uncertainty, alternatives, ethical tensions, and reflection. Include facilitator prompts but no answer key that short-circuits learner reasoning. Do not invent evidence or use patient or student-identifying data. End with a human review checklist. No patient data. Human review is required before use."
    },
    "educator-rubric": {
      label: "human-owned learning rubric",
      prompt: "Help me draft a transparent rubric for a nursing learning activity. Ask me for the assignment purpose, learner level, required competencies, submission format, and what must remain under faculty judgment. Draft four observable criteria with four performance levels, plain-language descriptors, and a separate feedback-notes area. Do not grade an individual learner, infer intent, use student-identifying data, or make clinical decisions. Identify bias and accessibility questions I should review before adoption. End with a human review checklist. No patient data. Human review is required before use."
    }
  };

  var roleSelect = document.getElementById("workflow-role");
  var taskSelect = document.getElementById("workflow-task");
  var promptField = document.getElementById("workflow-prompt");
  var promptTitle = document.getElementById("workflow-prompt-title");
  var copyButton = document.getElementById("copy-workflow");
  var status = document.getElementById("workflow-status");
  var roleLinks = document.querySelectorAll("[data-workflow-role]");

  if (!roleSelect || !taskSelect || !promptField || !promptTitle || !copyButton || !status) return;

  var tasksByRole = {
    leader: ["leader-huddle", "leader-meeting", "leader-improvement"],
    educator: ["educator-lesson", "educator-discussion", "educator-rubric"]
  };

  function renderTasks() {
    var keys = tasksByRole[roleSelect.value] || tasksByRole.leader;
    taskSelect.textContent = "";
    keys.forEach(function (key) {
      var option = document.createElement("option");
      option.value = key;
      option.textContent = workflows[key].label;
      taskSelect.appendChild(option);
    });
    renderPrompt();
  }

  function renderPrompt() {
    var workflow = workflows[taskSelect.value];
    if (!workflow) return;
    promptTitle.textContent = workflow.label;
    promptField.value = workflow.prompt;
    status.textContent = "Your prompt is ready. Read it before copying.";
    copyButton.textContent = "Copy this workflow";
  }

  function fallbackCopy() {
    promptField.focus();
    promptField.select();
    try {
      return document.execCommand("copy");
    } finally {
      copyButton.focus();
    }
  }

  async function copyPrompt() {
    var copied = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(promptField.value);
        copied = true;
      } else {
        copied = fallbackCopy();
      }
    } catch (error) {
      copied = fallbackCopy();
    }

    if (copied) {
      copyButton.textContent = "Copied";
      status.textContent = "Copied. Paste it into ChatGPT, Claude, or an intentionally installed and configured Hermes session. Then review every result before use.";
    } else {
      status.textContent = "Copy was blocked by your browser. Select the prompt and copy it manually.";
    }
  }

  roleSelect.addEventListener("change", renderTasks);
  taskSelect.addEventListener("change", renderPrompt);
  copyButton.addEventListener("click", copyPrompt);
  roleLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      var role = link.getAttribute("data-workflow-role");
      if (tasksByRole[role]) {
        roleSelect.value = role;
        renderTasks();
      }
    });
  });
  renderTasks();
})();
