(() => {
  'use strict';
  const search = document.querySelector('#course-search');
  const cards = Array.from(document.querySelectorAll('[data-course-card]'));
  if (search) {
    const entries = cards.map(card => ({ card, text: card.textContent.normalize('NFC').toLocaleLowerCase('th') }));
    search.addEventListener('input', () => {
      const query = search.value.normalize('NFC').trim().toLocaleLowerCase('th');
      let matches = 0;
      entries.forEach(({ card, text }) => {
        const visible = text.includes(query);
        card.hidden = !visible;
        if (visible) matches += 1;
      });
      document.querySelector('.results-count').textContent = matches;
      document.querySelector('#empty-search').hidden = matches > 0;
      document.querySelector('#search-status').textContent = `พบ ${matches} บทเรียน`;
    });
    document.addEventListener('keydown', event => {
      const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || document.activeElement.isContentEditable;
      if (event.key === '/' && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        search.focus();
      }
    });
  }
  const art = document.querySelector('.hero-art');
  const cube = document.querySelector('.object-cube');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (art && cube && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    let frame;
    art.addEventListener('pointermove', event => {
      if (reducedMotion.matches) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const rect = art.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - .5;
        const y = (event.clientY - rect.top) / rect.height - .5;
        cube.style.transform = `rotateX(${-20 - y * 14}deg) rotateY(${-30 + x * 20}deg) rotateZ(8deg)`;
      });
    });
    art.addEventListener('pointerleave', () => {
      cancelAnimationFrame(frame);
      cube.style.transform = '';
    });
    reducedMotion.addEventListener('change', () => {
      cancelAnimationFrame(frame);
      cube.style.transform = '';
    });
  }
})();
