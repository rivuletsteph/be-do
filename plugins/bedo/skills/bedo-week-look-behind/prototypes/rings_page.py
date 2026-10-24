import json, sys
DAY=sys.argv[1]
D=json.load(open(f'rings-{DAY}.json',encoding='utf-8'))
tpl=r'''<title>How Friday Went</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@1,9..144,500&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* concentric rings out from the center, one per thing she tracks; they overlap freely, nothing is forced into one slice. Natural pastels on be•do's ground. */
:root{--ground:#F4EEE4;--card:#FBF8F2;--ink:#2C2620;--soft:#4A4036;--muted:#7A6E60;--rule:#E3D9CA;--track:#F1EADF;--terra:#B5603F;
--core:#A9B9D6;--core-t:#EDF0F6;--core-d:#6E83AE;--body:#A4C497;--body-t:#ECF3E8;--body-d:#6A985A;--work:#D9A98F;--work-t:#F8ECE4;--work-d:#B07155;--other:#CDBE9F;--other-t:#F4EFE3;--other-d:#9C8A66;--screen:#2C2620;
--sans:"IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;--display:"Fraunces",Georgia,serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ground:#1B1A1F;--card:#232127;--ink:#EDE4E0;--soft:#D3C8C3;--muted:#A3958F;--rule:#3A3336;--track:#29262C;--terra:#E08A7F;--screen:#EDE4E0;--core-t:#2A2E37;--body-t:#29302A;--work-t:#352C29;--other-t:#322F29;--core-d:#D3DCEF;--body-d:#CCE2C2;--work-d:#F0CDBB;--other-d:#E6DABF;color-scheme:dark}}
:root[data-theme="dark"]{--ground:#1B1A1F;--card:#232127;--ink:#EDE4E0;--soft:#D3C8C3;--muted:#A3958F;--rule:#3A3336;--track:#29262C;--terra:#E08A7F;--screen:#EDE4E0;--core-t:#2A2E37;--body-t:#29302A;--work-t:#352C29;--other-t:#322F29;--core-d:#D3DCEF;--body-d:#CCE2C2;--work-d:#F0CDBB;--other-d:#E6DABF;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased}
.wrap{max-width:640px;margin:0 auto;padding-block:28px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.eyebrow{font:500 .72rem var(--mono);color:var(--muted);letter-spacing:.06em;text-transform:uppercase;margin:0}
h1{font:500 italic clamp(2rem,8vw,2.6rem)/1.05 var(--display);color:var(--terra);margin:8px 0 0}
.sub{color:var(--soft);line-height:1.5;margin:10px 0 0;max-width:60ch}
.card{background:var(--card);border:1px solid var(--rule);border-radius:20px;padding:16px;margin-top:18px}
svg{display:block;width:100%;max-width:460px;height:auto;margin:0 auto;overflow:visible}
svg text{font-family:var(--mono);fill:var(--muted)}
svg [data-tip]{cursor:pointer}
svg [data-tip]:focus-visible{outline:none;stroke:var(--ink);stroke-width:1.5}
.tip{min-height:2.6em;text-align:center;font-size:.85rem;color:var(--soft);margin:6px 0 0}
.label{font:600 .7rem var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:22px 0 10px}
.ring{display:grid;gap:6px;padding:12px 0;border-top:1px solid var(--rule)}
.ring:first-child{border-top:0;padding-top:0}
.rh{display:flex;align-items:baseline;gap:8px}
.rh b{font-weight:600}
.rh .v{margin-left:auto;font:500 .9rem var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
.rh .v small{color:var(--muted);font-weight:400}
.kinds{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:.8rem;color:var(--soft)}
.kinds i{display:inline-block;width:12px;height:12px;box-sizing:border-box;border-radius:3px;margin-right:5px;vertical-align:-1px}
.held{font-size:.8rem;color:var(--muted);line-height:1.45}
.note{font-size:.8rem;color:var(--muted);line-height:1.45;margin:14px 0 0}
</style>
<div class="wrap">
<p class="eyebrow">the day behind · how the day went · a proposal</p>
<h1>How __DAYNAME__ went</h1>
<p class="sub">__DAY__, your waking hours. The dial starts at the top when you got up and runs 16 hours round; the night before sits in the middle. From the center out: your dawn and dusk flows, then body (food and moving), working (professional, be•do, caretaking) and other. The thin line on the outside is time on a screen. They overlap freely.</p>
<div class="card">
<svg id="dial" viewBox="-12 -12 424 424" role="img" aria-label="The day as rings, one per thing tracked"></svg>
<p class="tip" id="tip" aria-live="polite">tap a ring to see its times</p>
<p class="label">from the core outward · share of the waking day</p>
<div id="rings"></div>
<p class="note" id="note"></p>
</div>
</div>
<script>
const D = /*DATA*/;
const C = k => `var(--${k})`, hm = m => { const h = Math.floor(m / 60), r = m % 60; return h ? (r ? `${h} h ${String(r).padStart(2, "0")}` : `${h} h`) : `${r} min`; };
const clock = m => { m = Math.min(m, 1439); const h = Math.floor(m / 60), mm = m % 60; return `${h % 12 || 12}:${String(mm).padStart(2, "0")}${h < 12 ? "a" : "p"}`; };
const hhmm = iso => clock(+iso.slice(11, 13) * 60 + +iso.slice(14, 16));
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const SPAN = 960, IDEAL_BED = 480;
const morning = (D.nights || []).find(n => n.a === 0), evening = (D.nights || []).find(n => n.b === 1440 && n.a > 0);
const WAKE = morning ? morning.b : 420, BED = evening ? evening.a : Math.min(1440, WAKE + SPAN);
const CX = 200, CY = 200, pt = (r, m) => { const a = ((m - WAKE) / SPAN) * 2 * Math.PI - Math.PI / 2; return [CX + r * Math.cos(a), CY + r * Math.sin(a)]; };
const clip = ([k, a, b]) => [k, Math.max(a, WAKE), Math.min(b, WAKE + SPAN)];
const arc = (r0, r1, a, b) => { b = Math.min(b, a + SPAN - 0.1); const L = b - a > SPAN / 2 ? 1 : 0, [x0, y0] = pt(r1, a), [x1, y1] = pt(r1, b), [x2, y2] = pt(r0, b), [x3, y3] = pt(r0, a);
  return `M${x0} ${y0}A${r1} ${r1} 0 ${L} 1 ${x1} ${y1}L${x2} ${y2}A${r0} ${r0} 0 ${L} 0 ${x3} ${y3}Z`; };
const CORE = 70, R0 = 76, W = 27, GAP = 3;
const SHORT = {sleep: "sleep", flow: "flows", body: "body", work: "working", other: "other", screen: "screen"};
D.rings.forEach(r => r.short = SHORT[r.k] || r.n);
const KN = Object.fromEntries(D.rings.flatMap(r => r.kinds.map(k => [k.k, `${r.e} ${k.n}`])));
// one hue per ring; within a ring the parts differ by pattern, never by colour (24 Oct 2026)
const STY = {sleep: ["core", "solid"], flow: ["core", "dots"], eat: ["body", "solid"], move: ["body", "stripes"],
  work: ["work", "solid"], care: ["work", "stripes"], system: ["work", "dots"], other: ["other", "solid"]};
const PAT = (ring, kind) => kind === "stripes"
  ? `<pattern id="${ring}-stripes" width="3.4" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3.4" height="3.4" fill="var(--${ring}-t)"/><rect width="1.6" height="3.4" fill="var(--${ring})"/></pattern>`
  : `<pattern id="${ring}-dots" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="var(--${ring}-t)"/><circle cx="1.5" cy="1.5" r=".85" fill="var(--${ring})"/></pattern>`;
let g = `<defs>${["core-dots", "body-stripes", "work-stripes", "work-dots"].map(x => PAT(...x.split("-"))).join("")}</defs>`;
const fillOf = k => { const [ring, pat] = STY[k]; return pat === "solid" ? `var(--${ring})` : `url(#${ring}-${pat})`; };
// sleep is the core: a filled disc in the middle, not a ring (24 Oct 2026: the most important thing)
const SL = D.rings.find(r => r.k === "sleep"), FL = D.rings.find(r => r.k === "flow"), SCR = D.rings.find(r => r.k === "screen");
const RINGS = D.rings.filter(r => !["sleep", "flow", "screen"].includes(r.k));
const STEPS = () => FL.runs.map(clip).filter(([, a, b]) => b > a).forEach(([k, a, b]) => { for (let m = a; m < b; m += 5) { const [x0, y0] = pt(HOLE + 2, m + 1), [x1, y1] = pt(CORE - 2, m + 1);
  g += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" stroke="var(--core-d)" stroke-width="1.3" stroke-linecap="round" pointer-events="none"/>`; } });
const HOLE = 34;   // a small hollow at the very center, left open for now
g += `<circle cx="${CX}" cy="${CY}" r="${CORE}" fill="var(--core-t)"/>`;

Object.entries(D.win).map(([k, w]) => [k, clip([k, ...w]).slice(1)]).filter(([, [a, b]]) => b > a).forEach(([k, [a, b]]) => { const lab = `${k === "dawn" ? "🌅 the dawn flow" : "🌄 the dusk flow"} · ${clock(a)} to ${clock(b)}`;
  g += `<path d="${arc(HOLE, CORE, a, b)}" fill="url(#core-dots)" stroke="var(--core-d)" stroke-width="1" tabindex="0" data-tip="${esc(lab)}"><title>${esc(lab)}</title></path>`; });

RINGS.forEach((r, i) => {
  const a0 = R0 + i * (W + GAP), a1 = a0 + W;
  g += `<circle cx="${CX}" cy="${CY}" r="${(a0 + a1) / 2}" fill="none" stroke="var(--${r.k}-t)" stroke-width="${W}"/>`;
  r.runs.map(clip).filter(([, a, b]) => b > a).forEach(([k, a, b]) => { const lab = `${KN[k]} · ${clock(a)}–${clock(b)} · ${hm(b - a)}`;
    g += `<path d="${arc(a0, a1, a, b)}" fill="${fillOf(k)}" stroke="var(--${STY[k][0]}-d)" stroke-width="1" tabindex="0" data-tip="${esc(lab)}"><title>${esc(lab)}</title></path>`; });
});
// on a screen or not: one thin line on the outside, black or nothing (24 Oct 2026)
const SR = R0 + RINGS.length * (W + GAP) + 2, SW = 4;
g += `<circle cx="${CX}" cy="${CY}" r="${SR + SW / 2}" fill="none" stroke="var(--track)" stroke-width="${SW}"/>`;
SCR.runs.map(clip).filter(([, a, b]) => b > a).forEach(([k, a, b]) => { const lab = `📱 on a screen · ${clock(a)}–${clock(b)} · ${hm(b - a)}`;
  g += `<path d="${arc(SR, SR + SW, a, b)}" fill="var(--screen)" tabindex="0" data-tip="${esc(lab)}"><title>${esc(lab)}</title></path>`; });
const RO = SR + SW + 4;
[0, 240, 480, 720].forEach(o => { const [x, y] = pt(RO + 16, WAKE + o);
  g += `<text x="${x}" y="${y + 3.5}" text-anchor="middle" font-size="10">${o ? clock(WAKE + o) : "up " + clock(WAKE)}</text>`; });
if (BED < WAKE + SPAN) { const [x0, y0] = pt(R0 - 4, BED), [x1, y1] = pt(SR + SW + 2, BED), lab = `🛏️ in bed at ${clock(BED)}, ${hm(WAKE + SPAN - BED)} before the 16 hours were up`;
  g += `<path d="${arc(R0 - 3, SR + SW, BED, WAKE + SPAN)}" fill="var(--core-t)" opacity=".7" tabindex="0" data-tip="${esc(lab)}"><title>${esc(lab)}</title></path>`;
  g += `<line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y1}" stroke="var(--core-d)" stroke-width="1.6"/>`; }
// the night that fed this day, in the middle: hours in bed against the eight
const inbed = morning ? morning.inbed : null;
STEPS();
g += `<circle cx="${CX}" cy="${CY}" r="${HOLE}" fill="var(--card)"/>`;
if (inbed != null) g += `<text x="${CX}" y="${CY + 1}" text-anchor="middle" style="font:600 13px var(--sans);fill:var(--ink)">${hm(inbed)}</text><text x="${CX}" y="${CY + 14}" text-anchor="middle" font-size="8">in bed</text>`;
const dial = document.getElementById("dial"), tip = document.getElementById("tip");
dial.innerHTML = g;
const show = e => { const t = e.target.closest("[data-tip]"); if (t) tip.textContent = t.dataset.tip; };
dial.addEventListener("click", show); dial.addEventListener("focusin", show); dial.addEventListener("mouseover", show);
const swatch = k => { const [ring, pat] = STY[k] || ["core", "solid"];
  return `border:1px solid var(--${ring}-d);` + (pat === "solid" ? `background:var(--${ring})` : pat === "stripes"
    ? `background:repeating-linear-gradient(45deg,var(--${ring}) 0 1.4px,var(--${ring}-t) 1.4px 2.8px)`
    : `background:radial-gradient(circle,var(--${ring}) .8px,var(--${ring}-t) 1px) 0 0/3px 3px`); };
const sgn = m => (m >= 0 ? "+" : "−") + hm(Math.abs(m));
D.rings.forEach(r => { if (r.k === "sleep") { r.kinds = [{k: "sleep", n: "in bed", min: r.total, held: []}];
    r.sleepNote = (D.nights || []).map(n => n.a === 0
      ? `Last night: asleep ${hm(n.asleep)} of a ${hm(n.need)} need, ${sgn(n.asleep - n.need)}${n.met != null ? `, met at ${clock(n.met)}` : ""}; in bed ${hhmm(n.start)}–${hhmm(n.end)}.`
      : `Tonight: in bed at ${clock(n.a)}${D.window ? `, ${n.a > D.window[1] ? hm(n.a - D.window[1]) + " after" : n.a < D.window[0] ? hm(D.window[0] - n.a) + " before" : "inside"} Oura's best bedtime of ${clock(D.window[0])}–${clock(D.window[1])}` : ""}; asleep ${hm(n.asleep)}, ${sgn(n.asleep - n.need)} against the need.`).join(" ") }
  if (r.k === "flow") { const w = Object.entries(D.win); r.total = w.reduce((s, [, [a, b]]) => s + b - a, 0);
    r.kinds = [{k: "flow", n: w.map(([k, [a, b]]) => `${k} ${clock(a)}–${clock(b)}`).join(" · ") + " ·", min: r.total, held: r.kinds[0].held}]; } });
document.getElementById("rings").innerHTML = `<div class="ring"><div class="rh"><b>The waking day</b><span class="v">${hm(Math.min(BED, 1440) - WAKE)}</span></div><div class="held">Up at ${clock(WAKE)}, in bed at ${clock(BED)}. The dial is the 16 hours from getting up; the night before was ${inbed != null ? hm(inbed) : "not read"} in bed, against an ideal of 8.</div></div>` + D.rings.filter(r => r.k !== "sleep").map(r => `<div class="ring"><div class="rh"><b>${esc(r.n)}</b><span class="v">${r.total ? hm(r.total) : "—"} <small>${Math.round(100 * r.total / (Math.min(BED, 1440) - WAKE))}%</small></span></div>` +
  (r.k !== "screen" ? `<div class="kinds">${r.kinds.map(k => `<span><i style="${swatch(k.k)}"></i>${esc(k.n)} ${k.min ? hm(k.min) : "—"}</span>`).join("")}</div>` : "") +
  `<div class="held">${esc(r.sleepNote || [...new Set(r.kinds.flatMap(k => k.held))].slice(0, 6).join(" · "))}</div></div>`).join("");
document.getElementById("note").textContent = `The rings overlap, so they don't add up to 24 hours. A moment with no length (a text, a check, a flow step) is a five-minute tick. A shaded wedge at the top means you went to bed before the 16 hours were up. Food is food only, no drinks, and a meal's minutes come out of moving: sitting to eat is not moving, and making food is food. On a screen means phone, laptop or TV; a paper book isn't a screen. Each ring keeps one shade; its parts differ by pattern. Working counts what you were doing: a session that ran while you drove, ate, moved or slept isn't your work. Other is time a row covers that none of the rings above claims. Caretaking is caring for others and the home: school runs, pickups, bedtime, the kitchen. In the core, each flow is dotted from its first step to its last, with a line at every step. Awake: ${hm(D.awake)}.`;
</script>'''
name=D['day'].split()[0]
out=tpl.replace('/*DATA*/',json.dumps(D,ensure_ascii=False)).replace('__DAYNAME__',name).replace('__DAY__',D['day']).replace('<title>How Friday Went</title>',f'<title>How {name} Went</title>')
open('how-friday-went.html','w',encoding='utf-8').write(out)
