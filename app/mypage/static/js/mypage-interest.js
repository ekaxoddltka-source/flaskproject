function drawCharts() {
    const raw = document.getElementById("chart-data").textContent;
    const data = JSON.parse(raw);

    const top5Labels = data.top5_labels || [];
    const top5Values = data.top5_values || [];
    const radarLabels = data.radar_labels || [];

    // Radar 값(0~1)을 사람이 보기 좋은 0~100 점수로 환산
    let radarValues = (data.radar_values || []).map(v => Math.round(v * 100));

  // -----------------------------
// BAR CHART (TOP 5)
// -----------------------------

// 최대값 가져오기
const maxValue = Math.max(...top5Values, 1);

// 0~100 비율로 정규화
const normalizedValues = top5Values.map(v => Math.round((v / maxValue) * 100));

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
            borderRadius: 6
        }]
    },
    options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                min: 0,
                max: 100,            // 항상 100 고정
                ticks: {
                    stepSize: 20     // 0,20,40,60,80,100
                },
                grid: {
                    color: "rgba(0,0,0,0.1)"
                }
            },
            y: {
                grid: { display: false }
            }
        }
    }
});


    // -----------------------------
    // RADAR CHART (개선된 가독성 버전)
    // -----------------------------
    const radarMax = Math.max(...radarValues, 50); // 최소 50 유지 → 작지 않게

    const ctxRadar = document.getElementById("radarTechChart");
    new Chart(ctxRadar, {
        type: "radar",
        data: {
            labels: radarLabels,
            datasets: [{
                label: "기술 역량 점수",
                data: radarValues,
                borderColor: "rgba(16,185,129,1)",        // 진한 초록
                backgroundColor: "rgba(16,185,129,0.25)", // 안쪽 색
                borderWidth: 2.5,
                pointBackgroundColor: "rgba(16,185,129,1)",
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            layout: { padding: 0 },

            scales: {
                r: {
                    min: 0,
                    max: radarMax,
                    ticks: {
                        stepSize: Math.round(radarMax / 5),
                        backdropColor: "transparent",
                        color: "#444",     // 숫자 색
                        font: { size: 11 }
                    },
                    grid: {
                        color: "rgba(0,0,0,0.15)" // 내부 원 라인
                    },
                    angleLines: {
                        color: "rgba(0,0,0,0.15)" // 방사형 라인
                    },
                    pointLabels: {
                        color: "#111",
                        font: { size: 13, weight: "600" } // 카테고리 글자 크기 증가
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
