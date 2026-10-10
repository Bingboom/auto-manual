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
