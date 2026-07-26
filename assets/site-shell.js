/* Shared new-visitor orientation for the public Nurse AI OS site shell. */
(function () {
  "use strict";

  var script = document.currentScript;
  var homeUrl = script && script.src
    ? new URL("../index.html#workbench", script.src).href
    : "index.html#workbench";

  var corePages = {
    "student-nurse.html": true,
    "nurse-practitioner.html": true,
    "soul-quiz.html": true,
    "soul-quiz-guide.html": true,
    "life-quiz.html": true,
    "intake.html": true,
    "personalize.html": true,
    "start-here.html": true,
    "setup.html": true,
    "setup-kit.html": true,
    "cheat-sheet.html": true
  };

  var localeHome = /^\/(?:es|tl|zh|ar|vi|ru|hi|fr)\/(?:index\.html)?$/;

  function isHomepage(path) {
    return path === "/" || path === "/index.html" || localeHome.test(path);
  }

  var copy = {
    en: ["New here?", "Try a 5-minute nurse workflow →"],
    es: ["¿Es tu primera vez aquí?", "Prueba un flujo de trabajo de 5 minutos →"],
    tl: ["Bago ka rito?", "Subukan ang 5-minutong workflow para sa nars →"],
    zh: ["第一次来？", "试用 5 分钟护理工作流程 →"],
    ar: ["هل هذه زيارتك الأولى؟", "جرّب سير عمل تمريضي لمدة 5 دقائق ←"],
    vi: ["Mới đến đây?", "Thử quy trình 5 phút dành cho điều dưỡng →"],
    ru: ["Впервые здесь?", "Попробуйте 5-минутный сестринский процесс →"],
    hi: ["पहली बार आए हैं?", "5-मिनट का नर्सिंग वर्कफ़्लो आज़माएँ →"],
    fr: ["Première visite ?", "Essayez un parcours infirmier de 5 minutes →"]
  };

  function addOrientation() {
    var path = window.location.pathname.replace(/\/{2,}/g, "/");
    var page = path.split("/").pop();
    if (isHomepage(path) || corePages[page] || path.indexOf("/setup-helper/") !== -1) return;
    if (document.querySelector(".new-here-bar")) return;

    var header = document.querySelector(".site-header");
    if (!header) return;

    var language = (document.documentElement.lang || "en").toLowerCase().split("-")[0];
    var words = copy[language] || copy.en;
    var bar = document.createElement("aside");
    var inner = document.createElement("div");
    var label = document.createElement("strong");
    var link = document.createElement("a");

    bar.className = "new-here-bar";
    bar.setAttribute("aria-label", words[0]);
    inner.className = "new-here-inner";
    label.textContent = words[0];
    link.href = homeUrl;
    link.textContent = words[1];

    inner.appendChild(label);
    inner.appendChild(link);
    bar.appendChild(inner);
    header.insertAdjacentElement("afterend", bar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addOrientation);
  } else {
    addOrientation();
  }
})();
