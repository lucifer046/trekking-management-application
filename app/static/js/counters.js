/* Animated count-up for elements with [data-count-to]. Runs once, when
 * the element scrolls into view. Reduced-motion: jump straight to the
 * final value instead of animating. */
(function () {
  "use strict";
  var targets = document.querySelectorAll("[data-count-to]");
  if (!targets.length) return;

  var prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function animate(el) {
    var to = parseInt(el.getAttribute("data-count-to"), 10) || 0;
    if (prefersReduced) {
      el.textContent = to.toLocaleString();
      return;
    }
    var duration = 1200;
    var start = null;
    function step(timestamp) {
      if (start === null) start = timestamp;
      var progress = Math.min((timestamp - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(eased * to).toLocaleString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animate(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    targets.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    targets.forEach(animate);
  }
})();
