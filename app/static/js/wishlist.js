/* Optimistic heart-icon toggle for trek cards / detail page, backed by
 * POST /api/wishlist/toggle/<id>. Falls back gracefully: if the fetch
 * fails, the button's underlying <form> (progressive-enhancement
 * baseline in app.blueprints.user.wishlist_toggle) still works via a
 * normal full-page POST because we only preventDefault() once the fetch
 * is actually in flight. */
(function () {
  "use strict";

  document.querySelectorAll("[data-wishlist-toggle]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var trekId = form.getAttribute("data-trek-id");
      if (!trekId || !window.fetch) return; // let the plain form POST happen

      event.preventDefault();
      form.setAttribute("aria-busy", "true");

      fetch("/api/wishlist/toggle/" + trekId, {
        method: "POST",
        headers: { "X-CSRFToken": TMA.csrfToken() },
      })
        .then(function (resp) {
          if (!resp.ok) throw new Error("request failed");
          return resp.json();
        })
        .then(function (data) {
          document.querySelectorAll('[data-wishlist-icon][data-trek-id-ref="' + trekId + '"]').forEach(function (icon) {
            icon.classList.toggle("bi-heart-fill", data.saved);
            icon.classList.toggle("bi-heart", !data.saved);
            var iconBtn = icon.closest(".wishlist-btn");
            if (iconBtn) {
              iconBtn.setAttribute("aria-pressed", data.saved ? "true" : "false");
              // Only the moment it's actively saved gets the little pop;
              // removing a heart, or the icon's state at page load,
              // shouldn't animate.
              if (data.saved) {
                iconBtn.classList.remove("is-popping");
                // Force a reflow so re-adding the class restarts the
                // animation even on a second save of the same trek.
                void iconBtn.offsetWidth;
                iconBtn.classList.add("is-popping");
                iconBtn.addEventListener("animationend", function handler() {
                  iconBtn.classList.remove("is-popping");
                  iconBtn.removeEventListener("animationend", handler);
                });
              }
            }
          });
          TMA.toast(data.saved ? "Saved to your wishlist." : "Removed from your wishlist.", "info");
        })
        .catch(function () {
          TMA.toast("Could not update your wishlist. Please try again.", "danger");
        })
        .finally(function () {
          form.removeAttribute("aria-busy");
        });
    });
  });
})();
