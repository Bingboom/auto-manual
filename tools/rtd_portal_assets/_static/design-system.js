'use strict';
// Size each same-origin component preview to its content; without JS the
// declared height (with scrolling) stays. Measure the preview's <main>, not
// the document: a document is never shorter than its frame, so measuring it
// could only ever grow the frame.
(() => {
  const fit = frame => {
    try {
      const doc = frame.contentDocument;
      const main = doc && doc.querySelector('main');
      if (!main || frame.offsetParent === null) return;
      const view = doc.defaultView;
      const margin = parseFloat(view.getComputedStyle(main).marginBottom) || 0;
      const bottom = main.getBoundingClientRect().bottom + view.scrollY + margin;
      if (bottom > 0) frame.style.height = Math.ceil(bottom) + 'px';
    } catch (error) {
      // A cross-origin frame keeps its declared height.
    }
  };
  // 概览's gallery lays each preview out SHOT_WIDTH px wide (the manual's widest table fits) and scales it to
  // its card; a hidden card measures 0 and is scaled when it is shown.
  const SHOT_WIDTH = 720;
  const scaleShot = box => {
    const width = box.clientWidth;
    if (width > 0) box.style.setProperty('--ds-shot-scale', String(Math.min(1, width / SHOT_WIDTH)));
  };
  document.querySelectorAll('.ds-shot-frame').forEach(box => {
    scaleShot(box);
    if ('ResizeObserver' in window) new ResizeObserver(() => scaleShot(box)).observe(box);
  });
  document.querySelectorAll('iframe.ds-preview').forEach(frame => {
    frame.addEventListener('load', () => {
      fit(frame);
      try {
        const main = frame.contentDocument && frame.contentDocument.querySelector('main');
        if (main && 'ResizeObserver' in window) new ResizeObserver(() => fit(frame)).observe(main);
      } catch (error) {
        // Keep the declared height.
      }
    });
  });
})();
