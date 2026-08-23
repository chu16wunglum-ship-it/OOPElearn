(function () {
  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match[2]) : '';
  }
  const csrftoken = getCookie('csrftoken');

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  document.querySelectorAll('[data-ai-summary-btn]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const url = btn.dataset.url;
      const target = document.getElementById(btn.dataset.target);
      if (!url || !target) return;

      btn.disabled = true;
      target.innerHTML = '<p class="text-secondary fst-italic mb-0">AI กำลังวิเคราะห์...</p>';

      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({}),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          const text = data.summary || data.error || 'เกิดข้อผิดพลาด';
          target.innerHTML = '<p class="mb-0" style="white-space: pre-wrap;">' + escapeHtml(text) + '</p>';
        })
        .catch(function () {
          target.innerHTML = '<p class="text-danger mb-0">เกิดข้อผิดพลาดในการเชื่อมต่อ</p>';
        })
        .finally(function () {
          btn.disabled = false;
        });
    });
  });
})();
