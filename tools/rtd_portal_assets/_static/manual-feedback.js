'use strict';

// The feedback card under a manual (tools/rtd/feedback.py): copy the folded context; when the clipboard is
// unavailable, unfold it so the reader can select it by hand. The messages come from the card, in its language.
document.querySelectorAll('[data-copy-feedback]').forEach(button => {
  button.addEventListener('click', async () => {
    const card = button.closest('.manual-feedback');
    const status = card.querySelector('.manual-feedback-status');
    const context = card.querySelector('.manual-feedback-context').textContent;
    try {
      await navigator.clipboard.writeText(context);
      status.textContent = card.getAttribute('data-copied') || '';
    } catch (_error) {
      const details = card.querySelector('.manual-feedback-details');
      if (details) details.open = true;
      status.textContent = card.getAttribute('data-copy-failed') || '';
    }
  });
});
