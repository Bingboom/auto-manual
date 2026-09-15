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
let products=[],category='all',view='home',edition='internal';
const preferred=['JE-1000F','JE-2000E','JS-100I','JBP-2000B','JE-500A','JA-AD600A'];
const grid=document.getElementById('product-grid');
const search=document.getElementById('search');
const region=document.getElementById('region');
const dialog=document.getElementById('detail-dialog');
const titles={home:['产品中心知识库','产品资料、使用说明与团队经验，在这里连接。','概览'],products:['产品资料','按产品和市场，找到说明书与使用资料。','产品资料'],ai:['AI 实践','一次尝试，一个方法。让团队经验持续积累。','AI 实践'],updates:['最近更新','产品内容与知识沉淀的最新动态。','最近更新']};
function render(){
 let matches=products.filter(p=>(region.value==='all'||p.region===region.value)&&(category==='all'||p.category===category));
 const q=search.value.trim().toLocaleLowerCase();
 matches=matches.filter(p=>`${p.model} ${p.name} ${p.category} ${p.edition}`.toLocaleLowerCase().includes(q));
 matches.sort((a,b)=>{const ai=preferred.indexOf(a.model),bi=preferred.indexOf(b.model);return (ai<0?100:ai)-(bi<0?100:bi);});
 document.getElementById('result-count').textContent=`${matches.length} 个`;
 document.getElementById('catalog-count').textContent=products.filter(p=>region.value==='all'||p.region===region.value).length;
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
 if(edition==='public'&&next==='ai')next='home';
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
 const p=products.find(x=>x.model===model&&x.region===(market||region.value))||products.find(x=>x.model===model);
 if(!p)return;
 document.getElementById('detail-label').textContent='产品资料 / '+p.category;
 document.getElementById('detail-body').innerHTML=`<div class="dialog-product">${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)}">`:''}<div><span class="article-example">${esc(p.edition)}</span><h2>${esc(p.name)}</h2><p>${esc(p.model)} · ${esc(p.category)}</p></div></div><h3 class="dialog-subheading">说明书与使用指引</h3><div class="language-links">${(p.languages.length?p.languages:[{url:p.url,label:'打开现有说明书'}]).map(l=>`<a href="${esc(l.url)}" target="_blank" rel="noopener noreferrer">${esc(l.label)} ↗</a>`).join('')}</div><p class="source-note">链接来自现有说明书站。点击语言后打开对应页面。<br>此处展示产品聚合页的布局，产品参数与内部资料可后续逐步补充。</p>`;
 dialog.showModal();
}
const articles=[
 {title:'AI 辅助说明书核对，如何保留人工判断？',tag:'文档与翻译',body:'<h3>要解决的问题</h3><p>多语言说明书存在重复核对工作。先让 AI 汇总可能的差异，再由负责人结合原文作出判断。</p><h3>一个可以尝试的流程</h3><ol><li>准备已确认版本的原文与译文，说明核对范围。</li><li>要求 AI 输出位置、原文、译文、差异及判断依据。</li><li>人工逐条检查，记录接受、驳回或待确认。</li><li>修订后再次核对本次涉及的位置，保留处理记录。</li></ol><h3>分享时带上什么</h3><p>一组脱敏示例、你用过的指令、最后保留的判断，以及 AI 容易误判的地方。</p>'},
 {title:'让 AI 先整理差异，再做产品判断',tag:'产品研究',body:'<h3>要解决的问题</h3><p>产品资料分散，比较口径容易不一致。先整理同口径信息，保留每条结论的来源。</p><h3>一个可以尝试的流程</h3><ol><li>限定需要比较的型号、地区和资料日期。</li><li>按容量、接口、适用场景等选定维度整理。</li><li>为每个值保留来源链接与原文；没有依据的留空。</li><li>人工核对关键差异，再写选择建议。</li></ol><h3>可以复用的要求</h3><p>“请区分原始事实与推测。信息缺失时标记未找到，不要补全参数。”</p>'},
 {title:'一份周报，从零散记录到清晰结论',tag:'日常效率',body:'<h3>要解决的问题</h3><p>把一周的工作记录整理成同事能够快速理解的进展、待办与需要协助的事项。</p><h3>一个可以尝试的流程</h3><ol><li>整理本周已完成事项、产物链接与未解决问题。</li><li>让 AI 按项目合并重复内容，保留结果和依据。</li><li>人工检查完成状态、负责人和时间。</li><li>删去空泛表达，只保留对协作有帮助的信息。</li></ol><h3>可复用结构</h3><p>本周结果 → 当前问题 → 下周行动 → 需要的协助。</p>'},
 {title:'分享一次 AI 实践',tag:'分享模板',body:'<p>用一个具体案例，让同事能够理解并尝试你的方法。</p><h3>01 · 我遇到了什么问题</h3><p>说明场景、重复工作，以及希望得到的结果。</p><h3>02 · 我怎么做</h3><p>写出工具、操作步骤和可复用的指令，配上脱敏输入示例。</p><h3>03 · 实际结果如何</h3><p>展示产物与原来的差异。有测量就写测量结果，没有就描述观察。</p><h3>04 · 哪些地方仍需人工判断</h3><p>记录错误、限制、适用范围，以及下次会怎么改。</p><h3>05 · 谁可以继续补充</h3><p>留下作者、日期和可复用材料的位置。</p>'}
];
function showArticle(index){const a=articles[index];if(!a)return;document.getElementById('detail-label').textContent='AI 实践 / '+a.tag;document.getElementById('detail-body').innerHTML=`<article class="article-body"><span class="article-example">示例内容 · 用于版面体验</span><h2>${a.title}</h2>${a.body}</article>`;dialog.showModal();}
document.addEventListener('click',e=>{
 const p=e.target.closest('[data-product]');if(p)showProduct(p.dataset.product,p.dataset.region);
 const a=e.target.closest('[data-article]');if(a)showArticle(Number(a.dataset.article));
 const f=e.target.closest('[data-category]');if(f){category=f.dataset.category;render();}
 const switcher=e.target.closest('[data-edition]');if(switcher){edition=switcher.dataset.edition;document.body.classList.toggle('public-edition',edition==='public');document.querySelectorAll('.edition-switch button').forEach(b=>{b.classList.toggle('selected',b===switcher);b.setAttribute('aria-pressed',String(b===switcher));});search.placeholder=edition==='public'?'搜索产品名称、型号…':'搜索产品名称、型号、AI 实践…';if(edition==='public'&&view==='ai'){location.hash='home';}setView(view);}
});
search.addEventListener('input',()=>{
 render();
 const q=search.value.trim().toLocaleLowerCase();
 document.querySelectorAll('[data-article]').forEach(el=>{const a=articles[Number(el.dataset.article)];el.hidden=!!q&&!`${a.title} ${a.tag} ai`.toLocaleLowerCase().includes(q);});
});
region.addEventListener('change',render);
document.getElementById('all-products').addEventListener('click',()=>location.hash='products');
document.getElementById('reset-search').addEventListener('click',()=>{search.value='';category='all';search.dispatchEvent(new Event('input'));});
document.getElementById('close-dialog').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
document.querySelector('.mobile-menu').addEventListener('click',()=>document.body.classList.toggle('menu-open'));
document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();search.focus();}if(e.key==='Escape')document.body.classList.remove('menu-open');});
window.addEventListener('hashchange',()=>setView(location.hash.slice(1)));
fetch('products.json').then(r=>{if(!r.ok)throw new Error('catalog');return r.json();}).then(data=>{products=data;setView(location.hash.slice(1)||'home');}).catch(()=>{grid.innerHTML='<p class="loading">产品目录暂时无法加载，请刷新页面重试。</p>';});
