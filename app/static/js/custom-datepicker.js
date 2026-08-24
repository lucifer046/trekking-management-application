/*
 * Replaces every native <input type="date"> with a fully custom-styled
 * calendar. Same architecture as custom-select.js (see that file for
 * the full rationale): the native input stays in the DOM, just
 * visually hidden, so it keeps submitting with its form under its
 * original name and in the browser's normal YYYY-MM-DD value format;
 * this only replaces how the *picker UI* looks and behaves, which is
 * otherwise OS-drawn and unreachable by CSS no matter what's done to
 * the input itself (the actual complaint this exists to fix).
 *
 * The calendar panel is a single shared node appended to <body> at
 * open time (a "portal"), positioned by measuring the trigger button,
 * not nested inside whatever card/form happens to contain the field;
 * several containers on this site intentionally clip overflow, which
 * would otherwise cut a same-container popup off.
 */
(function () {
  "use strict";

  var MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var WEEKDAY_LABELS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

  var openState = null; // { input, trigger, wrapper, viewYear, viewMonth, mode: "days"|"months" }

  var panel = document.createElement("div");
  panel.className = "datepicker-tma__panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "Choose a date");
  panel.hidden = true;
  panel.innerHTML =
    '<div class="datepicker-tma__header">' +
    '  <button type="button" class="datepicker-tma__nav" data-prev aria-label="Previous"><i class="bi bi-chevron-left"></i></button>' +
    '  <button type="button" class="datepicker-tma__monthyear" data-monthyear></button>' +
    '  <button type="button" class="datepicker-tma__nav" data-next aria-label="Next"><i class="bi bi-chevron-right"></i></button>' +
    '</div>' +
    '<div data-days-view>' +
    '  <div class="datepicker-tma__weekdays">' + WEEKDAY_LABELS.map(function (d) { return "<span>" + d + "</span>"; }).join("") + '</div>' +
    '  <div class="datepicker-tma__grid" data-grid role="grid"></div>' +
    '</div>' +
    '<div data-months-view hidden>' +
    '  <div class="datepicker-tma__months" data-months></div>' +
    '</div>' +
    '<div class="datepicker-tma__footer">' +
    '  <button type="button" class="datepicker-tma__action" data-clear>Clear</button>' +
    '  <button type="button" class="datepicker-tma__action" data-today>Today</button>' +
    '</div>';

  var elMonthYear = panel.querySelector("[data-monthyear]");
  var elPrev = panel.querySelector("[data-prev]");
  var elNext = panel.querySelector("[data-next]");
  var elDaysView = panel.querySelector("[data-days-view]");
  var elMonthsView = panel.querySelector("[data-months-view]");
  var elGrid = panel.querySelector("[data-grid]");
  var elMonths = panel.querySelector("[data-months]");
  var elClear = panel.querySelector("[data-clear]");
  var elToday = panel.querySelector("[data-today]");

  function pad2(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function toISO(y, m, d) {
    return y + "-" + pad2(m + 1) + "-" + pad2(d);
  }

  function parseISO(value) {
    // "YYYY-MM-DD" -> {y, m (0-indexed), d}; returns null for empty/invalid.
    if (!value) return null;
    var parts = value.split("-");
    if (parts.length !== 3) return null;
    var y = parseInt(parts[0], 10), m = parseInt(parts[1], 10) - 1, d = parseInt(parts[2], 10);
    if (isNaN(y) || isNaN(m) || isNaN(d)) return null;
    return { y: y, m: m, d: d };
  }

  function formatDisplay(value) {
    var parsed = parseISO(value);
    if (!parsed) return "";
    return parsed.d + " " + MONTH_NAMES[parsed.m].slice(0, 3) + " " + parsed.y;
  }

  function todayParts() {
    var now = new Date();
    return { y: now.getFullYear(), m: now.getMonth(), d: now.getDate() };
  }

  function enhance(input) {
    if (input.dataset.customDatepicker) return;
    input.dataset.customDatepicker = "true";

    var wrapper = document.createElement("div");
    wrapper.className = "datepicker-tma";
    var inlineStyle = input.getAttribute("style");
    if (inlineStyle) wrapper.setAttribute("style", inlineStyle);
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    input.classList.add("datepicker-tma__native");
    input.tabIndex = -1;

    var trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "datepicker-tma__trigger form-control" + (input.classList.contains("is-invalid") ? " is-invalid" : "");
    trigger.disabled = input.disabled;
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-expanded", "false");

    // Same reasoning as custom-select.js: don't move the native
    // input's id onto the trigger (nothing here currently depends on
    // it directly, but keeping the pattern identical avoids surprises
    // later), forward <label for="id"> clicks to the trigger instead.
    if (input.id) {
      var ownLabel = document.querySelector('label[for="' + input.id + '"]');
      if (ownLabel) {
        ownLabel.addEventListener("click", function (e) {
          e.preventDefault();
          trigger.focus();
          trigger.click();
        });
      }
    }

    var labelEl = document.createElement("span");
    labelEl.className = "datepicker-tma__label";
    trigger.appendChild(labelEl);

    var icon = document.createElement("i");
    icon.className = "bi bi-calendar3 datepicker-tma__icon";
    icon.setAttribute("aria-hidden", "true");
    trigger.appendChild(icon);

    wrapper.appendChild(trigger);

    var placeholder = input.getAttribute("placeholder") || "Select date";

    function sync() {
      var display = formatDisplay(input.value);
      labelEl.textContent = display || placeholder;
      labelEl.classList.toggle("is-placeholder", !display);
    }

    trigger.addEventListener("click", function () {
      if (openState && openState.input === input) closePanel();
      else openPanel(input, trigger, wrapper);
    });
    trigger.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        if (!openState || openState.input !== input) openPanel(input, trigger, wrapper);
      } else if (e.key === "Escape") {
        closePanel();
      }
    });

    input.addEventListener("change", sync);
    sync();
  }

  // ---------------------------------------------------------- rendering

  function inRange(input, y, m, d) {
    var iso = toISO(y, m, d);
    if (input.min && iso < input.min) return false;
    if (input.max && iso > input.max) return false;
    return true;
  }

  function renderDays() {
    var s = openState;
    var selected = parseISO(s.input.value);
    var today = todayParts();
    var firstOfMonth = new Date(s.viewYear, s.viewMonth, 1);
    var startWeekday = firstOfMonth.getDay(); // 0 = Sunday
    var daysInMonth = new Date(s.viewYear, s.viewMonth + 1, 0).getDate();
    var prevMonthDays = new Date(s.viewYear, s.viewMonth, 0).getDate();

    elMonthYear.textContent = MONTH_NAMES[s.viewMonth] + " " + s.viewYear;
    elGrid.innerHTML = "";

    var cellIndex = 0;
    var totalCells = 42; // a fixed 6-week grid keeps the panel height stable month to month
    for (var i = 0; i < totalCells; i++) {
      var y = s.viewYear, m = s.viewMonth, d;
      var outside = false;
      if (i < startWeekday) {
        d = prevMonthDays - startWeekday + i + 1;
        m = s.viewMonth - 1;
        outside = true;
      } else if (i >= startWeekday + daysInMonth) {
        d = i - (startWeekday + daysInMonth) + 1;
        m = s.viewMonth + 1;
        outside = true;
      } else {
        d = i - startWeekday + 1;
      }
      if (m < 0) { m = 11; y -= 1; }
      if (m > 11) { m = 0; y += 1; }

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "datepicker-tma__day";
      btn.textContent = String(d);
      btn.setAttribute("data-y", y);
      btn.setAttribute("data-m", m);
      btn.setAttribute("data-d", d);
      btn.tabIndex = -1;

      var isSelected = selected && selected.y === y && selected.m === m && selected.d === d;
      var isToday = today.y === y && today.m === m && today.d === d;
      if (outside) btn.classList.add("is-outside");
      if (isToday) btn.classList.add("is-today");
      if (isSelected) btn.classList.add("is-selected");

      if (!inRange(s.input, y, m, d)) {
        btn.disabled = true;
      } else {
        btn.addEventListener("click", function () {
          var yy = parseInt(this.getAttribute("data-y"), 10);
          var mm = parseInt(this.getAttribute("data-m"), 10);
          var dd = parseInt(this.getAttribute("data-d"), 10);
          commitDate(yy, mm, dd);
        });
      }
      elGrid.appendChild(btn);
      cellIndex++;
    }

    // Roving tabindex: the selected day (or today, or the 1st) is the
    // one Tab actually reaches; arrow keys move focus from there.
    var focusTarget =
      elGrid.querySelector(".is-selected:not(:disabled)") ||
      elGrid.querySelector(".is-today:not(:disabled)") ||
      elGrid.querySelector("button:not(.is-outside):not(:disabled)") ||
      elGrid.querySelector("button:not(:disabled)");
    if (focusTarget) focusTarget.tabIndex = 0;
  }

  function renderMonths() {
    var s = openState;
    var selected = parseISO(s.input.value);
    elMonthYear.textContent = String(s.viewYear);
    elMonths.innerHTML = "";
    MONTH_NAMES.forEach(function (name, idx) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "datepicker-tma__month";
      btn.textContent = name.slice(0, 3);
      if (selected && selected.y === s.viewYear && selected.m === idx) btn.classList.add("is-selected");
      // A month is only fully out of range if *every* day in it is;
      // approximated here by checking just the 1st, good enough for a
      // quick-jump view (the day grid enforces the real per-day limit).
      var daysInThisMonth = new Date(s.viewYear, idx + 1, 0).getDate();
      var anyDayInRange = false;
      for (var d = 1; d <= daysInThisMonth && !anyDayInRange; d++) {
        if (inRange(s.input, s.viewYear, idx, d)) anyDayInRange = true;
      }
      if (!anyDayInRange) btn.disabled = true;
      else {
        btn.addEventListener("click", function () {
          s.viewMonth = idx;
          setMode("days");
        });
      }
      elMonths.appendChild(btn);
    });
  }

  function setMode(mode) {
    openState.mode = mode;
    var isDays = mode === "days";
    elDaysView.hidden = !isDays;
    elMonthsView.hidden = isDays;
    if (isDays) {
      renderDays();
    } else {
      renderMonths();
    }
  }

  function commitDate(y, m, d) {
    var s = openState;
    var iso = toISO(y, m, d);
    if (s.input.value !== iso) {
      s.input.value = iso;
      s.input.dispatchEvent(new Event("change", { bubbles: true }));
    }
    closePanel();
    s.trigger.focus();
  }

  elPrev.addEventListener("click", function () {
    var s = openState;
    if (!s) return;
    if (s.mode === "days") {
      s.viewMonth -= 1;
      if (s.viewMonth < 0) { s.viewMonth = 11; s.viewYear -= 1; }
      renderDays();
    } else {
      s.viewYear -= 1;
      renderMonths();
    }
  });
  elNext.addEventListener("click", function () {
    var s = openState;
    if (!s) return;
    if (s.mode === "days") {
      s.viewMonth += 1;
      if (s.viewMonth > 11) { s.viewMonth = 0; s.viewYear += 1; }
      renderDays();
    } else {
      s.viewYear += 1;
      renderMonths();
    }
  });
  elMonthYear.addEventListener("click", function () {
    if (!openState) return;
    setMode(openState.mode === "days" ? "months" : "days");
  });
  elClear.addEventListener("click", function () {
    var s = openState;
    if (!s) return;
    if (s.input.value !== "") {
      s.input.value = "";
      s.input.dispatchEvent(new Event("change", { bubbles: true }));
    }
    closePanel();
    s.trigger.focus();
  });
  elToday.addEventListener("click", function () {
    var t = todayParts();
    if (openState && inRange(openState.input, t.y, t.m, t.d)) {
      commitDate(t.y, t.m, t.d);
    }
  });

  // Arrow-key navigation across the day grid; Home/End jump to the
  // start/end of the visible week is intentionally left out to keep
  // this to the interactions the spec actually asks for.
  elGrid.addEventListener("keydown", function (e) {
    var s = openState;
    if (!s || s.mode !== "days") return;
    var current = document.activeElement;
    if (!current || !current.classList.contains("datepicker-tma__day")) return;

    var delta = 0;
    if (e.key === "ArrowLeft") delta = -1;
    else if (e.key === "ArrowRight") delta = 1;
    else if (e.key === "ArrowUp") delta = -7;
    else if (e.key === "ArrowDown") delta = 7;
    else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (!current.disabled) current.click();
      return;
    } else if (e.key === "Escape") {
      e.stopPropagation();
      closePanel();
      s.trigger.focus();
      return;
    } else {
      return;
    }
    e.preventDefault();

    var y = parseInt(current.getAttribute("data-y"), 10);
    var m = parseInt(current.getAttribute("data-m"), 10);
    var d = parseInt(current.getAttribute("data-d"), 10);
    var next = new Date(y, m, d + delta);
    var crossedMonth = next.getMonth() !== s.viewMonth || next.getFullYear() !== s.viewYear;
    if (crossedMonth) {
      s.viewYear = next.getFullYear();
      s.viewMonth = next.getMonth();
      renderDays();
    }
    var selector = '.datepicker-tma__day[data-y="' + next.getFullYear() + '"][data-m="' + next.getMonth() + '"][data-d="' + next.getDate() + '"]';
    var target = elGrid.querySelector(selector);
    if (target) {
      current.tabIndex = -1;
      target.tabIndex = 0;
      target.focus();
    }
  });

  // ------------------------------------------------------------ position

  function position(trigger) {
    if (window.innerWidth < 576) {
      // Mobile gets a fixed, larger bottom-anchored panel via CSS
      // (see components.css); no inline positioning needed here.
      panel.style.cssText = "";
      return;
    }
    var margin = 8;
    var rect = trigger.getBoundingClientRect();
    // scrollHeight (not offsetHeight) deliberately: this runs again on
    // every scroll/resize while the panel is open, by which point a
    // previous call may have already clamped its max-height below, and
    // offsetHeight would then measure that *clamped* height instead of
    // how tall the content actually wants to be, only ever letting the
    // panel shrink further and never grow back if more room opens up.
    var naturalHeight = panel.scrollHeight;
    var spaceBelow = window.innerHeight - rect.bottom - margin;
    var spaceAbove = rect.top - margin;
    // Opening upward only helps if there's actually more room up there;
    // picking that side without checking it also fits let the panel
    // clip past the *top* of the viewport instead of the bottom, which
    // is the bug this replaced (a panel taller than either gap, on a
    // trigger near the top of a short-ish viewport, opened upward
    // anyway and rendered a few px into negative territory).
    var openUpward = naturalHeight > spaceBelow && spaceAbove > spaceBelow;
    var available = openUpward ? spaceAbove : spaceBelow;

    var left = rect.left + window.scrollX;
    var maxLeft = window.scrollX + window.innerWidth - panel.offsetWidth - margin;
    if (left > maxLeft) left = Math.max(window.scrollX + margin, maxLeft);
    panel.style.left = left + "px";

    // Whichever side is chosen, never let the panel claim more height
    // than that side actually has: clamp and let it scroll internally
    // rather than ever extending past either viewport edge.
    panel.style.maxHeight = Math.max(160, Math.min(naturalHeight, available)) + "px";
    panel.style.overflowY = naturalHeight > available ? "auto" : "";

    if (openUpward) {
      panel.style.top = "";
      panel.style.bottom = window.innerHeight - rect.top - window.scrollY + "px";
    } else {
      panel.style.bottom = "";
      panel.style.top = rect.bottom + window.scrollY + "px";
    }
  }

  function openPanel(input, trigger, wrapper) {
    closePanel();
    var current = parseISO(input.value);
    var base = current || todayParts();
    openState = { input: input, trigger: trigger, wrapper: wrapper, viewYear: base.y, viewMonth: base.m, mode: "days" };

    document.body.appendChild(panel);
    panel.hidden = false;
    document.body.classList.add("datepicker-open");
    setMode("days");
    position(trigger);

    trigger.setAttribute("aria-expanded", "true");
    wrapper.classList.add("is-open");

    // Moving focus into the grid doesn't need a paint frame to be
    // correct, only the animation class does (it needs the browser to
    // register the panel's pre-transition state on one frame before
    // switching to the post-transition one); keeping focus outside the
    // rAF means keyboard users reach the grid immediately rather than
    // however long the next frame happens to take.
    var focusTarget = elGrid.querySelector('[tabindex="0"]');
    if (focusTarget) focusTarget.focus();
    requestAnimationFrame(function () {
      panel.classList.add("is-visible");
    });

    window.addEventListener("scroll", onReposition, true);
    window.addEventListener("resize", onReposition);
    document.addEventListener("mousedown", onOutsideClick);
  }

  function onReposition() {
    if (openState) position(openState.trigger);
  }

  function onOutsideClick(e) {
    if (!openState) return;
    if (panel.contains(e.target) || openState.trigger.contains(e.target)) return;
    closePanel();
  }

  function closePanel() {
    if (!openState) return;
    openState.trigger.setAttribute("aria-expanded", "false");
    openState.wrapper.classList.remove("is-open");
    panel.classList.remove("is-visible");
    panel.hidden = true;
    if (panel.parentNode) panel.parentNode.removeChild(panel);
    document.body.classList.remove("datepicker-open");
    window.removeEventListener("scroll", onReposition, true);
    window.removeEventListener("resize", onReposition);
    document.removeEventListener("mousedown", onOutsideClick);
    openState = null;
  }

  document.addEventListener("keydown", function (e) {
    // The grid's own keydown handler (above) already covers Escape
    // while focus is on a day cell, and stops the event from reaching
    // here; this only needs to catch Escape while focus is elsewhere
    // in the panel (month/year view, footer buttons).
    if (e.key === "Escape" && openState && panel.contains(document.activeElement)) {
      var trigger = openState.trigger;
      closePanel();
      trigger.focus();
    }
  });

  document.querySelectorAll('input[type="date"]').forEach(enhance);
})();
