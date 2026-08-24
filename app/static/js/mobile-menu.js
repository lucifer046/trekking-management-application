/* Mobile slide-down navigation menu: open/close, backdrop, Escape to
 * close, and swapping the hamburger icon for a close icon while open.
 * Deliberately not a Bootstrap collapse/dropdown: those are built for
 * inline-flow or floating-anchored content, not a full-width overlay
 * panel anchored to the header with its own backdrop, so this is a
 * small purpose-built controller instead. */
(function () {
  "use strict";

  var toggle = document.querySelector("[data-mobile-menu-toggle]");
  var menu = document.querySelector("[data-mobile-menu]");
  var backdrop = document.querySelector("[data-mobile-menu-backdrop]");
  if (!toggle || !menu || !backdrop) return;

  var icon = toggle.querySelector("i");

  function isOpen() {
    return toggle.getAttribute("aria-expanded") === "true";
  }

  function open() {
    menu.hidden = false;
    backdrop.hidden = false;
    // Force a reflow between un-hiding and adding .is-open, so the
    // browser actually has a "before" state to transition from rather
    // than jumping straight to the open state with no animation.
    void menu.offsetWidth;
    menu.classList.add("is-open");
    backdrop.classList.add("is-visible");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Close navigation");
    if (icon) {
      icon.classList.remove("bi-list");
      icon.classList.add("bi-x-lg");
    }
  }

  function close() {
    menu.classList.remove("is-open");
    backdrop.classList.remove("is-visible");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Open navigation");
    if (icon) {
      icon.classList.remove("bi-x-lg");
      icon.classList.add("bi-list");
    }
    // Wait for the close transition before actually removing it from
    // the layout/accessibility tree; falls back to an immediate hide
    // if the transition is disabled (prefers-reduced-motion) since
    // transitionend still fires for a 0-duration transition, but a
    // timeout backstops that in case it doesn't in some browser.
    var done = false;
    var finish = function () {
      if (done) return;
      done = true;
      if (!isOpen()) {
        menu.hidden = true;
        backdrop.hidden = true;
      }
      menu.removeEventListener("transitionend", finish);
    };
    menu.addEventListener("transitionend", finish);
    window.setTimeout(finish, 300);
  }

  toggle.addEventListener("click", function () {
    if (isOpen()) close();
    else open();
  });

  backdrop.addEventListener("click", close);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && isOpen()) close();
  });

  // A resize up past the desktop breakpoint while the menu happens to
  // be open (e.g. rotating a tablet, or a real window resize) should
  // close it rather than leave an orphaned open mobile panel sitting
  // behind the now-visible desktop nav.
  window.addEventListener("resize", function () {
    if (window.innerWidth >= 992 && isOpen()) close();
  });

  // Close on navigation/logout rather than leaving the menu open in
  // the page the browser's back/forward cache restores.
  menu.querySelectorAll("a, button").forEach(function (el) {
    el.addEventListener("click", close);
  });
})();
