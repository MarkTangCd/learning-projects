// Click-to-reveal hidden text (for dictation / "listen first, then check" tasks).
// Usage: <span class="hidden-text">answer</span>
document.querySelectorAll('.hidden-text').forEach((el) => {
  el.addEventListener('click', () => el.classList.toggle('revealed'));
});
