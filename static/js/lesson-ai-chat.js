(function () {
  const cfg = window.LESSON_CONFIG;
  if (!cfg || !cfg.aiChatUrl) return;

  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match[2]) : '';
  }
  const csrftoken = getCookie('csrftoken');

  const listEl = document.getElementById('ai-messages');
  const formEl = document.getElementById('ai-form');
  const inputEl = document.getElementById('ai-text-input');
  const toggleBtn = document.getElementById('ai-widget-toggle');
  const panelEl = document.getElementById('ai-widget-panel');
  const closeBtn = document.getElementById('ai-widget-close');
  if (!listEl || !formEl) return;

  function isPanelOpen() {
    return panelEl && !panelEl.classList.contains('d-none');
  }

  if (toggleBtn && panelEl) {
    toggleBtn.addEventListener('click', function () {
      if (isPanelOpen()) {
        panelEl.classList.add('d-none');
      } else {
        panelEl.classList.remove('d-none');
        listEl.scrollTop = listEl.scrollHeight;
      }
    });
  }
  if (closeBtn && panelEl) {
    closeBtn.addEventListener('click', function () { panelEl.classList.add('d-none'); });
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'ai-msg ai-msg-user';
    div.textContent = text;
    listEl.appendChild(div);
    listEl.scrollTop = listEl.scrollHeight;
  }

  function appendLoading() {
    const div = document.createElement('div');
    div.className = 'ai-msg ai-msg-loading';
    div.id = 'ai-loading';
    div.textContent = 'AI กำลังคิด...';
    listEl.appendChild(div);
    listEl.scrollTop = listEl.scrollHeight;
  }

  function removeLoading() {
    const el = document.getElementById('ai-loading');
    if (el) el.remove();
  }

  function appendAnswer(text) {
    const div = document.createElement('div');
    div.className = 'ai-msg ai-msg-answer';
    div.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
    listEl.appendChild(div);
    listEl.scrollTop = listEl.scrollHeight;
  }

  formEl.addEventListener('submit', function (e) {
    e.preventDefault();
    const question = inputEl.value.trim();
    if (!question) return;
    appendUserMessage(question);
    inputEl.value = '';
    inputEl.disabled = true;
    appendLoading();

    fetch(cfg.aiChatUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ question: question }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        removeLoading();
        appendAnswer(data.answer || data.error || 'เกิดข้อผิดพลาด');
      })
      .catch(function () {
        removeLoading();
        appendAnswer('เกิดข้อผิดพลาดในการเชื่อมต่อ');
      })
      .finally(function () {
        inputEl.disabled = false;
        inputEl.focus();
      });
  });
})();
