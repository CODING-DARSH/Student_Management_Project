document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("gradeChart");
  if (!canvas) return;

  // If no chart data available
  if (!chartLabels || chartLabels.length === 0) {
    canvas.outerHTML = `<p class="text-gray-500 mt-4">No grades available yet. Enroll in courses to see your progress.</p>`;
    return;
  }

  const ctx = canvas.getContext("2d");

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: chartLabels,
      datasets: [{
        label: "Grades",
        data: chartData,
        backgroundColor: [
          "#3b82f6",
          "#8b5cf6",
          "#f59e0b",
          "#10b981",
          "#ef4444"
        ],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      animation: {
        duration: 900,
        easing: "easeOutQuart"
      },
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: "Your Course Performance",
          color: "#f1f1f1",
          font: { size: 18 }
        },
        tooltip: {
          backgroundColor: "#1f2937",
          titleColor: "#fff",
          bodyColor: "#d1d5db",
          borderWidth: 1,
          borderColor: "#374151"
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: "#f1f1f1" },
          grid: { color: "#2f2f2f" }
        },
        x: {
          ticks: { color: "#f1f1f1" },
          grid: { color: "#2f2f2f" }
        }
      }
    }
  });
});
