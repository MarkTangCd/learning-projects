// Shared quiz widget. Usage in a lesson:
//   <div class="quiz" data-answer="1">
//     <div class="q">Question text?</div>
//     <button class="opt">Option A</button>
//     <button class="opt">Option B</button>   <!-- index 1 = correct -->
//     <div class="fb ok"  data-for="correct">Why it's right.</div>
//     <div class="fb no" data-for="wrong">Why the others are wrong.</div>
//   </div>
// data-answer is the 0-based index of the correct .opt button.

document.addEventListener('click', function (e) {
  var btn = e.target.closest('.quiz .opt');
  if (!btn) return;
  var quiz = btn.closest('.quiz');
  if (quiz.dataset.done) return;

  var opts = Array.prototype.slice.call(quiz.querySelectorAll('.opt'));
  var answer = parseInt(quiz.dataset.answer, 10);
  var picked = opts.indexOf(btn);

  opts[answer].classList.add('correct');
  if (picked !== answer) btn.classList.add('wrong');

  var fb = quiz.querySelector(picked === answer ? '.fb[data-for="correct"]' : '.fb[data-for="wrong"]');
  if (fb) fb.classList.add('show');

  quiz.dataset.done = '1';
});
