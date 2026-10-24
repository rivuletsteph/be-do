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
--flow:#B4C3DE;--flow-t:#EDF0F6;--flow-d:#6E83AE;
--food:#86AF77;--move:#BCD6AF;--body-t:#ECF3E8;--body-d:#5F8D50;
--work:#C98A6B;--care:#DFB09A;--system:#EED3C4;--work-t:#F8ECE4;--work-d:#A8664A;
--other:#CDBE9F;--other-t:#F4EFE3;--other-d:#9C8A66;--screen:#2C2620;--screen-t:#ECE5DA;
--sans:"IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;--display:"Fraunces",Georgia,serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ground:#1B1A1F;--card:#232127;--ink:#EDE4E0;--soft:#D3C8C3;--muted:#A3958F;--rule:#3A3336;--terra:#E08A7F;
--flow-t:#2A2E37;--flow-d:#D3DCEF;--body-t:#29302A;--body-d:#CCE2C2;--work-t:#352C29;--work-d:#F0CDBB;--other-t:#322F29;--other-d:#E6DABF;--screen:#EDE4E0;--screen-t:#2E2A30;color-scheme:dark}}
:root[data-theme="dark"]{--ground:#1B1A1F;--card:#232127;--ink:#EDE4E0;--soft:#D3C8C3;--muted:#A3958F;--rule:#3A3336;--terra:#E08A7F;
--flow-t:#2A2E37;--flow-d:#D3DCEF;--body-t:#29302A;--body-d:#CCE2C2;--work-t:#352C29;--work-d:#F0CDBB;--other-t:#322F29;--other-d:#E6DABF;--screen:#EDE4E0;--screen-t:#2E2A30;color-scheme:dark}
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
<p class="sub">__DAY__, your waking hours as a rainbow: up on the left, the middle of the day at the top, the evening down on the right. From the inside out: your dawn and dusk flows, body, working, and everything else; the thin line on the outside is time on a screen. Tap any piece to see what it was.</p>
<div class="card">
<svg id="dial" viewBox="0 0 400 330" role="img" aria-label="The waking day as concentric arcs"></svg>
<div class="tip" id="tip" aria-live="polite">Tap a piece of the rainbow.</div>
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
const ang = m => (-90 - SWEEP / 2 + (Math.min(Math.max(m, WAKE), END) - WAKE) / SPAN * SWEEP) * Math.PI / 180;
const pt = (r, m) => [CX + r * Math.cos(ang(m)), CY + r * Math.sin(ang(m))];
const band = (r0, r1, a, b) => { const L = (b - a) / SPAN * SWEEP > 180 ? 1 : 0, [x0, y0] = pt(r1, a), [x1, y1] = pt(r1, b), [x2, y2] = pt(r0, b), [x3, y3] = pt(r0, a);
  return `M${x0} ${y0}A${r1} ${r1} 0 ${L} 1 ${x1} ${y1}L${x2} ${y2}A${r0} ${r0} 0 ${L} 0 ${x3} ${y3}Z`; };
const clip = ([k, a, b, t]) => [k, Math.max(a, WAKE), Math.min(b, END), t || []];
const R = Object.fromEntries(D.rings.map(r => [r.k, r]));
// bands from the inside out; parts of a band are shades of its colour (24 Oct 2026: shades, not patterns)
const BANDS = [
  {k: "flow", n: "Flows", fam: "flow", parts: {flow: ["flow", "a flow step"]}},
  {k: "body", n: "Body", fam: "body", parts: {eat: ["food", "food"], move: ["move", "moving"]}},
  {k: "work", n: "Working", fam: "work", parts: {work: ["work", "professional work"], care: ["care", "caretaking"], system: ["system", "be•do"]}},
  {k: "other", n: "Other", fam: "other", parts: {other: ["other", "everything else"]}}];
const HOLE = 52, W = 30, GAP = 3, R0 = 58;
let g = "", tips = [];
const piece = (d, fill, stroke, tip) => { tips.push(tip); return `<path d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="1" tabindex="0" data-i="${tips.length - 1}" data-tip="1"/>`; };
BANDS.forEach((B, i) => {
  const r0 = R0 + i * (W + GAP), r1 = r0 + W;
  g += `<path d="${band(r0, r1, WAKE, END)}" fill="var(--${B.fam}-t)"/>`;
  if (B.k === "flow") Object.entries(D.win).forEach(([k, w]) => { const [, a, b] = clip([k, ...w]); if (b <= a) return;
    g += piece(band(r0, r1, a, b), "var(--flow-t)", "var(--flow-d)", `<b>${k === "dawn" ? "🌅 The dawn flow" : "🌄 The dusk flow"}</b> · ${clock(a)}–${clock(b)}<br>${esc((R.flow.kinds[0].held || []).join(" · "))}`); });
  (R[B.k] || {runs: []}).runs.map(clip).filter(([, a, b]) => b - a >= 2).forEach(([k, a, b, t]) => {
    const [col, nm] = B.parts[k] || [B.fam, k];
    if (B.k === "flow") { for (let m = a; m < b; m += 5) { const [x0, y0] = pt(r0 + 2, m + 1), [x1, y1] = pt(r1 - 2, m + 1); g += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" stroke="var(--flow-d)" stroke-width="1.4" stroke-linecap="round" pointer-events="none"/>`; } return; }
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
[0, 240, 480, 720, 960].forEach(o => { const [x, y] = pt(SR + SW + 15, WAKE + o);
  g += `<text x="${x}" y="${y + 3.5}" text-anchor="middle" font-size="10">${o === 0 ? "up " + clock(WAKE) : clock(WAKE + o)}</text>`; });
// the night that fed the day, under the arch
const inbed = morning ? morning.inbed : null;
if (inbed != null) g += `<text x="${CX}" y="${CY - 6}" text-anchor="middle" style="font:600 17px var(--sans);fill:var(--ink)">${hm(inbed)}</text><text x="${CX}" y="${CY + 10}" text-anchor="middle" font-size="9">in bed last night</text><text x="${CX}" y="${CY + 22}" text-anchor="middle" font-size="9">of 8 h</text>`;
const dial = document.getElementById("dial"), tip = document.getElementById("tip");
dial.innerHTML = g;
const show = e => { const t = e.target.closest("[data-tip]"); if (!t) return; dial.querySelectorAll(".on").forEach(x => x.classList.remove("on")); t.classList.add("on"); tip.innerHTML = tips[+t.dataset.i]; };
dial.addEventListener("click", show); dial.addEventListener("focusin", show);
// the list
const AW = Math.min(BED, 1440) - WAKE;
const tot = B => B.k === "flow" ? Object.values(D.win).reduce((s, [a, b]) => s + Math.max(0, Math.min(b, END) - Math.max(a, WAKE)), 0) : (R[B.k] || {}).total || 0;
document.getElementById("rings").innerHTML = `<div class="ring"><div class="rh"><b>The waking day</b><span class="v">${hm(AW)}</span></div><div class="held">Up at ${clock(WAKE)}, in bed at ${clock(BED)}. ${inbed != null ? hm(inbed) : "Unknown"} in bed the night before, against an ideal of 8.</div></div>` +
  BANDS.map(B => { const r = R[B.k] || {kinds: []}, t = tot(B);
    const kinds = B.k === "flow" ? Object.entries(D.win).map(([k, [a, b]]) => `<span><i style="background:var(--flow-t);border:1px solid var(--flow-d)"></i>${k} ${clock(a)}–${clock(b)}</span>`).join("")
      : r.kinds.map(k => { const [col, nm] = B.parts[k.k] || [B.fam, k.n]; return `<span><i style="background:${C(col)};border:1px solid var(--${B.fam}-d)"></i>${esc(nm)} ${k.min ? hm(k.min) : "—"}</span>`; }).join("");
    return `<div class="ring"><div class="rh"><b>${B.n}</b><span class="v">${t ? hm(t) : "—"} <small>${Math.round(100 * t / AW)}%</small></span></div><div class="kinds">${kinds}</div></div>`; }).join("") +
  `<div class="ring"><div class="rh"><b>On a screen</b><span class="v">${hm(R.screen ? R.screen.total : 0)} <small>${Math.round(100 * (R.screen ? R.screen.total : 0) / AW)}%</small></span></div><div class="held">phone, laptop or TV; a paper book isn't a screen</div></div>`;
document.getElementById("note").textContent = "The bands overlap, so they don't add up to the waking day. Working counts what you were doing: a session that ran while you drove, ate, moved or slept isn't your work. A meal is not moving. Food is food only, no drinks. A moment with no length (a text, a check, a flow step) is a five-minute tick.";
</script>'''
out = tpl.replace('/*DATA*/', json.dumps(D, ensure_ascii=False)).replace('__NAME__', name).replace('__DAY__', D['day'])
open('how-friday-went.html', 'w', encoding='utf-8').write(out)
