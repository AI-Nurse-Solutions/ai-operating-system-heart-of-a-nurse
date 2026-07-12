/* Anonymous visit & download counters for nurse-ai-os.org.
   Backend: Abacus (https://abacus.jasoncameron.dev) — each event is a bare
   HTTPS GET that increments a shared number. No cookies, no personal data,
   nothing identifying leaves the browser. Failures are silent and ad-blockers
   may block the requests, so counts are approximate (and labeled as such).
   Pages with tracked download links must include this script; the stats strip
   renders only where <section id="site-stats"> exists (the home page). */
(function () {
  "use strict";
  var API = "https://abacus.jasoncameron.dev";
  var NS = "nurse-ai-os-org";

  function hit(key) {
    try {
      fetch(API + "/hit/" + NS + "/" + key, { mode: "cors", keepalive: true }).catch(function () {});
    } catch (e) { /* never interfere with navigation */ }
  }

  function get(key) {
    return fetch(API + "/get/" + NS + "/" + key, { mode: "cors" })
      .then(function (r) { return r.json(); })
      .then(function (d) { return typeof d.value === "number" ? d.value : null; })
      .catch(function () { return null; });
  }

  function keyFor(href) {
    if (!href) return null;
    if (href.indexOf("hermes-cheat-sheet.pdf") !== -1) return "dl-cheat-sheet";
    if (href.indexOf("nurse-ai-os-media-packet") !== -1 && href.indexOf(".pdf") !== -1) return "dl-media-packet";
    if (href.indexOf("nurse-ai-os-architecture-report.pdf") !== -1) return "dl-architecture-report";
    return null;
  }

  document.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (!a) return;
    var key = keyFor(a.getAttribute("href"));
    if (key) hit(key); /* keepalive lets the beacon finish while the PDF opens */
  }, true);

  function fmt(n) { return n.toLocaleString("en-US"); }
  function ordinal(n) {
    var s = ["th", "st", "nd", "rd"], v = n % 100;
    return fmt(n) + (s[(v - 20) % 10] || s[v] || s[0]);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var strip = document.getElementById("site-stats");
    if (!strip) return;
    /* Count a visit once per browser session; reloads only read. */
    var counted = null;
    try { counted = sessionStorage.getItem("naio-visit-counted"); } catch (e) { counted = "1"; }
    var visitPromise;
    if (!counted) {
      try { sessionStorage.setItem("naio-visit-counted", "1"); } catch (e) {}
      visitPromise = fetch(API + "/hit/" + NS + "/visits-home", { mode: "cors" })
        .then(function (r) { return r.json(); })
        .then(function (d) { return typeof d.value === "number" ? d.value : null; })
        .catch(function () { return null; });
    } else {
      visitPromise = get("visits-home");
    }
    Promise.all([visitPromise, get("dl-cheat-sheet"), get("dl-media-packet"), get("dl-architecture-report")])
      .then(function (vals) {
        if (vals[0] === null) return; /* blocked or backend down — strip stays hidden */
        var visitEl = document.getElementById("stat-visitor");
        if (visitEl) visitEl.textContent = "You are the " + ordinal(vals[0]) + " visitor";
        var map = { "stat-cheat": vals[1], "stat-media": vals[2], "stat-report": vals[3] };
        Object.keys(map).forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.textContent = map[id] === null ? "—" : fmt(map[id]);
        });
        strip.hidden = false;
      });
  });
})();
