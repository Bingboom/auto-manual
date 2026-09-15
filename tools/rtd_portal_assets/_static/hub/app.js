'use strict';
const iconPaths={
 home:'<path d="m3 10 9-7 9 7v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 21v-8h6v8"/>',
 grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
 book:'<path d="M12 5v16M3 3h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v16h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3z"/>',
 spark:'<path d="m12 3 2.7 6.3L21 12l-6.3 2.7L12 21l-2.7-6.3L3 12l6.3-2.7zM20 2v4m-2-2h4"/>',
 clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
 search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
 arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',
 external:'<path d="M14 3h7v7m0-7L10 14M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5"/>',
 globe:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
 chevrons:'<path d="m8 8 4-4 4 4m-8 8 4 4 4-4"/>',
 message:'<path d="M21 11a9 9 0 0 1-9 9H3l2-5a9 9 0 1 1 16-4Z"/><path d="M8 10h8m-8 4h5"/>',
 close:'<path d="m6 6 12 12M6 18 18 6"/>',
 menu:'<path d="M4 6h16M4 12h16M4 18h16"/>'
};
const icon=name=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${iconPaths[name]||iconPaths.book}</svg>`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function icons(){document.querySelectorAll('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));}
icons();
let practices=[],updates=[];
let products=[],category='all',view='home',edition='internal';
const preferred=['JE-1000F','JE-2000E','JS-100I','JBP-2000B','JE-500A','JA-AD600A'];
const grid=document.getElementById('product-grid');
const search=document.getElementById('search');
const region=document.getElementById('region');
const dialog=document.getElementById('detail-dialog');
const titles={home:['产品中心知识库','产品资料、使用说明与团队经验，在这里连接。','概览'],products:['产品资料','按产品和市场，找到说明书与使用资料。','产品资料'],ai:['AI 实践','一次尝试，一个方法。让团队经验持续积累。','AI 实践'],updates:['最近更新','产品内容与知识沉淀的最新动态。','最近更新']};
function render(){
 renderResources();
 renderContent();
 let matches=products.filter(p=>(region.value==='all'||p.region===(region.selectedOptions[0].dataset.binding||region.value))&&(category==='all'||p.category===category)&&($('#search-language').value==='all'||p.languages.some(l=>l.code===$('#search-language').value||(l.code==='current'&&$('#search-language').value==='legacy'))));
 const q=search.value.trim().toLocaleLowerCase();
 matches=matches.filter(p=>`${p.model} ${p.name} ${p.category} ${p.edition}`.toLocaleLowerCase().includes(q));
 matches.sort((a,b)=>{const ai=preferred.indexOf(a.model),bi=preferred.indexOf(b.model);return (ai<0?100:ai)-(bi<0?100:bi);});
 document.getElementById('result-count').textContent=`${matches.length} 个`;
 document.getElementById('catalog-count').textContent=products.filter(p=>region.value==='all'||p.region===(region.selectedOptions[0].dataset.binding||region.value)).length;
 const limit=view==='home'&&!q&&category==='all'?6:matches.length;
 grid.innerHTML=matches.slice(0,limit).map(p=>`<button class="product-card" data-product="${esc(p.model)}" data-region="${esc(p.region)}" aria-label="查看 ${esc(p.name)} 产品资料"><div class="product-art"><span class="edition">${esc(p.edition)}</span>${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy" width="180" height="125">`:`<span class="product-monogram">${esc(p.model)}</span>`}</div><div class="product-info"><div class="product-category">${esc(p.category)}</div><h3>${esc(p.name)}</h3><div class="model">${esc(p.model)}</div><div class="product-card-footer"><span>查看产品资料</span>${icon('arrow')}</div></div></button>`).join('');
 grid.hidden=!matches.length;
 document.getElementById('empty-state').hidden=!!matches.length;
 document.getElementById('all-products').hidden=view!=='home';
 document.querySelectorAll('.filter-bar button').forEach(b=>{b.classList.toggle('active',b.dataset.category===category);b.setAttribute('aria-pressed',String(b.dataset.category===category));});
}
function setView(next){
 if(next==='manuals'){next='products';history.replaceState(null,'','#products');}
 if(!titles[next])next='home';
 
 view=next;
 document.body.classList.remove('view-home','view-products','view-ai','view-updates','menu-open');
 document.body.classList.add('view-'+view);
 const t=titles[view];
 document.getElementById('page-title').innerHTML=esc(edition==='public'&&view==='home'?'产品与支持中心':t[0])+'<span class="title-dot">.</span>';
 document.getElementById('page-description').textContent=edition==='public'&&view==='home'?'了解产品，查找说明书，获取使用指引。':t[1];
 document.getElementById('breadcrumb-title').textContent=t[2];
 document.getElementById('products-heading').firstChild.textContent='产品资料 ';
 document.querySelectorAll('.nav-link').forEach(a=>{const active=a.dataset.view===view;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 render();window.scrollTo({top:0,behavior:'instant'});
}
function showProduct(model,market){
 const p=products.find(x=>x.model===model&&x.region===(market||region.selectedOptions[0].dataset.binding||region.value))||products.find(x=>x.model===model);
 if(!p)return;
 document.getElementById('detail-label').textContent='产品资料 / '+p.category;
 document.getElementById('detail-body').innerHTML=`<div class="dialog-product">${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)}">`:''}<div><span class="article-example">${esc(p.edition)}</span><h2>${esc(p.name)}</h2><p>${esc(p.model)} · ${esc(p.category)}</p></div></div><h3 class="dialog-subheading">说明书与使用指引</h3><div class="language-links">${(p.languages.length?p.languages:[{url:p.url,label:'打开现有说明书'}]).map(l=>`<a href="${esc(l.url)}" target="_blank" rel="noopener noreferrer">${esc(l.label)} ↗</a>`).join('')}</div><p class="source-note">点击语言打开对应说明书。</p>`;
 dialog.showModal();
}
function renderResources(){
 const q=search.value.trim().toLocaleLowerCase();
 const matches=practices.filter(a=>`${a.title} ${a.summary} ${a.tags.join(' ')}`.toLocaleLowerCase().includes(q));
 document.getElementById('practice-links').innerHTML=matches.map((a,i)=>`<a class="story-item" href="${esc(a.url)}" target="_blank" rel="noopener noreferrer"><span class="story-number">${String(i+1).padStart(2,'0')}</span><span><small>${esc(a.tags.join(' · '))}</small><strong>${esc(a.title)}</strong><em>${esc(a.summary)}</em></span>${icon('external')}</a>`).join('');
 document.getElementById('practice-empty').hidden=!!matches.length;
 document.querySelector('#practice-empty b').textContent=practices.length?'没有匹配的实践文档':'实践文档待收录';
 const visible=updates.filter(a=>(a.kind!=='practice'||edition==='internal')&&(a.kind==='practice'||region.value==='all'||a.region===(region.selectedOptions[0].dataset.binding||region.value))&&`${a.title} ${a.model||''} ${a.summary||''}`.toLocaleLowerCase().includes(q));
 document.getElementById('updates-list').innerHTML=visible.slice(0,view==='updates'?50:5).map(a=>`<a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer"><span class="update-icon">${icon(a.kind==='practice'?'external':'book')}</span><span><strong>${esc(a.title)}</strong><small>${esc(a.summary)} · ${esc(a.dateLabel)} ${esc(a.date.slice(0,10))}</small></span><span class="update-type">${a.kind==='practice'?'钉钉文档':'产品文档'}</span>${icon('external')}</a>`).join('')||'<p class="loading">暂无匹配的更新记录。</p>';
}
document.addEventListener('click',e=>{
 const p=e.target.closest('[data-product]');if(p)showProduct(p.dataset.product,p.dataset.region);
 const f=e.target.closest('[data-category]');if(f){category=f.dataset.category;render();}
 const switcher=e.target.closest('[data-edition]');if(switcher){edition=switcher.dataset.edition;document.body.classList.toggle('public-edition',edition==='public');document.querySelectorAll('.edition-switch button').forEach(b=>{b.classList.toggle('selected',b===switcher);b.setAttribute('aria-pressed',String(b===switcher));});search.placeholder=edition==='public'?'搜索产品名称、型号…':'搜索产品名称、型号、AI 实践…';if(edition==='public'&&view==='ai'){location.hash='home';}setView(view);}
});
search.addEventListener('input',()=>{resultLimit=12;render();});
region.addEventListener('change',render);
document.getElementById('all-products').addEventListener('click',()=>location.hash='products');
document.getElementById('reset-search').addEventListener('click',()=>{search.value='';category='all';search.dispatchEvent(new Event('input'));});
document.getElementById('close-dialog').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
document.querySelector('.mobile-menu').addEventListener('click',()=>document.body.classList.toggle('menu-open'));
document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();search.focus();}if(e.key==='Escape')document.body.classList.remove('menu-open');});
window.addEventListener('hashchange',()=>setView(location.hash.slice(1)));
const $=selector=>document.querySelector(selector);
let resultLimit=12;
const categoryLabels={'Power stations':'便携储能','Battery packs':'加电包','Solar panels':'太阳能板','Accessories':'配件'};
function highlight(element, text, tokens) {
  const escaped = tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp('(' + escaped.join('|') + ')', 'gi');
  text.split(regex).forEach((part, i) => {
    if (i % 2) { const mark = document.createElement('mark'); mark.textContent = part; element.append(mark); }
    else element.append(document.createTextNode(part));
  });
}
function renderContent() {
  const query=search.value.trim().toLowerCase();
  const market=region.selectedOptions[0].dataset.binding||region.value;
  const regionValue=market;
  const regionFilter=regionValue;
  const selectedCategory=Object.keys(categoryLabels).find(key=>categoryLabels[key]===category);

  const section = $('#content-results');
  section.hidden = !query;
  $('#content-list').replaceChildren();
  if (!query) return;
  const tokens = query.split(/\s+/).filter(Boolean);
  const language = $('#search-language').value;
  const hits = (window.manualSearchIndex || []).filter(item => (regionFilter === 'all' || item.region === regionFilter)
    && (category === 'all' || item.category === selectedCategory)
    && (language === 'all' || language === item.lang)
    && tokens.every(t => (item.model + ' ' + item.name + ' ' + item.title + ' ' + item.text).toLowerCase().includes(t)))
    .map(item => ({...item, score: tokens.reduce((score, t) => score + (item.model.toLowerCase().includes(t) ? 100 : 0) + (item.title.toLowerCase().includes(t) ? 20 : 0), 0)}))
    .sort((a,b) => b.score - a.score || a.model.localeCompare(b.model));
  $('#content-status').textContent = window.manualSearchIndex
    ? `${hits.length} 个匹配章节 · ${Math.min(resultLimit, hits.length)} 条已显示`
    : '正文搜索暂不可用，请通过下方产品目录阅读。';
  hits.slice(0,resultLimit).forEach(item => {
    const article = document.createElement('article'); article.className = 'search-hit';
    const meta = document.createElement('div'); meta.className = 'meta';
    meta.textContent = `${item.name} · ${item.model} · ${item.region === 'EU' ? 'EUUK' : item.region} · ${item.language}${item.version ? ' · ' + item.version : ''}`;
    const link = document.createElement('a'); link.href = item.url; highlight(link, item.title, tokens);
    const excerpt = document.createElement('p');
    const first = item.text.toLowerCase().indexOf(tokens[0]); const start = Math.max(0,first - 90);
    highlight(excerpt, (start ? '…' : '') + item.text.slice(start,start+310) + (item.text.length > start+310 ? '…' : ''), tokens);
    article.append(meta,link,excerpt); $('#content-list').append(article);
  });
  $('#more-results').hidden = hits.length <= resultLimit;
  
}

$('#more-results').addEventListener('click',()=>{resultLimit+=12;renderContent();});
$('#search-language').addEventListener('change',render);
products=window.hubData.products;
practices=window.hubData.practices;
updates=window.hubData.updates;
search.value=new URLSearchParams(location.search).get('q')||'';
setView(location.hash.slice(1)||'home');
