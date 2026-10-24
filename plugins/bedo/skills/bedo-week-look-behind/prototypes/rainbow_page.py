import json, sys
DAY = sys.argv[1]
D = json.load(open(f'rings-{DAY}.json', encoding='utf-8'))
name = D['day'].split()[0]
tpl = r'''<title>How __NAME__ Went</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@1,9..144,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* the waking day as a rainbow: up on the left, midday at the top, the evening down on the right; the ends
   bend back past the horizon like an open book's covers. Concentric bands, one colour family each, shades for parts. */
:root{--ground:#F4EEE4;--card:#FBF8F2;--ink:#2C2620;--soft:#4A4036;--muted:#7A6E60;--rule:#E3D9CA;--terra:#B5603F;
--flow-t:#F1ECE4;--dawn:#F3D27F;--dawn-d:#C29630;--dusk:#C3B8EC;--dusk-d:#7B6FD6;--sleep:#D4DEF0;--sleep-deep:#6F8CC4;--sleep-d:#5A73A8;
--eat:#6FAE9F;--move:#9DCDBF;--enjoy:#CDE7DF;--being-t:#EEF6F3;--being-d:#4A8577;
--work:#C27E5E;--care:#D9A086;--cook:#E8C0AA;--system:#F4E0D4;--doing-t:#FAF0EA;--doing-d:#9C5C3E;--screen:#2C2620;--screen-t:#ECE5DA;
--sans:"IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;--display:"Fraunces",Georgia,serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ground:#1B1A1F;--card:#232127;--ink:#EDE4E0;--soft:#D3C8C3;--muted:#A3958F;--rule:#3A3336;--terra:#E08A7F;
--flow-t:#2B2830;--dawn-d:#9A7621;--dusk-d:#6458BE;--sleep-d:#C9D6EE;--sleep:#3A4766;--sleep-deep:#8FA8DA;--being-t:#24302D;--being-d:#CDE7DF;--doing-t:#352B27;--doing-d:#F4E0D4;--screen:#EDE4E0;--screen-t:#2E2A30;color-scheme:dark}}
:root[data-theme="dark"]{--ground:#1B1A1F;--card:#232127;--ink:#EDE4E0;--soft:#D3C8C3;--muted:#A3958F;--rule:#3A3336;--terra:#E08A7F;
--flow-t:#2B2830;--dawn-d:#9A7621;--dusk-d:#6458BE;--sleep-d:#C9D6EE;--sleep:#3A4766;--sleep-deep:#8FA8DA;--being-t:#24302D;--being-d:#CDE7DF;--doing-t:#352B27;--doing-d:#F4E0D4;--screen:#EDE4E0;--screen-t:#2E2A30;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:640px;margin:0 auto;padding-block:28px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.eyebrow{font:500 .72rem var(--mono);color:var(--muted);letter-spacing:.06em;text-transform:uppercase;margin:0}
h1{font:500 italic clamp(2rem,8vw,2.6rem)/1.05 var(--display);color:var(--terra);margin:8px 0 0}
.sub{color:var(--soft);line-height:1.5;margin:10px 0 0;max-width:60ch}
.card{background:var(--card);border:1px solid var(--rule);border-radius:20px;padding:16px 10px;margin-top:18px}
svg{display:block;width:100%;max-width:520px;height:auto;margin:0 auto;overflow:visible}
svg text{font-family:var(--mono);fill:var(--muted)}
svg [data-tip]{cursor:pointer}
svg [data-tip]:focus-visible{outline:none;stroke:var(--ink);stroke-width:2}
svg [data-tip].on{stroke:var(--ink);stroke-width:2}
.tip{min-height:4.2em;margin:4px 6px 0;padding:10px 12px;border-radius:12px;background:var(--ground);font-size:.86rem;line-height:1.45;color:var(--soft)}
.tip b{color:var(--ink);font-weight:600}
.label{font:600 .7rem var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:22px 6px 10px}
.ring{display:grid;gap:6px;padding:12px 6px;border-top:1px solid var(--rule)}
.rh{display:flex;align-items:baseline;gap:8px}
.rh b{font-weight:600}
.rh .v{margin-left:auto;font:500 .9rem var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.rh .v small{color:var(--muted);font-weight:400}
.kinds{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.8rem;color:var(--soft)}
.kinds i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}
.held{font-size:.8rem;color:var(--muted);line-height:1.45}
.note{font-size:.8rem;color:var(--muted);line-height:1.45;margin:14px 6px 0}
</style>
<div class="wrap">
<p class="eyebrow">the day behind · how the day went · a proposal</p>
<h1>How __NAME__ went</h1>
<p class="sub">__DAY__, your waking hours as a rainbow: up on the left, the middle of the day at the top, the evening down on the right. The gap at the bottom is the night, eight hours, in blue for how long you were in bed. From the inside out: your dawn and dusk flows, then being (eating, moving, enjoying), then doing (work, caretaking, cooking, be•do); the thin line is time on a screen, and around the outside, the moments that mattered, where they happened. Tap anything to see what it was.</p>
<div class="card">
<svg id="dial" viewBox="-30 -20 460 410" role="img" aria-label="The waking day as concentric arcs"></svg>
<div class="tip" id="tip" aria-live="polite">Tap a piece of the rainbow or a moment around it.</div>
<p class="label">from the inside out · share of the waking day</p>
<div id="rings"></div>
<p class="note" id="note"></p>
</div>
</div>
<script>
const D = /*DATA*/;
const C = k => `var(--${k})`, hm = m => { m = Math.round(m); const h = Math.floor(m / 60), r = m % 60; return h ? (r ? `${h} h ${String(r).padStart(2, "0")}` : `${h} h`) : `${r} min`; };
const clock = m => { m = ((Math.round(m) % 1440) + 1440) % 1440; const h = Math.floor(m / 60), mm = m % 60; return `${h % 12 || 12}:${String(mm).padStart(2, "0")}${h < 12 ? "a" : "p"}`; };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
// the waking day: 16 hours from getting up (24 Oct 2026); in bed for the 8 that make 24
const SPAN = 960, morning = (D.nights || []).find(n => n.a === 0), evening = (D.nights || []).find(n => n.b === 1440 && n.a > 0);
const WAKE = morning ? morning.b : 420, BED = evening ? evening.a : Math.min(1440, WAKE + SPAN), END = WAKE + SPAN;
// a rainbow bent back like an open book: 240 degrees, from lower left over the top to lower right
const SWEEP = 240, CX = 200, CY = 205;
const theta = m => (-90 - SWEEP / 2 + (Math.min(Math.max(m, WAKE), END) - WAKE) / SPAN * SWEEP) * Math.PI / 180;
const pt = (r, m) => [CX + r * Math.cos(theta(m)), CY + r * Math.sin(theta(m))];
const band = (r0, r1, a, b) => { const L = (b - a) / SPAN * SWEEP > 180 ? 1 : 0, [x0, y0] = pt(r1, a), [x1, y1] = pt(r1, b), [x2, y2] = pt(r0, b), [x3, y3] = pt(r0, a);
  return `M${x0} ${y0}A${r1} ${r1} 0 ${L} 1 ${x1} ${y1}L${x2} ${y2}A${r0} ${r0} 0 ${L} 0 ${x3} ${y3}Z`; };
const clip = ([k, a, b, t]) => [k, Math.max(a, WAKE), Math.min(b, END), t || []];
const R = Object.fromEntries(D.rings.map(r => [r.k, r]));
// bands from the inside out; parts of a band are shades of its colour (24 Oct 2026: shades, not patterns)
const BANDS = [
  {k: "flow", n: "Flows", fam: "flow", parts: {flow: ["flow", "a flow step"]}},
  {k: "being", n: "Being", fam: "being", parts: {eat: ["eat", "eating and drinking"], move: ["move", "moving"], enjoy: ["enjoy", "enjoying"]}},
  {k: "doing", n: "Doing", fam: "doing", parts: {work: ["work", "professional work"], care: ["care", "caretaking (others and yourself)"], cook: ["cook", "cooking"], system: ["system", "be•do"]}}];
const HOLE = 52, W = 40, GAP = 4, R0 = 58;
let g = "", tips = [];
const piece = (d, fill, stroke, tip) => { tips.push(tip); return `<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="1" tabindex="0" data-i="${tips.length - 1}" data-tip="1"/>`; };
BANDS.forEach((B, i) => {
  const r0 = R0 + i * (W + GAP), r1 = r0 + W;
  g += `<path d="${band(r0, r1, WAKE, END)}" fill="var(--${B.fam}-t)"/>`;
  if (B.k === "flow") Object.entries(D.win).forEach(([k, w]) => { const [, a, b] = clip([k, ...w]); if (b <= a) return;
    g += piece(band(r0, r1, a, b), `var(--${k})`, `var(--${k}-d)`, `<b>${k === "dawn" ? "🌅 The dawn flow" : "🌄 The dusk flow"}</b> · ${clock(a)}–${clock(b)}<br>${esc((R.flow.kinds[0].held || []).join(" · "))}`); });
  (R[B.k] || {runs: []}).runs.map(clip).filter(([, a, b]) => b - a >= 2).forEach(([k, a, b, t]) => {
    const [col, nm] = B.parts[k] || [B.fam, k];
    if (B.k === "flow") { for (let m = a; m < b; m += 5) { const fk = Object.entries(D.win).find(([, [x, y]]) => m >= x && m < y), [x0, y0] = pt(r0 + 2, m + 1), [x1, y1] = pt(r1 - 2, m + 1);
      g += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" stroke="var(--${fk ? fk[0] : "dawn"}-d)" stroke-width="1.4" stroke-linecap="round" pointer-events="none"/>`; } return; }
    g += piece(band(r0, r1, a, b), C(col), `var(--${B.fam}-d)`, `<b>${nm[0].toUpperCase() + nm.slice(1)}</b> · ${clock(a)}–${clock(b)} · ${hm(b - a)}${t.length ? "<br>" + t.map(esc).join(" · ") : ""}`);
  });
});
// on a screen or not: a thin line on the outside
const SR = R0 + BANDS.length * (W + GAP) + 2, SW = 5;
g += `<path d="${band(SR, SR + SW, WAKE, END)}" fill="var(--screen-t)"/>`;
(R.screen ? R.screen.runs : []).map(clip).filter(([, a, b]) => b > a).forEach(([k, a, b, t]) => { g += piece(band(SR, SR + SW, a, b), "var(--screen)", "none", `<b>📱 On a screen</b> · ${clock(a)}–${clock(b)} · ${hm(b - a)}${t.length ? "<br>" + t.map(esc).join(" · ") : ""}`); });
// bed before the 16 hours were up: the end of the rainbow is shaded
if (BED < END) g += piece(band(R0, SR + SW, BED, END), "var(--flow-t)", "none", `<b>🛏️ In bed at ${clock(BED)}</b>, ${hm(END - BED)} before the 16 hours were up`);
// times along the outside: up, every four hours, and the end of the 16
[0, 240, 480, 720, 960].forEach(o => { const [x, y] = pt(SR + SW + (o % 960 ? 46 : 52), WAKE + o);
  g += `<text x="${x}" y="${y + 3.5}" text-anchor="middle" font-size="10">${o === 0 ? "up " + clock(WAKE) : clock(WAKE + o)}</text>`; });
// the night that fed the day, in the gap at the bottom: the gap is 8 hours (24 Oct 2026)
const inbed = morning ? morning.inbed : null, IDEAL = 480, GAPDEG = 360 - SWEEP;
const ntheta = m => (-90 - SWEEP / 2 - m / IDEAL * GAPDEG) * Math.PI / 180;          // minutes back from waking, along the gap
const npt = (r, m) => [CX + r * Math.cos(ntheta(m)), CY + r * Math.sin(ntheta(m))];
const nband = (r0, r1, a, b) => { const [x0, y0] = npt(r1, a), [x1, y1] = npt(r1, b), [x2, y2] = npt(r0, b), [x3, y3] = npt(r0, a), L = (b - a) / IDEAL * GAPDEG > 180 ? 1 : 0;
  return `M${x0} ${y0}A${r1} ${r1} 0 ${L} 0 ${x1} ${y1}L${x2} ${y2}A${r0} ${r0} 0 ${L} 1 ${x3} ${y3}Z`; };
const RIN = R0, ROUT = R0 + BANDS.length * (W + GAP) - GAP;
if (inbed != null) {
  const d = inbed - IDEAL, fill = Math.min(inbed, IDEAL), sg = (d >= 0 ? "+" : "−") + hm(Math.abs(d));
  const lab = `<b>😴 In bed last night</b> · ${hm(inbed)} · ${d === 0 ? "exactly 8 h" : sg + " against 8 h"}${morning ? ` · ${clock(+morning.start.slice(11, 13) * 60 + +morning.start.slice(14, 16))}–${clock(WAKE)}` : ""}`;
  g += piece(nband(RIN, ROUT, 0, fill), "var(--sleep)", "var(--sleep-d)", lab);
  if (d < 0) g += `<path d="${nband(RIN, ROUT, fill, IDEAL)}" fill="none" stroke="var(--sleep-d)" stroke-width="1.2" stroke-dasharray="3 3"/>`;
  if (d > 0) g += piece(nband(ROUT + 2, ROUT + 9, 0, Math.min(d, IDEAL)), "var(--sleep-deep)", "none", lab);
  const [tx, ty] = [CX, CY + (RIN + ROUT) / 2 - 6];
  g += `<text x="${tx}" y="${ty}" text-anchor="middle" style="font:600 15px var(--sans);fill:var(--sleep-d)">${hm(inbed)}</text><text x="${tx}" y="${ty + 13}" text-anchor="middle" font-size="9.5" style="fill:var(--sleep-d)">in bed · ${d === 0 ? "8 h" : sg}</text>`;
}
// the moments that mattered, around the outside at the time they happened (24 Oct 2026)
const MOM = D.moments || [];
let lastM = -999, lift = 0;
MOM.forEach(m => { lift = m.m - lastM < 25 ? (lift + 1) % 3 : 0; lastM = m.m;
  const [x, y] = pt(SR + SW + 13 + lift * 15, m.m);
  tips.push(`<b>${m.g} ${esc(m.p[0].toUpperCase() + m.p.slice(1))}</b> · ${clock(m.m)}${m.d ? " · " + hm(m.d) : ""}<br>${esc(m.t)}`);
  g += `<text x="${x}" y="${y + 5}" text-anchor="middle" style="font:14px var(--sans);cursor:pointer" data-tip="1" data-i="${tips.length - 1}" tabindex="0">${m.g}</text>`; });
const dial = document.getElementById("dial"), tip = document.getElementById("tip");
dial.innerHTML = g;
const show = e => { const t = e.target.closest("[data-tip]"); if (!t) return; dial.querySelectorAll(".on").forEach(x => x.classList.remove("on")); t.classList.add("on"); tip.innerHTML = tips[+t.dataset.i];
};
dial.addEventListener("click", show); dial.addEventListener("focusin", show);
// the list
const AW = Math.min(BED, 1440) - WAKE;
const tot = B => B.k === "flow" ? Object.values(D.win).reduce((s, [a, b]) => s + Math.max(0, Math.min(b, END) - Math.max(a, WAKE)), 0) : (R[B.k] || {}).total || 0;
document.getElementById("rings").innerHTML = `<div class="ring"><div class="rh"><b>The waking day</b><span class="v">${hm(AW)}</span></div><div class="held">Up at ${clock(WAKE)}, in bed at ${clock(BED)}. The rainbow is 16 hours; the gap at the bottom is the 8 hours of a night, in blue for the night before: ${inbed != null ? hm(inbed) : "not read"} in bed.</div></div>` +
  BANDS.map(B => { const r = R[B.k] || {kinds: []}, t = tot(B);
    const kinds = B.k === "flow" ? Object.entries(D.win).map(([k, [a, b]]) => `<span><i style="background:var(--${k});border:1px solid var(--${k}-d)"></i>${k} ${clock(a)}–${clock(b)}</span>`).join("")
      : r.kinds.map(k => { const [col, nm] = B.parts[k.k] || [B.fam, k.n]; return `<span><i style="background:${C(col)};border:1px solid var(--${B.fam}-d)"></i>${esc(nm)} ${k.min ? hm(k.min) : "—"}</span>`; }).join("");
    return `<div class="ring"><div class="rh"><b>${B.n}</b><span class="v">${t ? hm(t) : "—"} <small>${Math.round(100 * t / AW)}%</small></span></div><div class="kinds">${kinds}</div></div>`; }).join("") +
  `<div class="ring"><div class="rh"><b>On a screen</b><span class="v">${hm(R.screen ? R.screen.total : 0)} <small>${Math.round(100 * (R.screen ? R.screen.total : 0) / AW)}%</small></span></div><div class="held">phone, laptop or TV; a paper book isn't a screen</div></div>`;
document.getElementById("note").textContent = "The bands overlap, so they don't add up to the waking day: a pickup can be caretaking and a glimmer at once. Doing makes or moves something; being is when the moment itself is the point. Logged time that is none of these isn't drawn. Working counts what you were doing: a session that ran while you drove, ate, moved or slept isn't your work. A meal is not moving. Food is all nutrition, drinks too. A moment with no length (a text, a check, a flow step) is a five-minute tick.";
</script>'''
out = tpl.replace('/*DATA*/', json.dumps(D, ensure_ascii=False)).replace('__NAME__', name).replace('__DAY__', D['day'])
open('how-friday-went.html', 'w', encoding='utf-8').write(out)
