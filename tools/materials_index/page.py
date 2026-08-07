"""The self-contained INDEX.html shell (markup, styles and search script)."""

from __future__ import annotations


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Materials — catalogue</title>
<style>
/* ---- tokens: one accent, a neutral ramp, nothing else --------------------
   Contrast-checked (WCAG 2.1 AA, both modes):
     ink 17.3 / 13.9 · ink-2 6.9 / 6.7 · ink-3 5.1 / 5.2 (4.7 / 4.8 on panel-2)
     accent-on-soft 6.9 / 7.6 · amber-on-soft 5.2 / 6.7 · mark 15.1 / 8.3
   --line is a decorative divider only. Anything that bounds a CONTROL
   (input, chip, button) uses --ctl, which clears 3:1 per SC 1.4.11.        */
:root{
 --bg:#fbfbfa; --panel:#fff; --panel-2:#f7f7f5;
 --ink:#1b1b19; --ink-2:#5a5a54; --ink-3:#6f6f68;
 --line:#e8e7e3; --line-2:#f1f0ec; --ctl:#949490;
 --accent:#4338ca; --accent-soft:#eeeefb; --accent-line:#c9c7f2;
 --amber:#965612; --amber-soft:#fbf3e2;
 --hit:#fdf0b8;
 --r:10px; --r-sm:7px;
 --sh:0 1px 2px rgba(20,20,18,.04);
}
@media(prefers-color-scheme:dark){:root{
 --bg:#141416; --panel:#1c1c1f; --panel-2:#232327;
 --ink:#e8e8ea; --ink-2:#a2a2a8; --ink-3:#8e8e95;
 --line:#2a2a2f; --line-2:#232327; --ctl:#67676c;
 --accent:#a5b4fc; --accent-soft:#242438; --accent-line:#3b3b6b;
 --amber:#d7ac63; --amber-soft:#332a16;
 --hit:#4a4113;
 --sh:none;
}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);
 font:14.5px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
 -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}

/* ---- header -------------------------------------------------------------- */
header{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);
 backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--line)}
.hrow{display:flex;align-items:center;gap:14px;padding:13px 0 0}
h1{margin:0;font-size:15px;font-weight:640;letter-spacing:-.01em;white-space:nowrap}
.stat{margin-left:auto;color:var(--ink-3);font-size:11.5px;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums}
.seg{display:inline-flex;background:var(--panel-2);border:1px solid var(--ctl);
 border-radius:8px;padding:2px;gap:2px}
.seg button{font:inherit;font-size:12.5px;padding:5px 12px;border:0;border-radius:6px;
 background:transparent;color:var(--ink-2);cursor:pointer;transition:background .12s,color .12s}
.seg button:hover{color:var(--ink)}
.seg button[aria-selected="true"]{background:var(--panel);color:var(--ink);font-weight:560;box-shadow:var(--sh)}

.searchbar{position:relative;display:flex;align-items:center;margin:11px 0 0}
.searchbar svg{position:absolute;left:12px;width:15px;height:15px;stroke:var(--ink-3);
 fill:none;stroke-width:2;pointer-events:none}
#q{width:100%;padding:10px 78px 10px 35px;font:inherit;font-size:14px;
 border:1px solid var(--ctl);border-radius:var(--r);background:var(--panel);color:var(--ink);
 transition:border-color .12s,box-shadow .12s}
#q::placeholder{color:var(--ink-3)}
#q:focus{outline:0;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.kbd{position:absolute;right:11px;font-size:11px;color:var(--ink-3);border:1px solid var(--ctl);
 border-radius:5px;padding:1px 6px;background:var(--panel-2);pointer-events:none;
 font-family:ui-monospace,Menlo,monospace}
.clr{position:absolute;right:9px;border:0;background:var(--panel-2);color:var(--ink-2);
 width:26px;height:26px;border-radius:50%;cursor:pointer;font-size:12px;line-height:1;display:none}
.clr:hover{background:var(--line);color:var(--ink)}

.chiprow{display:flex;align-items:center;gap:6px;padding:10px 0 11px;flex-wrap:wrap}
/* controls: >=24px high per SC 2.5.8, >=3:1 border per SC 1.4.11 */
.chip{font:inherit;font-size:12px;padding:5px 11px;border-radius:999px;border:1px solid var(--ctl);
 background:var(--panel);color:var(--ink-2);cursor:pointer;user-select:none;white-space:nowrap;
 min-height:26px;transition:background .12s,color .12s,border-color .12s}
