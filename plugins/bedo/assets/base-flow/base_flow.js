// base flow — where am I at, going into the day.
//
// One number for the morning, made like Oura's readiness: three contributors carried from the day
// before, in equal thirds, 0–100 each.
//   body           this morning's readiness (nutrition from the day before folds in here later)
//   balance        the day before's wellness wheel: how evenly its eight shared the day
//   effectiveness  the day before: on a family day, intentions met; on a work day, half work-work
//                  against the work target and half intentions
// The states follow Oura's: 85 and up optimal, 70 to 84 good, under 70 pay attention.
//
// Each contributor has its own colour (teal body, ochre balance, brick effectiveness), and the ring
// is drawn as their three shares of the number, so the ring shows what made it.
//
// Usage:  BedoBaseFlow.render(element, {
//           parts: [{name, note, value, key}, ...],  // key: body | balance | effectiveness (sets the colour)
//           week:  [{label, value}, ...],            // optional: the last seven mornings, drawn as a line
//           today: 5                                 // optional: index of this morning in week
//         })
// The number is computed from the parts unless data.value is given. Styles: base_flow.css.

const BedoBaseFlow = (() => {
  const clamp = v => Math.max(0, Math.min(100, Math.round(v)));
  const score = parts => clamp(parts.reduce((a, p) => a + p.value, 0) / parts.length);
  const state = v => v >= 85 ? "optimal" : v >= 70 ? "good" : "pay attention";
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
  const COLOR = {body: "var(--bf-body)", balance: "var(--bf-balance)", effectiveness: "var(--bf-effect)"};
  const ORDER = ["body", "balance", "effectiveness"];
  const colorOf = (p, i) => COLOR[p.key || p.name] || COLOR[ORDER[i % 3]];

  // the ring: each contributor's share of the number, in its own colour, end to end from the top
  function ring(v, parts) {
    const r = 43, c = 2 * Math.PI * r, gap = 2.5, n = parts.length;
    let at = 0, arcs = "";
    parts.forEach((p, i) => {
      const len = c * (clamp(p.value) / n) / 100;
      if (len > gap) arcs += `<circle cx="54" cy="54" r="${r}" fill="none" stroke="${colorOf(p, i)}" stroke-width="9" ` +
        `stroke-dasharray="${(len - gap).toFixed(1)} ${c.toFixed(1)}" stroke-dashoffset="${(-at).toFixed(1)}" transform="rotate(-90 54 54)"/>`;
      at += len;
    });
    return `<svg class="bf-ring" viewBox="0 0 108 108" role="img" aria-label="base flow ${v}, ${state(v)}">` +
      `<circle class="bf-track" cx="54" cy="54" r="${r}" fill="none" stroke-width="9"/>${arcs}` +
      `<text class="bf-num" x="54" y="63" text-anchor="middle">${v}</text></svg>`;
  }

  // the week: a smooth line through the mornings, a soft fill under it, this morning marked
  function week(w, today) {
    const W = 350, H = 64, pad = 8, n = w.length, lo = Math.min(50, ...w.map(d => d.value));
    const x = i => (i + 0.5) / n * W, y = v => pad + (100 - v) / (100 - lo) * (H - 2 * pad);
    const P = w.map((d, i) => [x(i), y(d.value)]);
    let line = `M${P[0][0].toFixed(1)} ${P[0][1].toFixed(1)}`;
    for (let i = 0; i < n - 1; i++) {                      // Catmull-Rom through every point, as cubic Béziers
      const p0 = P[i - 1] || P[i], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2] || p2;
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      line += ` C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    const area = `${line} L${P[n - 1][0].toFixed(1)} ${H} L${P[0][0].toFixed(1)} ${H} Z`;
    return `<svg class="bf-week" viewBox="0 0 ${W} ${H}" role="img" aria-label="the last ${n} mornings">` +
      `<path class="bf-area" d="${area}"/><path class="bf-line" d="${line}"/>` +
      P.map((p, i) => `<circle class="bf-pt${i === today ? " bf-on" : ""}" cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="${i === today ? 5 : 3.5}"><title>${esc(w[i].label)} ${w[i].value}</title></circle>`).join("") +
      `</svg><div class="bf-days" style="grid-template-columns:repeat(${n},minmax(0,1fr))">` +
      w.map((d, i) => `<span class="${i === today ? "bf-on" : ""}">${esc(d.label)} ${d.value}</span>`).join("") + `</div>`;
  }

  function html(d) {
    const v = d.value != null ? clamp(d.value) : score(d.parts);
    const rows = d.parts.map((p, i) =>
      `<div class="bf-row" style="--bf-c:${colorOf(p, i)}"><div><b>${esc(p.name)}</b>${p.note ? `<small>${esc(p.note)}</small>` : ""}</div>` +
      `<span class="bf-bar"><i style="width:${clamp(p.value)}%"></i></span><span class="bf-val">${clamp(p.value)}</span></div>`).join("");
    return `<div class="bf-card"><div class="bf-dial">${ring(v, d.parts)}<div class="bf-state">base flow · <b>${state(v)}</b></div></div>` +
      `<div class="bf-parts"><p class="bf-label">going into the day</p>${rows}${d.week && d.week.length > 1 ? week(d.week, d.today) : ""}</div></div>`;
  }

  function render(el, d) { el.innerHTML = html(d); }

  return {render, html, score, state};
})();

if (typeof module !== "undefined") module.exports = BedoBaseFlow;
