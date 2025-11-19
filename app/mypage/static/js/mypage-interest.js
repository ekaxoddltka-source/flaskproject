function drawCharts() {
    const raw = document.getElementById("chart-data").textContent;
    const data = JSON.parse(raw);

    const top5Labels = data.top5_labels || [];
    const top5Values = data.top5_values || [];
    const radarLabels = data.radar_labels || [];
    const radarValues = data.radar_values || [];

    // BAR
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
        responsive: false,
        scales: {
            x: {
                type: 'linear',
        		min: 0,
        		max: 100,
       			suggestedMax: 100
            }
        }
    }
});


    // RADAR
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
        responsive: false,
        scales: {
            r: {
                min: 0,
        max: 100,
        suggestedMax: 100,
        beginAtZero: true
                
            }
        }
    }
});

	
}
document.addEventListener("DOMContentLoaded", function () {
    drawCharts();
});

