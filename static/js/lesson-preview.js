(() => {
  'use strict';
  const demo = document.querySelector('#lesson-demo');
  if (!demo) return;
  const byId = id => document.getElementById(`preview-${id}`);
  const episodes = [
    {
      topic: 'CLASS & OBJECT', file: 'class-and-object.cs', sourceKind: 'CLASS / ต้นแบบ', source: 'Car', property: 'color · Drive()',
      names: ['myCar', 'yourCar'], values: ['color = "purple"', 'color = "blue"'], symbols: ['◇', '◇'], note: 'ONE CLASS. MANY OBJECTS.',
      captions: ['เริ่มจาก Class ซึ่งเป็นต้นแบบที่บอกว่า Object มีข้อมูลและทำอะไรได้บ้าง', 'ใช้ new Car() สร้าง Object จากต้นแบบเดียวกันได้มากกว่าหนึ่งตัว', 'myCar เป็น Object ตัวแรก กำหนด color ให้เป็นสีม่วงได้', 'yourCar เป็นอีก Object หนึ่ง แต่ละตัวเก็บข้อมูล color ของตัวเองได้'],
      codes: ['class Car { public string color; }', 'Car myCar = new Car();\nCar yourCar = new Car();', 'myCar.color = "purple";\n// myCar มีข้อมูลของตัวเอง', 'yourCar.color = "blue";\n// ต้นแบบเดียวกัน แต่ข้อมูลต่างกันได้'],
    },
    {
      topic: 'INHERITANCE', file: 'inheritance.cs', sourceKind: 'PARENT CLASS / คลาสแม่', source: 'Animal', property: 'Eat()',
      names: ['Dog', 'Cat'], values: ['Eat() + Bark()', 'Eat() + Meow()'], symbols: ['↳', '↳'], note: 'INHERIT. EXTEND. CREATE.',
      captions: ['คลาส Animal มีเมธอด Eat() เป็นความสามารถพื้นฐานร่วมกัน', 'คลาสลูกใช้ : Animal เพื่อสืบทอดความสามารถจากคลาสแม่', 'Dog ใช้ Eat() ที่สืบทอดมาได้ และเพิ่มเมธอด Bark() ของตัวเอง', 'Cat ใช้ Eat() ได้เช่นกัน และเพิ่ม Meow() โดยไม่ต้องเขียน Eat() ซ้ำ'],
      codes: ['class Animal { public void Eat() { } }', 'class Dog : Animal { }\nclass Cat : Animal { }', 'class Dog : Animal { public void Bark() { } }\nnew Dog().Eat(); // สืบทอดจาก Animal', 'class Cat : Animal { public void Meow() { } }\nnew Cat().Eat(); // ใช้เมธอดที่สืบทอดมา'],
    },
    {
      topic: 'LOOP / CONTROL FLOW', file: 'your-first-loop.cs', sourceKind: 'FOR LOOP / ทำงานซ้ำ', source: 'i < 3', property: 'เริ่ม 0 · เพิ่มทีละ 1',
      names: ['รอบที่ 1', 'รอบที่ 2–3'], values: ['แสดงผล 0', 'แสดงผล 1, 2'], symbols: ['0', '↻'], note: 'LESS REPETITION. MORE POSSIBILITIES.',
      captions: ['กำหนด i = 0 และทำงานต่อเมื่อ i < 3 โดยเพิ่ม i ทีละหนึ่งหลังจบรอบ', 'ตรวจเงื่อนไขก่อนเริ่มแต่ละรอบ ถ้าเป็นจริงจึงทำคำสั่งใน Loop', 'รอบแรก i = 0 โปรแกรมแสดงผล 0 แล้วเพิ่ม i เป็น 1', 'ทำต่อจนแสดงผล 1 และ 2 เมื่อ i = 3 เงื่อนไขเป็นเท็จจึงออกจาก Loop'],
      codes: ['for (int i = 0; i < 3; i++) {\n  Console.WriteLine(i);\n}', '0 < 3 // true → เริ่มรอบแรก', '// i = 0\nConsole.WriteLine(i); // 0', '// ผลลัพธ์: 0, 1, 2\n// i = 3 → 3 < 3 เป็น false → จบ Loop'],
    },
  ];
  const duration = 16000;
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const buttons = [...demo.querySelectorAll('[data-preview-episode]')];
  const seek = byId('seek');
  let episodeIndex = 0;
  let position = 0;
  let currentStep = -1;
  let wantsToPlay = !motion.matches;
  let visible = false;
  let frame = null;
  let previousTime = null;

  function render() {
    const step = Math.min(3, Math.floor(position / 4000));
    const episode = episodes[episodeIndex];
    if (step !== currentStep) {
      currentStep = step;
      demo.dataset.step = step;
      byId('caption').textContent = episode.captions[step];
      byId('code').textContent = episode.codes[step];
      byId('step-number').textContent = String(step + 1).padStart(2, '0');
    }
    seek.value = String(Math.floor(position));
    const seconds = Math.floor(position / 1000);
    byId('time').textContent = `00:${String(seconds).padStart(2, '0')} / 00:16`;
    // Keep screen-reader updates at whole seconds instead of every animation frame.
    const valueText = `วินาทีที่ ${seconds} จาก 16`;
    if (seek.getAttribute('aria-valuetext') !== valueText) seek.setAttribute('aria-valuetext', valueText);
  }
  function updateButton() {
    byId('play').setAttribute('aria-label', wantsToPlay ? 'หยุดแอนิเมชันชั่วคราว' : 'เล่นแอนิเมชัน');
    byId('play-icon').textContent = wantsToPlay ? 'Ⅱ' : '▷';
    byId('play-text').textContent = wantsToPlay ? 'หยุดชั่วคราว' : 'เล่นตัวอย่าง';
  }
  function tick(time) {
    if (previousTime !== null) position = (position + time - previousTime) % duration;
    previousTime = time;
    render();
    frame = requestAnimationFrame(tick);
  }
  function syncPlayback() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    previousTime = null;
    if (wantsToPlay && visible && !document.hidden) frame = requestAnimationFrame(tick);
    updateButton();
  }
  function selectEpisode(index) {
    episodeIndex = index;
    const episode = episodes[index];
    const fields = {topic: episode.topic, file: episode.file, 'source-kind': episode.sourceKind, 'source-name': episode.source, 'source-property': episode.property, 'scene-note': episode.note};
    Object.entries(fields).forEach(([id, value]) => { byId(id).textContent = value; });
    ['one', 'two'].forEach((name, i) => {
      byId(`object-name-${name}`).textContent = episode.names[i];
      byId(`object-value-${name}`).textContent = episode.values[i];
      byId(`object-symbol-${name}`).textContent = episode.symbols[i];
    });
    buttons.forEach((button, i) => {
      button.classList.toggle('is-selected', i === index);
      button.setAttribute('aria-pressed', String(i === index));
    });
    position = 0;
    currentStep = -1;
    render();
    syncPlayback();
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    selectEpisode(Number(button.dataset.previewEpisode));
    byId('announcement').textContent = `เลือกตัวอย่าง ${episodes[episodeIndex].topic}`;
  }));
  byId('play').addEventListener('click', () => {
    wantsToPlay = !wantsToPlay;
    syncPlayback();
  });
  byId('restart').addEventListener('click', () => {
    position = 0;
    previousTime = null;
    render();
  });
  seek.addEventListener('input', () => {
    position = Number(seek.value);
    previousTime = null;
    render();
  });
  motion.addEventListener('change', () => {
    wantsToPlay = false;
    syncPlayback();
  });
  document.addEventListener('visibilitychange', syncPlayback);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      syncPlayback();
    }, {threshold: .15}).observe(demo.querySelector('.preview-player'));
  } else {
    visible = true;
  }
  selectEpisode(0);
})();
