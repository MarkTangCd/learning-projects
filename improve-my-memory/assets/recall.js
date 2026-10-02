// Free-recall ("brain dump") self-grading component.
// Markup:
//   <div class="recall" id="unique-id" data-prompt="Write everything you remember about ...">
//     <ul class="recall-keys">
//       <li>Key point 1</li>
//       <li>Key point 2</li>
//     </ul>
//   </div>
// Flow: user types from memory -> clicks "对答案" -> key points appear as
// checkboxes -> user ticks the ones they covered -> score is shown and
// persisted in localStorage so a later visit shows the previous score.
(function () {
  const STORAGE_PREFIX = 'recall:' + location.pathname + '#';

  function loadScore(id) {
    try { return JSON.parse(localStorage.getItem(STORAGE_PREFIX + id)); } catch (e) { return null; }
  }
  function saveScore(id, hit, total) {
    try {
      localStorage.setItem(STORAGE_PREFIX + id, JSON.stringify({ hit, total, at: Date.now() }));
    } catch (e) { /* storage unavailable: ignore */ }
  }

  document.querySelectorAll('.recall').forEach((box) => {
    const id = box.id || 'default';
    const keys = box.querySelector('.recall-keys');
    const keyItems = keys ? Array.from(keys.querySelectorAll('li')) : [];

    const prompt = document.createElement('p');
    prompt.innerHTML = `<strong>闭卷回忆。</strong>${box.dataset.prompt || '把你记得的全部写下来，写不出来再往下看。'}`;
    const ta = document.createElement('textarea');
    ta.placeholder = '先别往上翻。写到想不出为止，卡住再坚持 30 秒……';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = '我写完了，对答案';
    const result = document.createElement('p');
    result.className = 'recall-result';
    const last = document.createElement('p');
    last.className = 'recall-last';

    const prev = loadScore(id);
    if (prev) {
      const d = new Date(prev.at);
      last.textContent = `上次：${prev.hit} / ${prev.total}（${d.getMonth() + 1}/${d.getDate()}）`;
    }

    box.insertBefore(prompt, box.firstChild);
    box.insertBefore(ta, keys);
    box.insertBefore(btn, keys);
    box.insertBefore(last, keys);
    box.appendChild(result);

    const checks = keyItems.map((li) => {
      const label = document.createElement('label');
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      label.appendChild(cb);
      label.appendChild(document.createTextNode(li.textContent));
      li.innerHTML = '';
      li.appendChild(label);
      cb.addEventListener('change', update);
      return cb;
    });

    function update() {
      const hit = checks.filter((c) => c.checked).length;
      const total = checks.length;
      const pct = total ? Math.round((hit / total) * 100) : 0;
      result.textContent = `写到了 ${hit} / ${total}（${pct}%）。` +
        (pct >= 80 ? '很好，这些内容的存储强度已经在上升。' : '没写到的那几条，就是明天最该复习的。');
      saveScore(id, hit, total);
    }

    btn.addEventListener('click', () => {
      if (ta.value.trim().length < 10) {
        result.textContent = '先写点什么。哪怕只有两三个词，提取的努力本身就是训练。';
        return;
      }
      keys.classList.add('show');
      btn.disabled = true;
      ta.readOnly = true;
      result.textContent = '勾选你写到的要点（自己诚实打分）。';
    });
  });
})();