.chip:hover{border-color:var(--ink-2);color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);
 color:var(--accent);font-weight:560}
.sep{width:1px;height:18px;background:var(--ctl);margin:0 4px}
.tools{margin-left:auto;display:flex;gap:6px}
button.t{font:inherit;font-size:12px;padding:5px 10px;border-radius:var(--r-sm);min-height:26px;
 border:1px solid var(--ctl);background:var(--panel);color:var(--ink-2);cursor:pointer}
button.t:hover{border-color:var(--ink-2);color:var(--ink)}

/* ---- main ---------------------------------------------------------------- */
main{padding:18px 0 80px}
.domain{margin:0 0 12px}
details{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);
 margin:0 0 8px;box-shadow:var(--sh)}
details details{border:0;border-top:1px solid var(--line-2);border-radius:0;margin:0;
 background:transparent;box-shadow:none}
summary{cursor:pointer;padding:9px 13px;list-style:none;display:flex;align-items:center;
 gap:8px;flex-wrap:wrap;border-radius:var(--r)}
summary::-webkit-details-marker{display:none}
summary:hover{background:var(--panel-2)}
details details>summary{border-radius:0}
summary::before{content:"";width:0;height:0;flex:none;margin-top:1px;
 border:4px solid transparent;border-left:5px solid var(--ink-3);
 transition:transform .14s ease;align-self:flex-start;margin-top:6px}
