'use strict';

document.querySelectorAll('[data-copy-feedback]').forEach(button => {
  button.addEventListener('click', async () => {
    const status = button.parentElement.querySelector('.manual-feedback-status');
    const context = button.parentElement.querySelector('.manual-feedback-context').textContent;
    try {
      await navigator.clipboard.writeText(context);
      status.textContent = 'Context copied.';
    } catch (_error) {
      status.textContent = 'Copy unavailable; select the context manually.';
    }
  });
});
