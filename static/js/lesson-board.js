(function () {
  const cfg = window.LESSON_CONFIG;
  if (!cfg || !cfg.boardUrl) return;

  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match[2]) : '';
  }
  const csrftoken = getCookie('csrftoken');

  const listEl = document.getElementById('board-messages');
  const formEl = document.getElementById('board-form');
  const inputEl = document.getElementById('board-text-input');
  const toggleBtn = document.getElementById('chat-widget-toggle');
  const panelEl = document.getElementById('chat-widget-panel');
  const closeBtn = document.getElementById('chat-widget-close');
  if (!listEl || !formEl) return;

  function isPanelOpen() {
    return panelEl && !panelEl.classList.contains('d-none');
  }

  function openPanel() {
    if (!panelEl) return;
    panelEl.classList.remove('d-none');
    toggleBtn.classList.remove('has-unread');
    listEl.scrollTop = listEl.scrollHeight;
  }

  if (toggleBtn && panelEl) {
    toggleBtn.addEventListener('click', function () {
      isPanelOpen() ? panelEl.classList.add('d-none') : openPanel();
    });
  }
  if (closeBtn && panelEl) {
    closeBtn.addEventListener('click', function () { panelEl.classList.add('d-none'); });
  }

  let lastId = 0;
  listEl.querySelectorAll('.board-msg').forEach(function (el) {
    lastId = Math.max(lastId, parseInt(el.dataset.id, 10) || 0);
  });

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function appendMessage(message) {
    const hint = document.getElementById('board-empty-hint');
    if (hint) hint.remove();
    const div = document.createElement('div');
    div.className = 'board-msg' + (message.is_teacher ? ' teacher' : '');
    div.dataset.id = message.id;
    div.innerHTML =
      '<div class="board-msg-meta">' +
      '<span class="fw-semibold">' + escapeHtml(message.author_name) + '</span>' +
      (message.is_teacher ? ' <span class="badge role-badge role-teacher">ครู</span>' : '') +
      ' <span class="text-secondary">' + message.created_at + '</span>' +
      '</div><div class="board-msg-text">' + escapeHtml(message.text).replace(/\n/g, '<br>') + '</div>';
    listEl.appendChild(div);
    lastId = Math.max(lastId, message.id);
    if (isPanelOpen()) {
      listEl.scrollTop = listEl.scrollHeight;
    } else if (toggleBtn) {
      toggleBtn.classList.add('has-unread');
    }
  }

  function poll() {
    fetch(cfg.boardUrl + '?after_id=' + lastId)
      .then(function (r) { return r.json(); })
      .then(function (data) { (data.messages || []).forEach(appendMessage); });
  }

  formEl.addEventListener('submit', function (e) {
    e.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;
    fetch(cfg.boardUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ text: text }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.message) {
          appendMessage(data.message);
          inputEl.value = '';
        }
      });
  });

  setInterval(poll, 8000);
})();