details[open]>summary::before{transform:rotate(90deg) translateX(1px)}
.dlabel{font-weight:640;font-size:14.5px;letter-spacing:-.005em}
.dhint{color:var(--ink-3);font-size:11.5px}
.card>summary{align-items:flex-start}
.title{font-weight:560}
.metaline{flex-basis:100%;color:var(--ink-3);font-size:11.5px;padding-left:17px;margin-top:1px}
.slug{color:var(--ink-3);font-size:11.5px;font-family:ui-monospace,Menlo,monospace}
.fname{font-weight:530}
.badge{font-size:11px;background:var(--panel-2);color:var(--ink-2);padding:1px 7px;
 border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.badge-archived{color:var(--ink-3)}
.group-modules>summary,.group-library>summary{background:var(--panel-2)}
.group-modules>summary .fname,.group-library>summary .fname{font-weight:620}
.group-type>summary .fname,.module>summary .fname{font-weight:580}
.group-missing>summary .fname{color:var(--amber)}
.group-unreg>summary .fname{color:var(--ink-3)}
.ext-link-btn{font-size:11px;color:var(--accent);text-decoration:none;border:1px solid var(--accent-line);
 border-radius:999px;padding:2px 8px;white-space:nowrap;background:var(--accent-soft)}
.ext-link-btn:hover{filter:brightness(.97)}
.count{margin-left:auto;color:var(--ink-3);font-size:11.5px;white-space:nowrap;
 align-self:flex-start;margin-top:2px;font-variant-numeric:tabular-nums}
.body{padding:1px 8px 7px 19px}
details details .body{padding-left:15px}

a.file,span.file{display:flex;align-items:center;gap:9px;padding:6px 9px;border-radius:var(--r-sm);
 text-decoration:none;color:var(--ink);font-size:13.5px;min-height:28px}
a.file:hover{background:var(--accent-soft)}
span.file.nolink{color:var(--ink-2)}
.fn{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.src-meta{color:var(--ink-3);font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sz{margin-left:auto;color:var(--ink-3);font-size:11.5px;white-space:nowrap;
 font-variant-numeric:tabular-nums}

/* file-type tags: monochrome by default; colour reserved for real signals */
.ext{font-size:11px;text-transform:uppercase;letter-spacing:.03em;font-weight:600;
 color:var(--ink-3);background:transparent;border:1px solid var(--line);border-radius:4px;
 padding:0 5px;min-width:42px;text-align:center;flex:none;
 font-family:ui-monospace,Menlo,monospace}
.ext-link{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.ext-missing{color:var(--amber);border-color:var(--amber);background:var(--amber-soft)}

mark{background:var(--hit);color:inherit;border-radius:2px;padding:0 1px}
.hide{display:none!important}
.empty{color:var(--ink-3);padding:44px 20px;text-align:center;font-size:13.5px;line-height:1.7}
.empty kbd,footer kbd{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;
 border:1px solid var(--line);border-radius:4px;padding:1px 5px;background:var(--panel-2)}

/* ---- flat search results ------------------------------------------------- */
#results{padding-top:2px}
.reshdr{color:var(--ink-3);font-size:11.5px;padding:2px 2px 8px;
 display:flex;align-items:center;gap:10px;font-variant-numeric:tabular-nums}
.res{display:flex;align-items:baseline;gap:11px;padding:7px 10px;border-radius:var(--r-sm);
 text-decoration:none;color:var(--ink);scroll-margin:120px}
.res+.res{border-top:1px solid var(--line-2)}
.res:hover{background:var(--panel-2)}
.res.sel{background:var(--accent-soft);box-shadow:inset 2px 0 0 var(--accent)}
.res .rn{font-weight:540;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
 max-width:52%;font-size:13.5px}
.res .rc{color:var(--ink-3);font-size:11.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.res .rk{margin-left:auto;font-size:11px;text-transform:uppercase;letter-spacing:.03em;
 color:var(--ink-3);border:1px solid var(--line);border-radius:4px;padding:0 5px;
 white-space:nowrap;flex:none;font-family:ui-monospace,Menlo,monospace}
.res .rk.online{color:var(--accent);border-color:var(--accent-line);background:var(--accent-soft)}
.res .rk.missing{color:var(--amber);border-color:var(--amber);background:var(--amber-soft)}
.more{width:100%;margin-top:10px;padding:9px;font:inherit;font-size:12.5px;cursor:pointer;
 border:1px dashed var(--ctl);border-radius:var(--r-sm);background:transparent;color:var(--ink-2)}
.more:hover{border-color:var(--ink-2);color:var(--ink)}

footer{border-top:1px solid var(--line);color:var(--ink-3);font-size:11.5px;
 padding:16px 0 40px;line-height:1.8}
footer code{font-family:ui-monospace,Menlo,monospace;background:var(--panel-2);
 border:1px solid var(--line);border-radius:4px;padding:0 4px}

@media(max-width:720px){
 .wrap{padding:0 14px}
 .hrow{flex-wrap:wrap;gap:10px}
 .stat{margin-left:0;flex-basis:100%;white-space:normal}
 .chiprow{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
 .chiprow::-webkit-scrollbar{display:none}
 .tools{margin-left:8px}
 .res .rn{max-width:100%}
 .kbd{display:none}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
</style></head>
<body>
<header><div class="wrap">
 <div class="hrow">
  <h1>Materials</h1>
  <div class="seg" role="tablist" aria-label="View">
   <button id="vSources" role="tab" aria-selected="true">Sources</button>
   <button id="vFiles" role="tab" aria-selected="false">Files</button>
  </div>
  <span class="stat">⟪SUMMARY⟫</span>
 </div>
 <div class="searchbar">
  <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
  <input id="q" type="search" autocomplete="off" spellcheck="false"
   placeholder="Search titles, filenames, folders, authors, URLs — space-separated terms all must match"
   aria-label="Search materials" autofocus>
  <kbd class="kbd" id="kbd">/</kbd>
  <button class="clr" id="clear" aria-label="Clear search" title="Clear (Esc)">✕</button>
 </div>
 <div class="chiprow" role="group" aria-label="Filters">
  <button class="chip" data-type="*" aria-pressed="true">All</button>⟪CHIPS⟫
  <span class="sep" aria-hidden="true"></span>
  <button class="chip" id="onlineChip" aria-pressed="false">Online only</button>
  <button class="chip" id="supportChip" aria-pressed="false">Support files</button>
  <button class="chip" id="archChip" aria-pressed="false">Hide archived</button>
  <span class="tools">
   <button class="t" id="expand" title="Expand everything in this view">Expand</button>
   <button class="t" id="collapse" title="Collapse back to the domain map">Collapse</button>
  </span>
 </div>
</div></header>
<main class="wrap">
<div id="view-sources">⟪VIEWSOURCES⟫</div>
<div id="view-files" class="hide">⟪VIEWFILES⟫</div>
<div id="results" class="hide"></div>
<div id="treeEmpty" class="empty hide">Nothing matches these filters.</div>
</main>
<footer class="wrap">
 Generated ⟪DATE⟫ · rebuild with <code>make materials</code>. Disposable view — never the source of truth.<br>
 Local file links are relative to this page: keep <code>INDEX.html</code> inside <code>materials/</code> or they break.<br>
 <kbd>/</kbd> or <kbd>⌘K</kbd> search · <kbd>↑↓</kbd> move · <kbd>⏎</kbd> open ·
 <kbd>⌘⏎</kbd> new tab · <kbd>Esc</kbd> clear
</footer>
<script>
const LEAVES=⟪LEAVES⟫;
const $=id=>document.getElementById(id);
const q=$('q'), vs=$('view-sources'), vf=$('view-files'), res=$('results'),
      treeEmpty=$('treeEmpty'), clr=$('clear'), kbd=$('kbd');

let view='sources', types=new Set(), onlineOnly=false, showSupport=false, hideArchived=false;
let terms=[], hits=[], shown=0, sel=-1;
const PAGE_SIZE=200;

/* cache the DOM node lists once — the old build re-queried on every keystroke */
const CACHE={};
function nodes(root){
 const k=root.id;
 if(!CACHE[k]) CACHE[k]={leaves:[...root.querySelectorAll('.leaf')],
                         details:[...root.querySelectorAll('details')],
                         domains:[...root.querySelectorAll('section.domain')]};
 return CACHE[k];
}

function passes(k,t,sup,arch){
 if(types.size&&!types.has(t))return false;
 if(onlineOnly&&k==='local')return false;
 if(!showSupport&&sup)return false;
 if(hideArchived&&arch)return false;
 return true;
}
function esc(s){return (s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

/* escape + <mark> every matched term, without corrupting entities */
function hl(text){
 if(!terms.length)return esc(text);
 const low=(text||'').toLowerCase(); const sp=[];
 for(const t of terms){let i=low.indexOf(t);while(i!==-1){sp.push([i,i+t.length]);i=low.indexOf(t,i+1);}}
 if(!sp.length)return esc(text);
 sp.sort((a,b)=>a[0]-b[0]);
 const m=[];
 for(const s of sp){const l=m[m.length-1];
  if(l&&s[0]<=l[1])l[1]=Math.max(l[1],s[1]);else m.push([s[0],s[1]]);}
 let out='',pos=0;
 for(const [a,b] of m){out+=esc(text.slice(pos,a))+'<mark>'+esc(text.slice(a,b))+'</mark>';pos=b;}
 return out+esc(text.slice(pos));
}

/* relevance: filename prefix > filename hit > path hit > metadata hit */
function score(L){
 const n=L.n.toLowerCase(), c=(L.c||'').toLowerCase();
 let s=0;
 for(const t of terms){
  if(n.startsWith(t))s+=100; else if(n.includes(t))s+=45;
  else if(c.includes(t))s+=12; else s+=2;
 }
 if(L.k==='local')s+=4;
 if(L.a)s-=18;
 if(L.s===1)s-=30;
 return s;
}

function filterTree(root){
 const N=nodes(root); let visible=0;
 for(const f of N.leaves){
  const ok=passes(f.dataset.kind,f.dataset.type,f.dataset.support==='1',f.dataset.archived==='1');
  f.classList.toggle('hide',!ok); if(ok)visible++;
 }
 for(const d of N.details) d.classList.toggle('hide',!d.querySelector('.leaf:not(.hide)'));
 for(const s of N.domains) s.classList.toggle('hide',!s.querySelector('.leaf:not(.hide)'));
 return visible;
}

function rowHTML(L){
 const kind=L.k==='local'?(L.t||'file'):L.k;
 const cls=L.k==='online'?'rk online':L.k==='missing'?'rk missing':'rk';
 const tag=L.h?'a':'span';
 const attrs=L.h?` href="${esc(L.h)}"${L.k==='online'?' target="_blank" rel="noopener"':''}`:'';
 return `<${tag} class="res"${attrs} title="${esc(L.c)}"><span class="rn">${hl(L.n)}</span>`+
        `<span class="rc">${hl(L.c)}</span><span class="${cls}">${esc(kind)}</span></${tag}>`;
}

function paint(){
 const head=`<div class="reshdr"><strong>${hits.length}</strong> match${hits.length===1?'':'es'}`+
   (hits.length>shown?` · showing ${shown}`:'')+`</div>`;
 if(!hits.length){
  res.innerHTML='<div class="empty">No matches.<br>Try fewer or shorter terms — every space-separated word has to match.</div>';
  return;
 }
 let html=head;
 for(let i=0;i<shown;i++) html+=rowHTML(hits[i]);
 if(hits.length>shown) html+=`<button class="more" id="more">Show ${Math.min(PAGE_SIZE,hits.length-shown)} more of ${hits.length-shown}</button>`;
 res.innerHTML=html;
 const more=$('more'); if(more)more.onclick=()=>{shown=Math.min(shown+PAGE_SIZE,hits.length);paint();};
 mark();
}
function rows(){return [...res.querySelectorAll('.res')];}
function mark(){rows().forEach((r,i)=>r.classList.toggle('sel',i===sel));}
function move(d){
 const r=rows(); if(!r.length)return;
 sel=Math.max(0,Math.min(r.length-1,sel+d)); mark();
 r[sel].scrollIntoView({block:'nearest'});
}

function search(){
 const scored=[];
 for(const L of LEAVES){
  if(!passes(L.k,L.t,L.s===1,L.a===1))continue;
  let ok=true; for(const t of terms){if(!L.q.includes(t)){ok=false;break;}}
  if(ok)scored.push([score(L),L]);          /* score once, not per comparison */
 }
 scored.sort((a,b)=>b[0]-a[0]||a[1].n.localeCompare(b[1].n));
 hits=scored.map(p=>p[1]);
 shown=Math.min(PAGE_SIZE,hits.length); sel=-1;
 paint();
}

function update(){
 const raw=q.value.trim();
 terms=raw.toLowerCase().split(/\\s+/).filter(Boolean);
 clr.style.display=raw?'block':'none';
 kbd.style.display=raw?'none':'';
 if(terms.length){
  vs.classList.add('hide'); vf.classList.add('hide'); treeEmpty.classList.add('hide');
  res.classList.remove('hide'); search();
 }else{
  res.classList.add('hide');
  vs.classList.toggle('hide',view!=='sources');
  vf.classList.toggle('hide',view!=='files');
  const n=filterTree(view==='sources'?vs:vf);
  treeEmpty.classList.toggle('hide',n>0);
 }
}
let timer; const debounced=()=>{clearTimeout(timer);timer=setTimeout(update,90);};

function setView(v){
 view=v;
 $('vSources').setAttribute('aria-selected',v==='sources');
 $('vFiles').setAttribute('aria-selected',v==='files');
 update();
}
function toggle(btn,val){btn.setAttribute('aria-pressed',String(val));}

q.addEventListener('input',debounced);
$('vSources').onclick=()=>setView('sources');
$('vFiles').onclick=()=>setView('files');
clr.onclick=()=>{q.value='';update();q.focus();};

/* type chips: multi-select ("All" clears the set) */
const typeChips=[...document.querySelectorAll('.chip[data-type]')];
for(const c of typeChips) c.addEventListener('click',()=>{
 const t=c.dataset.type;
 if(t==='*') types.clear();
 else {types.has(t)?types.delete(t):types.add(t);}
 for(const x of typeChips){
  toggle(x, x.dataset.type==='*' ? types.size===0 : types.has(x.dataset.type));
 }
 update();
});
$('onlineChip').addEventListener('click',e=>{
 onlineOnly=!onlineOnly; toggle(e.currentTarget,onlineOnly);
 if(onlineOnly&&view==='files')setView('sources');else update();
});
$('supportChip').addEventListener('click',e=>{
 showSupport=!showSupport; toggle(e.currentTarget,showSupport); update();
});
$('archChip').addEventListener('click',e=>{
 hideArchived=!hideArchived; toggle(e.currentTarget,hideArchived); update();
});
$('expand').onclick=()=>{const r=view==='sources'?vs:vf;
 for(const d of nodes(r).details) d.open=true;};
$('collapse').onclick=()=>{const r=view==='sources'?vs:vf;
 for(const d of nodes(r).details) d.open=false;
 for(const s of nodes(r).domains){const d=s.querySelector(':scope > details'); if(d)d.open=true;}
 window.scrollTo({top:0});};

document.addEventListener('keydown',e=>{
 const typing=/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
 if((e.key==='k'&&(e.metaKey||e.ctrlKey))||(e.key==='/'&&!typing)){
  e.preventDefault(); q.focus(); q.select(); return;
 }
 if(e.key==='Escape'){ if(q.value){q.value='';update();} q.blur(); return; }
 if(res.classList.contains('hide'))return;
 if(e.key==='ArrowDown'){e.preventDefault();move(1);}
 else if(e.key==='ArrowUp'){e.preventDefault();move(-1);}
 else if(e.key==='Enter'&&sel>=0){
  const r=rows()[sel]; if(!r||r.tagName!=='A')return;
  e.preventDefault();
  if(e.metaKey||e.ctrlKey)window.open(r.href,'_blank','noopener');else r.click();
 }
});
if(navigator.platform&&/Mac/.test(navigator.platform))kbd.textContent='⌘K';
update();
</script>
</body></html>
"""
