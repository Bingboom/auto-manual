'use strict';
document.querySelector('#manual-locale-select')?.addEventListener('change', event => {
  const selected = event.target.selectedOptions[0];
  if (selected && !selected.disabled && selected.value) {
    // Options are generated from frozen same-product publications. Never copy
    // the current location's chapter hash or construct a language suffix.
    window.location.assign(selected.value);
  }
});
