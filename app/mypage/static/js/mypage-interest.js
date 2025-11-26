function drawCharts() {
    const raw = document.getElementById("chart-data").textContent;
    const data = JSON.parse(raw);

    const top5Labels = data.top5_labels || [];
    const top5Values = data.top5_values || [];
    const radarLabels = data.radar_labels || [];
    const radarValues = data.radar_values || [];

    // -----------------------------
    // BAR CHART (TOP 5)
    // -----------------------------

    // 자동 max 계산
    const barMax = Math.max(...top5Values, 5);  // 최소 5 보장

    const ctxBar = document.getElementById("top5TechChart");
    new Chart(ctxBar, {
        type: "bar",
        data: {
            labels: top5Labels,
            datasets: [{
                data: top5Values,
                backgroundColor: "rgba(99,102,241,0.65)",
                borderColor: "rgba(99,102,241,1)",
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    min: 0,
                    suggestedMax: barMax
                }
            }
        }
    });


    // -----------------------------
    // RADAR CHART
    // -----------------------------

    // Radar도 자동 max 계산
    const radarMax = Math.max(...radarValues, 5);

    const ctxRadar = document.getElementById("radarTechChart");
    new Chart(ctxRadar, {
        type: "radar",
        data: {
            labels: radarLabels,
            datasets: [{
                data: radarValues,
                borderColor: "rgba(16,185,129,1)",
                backgroundColor: "rgba(16,185,129,0.2)",
                pointBackgroundColor: "rgba(16,185,129,1)"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0,
                    suggestedMax: radarMax,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    drawCharts();
});
