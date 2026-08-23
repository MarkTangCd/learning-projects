// Reusable triage scorecard for strategy quick-screening.
// Markup contract:
//   <div class="scorecard" data-strategy="Strategy name">
//     <div class="sc-title">…</div>
//     <div class="sc-row sc-gate" data-id="G1" data-name="规则完整">
//       <div class="sc-label"><span class="sc-id">G1</span>规则完整
//         <span class="sc-desc">…rubric hint…</span></div>
//     </div>                                  <!-- gates get ✗/✓ buttons -->
//     <div class="sc-row sc-item" data-id="S1" data-name="经济逻辑">…</div>
//                                             <!-- items get 0/1/2 buttons -->
//     <textarea class="sc-notes" placeholder="…"></textarea>
//     <div class="sc-verdict"></div>
//     <button class="sc-copy">复制判决记录 (Markdown)</button>
//   </div>
// Verdict: any gate ✗ → 淘汰; else total ≥8 复现, 5–7 观察池, ≤4 淘汰.

const VERDICTS = [
  { min: 8, label: '复现', cls: 'go' },
  { min: 5, label: '观察池', cls: 'hold' },
  { min: 0, label: '淘汰', cls: 'kill' },
];

document.querySelectorAll('.scorecard').forEach(initScorecard);

function initScorecard(card) {
  card.querySelectorAll('.sc-row').forEach((row) => {
    const labels = row.classList.contains('sc-gate') ? ['✗', '✓'] : ['0', '1', '2'];
    const btns = document.createElement('div');
    btns.className = 'sc-btns';
    labels.forEach((label) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.addEventListener('click', () => {
        [...btns.children].forEach((x) => x.classList.remove('on'));
        b.classList.add('on');
        row.dataset.value = label;
        update(card);
      });
      btns.appendChild(b);
    });
    row.appendChild(btns);
  });
  const copyBtn = card.querySelector('.sc-copy');
  if (copyBtn) copyBtn.addEventListener('click', () => copyRecord(card, copyBtn));
}

function readState(card) {
  const gates = [...card.querySelectorAll('.sc-gate')];
  const items = [...card.querySelectorAll('.sc-item')];
  const answered = [...gates, ...items].filter((r) => r.dataset.value !== undefined);
  return {
    gates,
    items,
    answered,
    total: gates.length + items.length,
    killed: gates.some((g) => g.dataset.value === '✗'),
    score: items.reduce((sum, r) => sum + (Number(r.dataset.value) || 0), 0),
    maxScore: items.length * 2,
  };
}

function verdictOf(state) {
  if (state.killed) return { label: '淘汰', cls: 'kill', why: '硬门未过' };
  const v = VERDICTS.find((x) => state.score >= x.min);
  return { label: v.label, cls: v.cls, why: `${state.score}/${state.maxScore} 分` };
}

function update(card) {
  const out = card.querySelector('.sc-verdict');
  if (!out) return;
  const state = readState(card);
  if (!state.killed && state.answered.length < state.total) {
    out.textContent = `已答 ${state.answered.length}/${state.total} 项 — 当前 ${state.score} 分`;
    out.className = 'sc-verdict show';
    return;
  }
  const v = verdictOf(state);
  out.textContent = `判决:${v.label}(${v.why})`;
  out.className = `sc-verdict show ${v.cls}`;
}

function copyRecord(card, btn) {
  const state = readState(card);
  const v = verdictOf(state);
  const date = new Date().toISOString().slice(0, 10);
  const fmt = (r) => `${r.dataset.id} ${r.dataset.name} ${r.dataset.value ?? '—'}`;
  const notes = card.querySelector('.sc-notes')?.value.trim() || '(无)';
  const md = [
    `## ${card.dataset.strategy || '未命名策略'} — ${date}`,
    `- 判决: ${v.label}(${v.why})`,
    `- 硬门: ${state.gates.map(fmt).join(' · ')}`,
    `- 评分: ${state.items.map(fmt).join(' · ')}`,
    `- 备注: ${notes}`,
    '',
  ].join('\n');
  const done = () => {
    const old = btn.textContent;
    btn.textContent = '已复制 ✓';
    setTimeout(() => (btn.textContent = old), 1500);
  };
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(md).then(done);
  } else {
    const ta = document.createElement('textarea');
    ta.value = md;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    ta.remove();
    done();
  }
}
