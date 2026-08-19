// Reusable multiple-choice quiz with immediate feedback.
// Usage: renderQuiz(containerEl, [{ q, options, answer, explain }, ...])
//   q: question HTML; options: array of option HTML strings;
//   answer: index of the correct option; explain: feedback HTML.
function renderQuiz(container, questions) {
  let answered = 0;
  let correct = 0;

  const scoreBox = document.createElement('div');
  scoreBox.className = 'quiz-score';

  questions.forEach((item, qi) => {
    const wrap = document.createElement('div');
    wrap.className = 'quiz-q';

    const qText = document.createElement('div');
    qText.className = 'q-text';
    qText.innerHTML = `${qi + 1}. ${item.q}`;
    wrap.appendChild(qText);

    const opts = document.createElement('div');
    opts.className = 'quiz-options';

    const explain = document.createElement('div');
    explain.className = 'quiz-explain';
    explain.innerHTML = item.explain;

    item.options.forEach((opt, oi) => {
      const btn = document.createElement('button');
      btn.innerHTML = opt;
      btn.addEventListener('click', () => {
        opts.querySelectorAll('button').forEach(b => (b.disabled = true));
        if (oi === item.answer) {
          btn.classList.add('correct');
          correct++;
        } else {
          btn.classList.add('wrong');
          opts.children[item.answer].classList.add('correct');
        }
        explain.classList.add('show');
        answered++;
        if (answered === questions.length) {
          scoreBox.innerHTML =
            `<strong>${correct} / ${questions.length}</strong> — ` +
            (correct === questions.length
              ? '全对！可以进入下一课了。'
              : correct >= Math.ceil(questions.length * 0.7)
                ? '不错，把错题的解释读一遍再往下走。'
                : '别急，重读上面的规则卡片，刷新页面再来一轮。');
          scoreBox.classList.add('show');
        }
      });
      opts.appendChild(btn);
    });

    wrap.appendChild(opts);
    wrap.appendChild(explain);
    container.appendChild(wrap);
  });

  container.appendChild(scoreBox);
}
