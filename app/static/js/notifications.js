/* Navbar bell dropdown; fetches recent notifications on open, marks
 * read on click. Purely additive: the notification bell link still
 * works as a plain link to /user/notifications if JS never runs. */
(function () {
  "use strict";
  var toggle = document.querySelector("[data-notification-toggle]");
  // Only this inner list gets replaced on load; the panel's own header
  // and "View all" footer are siblings of it, not descendants, so a
  // previous version of this script that set the *panel's* innerHTML
  // wiped both of them out the moment notifications finished loading.
  var list = document.querySelector("[data-notification-list]");
  if (!toggle || !list || !window.fetch) return;

  var loaded = false;

  function render(data) {
    if (!data.notifications.length) {
      list.innerHTML = '<div class="empty-state py-4"><p class="mb-0 fs-sm">You\'re all caught up.</p></div>';
      return;
    }
    list.innerHTML = data.notifications
      .map(function (n) {
        var href = n.link_url || "/user/notifications";
        return (
          '<a class="dropdown-item py-2' + (n.is_read ? "" : " fw-semibold") + '" href="' + href + '">' +
          '<div class="fs-sm">' + escapeHtml(n.title) + "</div>" +
          '<div class="fs-xs text-muted-tma">' + escapeHtml(n.message) + "</div>" +
          "</a>"
        );
      })
      .join("");
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  toggle.addEventListener("shown.bs.dropdown", function () {
    if (loaded) return;
    fetch("/api/notifications")
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        loaded = true;
        render(data);
      })
      .catch(function () {
        list.innerHTML = '<div class="p-3 fs-sm text-muted-tma">Couldn\'t load notifications.</div>';
      });
  });
})();
