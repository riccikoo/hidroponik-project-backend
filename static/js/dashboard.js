const ctx = document.getElementById('sensorChart').getContext('2d');

const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Nilai Sensor pH Air',
            data: [],
            borderColor: '#43a047',
            borderWidth: 2,
            fill: false,
            tension: 0.3
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: 'Nilai pH' }
            },
            x: {
                title: { display: true, text: 'Waktu' }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#333' }
            }
        }
    }
});

let dataPoints = [];

function simulateData() {
    const value = 6 + Math.random() * 2; // simulasi nilai pH (6 - 8)
    const time = new Date().toLocaleTimeString();

    dataPoints.push({ time, value });
    if (dataPoints.length > 15) dataPoints.shift();

    updateDashboard();
}

function updateDashboard() {
    const labels = dataPoints.map(d => d.time);
    const values = dataPoints.map(d => d.value);

    chart.data.labels = labels;
    chart.data.datasets[0].data = values;
    chart.update();

    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);
    const latest = values[values.length - 1].toFixed(2);

    document.getElementById('maxVal').textContent = max.toFixed(2);
    document.getElementById('minVal').textContent = min.toFixed(2);
    document.getElementById('avgVal').textContent = avg;
    document.getElementById('latestVal').textContent = latest;
    document.getElementById('updateTime').textContent = new Date().toLocaleTimeString();
}

setInterval(simulateData, 2000);
simulateData();
