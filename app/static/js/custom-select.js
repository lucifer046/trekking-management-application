/*
 * Replaces every native <select class="form-select"> with a fully
 * custom-styled dropdown. The native <select> stays in the DOM (just
 * visually hidden, not display:none-removed) so it keeps submitting
 * with its form exactly as before; this only replaces how the *popup
 * list* looks, which is otherwise OS-drawn in most browsers and
 * unreachable by CSS no matter what's done to the <select> itself.
 *
 * The popup menu is rendered into a single shared node appended to
 * <body> (a "portal"), positioned by measuring the trigger button at
 * open time, not nested inside whatever card/search-bar the select
 * happens to live in. Several containers on this site (.search-bar)
 * intentionally set overflow:hidden to fix an unrelated bug, which
 * would otherwise clip a same-container popup; a body-level portal
 * sidesteps that regardless of which container a select is ever put in
 * later, the same way a native <select>'s popup isn't clipped by page
 * layout either.
 */
(function () {
  "use strict";

  var openState = null; // { select, trigger, menu }; at most one open at a time

  var sharedMenu = document.createElement("ul");
  sharedMenu.className = "select-tma__menu";
  sharedMenu.setAttribute("role", "listbox");
  sharedMenu.hidden = true;

  function enhance(select) {
    if (select.dataset.customSelect) return;
    select.dataset.customSelect = "true";

    var wrapper = document.createElement("div");
    wrapper.className = "select-tma";
    // Any inline sizing the <select> itself carried (several templates set
    // e.g. style="max-width:160px" directly on it for a filter row) has to
    // move to the wrapper; that's the element actually occupying space in
    // the layout once the select is hidden inside it.
    var inlineStyle = select.getAttribute("style");
    if (inlineStyle) wrapper.setAttribute("style", inlineStyle);
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);
    select.classList.add("select-tma__native");
    select.tabIndex = -1;

    var trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "select-tma__trigger form-select";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    trigger.disabled = select.disabled;
    // Deliberately NOT moving select.id onto the trigger: page-specific
    // scripts (register.html's role-based field toggle, for one) do
    // getElementById(originalId).value / .addEventListener("change", …)
    // expecting the real value-holding element; moving the id would
    // silently break that (a button has no .value, its own clicks don't
    // fire "change"). Forward label clicks to the trigger instead, so
    // `<label for="field-id">` still opens the dropdown without needing
    // the id to live on the button at all.
    if (select.id) {
      var ownLabel = document.querySelector('label[for="' + select.id + '"]');
      if (ownLabel) {
        ownLabel.addEventListener("click", function (e) {
          e.preventDefault();
          trigger.focus();
          trigger.click();
        });
      }
    }

    var labelEl = document.createElement("span");
    labelEl.className = "select-tma__label";
    trigger.appendChild(labelEl);

    var chevron = document.createElement("i");
    chevron.className = "bi bi-chevron-down select-tma__chevron";
    chevron.setAttribute("aria-hidden", "true");
    trigger.appendChild(chevron);

    wrapper.appendChild(trigger);

    function currentLabel() {
      var opt = select.options[select.selectedIndex];
      return opt ? opt.textContent : "";
    }

    function sync() {
      labelEl.textContent = currentLabel();
    }

    function selectIndex(i) {
      if (select.selectedIndex !== i) {
        select.selectedIndex = i;
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      sync();
    }

    trigger.addEventListener("click", function () {
      if (openState && openState.select === select) {
        closeMenu();
      } else {
        openMenu(select, trigger, selectIndex);
      }
    });

    trigger.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (!openState || openState.select !== select) {
          openMenu(select, trigger, selectIndex);
        }
        if (e.key === "ArrowDown") moveActive(1);
        if (e.key === "ArrowUp") moveActive(-1);
        if (e.key === "Enter" || e.key === " ") {
          var active = sharedMenu.querySelector(".is-active");
          if (active) {
            selectIndex(parseInt(active.getAttribute("data-index"), 10));
            closeMenu();
          }
        }
      } else if (e.key === "Escape") {
        closeMenu();
      }
    });

    // The rest of the app (explore-filters.js's auto-submit, form resets,
    // etc.) still just reads/writes the real <select>, so nothing else
    // needs to know a custom UI is sitting in front of it. Keep the
    // visible label in sync if something else changes the value.
    select.addEventListener("change", sync);

    sync();
  }

  function renderOptions(select, onPick) {
    sharedMenu.innerHTML = "";
    Array.from(select.options).forEach(function (opt, i) {
      var li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("data-index", String(i));
      li.className = "select-tma__option" + (opt.selected ? " is-selected is-active" : "");
      li.setAttribute("aria-selected", opt.selected ? "true" : "false");
      li.textContent = opt.textContent;
      li.addEventListener("mouseenter", function () {
        var current = sharedMenu.querySelector(".is-active");
        if (current) current.classList.remove("is-active");
        li.classList.add("is-active");
      });
      li.addEventListener("click", function () {
        onPick(i);
        closeMenu();
      });
      sharedMenu.appendChild(li);
    });
  }

  function moveActive(delta) {
    var items = Array.from(sharedMenu.children);
    if (!items.length) return;
    var idx = items.findIndex(function (el) {
      return el.classList.contains("is-active");
    });
    if (idx === -1) idx = 0;
    items[idx].classList.remove("is-active");
    idx = Math.max(0, Math.min(items.length - 1, idx + delta));
    items[idx].classList.add("is-active");
    items[idx].scrollIntoView({ block: "nearest" });
  }

  function position(trigger) {
    var rect = trigger.getBoundingClientRect();
    var menuMaxHeight = 260;
    var spaceBelow = window.innerHeight - rect.bottom;
    var openUpward = spaceBelow < menuMaxHeight && rect.top > spaceBelow;

    sharedMenu.style.left = rect.left + window.scrollX + "px";
    sharedMenu.style.width = rect.width + "px";
    sharedMenu.style.maxHeight = menuMaxHeight + "px";
    if (openUpward) {
      sharedMenu.style.top = "";
      sharedMenu.style.bottom = window.innerHeight - rect.top - window.scrollY + "px";
    } else {
      sharedMenu.style.bottom = "";
      sharedMenu.style.top = rect.bottom + window.scrollY + "px";
    }
  }

  function openMenu(select, trigger, onPick) {
    closeMenu();
    renderOptions(select, onPick);
    document.body.appendChild(sharedMenu);
    sharedMenu.hidden = false;
    position(trigger);
    trigger.setAttribute("aria-expanded", "true");
    trigger.closest(".select-tma").classList.add("is-open");
    openState = { select: select, trigger: trigger };

    window.addEventListener("scroll", onReposition, true);
    window.addEventListener("resize", onReposition);
    document.addEventListener("mousedown", onOutsideClick);
  }

  function onReposition() {
    if (openState) position(openState.trigger);
  }

  function onOutsideClick(e) {
    if (!openState) return;
    if (sharedMenu.contains(e.target) || openState.trigger.contains(e.target)) return;
    closeMenu();
  }

  function closeMenu() {
    if (!openState) return;
    openState.trigger.setAttribute("aria-expanded", "false");
    var wrap = openState.trigger.closest(".select-tma");
    if (wrap) wrap.classList.remove("is-open");
    sharedMenu.hidden = true;
    if (sharedMenu.parentNode) sharedMenu.parentNode.removeChild(sharedMenu);
    window.removeEventListener("scroll", onReposition, true);
    window.removeEventListener("resize", onReposition);
    document.removeEventListener("mousedown", onOutsideClick);
    openState = null;
  }

  document.querySelectorAll("select.form-select").forEach(enhance);
})();
