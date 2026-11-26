(function () {
  "use strict";
  document.documentElement.classList.add("js");
  var menu = document.querySelector(".menu"), nav = document.getElementById("nav");
  if (menu) {
    menu.hidden = false;
    menu.addEventListener("click", function () {
      menu.setAttribute("aria-expanded", String(nav.classList.toggle("open")));
    });
  }
  var filters = document.querySelector(".filters");
  if (filters) {
    filters.hidden = false;
    filters.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b) return;
      filters.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      document.querySelectorAll(".card").forEach(function (c) { c.hidden = !!b.dataset.filter && c.dataset.cat !== b.dataset.filter; });
    });
  }
  var viewer = document.querySelector(".viewer");
  document.querySelectorAll(".shot").forEach(function (s) {
    s.addEventListener("click", function () {
      var src = s.querySelector("img"), big = viewer.querySelector("img");
      big.src = src.src; big.alt = src.alt; viewer.showModal();
    });
  });
  var share = document.querySelector(".share");
  if (share && navigator.share) {
    share.hidden = false;
    share.addEventListener("click", function () { navigator.share({ title: document.title, url: location.href }).catch(function () {}); });
  }
  var form = document.getElementById("booking");
  if (form) {
    var d = new Date(), pad = function (n) { return String(n).padStart(2, "0"); };
    form.elements.date.min = d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
    try { form.elements.timezone.value = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var lines = ["BOOKING ENQUIRY (not yet confirmed)"];
      form.querySelectorAll("[data-label]").forEach(function (f) {
        var v = f.value.trim();
        if (v) lines.push(f.dataset.label + ": " + v);
      });
      var url = "https://wa.me/" + form.dataset.wa + "?text=" + encodeURIComponent(lines.join("\n"));
      var status = document.getElementById("sent"), a = document.createElement("a");
      a.href = url; a.className = "btn"; a.textContent = "Open WhatsApp and send";
      status.textContent = "Your message is ready. It is not sent until you press send in WhatsApp. ";
      status.appendChild(a);
      a.focus();
    });
  }
})();
