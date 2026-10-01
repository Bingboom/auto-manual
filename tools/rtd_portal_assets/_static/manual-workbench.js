/* Progressive enhancement: navigation links and all panels work without JS. */
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
  nodes.forEach((node) => node.addEventListener('click', () => select(node)));
  select(nodes[0]);
})();
