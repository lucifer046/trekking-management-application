/* Progressive-enhancement auto-submit for the explore page filter bar.
 * Deliberately a plain GET form submit (debounced for the text input),
 * not a fetch/JSON partial refresh — the spec requires server-side
 * filtering for database queries, and a full Jinja-rendered response is
 * the simplest way to guarantee filtering stays authoritative there
 * rather than duplicated in JS. Works with JS disabled via the form's
 * own Search button either way. */
(function () {
  "use strict";
  var form = document.querySelector("[data-explore-form]");
  if (!form) return;

  form.querySelectorAll("select, input[type=checkbox]").forEach(function (field) {
    field.addEventListener("change", function () {
      form.submit();
    });
  });

  var searchInput = form.querySelector('input[type="search"], input[name="q"]');
  if (searchInput) {
    var timer = null;
    searchInput.addEventListener("input", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        form.submit();
      }, 550);
    });
  }
})();
