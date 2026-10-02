// Dictation widget: speaks a sentence with the browser's TTS, user types what they hear,
// then gets word-level feedback. Usage:
// <div class="dictation" data-dictation='{"text":"What are you going to do?","focus":"gonna · weak are"}'></div>
(function () {
  const VOICE_LANG = 'en-US';
  const PREFERRED_VOICES = ['Samantha', 'Ava', 'Allison', 'Google US English'];

  function pickVoice() {
    const voices = speechSynthesis.getVoices().filter((v) => v.lang.startsWith('en'));
    for (const name of PREFERRED_VOICES) {
      const v = voices.find((x) => x.name.includes(name));
      if (v) return v;
    }
    return voices.find((v) => v.lang === VOICE_LANG) || voices[0] || null;
  }

  function speak(text, rate) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = VOICE_LANG;
    u.rate = rate;
    const v = pickVoice();
    if (v) u.voice = v;
    speechSynthesis.speak(u);
  }

  function tokens(s) {
    return s.toLowerCase().replace(/[’]/g, "'").replace(/[^a-z0-9' ]+/g, ' ').trim().split(/\s+/).filter(Boolean);
  }

  // Longest common subsequence alignment; returns set of indices in `ref` that were matched.
  function matchedIndices(ref, hyp) {
    const m = ref.length, n = hyp.length;
    const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
    for (let i = m - 1; i >= 0; i--) {
      for (let j = n - 1; j >= 0; j--) {
        dp[i][j] = ref[i] === hyp[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
    const hit = new Set();
    let i = 0, j = 0;
    while (i < m && j < n) {
      if (ref[i] === hyp[j]) { hit.add(i); i++; j++; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
      else j++;
    }
    return hit;
  }

  function render(el, idx) {
    let data;
    try { data = JSON.parse(el.dataset.dictation); } catch (e) { return; }
    const refWords = data.text.split(/\s+/);
    const refTok = tokens(data.text);
    let plays = 0;

    el.innerHTML = `
      <div class="d-head"><span class="d-num">${idx + 1}</span>
        <button type="button" class="d-play">▶ 播放 (1.0x)</button>
        <button type="button" class="d-slow">▶ 慢速 (0.8x)</button>
        <span class="d-plays small"></span></div>
      <textarea class="d-input" rows="2" placeholder="听到什么就写什么，不确定的词也写上" spellcheck="false"></textarea>
      <div class="d-actions"><button type="button" class="d-check">核对</button></div>
      <div class="d-result"></div>`;

    const input = el.querySelector('.d-input');
    const result = el.querySelector('.d-result');
    const playsEl = el.querySelector('.d-plays');
    const bump = () => { plays++; playsEl.textContent = `已播放 ${plays} 次`; };
    el.querySelector('.d-play').addEventListener('click', () => { speak(data.text, 1.0); bump(); });
    el.querySelector('.d-slow').addEventListener('click', () => { speak(data.text, 0.8); bump(); });

    el.querySelector('.d-check').addEventListener('click', () => {
      const hit = matchedIndices(refTok, tokens(input.value));
      const html = refWords.map((w, i) => hit.has(i) ? `<span class="d-ok">${w}</span>` : `<mark class="d-miss">${w}</mark>`).join(' ');
      const score = Math.round((hit.size / refTok.length) * 100);
      result.innerHTML = `<p class="d-ref">${html}</p>
        <p class="small">准确率 ${score}%，播放 ${plays} 次。${data.focus ? '考点：' + data.focus : ''}</p>`;
      el.dataset.score = String(score);
      el.dataset.plays = String(plays);
      updateSummary();
    });
  }

  function updateSummary() {
    const box = document.getElementById('dictation-summary');
    if (!box) return;
    const all = Array.from(document.querySelectorAll('.dictation[data-score]'));
    if (!all.length) return;
    const avg = Math.round(all.reduce((s, x) => s + Number(x.dataset.score), 0) / all.length);
    box.textContent = `已完成 ${all.length} 句，平均准确率 ${avg}%`;
    box.dataset.avg = String(avg);
    box.dispatchEvent(new CustomEvent('dictation:update', { detail: { avg, done: all.length } }));
  }

  if (!('speechSynthesis' in window)) {
    document.querySelectorAll('.dictation').forEach((el) => { el.textContent = '此浏览器不支持语音合成，请用 Safari 或 Chrome 打开。'; });
    return;
  }
  speechSynthesis.getVoices();
  document.querySelectorAll('.dictation[data-dictation]').forEach(render);
})();
