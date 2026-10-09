(function () {
  const cfg = window.BOSS_BATTLE_CONFIG;
  if (!cfg || !cfg.questions || !cfg.questions.length) return;

  function getCookie(name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? decodeURIComponent(match[2]) : '';
  }
  const csrftoken = getCookie('csrftoken');

  const ATTACK_NAMES = [
    'Inheritance Strike!', 'Polymorphism Combo!', 'Encapsulation Shield Breaker!',
    'Abstraction Blast!', 'Constructor Call!', 'Method Override!',
  ];
  const BOSS_ATTACK_NAMES = [
    'Null Pointer Slam!', 'Syntax Error Breath!', 'Stack Overflow Crush!', 'Infinite Loop Trap!',
  ];
  const CONFETTI_COLORS = ['#f59e0b', '#8b5cf6', '#06b6d4', '#10b981', '#f43f5e', '#fff'];
  const CHOICE_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F'];

  let pool = shuffle(cfg.questions.slice());
  let poolIndex = 0;
  let studentHp = cfg.studentHp;
  let bossHp = cfg.bossHp;
  let busy = false;
  let questionNumber = 0;
  let correctCount = 0;

  const arena = document.querySelector('.boss-arena');
  const studentHpFill = document.getElementById('student-hp-fill');
  const studentHpText = document.getElementById('student-hp-text');
  const bossHpFill = document.getElementById('boss-hp-fill');
  const bossHpText = document.getElementById('boss-hp-text');
  const studentSprite = document.getElementById('student-sprite');
  const bossSprite = document.getElementById('boss-sprite');
  const studentFxLayer = document.getElementById('student-fx-layer');
  const bossFxLayer = document.getElementById('boss-fx-layer');
  const logEl = document.getElementById('boss-battle-log');
  const questionCounterEl = document.getElementById('boss-question-counter');
  const correctCounterEl = document.getElementById('boss-correct-counter');
  const questionPanel = document.getElementById('boss-question-panel');
  const questionText = document.getElementById('boss-question-text');
  const choicesEl = document.getElementById('boss-choices');
  const endPanel = document.getElementById('boss-end-panel');
  const endEmoji = document.getElementById('boss-end-emoji');
  const endTitle = document.getElementById('boss-end-title');
  const endText = document.getElementById('boss-end-text');
  const retryBtn = document.getElementById('boss-retry-btn');
  const confettiLayer = document.getElementById('boss-confetti-layer');

  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    return arr;
  }

  function nextQuestion() {
    if (poolIndex >= pool.length) {
      pool = shuffle(cfg.questions.slice());
      poolIndex = 0;
    }
    const q = pool[poolIndex];
    poolIndex += 1;
    return q;
  }

  function hpFillClass(hp, max) {
    const pct = hp / max;
    if (pct <= 0.2) return 'boss-hp-fill-bad';
    if (pct <= 0.5) return 'boss-hp-fill-warn';
    return 'boss-hp-fill-good';
  }

  function updateBars() {
    const sp = Math.max(0, Math.round((studentHp / cfg.studentHp) * 100));
    const bp = Math.max(0, Math.round((bossHp / cfg.bossHp) * 100));
    studentHpFill.style.width = sp + '%';
    bossHpFill.style.width = bp + '%';
    studentHpFill.className = 'progress-bar ' + hpFillClass(Math.max(0, studentHp), cfg.studentHp);
    bossHpFill.className = 'progress-bar ' + hpFillClass(Math.max(0, bossHp), cfg.bossHp);
    studentHpText.textContent = Math.max(0, studentHp) + ' / ' + cfg.studentHp + ' HP';
    bossHpText.textContent = Math.max(0, bossHp) + ' / ' + cfg.bossHp + ' HP';
  }

  function log(message, variant) {
    logEl.textContent = message;
    logEl.className = 'boss-battle-log' + (variant ? ' log-' + variant : '');
  }

  function randomOf(list) {
    return list[Math.floor(Math.random() * list.length)];
  }

  function restartAnimation(el, className) {
    el.classList.remove(className);
    // eslint-disable-next-line no-unused-expressions
    el.offsetWidth;
    el.classList.add(className);
  }

  function spawnFx(layer, text, dmgClass) {
    const burst = document.createElement('div');
    burst.className = 'boss-hit-burst';
    layer.appendChild(burst);
    burst.addEventListener('animationend', function () { burst.remove(); });

    const dmg = document.createElement('div');
    dmg.className = 'boss-dmg-float ' + dmgClass;
    dmg.textContent = text;
    layer.appendChild(dmg);
    dmg.addEventListener('animationend', function () { dmg.remove(); });
  }

  function playAttack(attackerSprite, attackerLungeClass, targetSprite, targetFxLayer, dmgText) {
    restartAnimation(attackerSprite, attackerLungeClass);
    setTimeout(function () {
      restartAnimation(targetSprite, 'sprite-hit');
      spawnFx(targetFxLayer, dmgText, 'dmg-damage');
    }, 180);
  }

  function spawnConfetti() {
    for (let i = 0; i < 36; i += 1) {
      const piece = document.createElement('div');
      piece.className = 'boss-confetti-piece';
      piece.style.left = Math.random() * 100 + '%';
      piece.style.background = randomOf(CONFETTI_COLORS);
      piece.style.animationDuration = (1.4 + Math.random() * 1.2) + 's';
      piece.style.animationDelay = (Math.random() * 0.6) + 's';
      confettiLayer.appendChild(piece);
      piece.addEventListener('animationend', function () { piece.remove(); });
    }
  }

  function renderQuestion() {
    const q = nextQuestion();
    questionNumber += 1;
    questionCounterEl.textContent = 'คำถามข้อที่ ' + questionNumber;
    questionText.textContent = q.text;
    choicesEl.innerHTML = '';
    const choices = shuffle(q.choices.slice());
    choices.forEach(function (choice, idx) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'boss-choice-btn';
      btn.dataset.choiceId = choice.id;

      const letter = document.createElement('span');
      letter.className = 'boss-choice-letter';
      letter.textContent = CHOICE_LETTERS[idx] || '?';
      btn.appendChild(letter);

      const label = document.createElement('span');
      label.textContent = choice.text;
      btn.appendChild(label);

      btn.addEventListener('click', function () { submitAnswer(q, choice, btn); });
      choicesEl.appendChild(btn);
    });
  }

  function submitAnswer(question, choice, clickedBtn) {
    if (busy) return;
    busy = true;
    Array.prototype.forEach.call(choicesEl.children, function (btn) { btn.disabled = true; });
    log('กำลังตรวจคำตอบ...', 'wait');

    fetch(cfg.answerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ question_id: question.id, choice_id: choice.id }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.is_correct) {
          clickedBtn.classList.add('choice-correct');
          bossHp -= cfg.dmgCorrect;
          correctCount += 1;
          correctCounterEl.textContent = String(correctCount);
          playAttack(studentSprite, 'sprite-attack-right', bossSprite, bossFxLayer, '-' + cfg.dmgCorrect);
          log('✅ ' + randomOf(ATTACK_NAMES) + ' โจมตีบอสสำเร็จ!', 'success');
        } else {
          clickedBtn.classList.add('choice-wrong');
          if (data.correct_choice_id) {
            const correctBtn = choicesEl.querySelector('[data-choice-id="' + data.correct_choice_id + '"]');
            if (correctBtn) correctBtn.classList.add('choice-correct');
          }
          studentHp -= cfg.dmgWrong;
          playAttack(bossSprite, 'sprite-attack-left', studentSprite, studentFxLayer, '-' + cfg.dmgWrong);
          log('❌ ตอบผิด! บอสสวน ' + randomOf(BOSS_ATTACK_NAMES) + ' เฉลย: ' + data.correct_choice_text, 'danger');
        }
        updateBars();

        setTimeout(function () {
          busy = false;
          if (bossHp <= 0) {
            endBattle(true);
          } else if (studentHp <= 0) {
            endBattle(false);
          } else {
            renderQuestion();
          }
        }, 1100);
      });
  }

  function endBattle(won) {
    questionPanel.classList.add('d-none');
    endPanel.classList.remove('d-none');
    if (won) {
      restartAnimation(bossSprite, 'sprite-defeated');
      spawnConfetti();
      endEmoji.textContent = '🏆';
      endTitle.textContent = 'ชนะแล้ว! ปราบบอสสำเร็จ';
      endTitle.className = 'fw-bold mb-2 text-success';
      endText.textContent = 'ตอบถูก ' + correctCount + ' ข้อ เยี่ยมมาก! คุณพร้อมไปทำแบบทดสอบหลังเรียนแล้ว';
    } else {
      restartAnimation(studentSprite, 'sprite-defeated');
      arena.classList.add('boss-arena-defeated');
      endEmoji.textContent = '💀';
      endTitle.textContent = 'พ่ายแพ้! ลองใหม่อีกครั้งนะ';
      endTitle.className = 'fw-bold mb-2 text-danger';
      endText.textContent = 'ตอบถูกไป ' + correctCount + ' ข้อ ทบทวนเนื้อหาอีกนิดแล้วกลับมาปราบบอสใหม่ได้เลย';
    }

    fetch(cfg.finishUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ won: won, boss_hp_left: Math.max(0, bossHp) }),
    });
  }

  retryBtn.addEventListener('click', function () {
    window.location.reload();
  });

  updateBars();
  renderQuestion();
})();
