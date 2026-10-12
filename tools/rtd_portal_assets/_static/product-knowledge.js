(() => {
  const region = document.getElementById('learning-region');
  const product = document.getElementById('learning-product');
  const cards = [...document.querySelectorAll('.knowledge-item')];
  const tags = [...document.querySelectorAll('[data-tag]')];
  let tag = 'all';
  const contains = (value, item) => value.split(' ').includes(item);
  const regionMatches = value => region.value === 'all' || value === region.value;
  function render() {
    [...product.options].forEach(option => {
      const available = option.value === 'all' || regionMatches(option.dataset.region);
      option.hidden = !available;
      option.disabled = !available;
    });
    if (!product.selectedOptions.length || product.selectedOptions[0].disabled) product.value = 'all';
    let count = 0;
    cards.forEach(card => {
      const references = [...card.querySelectorAll('li[data-region]')];
      references.forEach(ref => {
        ref.hidden = !regionMatches(ref.dataset.region)
          || (product.value !== 'all' && ref.dataset.model !== product.value);
      });
      const available = references.filter(ref => !ref.hidden).length;
      card.hidden = (tag !== 'all' && !contains(card.dataset.tags, tag))
        || (product.value !== 'all' && !contains(card.dataset.models, product.value)) || available === 0;
      card.querySelector('.reference-count').textContent = `（${available}）`;
      if (!card.hidden) count += 1;
    });
    tags.forEach(button => {
      const selected = button.dataset.tag === tag;
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
    document.getElementById('learning-count').textContent = `${count} 项相关知识`;
    document.getElementById('learning-empty').hidden = count !== 0;
  }
  tags.forEach(button => button.addEventListener('click', () => {tag = button.dataset.tag; render();}));
  document.querySelectorAll('[data-topic]').forEach(button => button.addEventListener('click', () => {
    tag = button.dataset.topic; render();
    document.getElementById('knowledge-list').scrollIntoView({block:'start'});
  }));
  region.addEventListener('change', render);
  product.addEventListener('change', render);
  document.getElementById('learning-reset').addEventListener('click', () => {
    tag = 'all'; product.value = 'all'; render();
  });
  render();
})();
