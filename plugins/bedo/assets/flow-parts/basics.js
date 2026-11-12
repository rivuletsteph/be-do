/* the small things every be•do page needs: the theme button's icons and wiring, the chip, the
   heading, and the handful of helpers the drawing code is written in. Expects `const D` (the page's
   data) to be defined already, and a #chip and #h1 in the page. Lifted out of flow_engine.html,
   9 Nov 2026. */
const THEMEICON={"auto": "<svg viewBox=\"0 0 24 24\" width=\"15\" height=\"15\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\" style=\"vertical-align:-3px\"><rect x=\"7\" y=\"2.5\" width=\"10\" height=\"19\" rx=\"2.2\"/><path d=\"M11 18.5h2\"/></svg>", "light": "<svg viewBox=\"0 0 24 24\" width=\"15\" height=\"15\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\" style=\"vertical-align:-3px\"><circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4\"/></svg>", "dark": "<svg viewBox=\"0 0 24 24\" width=\"15\" height=\"15\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.7\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\" style=\"vertical-align:-3px\"><path d=\"M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z\"/></svg>"};
const NS='http://www.w3.org/2000/svg', cv=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const col=c=>cv('--c-'+(c||'clay'));
const S=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(p)p.append(e);return e;};
const T=(s,a,p)=>{const e=S('text',Object.assign({'font-family':'IBM Plex Sans, sans-serif','font-size':13,fill:cv('--ink')},a),p);e.textContent=s;return e;};
const MONO='IBM Plex Mono, monospace';
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const plus=(a,b)=>{const d=new Date(a+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+b);return d.toISOString().slice(0,10);};
const fmt=s=>new Date(s+'T12:00:00Z').toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short',timeZone:'UTC'});
const cut=(s,n)=>s.length>n?s.slice(0,n-1).replace(/\s\S*$/,'')+'…':s;
{ const c=document.getElementById('chip');
  const lbl=()=>window.bedoThemeNow()==='night'?'switch to light':'switch to dark';
  c.innerHTML=`<button type="button" class="theme1" aria-label="${lbl()}" title="${lbl()}">${THEMEICON[window.bedoThemeNow()==='night'?'light':'dark']}</button>`;
  c.append(document.createTextNode(D.chip||''));
  const b=c.querySelector('.theme1');
  b.onclick=()=>window.bedoThemeFlip();
  document.addEventListener('bedo-theme',()=>{ b.innerHTML=THEMEICON[window.bedoThemeNow()==='night'?'light':'dark']; b.setAttribute('aria-label',lbl()); b.title=lbl(); }); }
document.getElementById('h1').innerHTML=esc(D.label)+(D.word?` <span class="w">— ${esc(D.word)}</span>`:'');
