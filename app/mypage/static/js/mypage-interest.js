function drawCharts() {
    const raw = document.getElementById("chart-data").textContent;
    const data = JSON.parse(raw);

    const top5Labels = data.top5_labels || [];
    const top5Values = data.top5_values || [];
    const radarLabels = data.radar_labels || [];
    const radarValues = (data.radar_values || []).map(v => Math.round(v * 100));

    /* =========================
       BAR CHART (TOP 5)
    ========================= */
    const maxValue = Math.max(...top5Values, 1);
    const normalizedValues = top5Values.map(v =>
        Math.round((v / maxValue) * 100)
    );

    const ctxBar = document.getElementById("top5TechChart");

    new Chart(ctxBar, {
        type: "bar",
        data: {
            labels: top5Labels,
            datasets: [{
                data: normalizedValues,
                backgroundColor: "rgba(99,102,241,0.8)",
                borderColor: "rgba(99,102,241,1)",
                borderWidth: 2,
                borderRadius: 6,
                barThickness: 22   // ✅ hover 영역 고정
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            animation: false,

            interaction: {
                mode: "nearest",
                intersect: true,
                axis: "y"
            },

            scales: {
                x: {
                    min: 0,
                    max: 100,
                    ticks: { stepSize: 20 }
                },
                y: {
                    grid: { display: false },
                    ticks: { autoSkip: false }
                }
            },

            plugins: {
                legend: { display: false },
                tooltip: { animation: false }
            }
        }
    });

    /* =========================
       RADAR CHART
    ========================= */
    const radarMax = Math.max(...radarValues, 50);
    const ctxRadar = document.getElementById("radarTechChart");

    new Chart(ctxRadar, {
        type: "radar",
        data: {
            labels: radarLabels,
            datasets: [{
                data: radarValues,
                borderColor: "rgba(16,185,129,1)",
                backgroundColor: "rgba(16,185,129,0.25)",
                borderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            layout: { padding: 8 },

            scales: {
                r: {
                    min: 0,
                    max: radarMax,
                    ticks: { display: false },
                    pointLabels: {
                        font: { size: 12, weight: "600" },
                        padding: 6
                    },
                    grid: {
                        color: "rgba(0,0,0,0.15)"
                    },
                    angleLines: {
                        color: "rgba(0,0,0,0.15)"
                    }
                }
            },

            plugins: {
                legend: { display: false }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", drawCharts);
