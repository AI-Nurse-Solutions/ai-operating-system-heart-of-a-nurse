/* Shared new-visitor orientation for the public Nurse AI OS site shell. */
(function () {
  "use strict";

  var script = document.currentScript;
  var quizUrl = script && script.src
    ? new URL("../soul-quiz.html", script.src).href
    : "soul-quiz.html";

  var corePages = {
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
    en: ["New here?", "Start with the 2-minute SOUL Quiz →"],
    es: ["¿Es tu primera vez aquí?", "Empieza con el Quiz SOUL de 2 minutos →"],
    tl: ["Bago ka rito?", "Magsimula sa 2-minutong SOUL Quiz →"],
    zh: ["第一次来？", "先做 2 分钟 SOUL 测验 →"],
    ar: ["هل هذه زيارتك الأولى؟", "ابدأ باختبار SOUL لمدة دقيقتين ←"],
    vi: ["Mới đến đây?", "Bắt đầu với Bài kiểm tra SOUL trong 2 phút →"],
    ru: ["Впервые здесь?", "Начните с 2-минутного теста SOUL →"],
    hi: ["पहली बार आए हैं?", "2-मिनट के SOUL Quiz से शुरू करें →"],
    fr: ["Nouveau ici ?", "Commencez par le quiz SOUL de 2 minutes →"]
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
    link.href = quizUrl;
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
