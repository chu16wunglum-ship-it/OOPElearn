(function () {
  const dataEl = document.getElementById('chart-data');
  const canvas = document.getElementById('progress-chart');
  if (!dataEl || !canvas || typeof Chart === 'undefined') return;

  const data = JSON.parse(dataEl.textContent);

  const seriesColor = { pretest: '#4f46e5', video: '#06b6d4', invideo: '#f59e0b', posttest: '#10b981' };
  const ink = '#52514e';
  const gridline = '#e1e0d9';

  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        { label: 'ก่อนเรียน', data: data.pretest, backgroundColor: seriesColor.pretest },
        { label: 'ดูวิดีโอ', data: data.video, backgroundColor: seriesColor.video },
        { label: 'ระหว่างวิดีโอ', data: data.invideo, backgroundColor: seriesColor.invideo },
        { label: 'หลังเรียน', data: data.posttest, backgroundColor: seriesColor.posttest },
      ].map(function (ds) {
        return Object.assign(ds, { borderRadius: 4, barThickness: 20, borderSkipped: 'bottom' });
      }),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0, max: 100, ticks: { stepSize: 20, color: ink, callback: function (v) { return v + '%'; } },
          grid: { color: gridline, drawTicks: false },
          border: { display: false },
        },
        x: {
          ticks: { color: ink },
          grid: { display: false },
          border: { color: gridline },
        },
      },
      plugins: {
        legend: { position: 'top', labels: { color: ink, usePointStyle: true, boxWidth: 8 } },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              const v = ctx.parsed.y;
              return ctx.dataset.label + ': ' + (v === null ? 'ไม่มีข้อมูล' : v + '%');
            },
          },
        },
      },
    },
  });
})();
