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
// Usage:  BedoBaseFlow.render(element, {
//           parts: [{name, note, value}, ...],     // the contributors, in the order shown
//           week:  [{label, value}, ...],          // optional: the last seven mornings
//           today: 5                               // optional: index of this morning in week
//         })
// The number is computed from the parts unless data.value is given. Styles: base_flow.css.

const BedoBaseFlow = (() => {
  const clamp = v => Math.max(0, Math.min(100, Math.round(v)));
  const score = parts => clamp(parts.reduce((a, p) => a + p.value, 0) / parts.length);
  const state = v => v >= 85 ? "optimal" : v >= 70 ? "good" : "pay attention";
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));

  function ring(v) {
    const r = 42, c = 2 * Math.PI * r;
    return `<svg class="bf-ring" viewBox="0 0 104 104" role="img" aria-label="base flow ${v}, ${state(v)}">` +
      `<circle class="bf-track" cx="52" cy="52" r="${r}" fill="none" stroke-width="8"/>` +
      `<circle class="bf-arc" cx="52" cy="52" r="${r}" fill="none" stroke-width="8" stroke-linecap="round" ` +
      `stroke-dasharray="${(c * v / 100).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 52 52)"/>` +
      `<text class="bf-num" x="52" y="61" text-anchor="middle">${v}</text></svg>`;
  }

  function html(d) {
    const v = d.value != null ? clamp(d.value) : score(d.parts);
    const rows = d.parts.map(p =>
      `<div class="bf-row"><div><b>${esc(p.name)}</b>${p.note ? `<small>${esc(p.note)}</small>` : ""}</div>` +
      `<span class="bf-bar"><i style="width:${clamp(p.value)}%"></i></span><span class="bf-val">${clamp(p.value)}</span></div>`).join("");
    let week = "";
    if (d.week && d.week.length) {
      const lo = Math.min(50, ...d.week.map(w => w.value));            // the strip starts at 50, or lower if a morning was
      const h = w => Math.max(6, (w.value - lo) / (100 - lo) * 100);
      week = `<div class="bf-week" aria-hidden="true">${d.week.map((w, i) =>
          `<i class="${i === d.today ? "bf-on" : ""}" style="height:${h(w).toFixed(0)}%" title="${esc(w.label)} ${w.value}"></i>`).join("")}</div>` +
        `<div class="bf-days">${d.week.map((w, i) => `<span class="${i === d.today ? "bf-on" : ""}">${esc(w.label)} ${w.value}</span>`).join("")}</div>`;
    }
    return `<div class="bf-card"><div class="bf-dial">${ring(v)}<div class="bf-state">base flow · <b>${state(v)}</b></div></div>` +
      `<div class="bf-parts"><p class="bf-label">going into the day</p>${rows}${week}</div></div>`;
  }

  function render(el, d) { el.innerHTML = html(d); }

  return {render, html, score, state};
})();

if (typeof module !== "undefined") module.exports = BedoBaseFlow;
