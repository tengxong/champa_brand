/**
 * โหลด header จาก partials/header.html แล้วใส่ใน #header-container
 * หลังโหลดจะตั้ง .active ให้เมนูตามหน้าที่อยู่ และ dispatch event 'header-loaded'
 */
(function () {
  var container = document.getElementById("header-container");
  if (!container) return;
  var path = window.location.pathname || "";
  var page = path.split("/").pop() || "index.html";
  if (page === "" || path.endsWith("/")) page = "index.html";

  fetch("partials/header.html")
    .then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    })
    .then(function (html) {
      container.innerHTML = html;
      container.querySelectorAll(".header .menu a").forEach(function (a) {
        var href = (a.getAttribute("href") || "").trim();
        var isActive = href === page || (page === "index.html" && (href === "index.html" || href === ""));
        a.classList.toggle("active", isActive);
      });
      document.dispatchEvent(new CustomEvent("header-loaded"));
    })
    .catch(function () {
      document.dispatchEvent(new CustomEvent("header-loaded"));
    });
})();
