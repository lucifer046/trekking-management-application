/* Thin Chart.js wrapper for the admin dashboard. Every chart is driven by
 * one of the /api/charts/* endpoints, which aggregate real rows from the
 * database; per the spec's explicit instruction, nothing here ever
 * generates or displays random/fake numbers.
 *
 * Usage: <canvas data-chart="booking-trends" data-chart-type="line"></canvas>
 * The endpoint slug is derived from data-chart automatically.
 */
(function () {
  "use strict";
  if (!window.Chart) return;

  var palette = ["#1b4332", "#c1502e", "#d4a24c", "#3a6ea5", "#2f855a", "#8b948a"];

  Chart.defaults.font.family = "Inter, sans-serif";
  Chart.defaults.color = "#4d5347";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;

  document.querySelectorAll("[data-chart]").forEach(function (canvas) {
    var slug = canvas.getAttribute("data-chart");
    var type = canvas.getAttribute("data-chart-type") || "bar";

    fetch("/api/charts/" + slug)
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        renderChart(canvas, type, data);
      })
      .catch(function () {
        var wrap = canvas.closest(".chart-wrap");
        if (wrap) wrap.innerHTML = '<p class="text-muted-tma fs-sm text-center py-5">Chart data unavailable.</p>';
      });
  });

  function renderChart(canvas, type, data) {
    var isLine = type === "line";
    var isDoughnut = type === "doughnut";
    new Chart(canvas, {
      type: type,
      data: {
        labels: data.labels,
        datasets: [
          {
            label: canvas.getAttribute("data-chart-label") || "",
            data: data.data,
            backgroundColor: isDoughnut ? palette : isLine ? "rgba(27,67,50,0.12)" : palette[0],
            borderColor: isLine ? palette[0] : "transparent",
            borderWidth: isLine ? 3 : 0,
            borderRadius: type === "bar" ? 8 : 0,
            tension: 0.35,
            fill: isLine,
            pointRadius: isLine ? 3 : 0,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: isDoughnut },
        },
        scales: isDoughnut
          ? {}
          : {
              y: { beginAtZero: true, grid: { color: "#dfdfd3" } },
              x: { grid: { display: false } },
            },
      },
    });
  }
})();
