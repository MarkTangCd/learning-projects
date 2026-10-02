// Declarative multiple-choice quiz with immediate feedback.
// Markup:
//   <p class="quiz-score"></p>              (optional, one per page)
//   <div class="quiz" data-answer="2">      (1-based index of the correct option)
//     <p class="q">Question?</p>
//     <ol><li>A</li><li>B</li><li>C</li><li>D</li></ol>
//     <p class="why">Shown after answering.</p>
//   </div>
(function () {
  const quizzes = Array.from(document.querySelectorAll('.quiz'));
  if (quizzes.length === 0) return;
  const scoreBox = document.querySelector('.quiz-score');
  let answered = 0;
  let correct = 0;

  function verdict() {
    if (correct === quizzes.length) return '全对。可以进入下一课了。';
    if (correct >= Math.ceil(quizzes.length * 0.7)) return '不错，把错题的解释读一遍再往下走。';
    return '别急，回到上面的卡片重读，刷新页面再来一轮。';
  }

  quizzes.forEach((quiz) => {
    const answerIdx = parseInt(quiz.dataset.answer, 10) - 1;
    const items = Array.from(quiz.querySelectorAll('ol > li'));
    const why = quiz.querySelector('.why');
    items.forEach((li, i) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.innerHTML = li.innerHTML;
      li.innerHTML = '';
      li.appendChild(btn);
      btn.addEventListener('click', () => {
        items.forEach((x) => (x.firstChild.disabled = true));
        if (i === answerIdx) {
          btn.classList.add('correct');
          correct++;
        } else {
          btn.classList.add('wrong');
          items[answerIdx].firstChild.classList.add('correct');
        }
        if (why) why.classList.add('show');
        answered++;
        if (answered === quizzes.length && scoreBox) {
          scoreBox.innerHTML = `<strong>${correct} / ${quizzes.length}</strong> — ${verdict()}`;
          scoreBox.classList.add('show');
        }
      });
    });
  });
})();
