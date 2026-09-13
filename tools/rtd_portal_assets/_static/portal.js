'use strict';
const $ = selector => document.querySelector(selector);
const cards = [...document.querySelectorAll('.card')];
let category = 'All products';

function render() {
  const selected = $('#region').selectedOptions[0];
  const query = $('#search').value.trim().toLowerCase();
  let count = 0;
  cards.forEach(card => {
    card.hidden = card.dataset.region !== selected.dataset.binding
      || (category !== 'All products' && card.dataset.category !== category)
      || !card.dataset.search.includes(query);
    if (!card.hidden) count += 1;
  });
  $('#market-title').textContent = `${selected.value} manuals`;
  $('#market-note').textContent = selected.value === 'US'
    ? 'Manuals for the US edition.'
    : 'EU and UK share the same products and manuals. Edition: EUUK.';
  $('#count').textContent = `${count} ${count === 1 ? 'product' : 'products'}`;
  $('#products').classList.toggle('single', count === 1);
  $('#empty').hidden = count !== 0;
  $('#clear').hidden = !$('#search').value;
}

function chooseCategory(value) {
  category = value;
  document.querySelectorAll('button[data-category]').forEach(button => {
    const active = button.dataset.category === category;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  render();
}

$('#region').addEventListener('change', render);
$('#search').addEventListener('input', render);
$('#clear').addEventListener('click', () => {
  $('#search').value = '';
  render();
  $('#search').focus();
});
document.querySelectorAll('button[data-category]').forEach(button => {
  button.addEventListener('click', () => chooseCategory(button.dataset.category));
});
$('#reset').addEventListener('click', () => {
  $('#search').value = '';
  chooseCategory('All products');
});
document.querySelectorAll('[data-manual]').forEach(link => {
  link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
        || typeof $('#manual-dialog').showModal !== 'function') return;
    event.preventDefault();
    $('#dialog-title').textContent = link.dataset.name;
    $('#dialog-model').textContent = `${link.dataset.model} · ${link.dataset.edition} edition`;
    $('#language').replaceChildren();
    JSON.parse(link.dataset.languages).forEach(item => {
      const option = new Option(item.label + (item.url ? '' : ' — Not yet published'), item.url || '');
      option.disabled = !item.url;
      option.selected = Boolean(item.url) && new URL(item.url, document.baseURI).href === link.href;
      $('#language').add(option);
    });
    $('#open-manual').href = link.href;
    $('#manual-dialog').showModal();
  });
});
$('#language').addEventListener('change', () => {
  if ($('#language').value) $('#open-manual').href = $('#language').value;
});
$('.close').addEventListener('click', () => $('#manual-dialog').close());
render();
