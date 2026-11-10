'use strict';
// The reading frame around a verified manual (manual_reader.html, 2026-11): the language selects, the
// chapter list that follows the reading position, and the chapter sheet on narrow screens.
(() => {
  document.querySelectorAll('select[data-manual-locale]').forEach(select => {
    select.addEventListener('change', () => {
      const selected = select.selectedOptions[0];
      if (selected && !selected.disabled && selected.value) {
        // Options are generated from frozen same-product publications. Never copy
        // the current location's chapter hash or construct a language suffix.
        window.location.assign(selected.value);
      }
    });
  });

  // Jumps land under the top bar and the chapter list sticks below it (--mr-top in manual-reader.css). A long
  // product name can wrap the bar, so the frame takes the bar's real height.
  const frame = document.querySelector('.mr');
  const bar = document.querySelector('.mr-top');
  if (frame && bar) {
    const fit = () => frame.style.setProperty('--mr-top', `${Math.ceil(bar.getBoundingClientRect().height)}px`);
    fit();
    if (window.ResizeObserver) new window.ResizeObserver(fit).observe(bar);
    else window.addEventListener('resize', fit);
  }

  const toc = document.getElementById('mr-toc');
  if (!toc) return;
  const opener = document.querySelector('.mr-toc-open');
  const scrim = document.querySelector('.mr-scrim');
  const isOpen = () => toc.classList.contains('is-open');
  // Below 1,100px the list is a sheet that the top bar's contents button opens; wider, it is always shown.
  const setOpen = on => {
    toc.classList.toggle('is-open', on);
    if (scrim) scrim.hidden = !on;
    if (opener) opener.setAttribute('aria-expanded', String(on));
    if (on) {
      const here = toc.querySelector('a[aria-current]') || toc.querySelector('.mr-toc-list a');
      if (here) here.focus();
    } else if (opener && toc.contains(document.activeElement)) {
      opener.focus();
    }
  };
  if (opener) opener.addEventListener('click', () => setOpen(!isOpen()));
  if (scrim) scrim.addEventListener('click', () => setOpen(false));
  const closer = toc.querySelector('.mr-toc-close');
  if (closer) closer.addEventListener('click', () => setOpen(false));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && isOpen()) setOpen(false);
  });
  toc.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    if (isOpen()) setOpen(false);
  }));

  // The current section is the last listed one whose heading has passed under the top bar; its chapter
  // shows its sections, and the list keeps the current entry in view.
  const entries = [...toc.querySelectorAll('.mr-toc-list a[href^="#"]')]
    .map(link => ({link, target: document.getElementById(decodeURIComponent(link.getAttribute('href').slice(1)))}))
    .filter(entry => entry.target);
  let current = null;
  const reveal = link => {
    const box = toc.getBoundingClientRect();
    const spot = link.getBoundingClientRect();
    if (spot.top < box.top || spot.bottom > box.bottom) toc.scrollTop += spot.top - box.top - box.height / 3;
  };
  const mark = () => {
    const line = (bar ? bar.getBoundingClientRect().bottom : 0) + 24;
    // Before the first chapter (the manual's opening notes) the first chapter is the one to read next; at the
    // page's end the last sections cannot reach the line, so the last one in view counts.
    const end = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
    const limit = end ? window.innerHeight : line;
    let found = entries[0] || null;
    for (const entry of entries) {
      if (entry.target.getBoundingClientRect().top > limit) break;
      found = entry;
    }
    if (found === current) return;
    if (current) current.link.removeAttribute('aria-current');
    toc.querySelectorAll('.mr-chapter.is-current').forEach(item => item.classList.remove('is-current'));
    current = found;
    if (!found) return;
    found.link.setAttribute('aria-current', 'location');
    const chapter = found.link.closest('.mr-chapter');
    if (chapter) chapter.classList.add('is-current');
    reveal(found.link);
  };
  let waiting = false;
  const schedule = () => {
    if (waiting) return;
    waiting = true;
    window.requestAnimationFrame(() => {
      waiting = false;
      mark();
    });
  };
  window.addEventListener('scroll', schedule, {passive: true});
  window.addEventListener('resize', schedule);
  mark();

  // Images above a section load after a jump to it and push it down: keep the section where the jump put
  // it until the page settles, unless the reader scrolls first.
  const SETTLE_MS = 2500;
  const settle = () => {
    const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!target || !document.getElementById('furo-main-content').contains(target)) return;
    const stop = () => {
      document.removeEventListener('load', align, true);
      ['wheel', 'touchstart', 'keydown'].forEach(name => window.removeEventListener(name, stop));
    };
    const align = event => {
      if (event.target && event.target.tagName === 'IMG') target.scrollIntoView({block: 'start'});
    };
    document.addEventListener('load', align, true);
    ['wheel', 'touchstart', 'keydown'].forEach(name => window.addEventListener(name, stop, {passive: true}));
    window.setTimeout(stop, SETTLE_MS);
  };
  window.addEventListener('hashchange', settle);
  settle();
})();
