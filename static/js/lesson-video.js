(function () {
  const cfg = window.LESSON_CONFIG;
  if (!cfg || !cfg.videoKind) return;

  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match[2]) : '';
  }
  const csrftoken = getCookie('csrftoken');

  const questions = (cfg.invideoQuestions || []).filter(function (q) { return !q.answered; });
  questions.sort(function (a, b) { return a.trigger_time - b.trigger_time; });
  let questionIndex = 0;
  let isModalOpen = false;
  let player = null;
  let pollTimer = null;
  let progressTimer = null;
  let lastSentPosition = -1;

  const modalEl = document.getElementById('invideoModal');
  const bsModal = modalEl ? new bootstrap.Modal(modalEl, { backdrop: 'static', keyboard: false }) : null;
  const questionTextEl = document.getElementById('invideo-question-text');
  const choicesEl = document.getElementById('invideo-choices');
  const feedbackEl = document.getElementById('invideo-feedback');
  const continueBtn = document.getElementById('invideo-continue-btn');

  function showQuestion(q) {
    isModalOpen = true;
    questionTextEl.textContent = q.text;
    choicesEl.innerHTML = '';
    feedbackEl.classList.add('d-none');
    continueBtn.classList.add('d-none');
    q.choices.forEach(function (choice) {
      const wrapper = document.createElement('div');
      wrapper.className = 'form-check mb-2';
      wrapper.innerHTML =
        '<input class="form-check-input" type="radio" name="invideo-choice" id="ivc-' + choice.id + '" value="' + choice.id + '">' +
        '<label class="form-check-label" for="ivc-' + choice.id + '">' + choice.text + '</label>';
      choicesEl.appendChild(wrapper);
    });
    const submitBtn = document.getElementById('invideo-submit-btn');
    submitBtn.classList.remove('d-none');
    submitBtn.onclick = function () { submitAnswer(q); };
    if (player) player.pauseVideo();
    bsModal.show();
  }

  function submitAnswer(q) {
    const selected = document.querySelector('input[name="invideo-choice"]:checked');
    if (!selected) return;
    fetch(cfg.answerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ question_id: q.id, choice_id: selected.value }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        document.getElementById('invideo-submit-btn').classList.add('d-none');
        feedbackEl.classList.remove('d-none');
        if (data.is_correct) {
          feedbackEl.className = 'alert alert-success';
          feedbackEl.textContent = 'ถูกต้อง!';
        } else {
          feedbackEl.className = 'alert alert-danger';
          feedbackEl.textContent = 'ยังไม่ถูกต้อง เฉลย: ' + data.correct_choice_text;
        }
        continueBtn.classList.remove('d-none');
      });
  }

  continueBtn && continueBtn.addEventListener('click', function () {
    bsModal.hide();
    isModalOpen = false;
    questionIndex += 1;
    if (player) player.playVideo();
  });

  function sendProgress(position, duration) {
    if (!cfg.progressUrl || Math.floor(position) === lastSentPosition) return;
    lastSentPosition = Math.floor(position);
    fetch(cfg.progressUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ position: position, duration: duration }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        const bar = document.getElementById('video-progress-bar');
        const text = document.getElementById('video-progress-text');
        if (bar) {
          bar.style.width = data.percent_watched + '%';
          bar.setAttribute('aria-valuenow', data.percent_watched);
        }
        if (text) text.textContent = data.percent_watched + '%';
        if (data.completed) {
          ['posttest', 'retest'].forEach(function (prefix) {
            const lockBanner = document.getElementById(prefix + '-locked-banner');
            if (lockBanner) lockBanner.classList.add('d-none');
            const unlockBanner = document.getElementById(prefix + '-unlocked-banner');
            if (unlockBanner) unlockBanner.classList.remove('d-none');
          });
        }
      });
  }

  function startTimers() {
    pollTimer = setInterval(function () {
      const time = player.getCurrentTime();
      if (!isModalOpen && questionIndex < questions.length && time >= questions[questionIndex].trigger_time) {
        showQuestion(questions[questionIndex]);
      }
    }, 500);
    if (cfg.progressUrl) {
      progressTimer = setInterval(function () {
        sendProgress(player.getCurrentTime(), player.getDuration());
      }, 5000);
    }
  }

  if (cfg.videoKind === 'file') {
    const videoEl = document.getElementById('html5-player');
    if (!videoEl) return;
    player = {
      getCurrentTime: function () { return videoEl.currentTime; },
      getDuration: function () { return videoEl.duration || 0; },
      pauseVideo: function () { videoEl.pause(); },
      playVideo: function () { videoEl.play(); },
    };
    videoEl.addEventListener('loadedmetadata', startTimers, { once: true });
    videoEl.addEventListener('pause', function () { sendProgress(videoEl.currentTime, videoEl.duration || 0); });
    videoEl.addEventListener('ended', function () { sendProgress(videoEl.currentTime, videoEl.duration || 0); });
    return;
  }

  if (cfg.videoKind === 'youtube') {
    if (!cfg.videoId) return;
    window.onYouTubeIframeAPIReady = function () {
      const ytPlayer = new YT.Player('yt-player', {
        videoId: cfg.videoId,
        playerVars: { rel: 0 },
        events: {
          onReady: function () {
            player = {
              getCurrentTime: function () { return ytPlayer.getCurrentTime(); },
              getDuration: function () { return ytPlayer.getDuration(); },
              pauseVideo: function () { ytPlayer.pauseVideo(); },
              playVideo: function () { ytPlayer.playVideo(); },
            };
            startTimers();
          },
          onStateChange: function (event) {
            if (event.data === YT.PlayerState.PAUSED || event.data === YT.PlayerState.ENDED) {
              sendProgress(ytPlayer.getCurrentTime(), ytPlayer.getDuration());
            }
          },
        },
      });
    };
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.body.appendChild(tag);
  }
})();
