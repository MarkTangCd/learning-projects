// Reusable Monte Carlo option-pricing widget.
//
// Drop this markup into any lesson and the widget wires itself up:
//   <div class="mcp" data-mu="0.05" data-sigma="0.20"></div>
//
// Optional data-* overrides: s0, k, t, r, paths.
// It renders sliders for mu (drift) and sigma (vol), a histogram of the
// simulated terminal price cloud with the strike marked, and the resulting
// Monte Carlo price next to the Black-Scholes benchmark.
//
// The teaching point it exists to make: dragging mu moves the naive price
// enormously, while the market price (BS) never moves. Later lessons reuse it
// for vega/gamma intuition, so keep the API stable.

(function () {
  'use strict';

  // --- maths ------------------------------------------------------------
  function normCdf(x) {
    // Abramowitz & Stegun 7.1.26 approximation of erf (|error| < 1.5e-7).
    const s = x < 0 ? -1 : 1;
    const z = Math.abs(x) / Math.SQRT2;
    const t = 1 / (1 + 0.3275911 * z);
    const y =
      1 -
      ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t +
        0.254829592) *
        t *
        Math.exp(-z * z);
    return 0.5 * (1 + s * y);
  }

  function bsCall(s0, k, t, r, sigma) {
    const d1 = (Math.log(s0 / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * Math.sqrt(t));
    const d2 = d1 - sigma * Math.sqrt(t);
    return s0 * normCdf(d1) - k * Math.exp(-r * t) * normCdf(d2);
  }

  // Deterministic normal draws so the widget does not flicker while dragging.
  // Box-Muller on a seeded LCG: same slider position always gives same price.
  function normals(n, seed) {
    let state = seed >>> 0;
    const rand = () => {
      state = (1664525 * state + 1013904223) >>> 0;
      return (state + 0.5) / 4294967296;
    };
    const out = new Float64Array(n);
    for (let i = 0; i < n; i += 2) {
      const u1 = rand();
      const u2 = rand();
      const rad = Math.sqrt(-2 * Math.log(u1));
      out[i] = rad * Math.cos(2 * Math.PI * u2);
      if (i + 1 < n) out[i + 1] = rad * Math.sin(2 * Math.PI * u2);
    }
    return out;
  }

  function simulate(cfg, mu, sigma, z) {
    const drift = (mu - 0.5 * sigma * sigma) * cfg.t;
    const spread = sigma * Math.sqrt(cfg.t);
    const disc = Math.exp(-cfg.r * cfg.t);
    const terminal = new Float64Array(z.length);
    let sum = 0;
    for (let i = 0; i < z.length; i++) {
      const st = cfg.s0 * Math.exp(drift + spread * z[i]);
      terminal[i] = st;
      sum += Math.max(st - cfg.k, 0);
    }
    return { terminal, price: (disc * sum) / z.length };
  }

  // --- drawing ----------------------------------------------------------
  function draw(canvas, terminal, cfg) {
    const css = getComputedStyle(document.documentElement);
    const ink = css.getPropertyValue('--ink-faint').trim() || '#888';
    const accent = css.getPropertyValue('--accent').trim() || '#b8341b';
    const good = css.getPropertyValue('--good').trim() || '#1a7a4c';

    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // Fixed x-window so the cloud visibly SLIDES when mu changes.
    const lo = 0;
    const hi = cfg.s0 * 3;
    const bins = 70;
    const counts = new Array(bins).fill(0);
    for (let i = 0; i < terminal.length; i++) {
      const b = Math.floor(((terminal[i] - lo) / (hi - lo)) * bins);
      if (b >= 0 && b < bins) counts[b]++;
    }
    const peak = Math.max(...counts, 1);
    const bw = w / bins;
    const xOf = (p) => ((p - lo) / (hi - lo)) * w;

    for (let b = 0; b < bins; b++) {
      const barH = (counts[b] / peak) * (h - 22);
      const x = b * bw;
      // In-the-money region (S_T > K) is where the option pays.
      ctx.fillStyle = lo + ((b + 0.5) / bins) * (hi - lo) > cfg.k ? good : ink;
      ctx.globalAlpha = lo + ((b + 0.5) / bins) * (hi - lo) > cfg.k ? 0.75 : 0.3;
      ctx.fillRect(x, h - 18 - barH, Math.max(bw - 1, 1), barH);
    }
    ctx.globalAlpha = 1;

    // Strike line.
    ctx.strokeStyle = accent;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(xOf(cfg.k), 0);
    ctx.lineTo(xOf(cfg.k), h - 18);
    ctx.stroke();
    ctx.fillStyle = accent;
    ctx.font = '600 11px -apple-system, system-ui, sans-serif';
    ctx.fillText('K = ' + cfg.k, xOf(cfg.k) + 5, 12);

    // Axis.
    ctx.strokeStyle = ink;
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    ctx.moveTo(0, h - 18);
    ctx.lineTo(w, h - 18);
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.fillStyle = ink;
    ctx.font = '11px -apple-system, system-ui, sans-serif';
    ctx.fillText('0', 2, h - 5);
    ctx.fillText('S_T at expiry', w / 2 - 35, h - 5);
    ctx.fillText(String(hi), w - 26, h - 5);
  }

  // --- widget -----------------------------------------------------------
  function build(el) {
    const cfg = {
      s0: Number(el.dataset.s0 || 100),
      k: Number(el.dataset.k || 100),
      t: Number(el.dataset.t || 1),
      r: Number(el.dataset.r || 0.05),
      paths: Number(el.dataset.paths || 40000),
    };
    const z = normals(cfg.paths, 20260811);
    const bs = bsCall(cfg.s0, cfg.k, cfg.t, cfg.r, Number(el.dataset.sigma || 0.2));

    el.innerHTML = `
      <div class="mcp-head">蒙特卡洛定价台 · S₀=${cfg.s0} · K=${cfg.k} · T=${cfg.t}年 · r=${(cfg.r * 100).toFixed(0)}%</div>
      <canvas class="mcp-canvas"></canvas>
      <div class="mcp-row">
        <label>μ 我对股票的收益预测<b class="mcp-mu"></b></label>
        <input class="mcp-mu-in" type="range" min="-30" max="40" step="1" value="${Math.round(Number(el.dataset.mu || 0.05) * 100)}">
      </div>
      <div class="mcp-row">
        <label>σ 波动率<b class="mcp-sig"></b></label>
        <input class="mcp-sig-in" type="range" min="5" max="60" step="1" value="${Math.round(Number(el.dataset.sigma || 0.2) * 100)}">
      </div>
      <div class="mcp-out">
        <div class="mcp-cell"><span>我算出的价格</span><b class="mcp-price"></b></div>
        <div class="mcp-cell"><span>市场实际价格</span><b class="mcp-bs"></b></div>
        <div class="mcp-cell"><span>偏差</span><b class="mcp-gap"></b></div>
      </div>
      <div class="mcp-note"></div>`;

    const canvas = el.querySelector('.mcp-canvas');
    const muIn = el.querySelector('.mcp-mu-in');
    const sigIn = el.querySelector('.mcp-sig-in');

    function render() {
      const mu = Number(muIn.value) / 100;
      const sigma = Number(sigIn.value) / 100;
      const { terminal, price } = simulate(cfg, mu, sigma, z);
      const market = bsCall(cfg.s0, cfg.k, cfg.t, cfg.r, sigma);
      const gap = price / market - 1;

      el.querySelector('.mcp-mu').textContent = (mu * 100).toFixed(0) + '%';
      el.querySelector('.mcp-sig').textContent = (sigma * 100).toFixed(0) + '%';
      el.querySelector('.mcp-price').textContent = price.toFixed(2);
      el.querySelector('.mcp-bs').textContent = market.toFixed(2);
      const gapEl = el.querySelector('.mcp-gap');
      gapEl.textContent = (gap >= 0 ? '+' : '') + (gap * 100).toFixed(0) + '%';
      gapEl.className = 'mcp-gap ' + (Math.abs(gap) < 0.02 ? 'ok' : 'bad');

      const note = el.querySelector('.mcp-note');
      if (Math.abs(mu - cfg.r) < 0.005) {
        note.textContent = '⟵ μ 正好等于无风险利率 r。偏差归零。为什么偏偏是这个值?';
        note.className = 'mcp-note hit';
      } else if (mu > cfg.r) {
        note.textContent = '我比市场看涨 → 我算出的价格高于市场。谁错了?';
        note.className = 'mcp-note';
      } else {
        note.textContent = '我比市场看跌 → 我算出的价格低于市场。谁错了?';
        note.className = 'mcp-note';
      }
      draw(canvas, terminal, cfg);
    }

    muIn.addEventListener('input', render);
    sigIn.addEventListener('input', render);
    window.addEventListener('resize', render);
    render();
    void bs;
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.mcp').forEach(build);
  });
})();
