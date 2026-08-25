// Reusable scatter-plot component. Renders an inline SVG from data attributes.
// No dependencies, no network. Axes auto-scale to the data.
//
// Markup contract:
//   <div class="scatter"
//        data-points="1,10.1 2,10.0 3,10.4"
//        data-title="A · 信号 vs 收益"
//        data-x="信号强度" data-y="次日收益 (%)"
//        data-note="r = 0.95"
//        data-fit="1">              <!-- optional: draw least-squares line -->
//   </div>
// Wrap several in <div class="scatter-grid"> for a responsive grid.

const SC_W = 300;
const SC_H = 200;
const SC_PAD = { l: 42, r: 12, t: 12, b: 32 };

const scParse = (str) =>
  str
    .trim()
    .split(/\s+/)
    .map((pair) => pair.split(',').map(Number));

const scStats = (values) => {
  const n = values.length;
  const mean = values.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / n);
  return { mean, sd };
};

const scPearson = (points) => {
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const sx = scStats(xs);
  const sy = scStats(ys);
  const sum = points.reduce(
    (acc, [x, y]) => acc + ((x - sx.mean) / sx.sd) * ((y - sy.mean) / sy.sd),
    0
  );
  return { r: sum / points.length, sx, sy };
};

// Pad a [min, max] range by 8% so points never sit on the axis.
const scRange = (values) => {
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const pad = (hi - lo) * 0.08 || 1;
  return [lo - pad, hi + pad];
};

const scFmt = (v) => (Math.abs(v) >= 100 || Number.isInteger(v) ? String(v) : v.toFixed(1));

function scRender(el) {
  const points = scParse(el.dataset.points || '');
  if (points.length < 2) return;

  const [x0, x1] = scRange(points.map((p) => p[0]));
  const [y0, y1] = scRange(points.map((p) => p[1]));
  const px = (x) => SC_PAD.l + ((x - x0) / (x1 - x0)) * (SC_W - SC_PAD.l - SC_PAD.r);
  const py = (y) => SC_H - SC_PAD.b - ((y - y0) / (y1 - y0)) * (SC_H - SC_PAD.t - SC_PAD.b);

  const parts = [];
  // Axes
  parts.push(
    `<line x1="${SC_PAD.l}" y1="${SC_PAD.t}" x2="${SC_PAD.l}" y2="${SC_H - SC_PAD.b}" class="ax"/>`,
    `<line x1="${SC_PAD.l}" y1="${SC_H - SC_PAD.b}" x2="${SC_W - SC_PAD.r}" y2="${SC_H - SC_PAD.b}" class="ax"/>`
  );
  // Corner labels only — this is a shape-reading tool, not a measuring instrument.
  parts.push(
    `<text x="${SC_PAD.l - 6}" y="${SC_PAD.t + 4}" class="tick end">${scFmt(y1)}</text>`,
    `<text x="${SC_PAD.l - 6}" y="${SC_H - SC_PAD.b}" class="tick end">${scFmt(y0)}</text>`,
    `<text x="${SC_PAD.l}" y="${SC_H - SC_PAD.b + 15}" class="tick">${scFmt(x0)}</text>`,
    `<text x="${SC_W - SC_PAD.r}" y="${SC_H - SC_PAD.b + 15}" class="tick end">${scFmt(x1)}</text>`
  );

  if (el.dataset.fit) {
    const { r, sx, sy } = scPearson(points);
    const slope = (r * sy.sd) / sx.sd;
    const at = (x) => sy.mean + slope * (x - sx.mean);
    parts.push(`<line x1="${px(x0)}" y1="${py(at(x0))}" x2="${px(x1)}" y2="${py(at(x1))}" class="fit"/>`);
  }

  points.forEach(([x, y]) => parts.push(`<circle cx="${px(x)}" cy="${py(y)}" r="4" class="pt"/>`));

  if (el.dataset.y) {
    parts.push(
      `<text x="10" y="${(SC_H - SC_PAD.b) / 2}" class="axlabel" transform="rotate(-90 10 ${(SC_H - SC_PAD.b) / 2})">${el.dataset.y}</text>`
    );
  }
  if (el.dataset.x) {
    parts.push(
      `<text x="${(SC_PAD.l + SC_W - SC_PAD.r) / 2}" y="${SC_H - 4}" class="axlabel mid">${el.dataset.x}</text>`
    );
  }

  el.innerHTML =
    (el.dataset.title ? `<div class="sc-title">${el.dataset.title}</div>` : '') +
    `<svg viewBox="0 0 ${SC_W} ${SC_H}" role="img" aria-label="${el.dataset.title || 'scatter plot'}">${parts.join('')}</svg>` +
    (el.dataset.note ? `<div class="sc-note">${el.dataset.note}</div>` : '');
}

document.querySelectorAll('.scatter').forEach(scRender);
