/* Progressive enhancement: navigation links and all panels work without JS.
   With JS (2026-11 design, step 9) no panel is open until a node is chosen: a node opens its panel and
   closes the others, and choosing the open node again closes it. */
(() => {
  const nodes = [...document.querySelectorAll('[data-workbench-node]')];
  const panels = nodes.map((node) => document.getElementById(node.getAttribute('aria-controls')));
  if (!nodes.length || panels.some((panel) => !panel)) return;

  function select(selected) {
    nodes.forEach((node, index) => {
      const active = node === selected;
      node.setAttribute('aria-pressed', String(active));
      panels[index].hidden = !active;
    });
  }
  nodes.forEach((node) => node.addEventListener('click', () => {
    select(node.getAttribute('aria-pressed') === 'true' ? null : node);
  }));
  select(null);
})();
