// Quiz component. Markup:
// <div class="quiz" data-answer="2">
//   <p class="q">Question?</p>
//   <ol><li>A</li><li>B</li><li>C</li></ol>
//   <p class="why">Explanation shown after answering.</p>
// </div>
// data-answer is 1-based. An optional <p class="quiz-score"></p> shows the running score.
(function () {
  const quizzes = Array.from(document.querySelectorAll('.quiz'));
  const scoreEl = document.querySelector('.quiz-score');
  let answered = 0;
  let correct = 0;

  function renderScore() {
    if (!scoreEl) return;
    scoreEl.textContent = `已答 ${answered} / ${quizzes.length}，答对 ${correct}`;
    if (answered === quizzes.length) {
      scoreEl.textContent += correct === quizzes.length
        ? '。全对，这一课的核心你已经拿下了。'
        : '。答错的题请回看对应小节，隔天再来重做一次（间隔重复才记得住）。';
    }
  }

  function handleChoice(quiz, options, index) {
    if (quiz.classList.contains('done')) return;
    const answer = Number(quiz.dataset.answer) - 1;
    quiz.classList.add('done');
    answered += 1;
    if (index === answer) correct += 1;
    options.forEach((li, i) => {
      if (i === answer) li.classList.add('correct');
      else if (i === index) li.classList.add('wrong');
    });
    renderScore();
  }

  quizzes.forEach((quiz) => {
    const options = Array.from(quiz.querySelectorAll('ol > li'));
    options.forEach((li, index) => {
      li.addEventListener('click', () => handleChoice(quiz, options, index));
    });
  });
  renderScore();
})();
