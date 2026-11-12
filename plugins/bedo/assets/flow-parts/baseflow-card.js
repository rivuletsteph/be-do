/* the base-flow card. BF is the page’s own baseflow block, BFV its score; card() draws the
   river into #rv and lets a tap pick a morning. Expects `const D`, esc() from basics.js and
   BedoBaseFlow from base-flow/base_flow.js. Lifted out of flow_engine.html, 9 Nov 2026 — one
   copy, so a morning reads the same on both pages. */
const BF = D.baseflow||{parts:[],missing:[]};
const BFV = BF.parts.length ? BedoBaseFlow.score(BF.parts) : null;
/* base flow as water through the week (29 Oct 2026, her words): each morning the river is as wide as
   that morning's base flow, its three strands as wide as their shares (readiness teal, balance ochre,
   growth brick — her word for it, 29 Oct 2026); a part that couldn't be read leaves its strand dry, dotted. The river runs into
   this morning's number. Tap a morning to see how its number was made. */
const BFC={body:'#4F8A8B',balance:'#D4A055',effectiveness:'#BE5B50'}, BFN={body:'#8CC3C3',balance:'#E3BB77',effectiveness:'#E08A7F'};
const bfc=k=>(document.documentElement.getAttribute('data-bedo')==='night'?BFN:BFC)[k];
const KEYS=['body','balance','effectiveness'];
let rvSel=null;
function dayFlow(w){ const have=KEYS.filter(k=>w[k]!=null); return have.length?Math.round(have.reduce((a,k)=>a+w[k],0)/have.length):null; }
function card(){
  const wk=(BF.week||[]).slice(); const el=document.getElementById('rv'); if(!wk.length){ el.innerHTML=''; return; }
  wk.forEach(w=>w.v=dayFlow(w)); const sel=rvSel==null?wk.length-1:rvSel, w=wk[sel];
  const VW=1000, VH=190, X0=40, X1=760, MID=86;
  // the river's width follows the morning's base flow, from a trickle at 40 to full at 100, so a dip shows
  const xs=wk.map((_,i)=>X0+i*(X1-X0)/(wk.length-1));
  // the strands, stacked about the middle line; each morning's total width is its base flow
  const span=v=>Math.max(8,(v-40)*2.2), width=(w,k)=>{ if(w[k]==null||w.v==null) return 0; const have=KEYS.filter(j=>w[j]!=null);
    return span(w.v)*w[k]/have.reduce((a,j)=>a+w[j],0); };
  const tops=wk.map(w=>MID-KEYS.reduce((a,k)=>a+width(w,k),0)/2);
  let svg=`<svg viewBox="0 0 ${VW} ${VH}" role="img" aria-label="base flow through the last seven mornings">`;
  const smooth=pts=>{ let d=`M${pts[0][0]},${pts[0][1]}`; for(let i=0;i<pts.length-1;i++){ const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||p2;
      d+=` C${(p1[0]+(p2[0]-p0[0])/6).toFixed(1)},${(p1[1]+(p2[1]-p0[1])/6).toFixed(1)} ${(p2[0]-(p3[0]-p1[0])/6).toFixed(1)},${(p2[1]-(p3[1]-p1[1])/6).toFixed(1)} ${p2[0]},${p2[1].toFixed(1)}`; } return d; };
  let acc=tops.slice();
  KEYS.forEach(k=>{ const top=acc.map((y,i)=>[xs[i],y]), bot=acc.map((y,i)=>[xs[i],y+width(wk[i],k)]);
    const back=bot.slice().reverse(); let d=smooth(top)+' L'+back[0][0]+','+back[0][1].toFixed(1)+smooth(back).slice(smooth(back).indexOf(' C'))+' Z';
    svg+=`<path d="${d}" fill="${bfc(k)}" opacity=".78"/>`;
    wk.forEach((x,i)=>{ if(x[k]==null) svg+=`<line x1="${xs[i]-14}" y1="${acc[i]}" x2="${xs[i]+14}" y2="${acc[i]}" stroke="${bfc(k)}" stroke-width="2" stroke-dasharray="2 3"/>`; });
    acc=acc.map((y,i)=>y+width(wk[i],k)); });
  // the river runs into this morning's number
  const last=wk.length-1, ty=MID, tx=X1;
  svg+=`<path d="M${tx},${tops[last]} C${tx+60},${tops[last]} ${880-70},${ty-46} ${880},${ty-46} L880,${ty+46} C${880-70},${ty+46} ${tx+60},${acc[last]} ${tx},${acc[last]} Z" fill="var(--rule)" opacity=".5"/>`;
  svg+=`<circle cx="905" cy="${ty}" r="46" fill="var(--card)" stroke="var(--accent)" stroke-width="3"/><text x="905" y="${ty+10}" text-anchor="middle" font-family="Spectral, serif" font-weight="600" font-size="30" fill="var(--ink)">${wk[last].v??'—'}</text>`;
  svg+=`<text x="905" y="${ty+66}" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="12" fill="var(--muted)">this morning · ${wk[last].v!=null?BedoBaseFlow.state(wk[last].v):''}</text>`;
  // the mornings
  wk.forEach((x,i)=>{ const on=i===sel;
    svg+=`<g class="day" data-i="${i}"><rect x="${xs[i]-40}" y="0" width="80" height="${VH}" fill="transparent"/>`
      +`<line x1="${xs[i]}" y1="18" x2="${xs[i]}" y2="150" stroke="${on?'var(--accent)':'var(--rule)'}" stroke-width="${on?1.6:1}" stroke-dasharray="${on?'0':'2 4'}"/>`
      +`<text x="${xs[i]}" y="170" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="12.5" font-weight="${on?600:400}" fill="${on?'var(--ink)':'var(--muted)'}">${x.label} ${x.v??'—'}</text></g>`; });
  svg+='</svg>';
  // how it was made, for the chosen morning
  const note={body:`Oura readiness ${w.label} morning`, balance:`how evenly ${w.yday}'s wheel was shared`, effectiveness:(w.grew?`forward: ${w.grew.steps} step${w.grew.steps===1?'':'s'} closed on ${w.grew.drives} drive${w.grew.drives===1?'':'s'} in the last 7 days · `:'')+(w.late?(w.late[0]+w.late[1]?`free: ${w.late[0]+w.late[1]} past a date you set`:'free: nothing past a date you set'):'free: not read')};
  const have=KEYS.filter(k=>w[k]!=null);
  const NAME={body:'readiness',balance:'balance',effectiveness:'growth'};  // her three, 11 Nov 2026: readiness, balance, growth (growth holds the buffer as its free reading, 261111_f16)
  const how=KEYS.map(k=>`<div class="r${w[k]==null?' off':''}" style="--c:${bfc(k)}"><b>${NAME[k]}<small>${esc(note[k])}</small></b><span class="bar"><i style="width:${w[k]??0}%"></i></span><span class="v">${w[k]??'—'}</span></div>`).join('');
  const sumline = have.length ? `${have.length>1?'(':''}${have.map(k=>w[k]).join(' + ')}${have.length>1?')':''} <span>÷ ${have.length}</span> = ${w.v} <span>· ${BedoBaseFlow.state(w.v)} (85+ optimal · 70–84 good · under 70 pay attention)${have.length<3?' · '+(3-have.length)+' part not in yet':''}</span>` : 'nothing to read yet';
  el.innerHTML=`<h2>base flow</h2><p class="s">the steady supply going into the day · the river is each morning's base flow through the last week · tap a morning to see how it was made</p>${svg}<div class="how"><div style="font:500 11px var(--mono);color:var(--muted)">${sel===last?'this morning':esc(w.label+' morning')}</div>${how}<div class="sumline">${sumline}</div></div>`;
  el.querySelectorAll('.day').forEach(g=>g.addEventListener('click',()=>{ const i=+g.dataset.i; rvSel = (i===wk.length-1)?null:(rvSel===i?null:i); card(); }));
}
