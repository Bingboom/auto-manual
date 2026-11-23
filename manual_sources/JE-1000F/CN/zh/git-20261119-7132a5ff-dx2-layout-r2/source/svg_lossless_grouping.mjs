/** Lossless SVG storage normalization, SVGO 4.0.0 structural plugins only.
 * Usage: node svg_lossless_grouping.mjs INPUT.svg OUTPUT.svg /absolute/path/to/svgo/lib/svgo.js
 * Path data, transforms, clipping and opacity are not rounded or simplified.
 * Each acquired source output must pass a before/after 12x RGBA equality check.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const [input, output, svgoModule] = process.argv.slice(2);
if (!input || !output || !svgoModule) throw new Error('input, output and installed SVGO4 module path required');
const {optimize} = await import(pathToFileURL(svgoModule).href);
const paintAttrs = new Set(['fill','fill-rule','fill-opacity','stroke','stroke-width','stroke-opacity','stroke-linecap','stroke-linejoin','stroke-miterlimit','stroke-dasharray','stroke-dashoffset']);
const groupPaint = {name:'groupAdjacentPaint',fn:()=>({element:{exit:(parent)=>{
 const children=parent.children; if(!children) return;
 const out=[];
 for(let i=0;i<children.length;){
  const first=children[i];
  if(first.type!=='element'||first.name!=='path'){out.push(first);i++;continue;}
  const attrs=Object.fromEntries(Object.entries(first.attributes).filter(([k])=>paintAttrs.has(k)));
  const key=JSON.stringify(attrs);
  let end=i+1;
  while(end<children.length){const e=children[end];if(e.type!=='element'||e.name!=='path'||JSON.stringify(Object.fromEntries(Object.entries(e.attributes).filter(([k])=>paintAttrs.has(k))))!==key)break;end++;}
  if(end-i>1&&Object.keys(attrs).length>2){
   const group={type:'element',name:'g',attributes:attrs,children:children.slice(i,end)};
   for(const child of group.children)for(const k of Object.keys(attrs))delete child.attributes[k];
   out.push(group);
  }else out.push(...children.slice(i,end));
  i=end;
 }
 parent.children=out;
}}})};
const result=optimize(fs.readFileSync(input,'utf8'),{path:input,multipass:true,
  plugins:[groupPaint,'moveElemsAttrsToGroup','collapseGroups','removeUnusedNS','removeUselessDefs','removeEmptyContainers'],
  js2svg:{pretty:false}});
fs.writeFileSync(output,result.data);
