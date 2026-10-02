// Energy ledger calculator. Renders into #tdee-calc.
// BMR: Mifflin-St Jeor (Am J Clin Nutr 1990). Running METs: 2024 Adult Compendium.
// Exercise compensation factor from Pontzer & Trexler 2026 review (~46% of expected gain lost to compensation).
(function () {
  const root = document.getElementById('tdee-calc');
  if (!root) return;

  // [min speed km/h, MET] from the 2024 Compendium (walking + running rows), nearest lower bound wins.
  const MET_TABLE = [[0, 2.5], [4.0, 3.0], [5.0, 3.5], [5.6, 4.3], [6.4, 6.5], [7.2, 7.8], [8.0, 8.5], [8.9, 9.0], [9.7, 9.3], [10.8, 10.5], [12.9, 12.0]];
  const COMPENSATION = 0.46;
  const INTAKE_FLOOR = 1500; // NHC obesity guideline: men 1200~1500 kcal/day is the lowest sensible band

  const fields = [
    ['weight', '体重 kg', 81.5], ['height', '身高 cm', 173], ['age', '年龄', 34],
    ['speed', '跑步机速度 km/h', 8], ['minutes', '每次分钟', 70], ['sessions', '每周次数', 4],
  ];

  root.innerHTML = `
    <div class="grid">
      ${fields.map(([k, l, v]) => `<div><label for="f-${k}">${l}</label><input id="f-${k}" type="number" step="any" value="${v}"></div>`).join('')}
      <div><label for="f-sex">性别</label><select id="f-sex"><option value="m">男</option><option value="f">女</option></select></div>
      <div><label for="f-base">非运动日活动量</label><select id="f-base">
        <option value="1.2">久坐（程序员/交易员）</option><option value="1.3">轻活动（常走动）</option></select></div>
    </div>
    <p style="margin:0.75rem 0 0"><button class="btn" id="f-go">算一算</button></p>
    <div class="result" id="f-out"></div>`;

  const val = (k) => Number(document.getElementById(`f-${k}`).value);

  function metFor(speed) {
    let met = MET_TABLE[0][1];
    MET_TABLE.forEach(([min, m]) => { if (speed >= min) met = m; });
    return met;
  }

  function compute() {
    const w = val('weight'), h = val('height'), a = val('age');
    const sexTerm = document.getElementById('f-sex').value === 'm' ? 5 : -161;
    const bmr = 9.99 * w + 6.25 * h - 4.92 * a + sexTerm;
    const base = bmr * Number(document.getElementById('f-base').value);
    const met = metFor(val('speed'));
    const perSession = (met - 1) * w * val('minutes') / 60; // net of resting cost
    const weekly = perSession * val('sessions');
    const dailyAvgRaw = weekly / 7;
    const dailyAvgAdj = dailyAvgRaw * (1 - COMPENSATION);
    const tdeeLow = base + dailyAvgAdj;
    const tdeeHigh = base + dailyAvgRaw;
    const target = [Math.max(INTAKE_FLOOR, tdeeLow - 1000), Math.max(INTAKE_FLOOR, tdeeLow - 500)];
    return { bmr, base, met, perSession, dailyAvgRaw, dailyAvgAdj, tdeeLow, tdeeHigh, target };
  }

  function stat(label, value, hi) {
    return `<div class="stat${hi ? ' hi' : ''}"><span class="v">${value}</span><span class="l">${label}</span></div>`;
  }

  function render() {
    const r = compute();
    const n = (x) => Math.round(x).toLocaleString('zh-CN');
    document.getElementById('f-out').innerHTML = [
      stat('基础代谢 BMR（kcal/天）', n(r.bmr)),
      stat('不跑步时的每日消耗', n(r.base)),
      stat(`单次跑步净消耗（${r.met} MET）`, n(r.perSession)),
      stat('跑步摊到每天（纸面）', n(r.dailyAvgRaw)),
      stat('跑步摊到每天（扣除补偿后）', n(r.dailyAvgAdj)),
      stat('真实 TDEE 可能区间', `${n(r.tdeeLow)}~${n(r.tdeeHigh)}`, true),
      stat('痛风安全减重的摄入目标', `${n(r.target[0])}~${n(r.target[1])}`, true),
    ].join('');
  }

  document.getElementById('f-go').addEventListener('click', render);
  render();
})();
