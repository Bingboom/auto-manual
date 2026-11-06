'use strict';
// 产品矩阵 (2026-11 layout). Without JavaScript every 产品类别 shows stacked and a card's link opens its detail
// through :target. With it, the tabs show one category at a time and a card opens its product's detail under its
// row (a second click closes it); the URL hash names the open product or category, so links to either still work.
(() => {
  const panels = [...document.querySelectorAll('[data-panel]')];
  if (!panels.length) return;
  const tabs = [...document.querySelectorAll('[data-tab]')];
  const details = new Map([...document.querySelectorAll('.mx-detail')].map(detail => [detail.id, detail]));
  document.documentElement.classList.add('mx-js');
  let open = null;

  const setHash = hash => {
    try { history.replaceState(null, '', hash); } catch (error) { /* a file:// preview may refuse; the page still works */ }
  };
  const panelOf = element => panels.find(panel => panel.contains(element));
  const show = id => {
    panels.forEach(panel => { panel.hidden = panel.dataset.panel !== id; });
    tabs.forEach(tab => {
      const on = tab.dataset.tab === id;
      tab.classList.toggle('is-on', on);
      tab.setAttribute('aria-current', on ? 'true' : 'false');
    });
  };
  const cardsOf = id => [...document.querySelectorAll(`.mx-prod[data-product="${CSS.escape(id)}"]`)];
  const close = () => {
    if (!open) return;
    open.classList.remove('is-open');
    cardsOf(open.id).forEach(card => card.setAttribute('aria-expanded', 'false'));
    open = null;
  };
  const openDetail = (id, focus) => {
    const detail = details.get(id);
    if (!detail) return false;
    close();
    show(panelOf(detail).dataset.panel);
    detail.classList.add('is-open');
    cardsOf(id).forEach(card => card.setAttribute('aria-expanded', 'true'));
    open = detail;
    if (focus) detail.focus({preventScroll: true});
    detail.scrollIntoView({block: 'nearest'});
    return true;
  };

  tabs.forEach(tab => tab.addEventListener('click', event => {
    event.preventDefault();
    close();
    show(tab.dataset.tab);
    setHash(`#cat-${tab.dataset.tab}`);
  }));
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-product], [data-close]');
    if (!link) return;
    event.preventDefault();
    const id = link.dataset.product;
    if (id === undefined || (open && open.id === id && link.classList.contains('mx-prod'))) {
      const panel = open && panelOf(open);
      close();
      if (panel) setHash(`#cat-${panel.dataset.panel}`);
    } else if (openDetail(id, !link.classList.contains('mx-prod'))) {
      setHash(`#${id}`);
    }
  });

  const fromHash = () => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (details.has(id)) {
      openDetail(id, false);
      return;
    }
    close();
    const panel = panels.find(item => item.id === id);
    show((panel || panels[0]).dataset.panel);
  };
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
