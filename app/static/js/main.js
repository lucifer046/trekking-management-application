/*
 * Core shared behavior: CSRF header helper, toast rendering (upgrades
 * server-rendered flash alerts into the floating toast stack), the
 * destructive-action confirm modal, sticky-navbar scroll state, mobile
 * nav toggle, and password-visibility toggles. Loaded on every page.
 *
 * Classic scripts (no bundler, no ES module imports); everything shared
 * across files hangs off one `window.TMA` namespace.
 */
window.TMA = window.TMA || {};

(function () {
  "use strict";

  TMA.csrfToken = function () {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  };

  /* ---------------------------------------------------------- toasts --- */
  function ensureToastStack() {
    var stack = document.querySelector(".toast-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "toast-stack";
      stack.setAttribute("aria-live", "polite");
      document.body.appendChild(stack);
    }
    return stack;
  }

  TMA.toast = function (message, category) {
    category = category || "info";
    var stack = ensureToastStack();
    var el = document.createElement("div");
    el.className = "toast-tma toast-tma--" + category;
    el.setAttribute("role", "status");
    el.innerHTML =
      '<span aria-hidden="true">' + iconFor(category) + "</span>" +
      '<span class="toast-tma__message"></span>' +
      '<button type="button" aria-label="Dismiss" class="btn-close btn-close-white ms-auto"></button>';
    el.querySelector(".toast-tma__message").textContent = message;
    stack.appendChild(el);

    requestAnimationFrame(function () {
      el.classList.add("is-visible");
    });

    var remove = function () {
      el.classList.remove("is-visible");
      setTimeout(function () {
        el.remove();
      }, 260);
    };
    el.querySelector("button").addEventListener("click", remove);
    setTimeout(remove, 6000);
  };

  function iconFor(category) {
    switch (category) {
      case "success":
        return "✓";
      case "danger":
        return "⚠";
      case "warning":
        return "⚠";
      default:
        return "ℹ";
    }
  }

  // Upgrade server-rendered flash alerts (the no-JS baseline) into
  // floating toasts once JS is available, so the visual language matches
  // the AJAX-triggered toasts from wishlist.js / notifications.js.
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-flash]").forEach(function (node) {
      TMA.toast(node.textContent.trim(), node.getAttribute("data-flash"));
      node.remove();
    });
  });

  /* ------------------------------------------------- confirm modal ---- */
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (!form.hasAttribute("data-confirm")) return;
    if (form.dataset.confirmed === "true") return;

    event.preventDefault();
    openConfirmModal(form.getAttribute("data-confirm"), form.dataset.confirmTitle || "Please confirm", function () {
      form.dataset.confirmed = "true";
      form.submit();
    });
  });

  function openConfirmModal(message, title, onConfirm) {
    var modalEl = document.getElementById("confirmActionModal");
    if (!modalEl || !window.bootstrap) {
      // Fallback so the action still works if Bootstrap JS hasn't loaded.
      if (window.confirm(message)) onConfirm();
      return;
    }
    modalEl.querySelector(".modal-title").textContent = title;
    modalEl.querySelector(".modal-body").textContent = message;
    var confirmBtn = modalEl.querySelector("[data-confirm-accept]");
    var modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);

    var handler = function () {
      confirmBtn.removeEventListener("click", handler);
      modal.hide();
      onConfirm();
    };
    confirmBtn.addEventListener("click", handler);
    modal.show();
  }

  /* --------------------------------------------------- sticky navbar -- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ------------------------------------------------ password toggles -- */
  document.querySelectorAll(".password-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = document.getElementById(btn.getAttribute("data-target"));
      if (!input) return;
      var showing = input.type === "text";
      input.type = showing ? "password" : "text";
      btn.setAttribute("aria-label", showing ? "Show password" : "Hide password");
      btn.innerHTML = showing
        ? '<i class="bi bi-eye"></i>'
        : '<i class="bi bi-eye-slash"></i>';
    });
  });
})();
