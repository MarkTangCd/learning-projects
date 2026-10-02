// Reusable quiz component. Usage:
// <div class="quiz" data-quiz='{"q":"...","opts":["A","B","C"],"answer":1,"why":"..."}'></div>
// Options are shuffled on render so position never leaks the answer.
(function () {
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function render(el) {
    let data;
    try { data = JSON.parse(el.dataset.quiz); } catch (e) { return; }
    const q = document.createElement('div');
    q.className = 'q';
    q.textContent = data.q;
    el.appendChild(q);

    const opts = document.createElement('div');
    opts.className = 'opts';
    const order = shuffle(data.opts.map((_, i) => i));
    const fb = document.createElement('div');
    fb.className = 'fb';

    order.forEach((origIdx) => {
      const b = document.createElement('button');
      b.className = 'opt';
      b.type = 'button';
      b.textContent = data.opts[origIdx];
      b.addEventListener('click', () => {
        const buttons = opts.querySelectorAll('button');
        buttons.forEach((x) => (x.disabled = true));
        if (origIdx === data.answer) {
          b.classList.add('correct');
          fb.className = 'fb ok';
          fb.textContent = '✓ ' + (data.why || '正确。');
          el.dataset.result = 'ok';
        } else {
          b.classList.add('wrong');
          buttons.forEach((x) => {
            if (x.textContent === data.opts[data.answer]) x.classList.add('correct');
          });
          fb.className = 'fb bad';
          fb.textContent = '✗ ' + (data.why || '再想想。');
          el.dataset.result = 'bad';
        }
        updateScore();
      });
      opts.appendChild(b);
    });
    el.appendChild(opts);
    el.appendChild(fb);
  }

  function updateScore() {
    const all = document.querySelectorAll('.quiz[data-quiz]');
    const done = Array.from(all).filter((x) => x.dataset.result);
    const ok = done.filter((x) => x.dataset.result === 'ok').length;
    const box = document.getElementById('quiz-score');
    if (box) box.textContent = `已答 ${done.length}/${all.length}，答对 ${ok}`;
  }

  document.querySelectorAll('.quiz[data-quiz]').forEach(render);
})();
