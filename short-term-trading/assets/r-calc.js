// Reusable R calculator: turns a trade plan (entry / stop / target / fees)
// into R numbers, so the learner sees fee drag in units of risk.
// Markup contract:
//   <div class="rcalc" data-entry="60000" data-stop="59700" data-target="60600"
//        data-fee="5" data-risk="10"></div>
// data-fee = fee in basis points PER SIDE (Binance taker 5, maker 2).
// data-risk = planned loss (1R) in USD.

const RCALC_FIELDS = [
  ['side', 'Side', 'select'],
  ['entry', 'Entry', 'number'],
  ['stop', 'Stop', 'number'],
  ['target', 'Target', 'number'],
  ['fee', 'Fee bps / side', 'number'],
  ['risk', '1R in USD', 'number'],
];

function fmt(x, digits = 2) {
  if (!Number.isFinite(x)) return '—';
  return x.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function renderCalc(root) {
  const d = root.dataset;
  const defaults = { side: 'long', entry: d.entry || 60000, stop: d.stop || 59700,
                     target: d.target || 60600, fee: d.fee || 5, risk: d.risk || 10 };
  const inputs = RCALC_FIELDS.map(([k, label, type]) => {
    const ctl = type === 'select'
      ? `<select name="${k}"><option value="long">Long</option><option value="short">Short</option></select>`
      : `<input name="${k}" type="number" step="any" value="${defaults[k]}">`;
    return `<div><label>${label}</label>${ctl}</div>`;
  }).join('');
  root.innerHTML = `
    <div class="title">R 计算器 —— 改任何一个数字，看 R 怎么变</div>
    <div class="grid">${inputs}</div>
    <div class="out">
      <div>止损距离<b data-o="stopPct"></b></div>
      <div>计划 R（毛）<b data-o="plannedR"></b></div>
      <div>名义仓位 USD<b data-o="notional"></b></div>
      <div>来回手续费 USD<b data-o="feeUsd"></b></div>
      <div>手续费占 R<b data-o="feeR"></b></div>
      <div>到目标净 R<b data-o="netWin"></b></div>
      <div>被止损净 R<b data-o="netLoss"></b></div>
    </div>
    <div class="note" data-o="note"></div>`;
  root.addEventListener('input', () => updateCalc(root));
  updateCalc(root);
}

function updateCalc(root) {
  const v = (k) => Number(root.querySelector(`[name="${k}"]`).value);
  const side = root.querySelector('[name="side"]').value;
  const dir = side === 'long' ? 1 : -1;
  const entry = v('entry'), stop = v('stop'), target = v('target');
  const feeBps = v('fee'), risk = v('risk');
  const stopDist = (entry - stop) * dir;            // positive when stop is on the right side
  const targetDist = (target - entry) * dir;
  const stopPct = stopDist / entry;
  const plannedR = targetDist / stopDist;
  const qty = risk / stopDist;                      // units of the asset
  const notional = qty * entry;
  const feeUsd = notional * (feeBps / 1e4) * 2;     // round trip, taker both sides
  const feeR = feeUsd / risk;                       // = 2 * fee / stopPct
  const valid = stopDist > 0 && targetDist > 0 && risk > 0;
  const set = (k, text, cls) => {
    const el = root.querySelector(`[data-o="${k}"]`);
    el.textContent = text; el.className = cls || '';
  };
  if (!valid) {
    ['stopPct','plannedR','notional','feeUsd','feeR','netWin','netLoss'].forEach((k) => set(k, '—'));
    set('note', '止损必须在进场价的亏损一侧，目标必须在盈利一侧。');
    return;
  }
  set('stopPct', fmt(stopPct * 100, 3) + ' %');
  set('plannedR', fmt(plannedR) + ' R');
  set('notional', '$' + fmt(notional, 0));
  set('feeUsd', '$' + fmt(feeUsd));
  set('feeR', fmt(feeR) + ' R', feeR >= 0.25 ? 'bad' : 'ok');
  set('netWin', (plannedR - feeR >= 0 ? '+' : '') + fmt(plannedR - feeR) + ' R', plannedR - feeR > 0 ? 'ok' : 'bad');
  set('netLoss', '−' + fmt(1 + feeR) + ' R', 'bad');
  set('note', `仓位 = 1R ÷ 止损距离 = ${fmt(risk)} ÷ ${fmt(stopDist, 2)} = ${fmt(qty, 4)} 个。`
    + ` 手续费按名义收（$${fmt(notional, 0)} × ${feeBps} bp × 2），换算成 R 就是 2 × 费率 ÷ 止损距离%。`
    + ` 止损越近，手续费占 R 越大——这就是剥头皮的税。`);
}

document.querySelectorAll('.rcalc').forEach(renderCalc);
