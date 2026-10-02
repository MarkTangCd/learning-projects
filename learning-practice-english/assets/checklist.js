// Persistent checklist: checkbox state is saved in localStorage per page + item id.
// Usage: <ul class="checklist"><li><input type="checkbox" id="c1"><label for="c1">...</label></li></ul>
(function () {
  const key = (id) => `chk:${location.pathname}:${id}`;
  document.querySelectorAll('.checklist input[type=checkbox]').forEach((cb) => {
    try { cb.checked = localStorage.getItem(key(cb.id)) === '1'; } catch (e) {}
    cb.addEventListener('change', () => {
      try { localStorage.setItem(key(cb.id), cb.checked ? '1' : '0'); } catch (e) {}
    });
  });
})();
