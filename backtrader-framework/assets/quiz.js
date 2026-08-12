// Reusable quiz widget for retrieval practice across lessons.
// Markup contract:
//   <div class="quiz" data-answer="1">
//     <div class="q">Question text?</div>
//     <button class="opt">Option A</button>   <!-- index 0 -->
//     <button class="opt">Option B</button>   <!-- index 1 (correct) -->
//     <div class="fb right" data-for="right">Feedback when correct.</div>
//     <div class="fb nope" data-for="nope">Feedback when wrong.</div>
//   </div>
// Give every option the SAME length where possible — no formatting tells.

document.addEventListener('click', (e) => {
  const opt = e.target.closest('.quiz .opt');
  if (!opt) return;
  const quiz = opt.closest('.quiz');
  if (quiz.dataset.done) return;

  const opts = [...quiz.querySelectorAll('.opt')];
  const chosen = opts.indexOf(opt);
  const answer = Number(quiz.dataset.answer);
  const correct = chosen === answer;

  opts[answer].classList.add('correct');
  if (!correct) opt.classList.add('wrong');
  opts.forEach((o) => (o.disabled = true));

  const fb = quiz.querySelector(correct ? '.fb.right' : '.fb.nope');
  if (fb) fb.classList.add('show');
  quiz.dataset.done = '1';
});
