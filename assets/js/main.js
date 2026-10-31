/* Progressive enhancement: all content is already in the HTML.
   This script only adds publication filters, current-section highlighting and printing. */
(function () {
  "use strict";

  // ---------- Publication filters
  var form = document.getElementById("pub-filters");
  if (form) {
    var refs = Array.prototype.slice.call(document.querySelectorAll(".pub-group .ref"));
    var groups = Array.prototype.slice.call(document.querySelectorAll(".pub-group[data-group]"));
    var fType = document.getElementById("f-type");
    var fYear = document.getElementById("f-year");
    var fText = document.getElementById("f-text");
    var status = document.getElementById("f-status");
    var empty = document.getElementById("f-empty");
    var clear = document.getElementById("f-clear");
    var total = refs.length;

    function norm(s) {
      return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[-\u2010-\u2015]/g, " ").replace(/\s+/g, " ");
    }

    function apply() {
      var t = fType.value, y = fYear.value, q = norm(fText.value.trim());
      var shown = 0;
      refs.forEach(function (li) {
        var ok = (!t || li.dataset.type === t) &&
                 (!y || li.dataset.year === y) &&
                 (!q || norm(li.dataset.search).indexOf(q) !== -1);
        li.hidden = !ok;
        if (ok) shown++;
      });
      groups.forEach(function (g) {
        g.hidden = !g.querySelector(".ref:not([hidden])");
      });
      var filtered = t || y || q;
      status.textContent = filtered ? "Showing " + shown + " of " + total + " publications." : total + " publications.";
      empty.hidden = shown !== 0;
    }

    form.hidden = false;
    form.addEventListener("input", apply);
    form.addEventListener("change", apply);
    form.addEventListener("submit", function (ev) { ev.preventDefault(); });
    form.addEventListener("reset", function () { setTimeout(apply, 0); });
    clear.addEventListener("click", function () { form.reset(); fType.focus(); });
    apply();

    // Show every publication before printing
    window.addEventListener("beforeprint", function () {
      refs.forEach(function (li) { li.hidden = false; });
      groups.forEach(function (g) { g.hidden = false; });
    });
    window.addEventListener("afterprint", apply);
  }

  // ---------- Print button
  var printBtn = document.getElementById("print-btn");
  if (printBtn) {
    printBtn.hidden = false;
    printBtn.addEventListener("click", function () { window.print(); });
  }

  // ---------- Current section in the side index
  var tocLinks = document.querySelectorAll(".toc a[href^='#']");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && map[en.target.id]) {
          tocLinks.forEach(function (a) { a.classList.remove("is-current"); a.removeAttribute("aria-current"); });
          map[en.target.id].classList.add("is-current");
          map[en.target.id].setAttribute("aria-current", "location");
        }
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    document.querySelectorAll(".cv-section").forEach(function (s) { io.observe(s); });
  }
})();
