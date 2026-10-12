/* ================================================
   VocabQuiz — Main Application Logic
   ================================================ */

// ===== STATE =====
let vocabData = null;
let currentLesson = null;
let currentLessonId = null;

// Flashcard state
let fcWords = [];
let fcIndex = 0;

// Quiz state
let quizMode = '';
let quizWords = [];
let quizIndex = 0;
let quizScore = 0;
let quizWrongWords = [];
let quizAnswered = false;

// Typing state
let typingWords = [];
let typingIndex = 0;
let typingScore = 0;
let typingWrongWords = [];
let typingAnswered = false;

// Matching state
let matchingWords = [];
let matchingSelected = null;
let matchingMatched = 0;
let matchingTimer = null;
let matchingSeconds = 0;
let matchingAttempts = 0;

// ===== STORAGE =====
const STORAGE_KEY = 'vocabquiz_progress';
const THEME_KEY = 'vocabquiz_theme';
const STARRED_KEY = 'vocabquiz_starred';

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch { return {}; }
}

function saveProgress(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function getStarred() {
  try {
    return JSON.parse(localStorage.getItem(STARRED_KEY)) || [];
  } catch { return []; }
}

function saveStarred(starred) {
  localStorage.setItem(STARRED_KEY, JSON.stringify(starred));
  updateStarredBadge();
}

function isStarred(wordId) {
  return getStarred().includes(wordId);
}

function toggleStarWord(wordId) {
  let starred = getStarred();
  if (starred.includes(wordId)) {
    starred = starred.filter(id => id !== wordId);
  } else {
    starred.push(wordId);
  }
  saveStarred(starred);
  return starred.includes(wordId);
}

function updateStarredBadge() {
  const count = getStarred().length;
  const badge = document.getElementById('starred-count');
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = 'flex';
  } else {
    badge.style.display = 'none';
  }
}

function recordWordResult(wordId, correct) {
  const progress = loadProgress();
  if (!progress.words) progress.words = {};
  if (!progress.words[wordId]) {
    progress.words[wordId] = { correct: 0, wrong: 0, learned: false };
  }
  if (correct) {
    progress.words[wordId].correct++;
    if (progress.words[wordId].correct >= 2) {
      progress.words[wordId].learned = true;
    }
  } else {
    progress.words[wordId].wrong++;
  }
  // Update streak
  const today = new Date().toDateString();
  if (progress.lastStudyDate !== today) {
    if (progress.lastStudyDate === new Date(Date.now() - 86400000).toDateString()) {
      progress.streak = (progress.streak || 0) + 1;
    } else {
      progress.streak = 1;
    }
    progress.lastStudyDate = today;
  }
  saveProgress(progress);
}

function getLearnedCount(lessonWords) {
  const progress = loadProgress();
  if (!progress.words) return 0;
  return lessonWords.filter(w => progress.words[w.id]?.learned).length;
}

function getOverallStats() {
  const progress = loadProgress();
  if (!progress.words) return { learned: 0, streak: 0, accuracy: 0 };
  
  const words = Object.values(progress.words);
  const learned = words.filter(w => w.learned).length;
  const totalCorrect = words.reduce((s, w) => s + w.correct, 0);
  const totalWrong = words.reduce((s, w) => s + w.wrong, 0);
  const total = totalCorrect + totalWrong;
  const accuracy = total > 0 ? Math.round(totalCorrect / total * 100) : 0;
  
  return {
    learned,
    streak: progress.streak || 0,
    accuracy
  };
}

// ===== THEME =====
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  if (current === 'light') {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem(THEME_KEY, 'dark');
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem(THEME_KEY, 'light');
  }
}

// ===== TOAST =====
let toastTimeout;
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.remove('hidden');
  toast.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.classList.add('hidden'), 400);
  }, 2000);
}

// ===== TEXT-TO-SPEECH =====
function speak(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.85;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }
}

// ===== NAVIGATION =====
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  document.getElementById(pageId).classList.remove('hidden');
  window.scrollTo(0, 0);
}

function goHome() {
  window.location.hash = '/';
}

function goToLesson() {
  if (currentLessonId) {
    window.location.hash = '/lesson/' + currentLessonId;
  } else {
    goHome();
  }
  // Stop matching timer
  if (matchingTimer) {
    clearInterval(matchingTimer);
    matchingTimer = null;
  }
}

function handleRoute() {
  const hash = window.location.hash || '#/';
  
  if (hash === '#/' || hash === '#') {
    renderHome();
  } else if (hash.startsWith('#/lesson/')) {
    const id = parseInt(hash.split('/')[2]);
    renderLesson(id);
  }
}

// ===== HOME PAGE =====
function renderHome() {
  showPage('page-home');
  if (!vocabData) return;
  
  const stats = getOverallStats();
  document.getElementById('stat-learned').textContent = stats.learned;
  document.getElementById('stat-streak').textContent = stats.streak;
  document.getElementById('stat-accuracy').textContent = stats.accuracy + '%';
  
  renderLessonGrid(vocabData.lessons);
  updateStarredBadge();
}

function renderLessonGrid(lessons) {
  const grid = document.getElementById('lesson-grid');
  grid.innerHTML = lessons.map(lesson => {
    const learned = getLearnedCount(lesson.words);
    const percent = lesson.wordCount > 0 ? Math.round(learned / lesson.wordCount * 100) : 0;
    
    return `
      <div class="lesson-card" onclick="window.location.hash='/lesson/${lesson.id}'" tabindex="0" role="button">
        <div class="lesson-card-number">Lesson ${lesson.id}</div>
        <div class="lesson-card-name">${lesson.name}</div>
        <div class="lesson-card-count">${lesson.wordCount} từ vựng</div>
        <div class="lesson-card-progress">
          <div class="lesson-card-progress-fill" style="width: ${percent}%"></div>
        </div>
        <div class="lesson-card-percent">${learned}/${lesson.wordCount} (${percent}%)</div>
      </div>
    `;
  }).join('');
}

function filterLessons(query) {
  if (!vocabData) return;
  query = query.toLowerCase().trim();
  
  if (!query) {
    renderLessonGrid(vocabData.lessons);
    return;
  }
  
  const filtered = vocabData.lessons.filter(l => {
    if (l.name.toLowerCase().includes(query)) return true;
    if (String(l.id).includes(query)) return true;
    // Search in words
    return l.words.some(w => 
      w.word.toLowerCase().includes(query) || 
      w.meaning.toLowerCase().includes(query)
    );
  });
  
  renderLessonGrid(filtered);
}

// ===== LESSON DETAIL =====
function renderLesson(lessonId) {
  const lesson = vocabData.lessons.find(l => l.id === lessonId);
  if (!lesson) {
    goHome();
    return;
  }
  
  currentLesson = lesson;
  currentLessonId = lessonId;
  
  document.getElementById('lesson-title').textContent = lesson.name;
  document.getElementById('lesson-word-count').textContent = lesson.wordCount + ' từ';
  
  showPage('page-lesson');
}

// ===== FLASHCARD =====
function startFlashcard() {
  fcWords = [...currentLesson.words];
  fcIndex = 0;
  showPage('page-flashcard');
  renderFlashcard();
}

function renderFlashcard() {
  const word = fcWords[fcIndex];
  if (!word) return;
  
  // Update progress
  document.getElementById('fc-current').textContent = fcIndex + 1;
  document.getElementById('fc-total').textContent = fcWords.length;
  document.getElementById('fc-progress-bar').style.width = 
    ((fcIndex + 1) / fcWords.length * 100) + '%';
  
  // Reset flip
  document.getElementById('flashcard').classList.remove('flipped');
  
  // Front side
  const imgContainer = document.getElementById('fc-image');
  if (word.image) {
    imgContainer.innerHTML = `<img src="${word.image}" alt="${word.word}" onerror="this.parentElement.style.display='none'">`;
    imgContainer.style.display = 'block';
  } else {
    imgContainer.innerHTML = '';
    imgContainer.style.display = 'none';
  }
  
  const wordEl = document.getElementById('fc-word');
  const pronEl = document.getElementById('fc-pronunciation');
  
  if (word.allWords && word.allWords.length > 1) {
    const isAntonym = word.word.includes('><');
    const sep = isAntonym ? ' >< ' : ' = ';
    
    if (word.wordDetails && word.wordDetails.length > 1) {
      wordEl.innerHTML = `<div class="fc-word-group"><div class="fc-word-items">${word.wordDetails.map(wd => 
        `<span class="fc-syn-item"><span class="fc-syn-w">${escapeHtml(wd.word)}</span>${wd.ipa ? `<span class="fc-syn-ipa">${escapeHtml(wd.ipa)}</span>` : ''}</span>`
      ).join(`<span class="fc-syn-sep">${escapeHtml(sep)}</span>`)}</div></div>`;
      pronEl.textContent = word.partOfSpeech ? `(${word.partOfSpeech})` : '';
    } else {
      wordEl.textContent = word.word;
      pronEl.textContent = (word.pronunciation ? word.pronunciation + ' ' : '') + (word.partOfSpeech ? `(${word.partOfSpeech})` : '');
    }
  } else {
    wordEl.textContent = word.word;
    pronEl.textContent = (word.pronunciation ? word.pronunciation + ' ' : '') + (word.partOfSpeech ? `(${word.partOfSpeech})` : '');
  }
  
  // Back side
  document.getElementById('fc-meaning').textContent = word.meaning || '—';
  document.getElementById('fc-example').textContent = word.example || '';
  document.getElementById('fc-example-vi').textContent = word.exampleVi ? `(${word.exampleVi})` : '';
  
  // Star state
  updateStarButton();
  
  // Nav buttons
  document.getElementById('fc-prev').disabled = fcIndex === 0;
  document.getElementById('fc-next').disabled = fcIndex === fcWords.length - 1;
}

function flipCard() {
  document.getElementById('flashcard').classList.toggle('flipped');
}

function nextCard() {
  if (fcIndex < fcWords.length - 1) {
    fcIndex++;
    renderFlashcard();
  }
}

function prevCard() {
  if (fcIndex > 0) {
    fcIndex--;
    renderFlashcard();
  }
}

function speakWord() {
  const word = fcWords[fcIndex];
  if (word) {
    const text = (word.allWords && word.allWords.length > 1)
      ? word.allWords.join(', ')
      : word.word;
    speak(text);
  }
}

function toggleStar() {
  const word = fcWords[fcIndex];
  if (word) {
    toggleStarWord(word.id);
    updateStarButton();
    showToast(isStarred(word.id) ? '⭐ Đã đánh dấu' : '✓ Đã bỏ đánh dấu');
  }
}

function updateStarButton() {
  const word = fcWords[fcIndex];
  const btn = document.getElementById('fc-star');
  if (isStarred(word.id)) {
    btn.classList.add('fc-star-active');
  } else {
    btn.classList.remove('fc-star-active');
  }
}

// Keyboard navigation for flashcard
document.addEventListener('keydown', (e) => {
  const fcPage = document.getElementById('page-flashcard');
  if (fcPage.classList.contains('hidden')) return;
  
  if (e.key === 'ArrowRight' || e.key === ' ') {
    e.preventDefault();
    nextCard();
  } else if (e.key === 'ArrowLeft') {
    prevCard();
  } else if (e.key === 'Enter') {
    flipCard();
  } else if (e.key === 's') {
    toggleStar();
  }
});

// ===== QUIZ =====
function startQuiz(mode) {
  quizMode = mode;
  quizWords = shuffleArray([...currentLesson.words]);
  quizIndex = 0;
  quizScore = 0;
  quizWrongWords = [];
  quizAnswered = false;
  
  document.getElementById('quiz-total').textContent = quizWords.length;
  document.getElementById('quiz-score').textContent = '0';
  
  showPage('page-quiz');
  renderQuizQuestion();
}

function renderQuizQuestion() {
  if (quizIndex >= quizWords.length) {
    showQuizResults();
    return;
  }
  
  quizAnswered = false;
  const word = quizWords[quizIndex];
  
  // Update progress
  document.getElementById('quiz-current').textContent = quizIndex + 1;
  document.getElementById('quiz-progress-bar').style.width = 
    ((quizIndex + 1) / quizWords.length * 100) + '%';
  
  // Hide feedback & next button
  document.getElementById('quiz-feedback').classList.add('hidden');
  document.getElementById('quiz-next-btn').classList.add('hidden');
  
  const promptEl = document.getElementById('quiz-prompt');
  const speakBtn = document.getElementById('quiz-speak-btn');
  
  // Generate wrong options from ALL lessons (for more variety)
  const allWords = vocabData.lessons.flatMap(l => l.words);
  
  let correctAnswer, options;
  
  if (quizMode === 'en-vi') {
    promptEl.textContent = word.word;
    speakBtn.style.display = 'none';
    correctAnswer = word.meaning || '—';
    options = generateOptions(correctAnswer, allWords.map(w => w.meaning).filter(m => m), 4);
  } else if (quizMode === 'vi-en') {
    promptEl.textContent = word.meaning || '—';
    speakBtn.style.display = 'none';
    correctAnswer = word.word;
    options = generateOptions(correctAnswer, allWords.map(w => w.word), 4);
  } else if (quizMode === 'listen') {
    promptEl.textContent = '🎧 Nghe và chọn từ đúng';
    speakBtn.style.display = 'flex';
    correctAnswer = word.word;
    options = generateOptions(correctAnswer, allWords.map(w => w.word), 4);
    // Auto speak
    const textToSpeak = (word.allWords && word.allWords.length > 1) ? word.allWords.join(', ') : word.word;
    setTimeout(() => speak(textToSpeak), 500);
  }
  
  // Render options
  const optionsEl = document.getElementById('quiz-options');
  optionsEl.innerHTML = options.map((opt, i) => 
    `<button class="quiz-option" data-index="${i}" data-value="${escapeHtml(opt)}" onclick="selectQuizOption(this)">${escapeHtml(opt)}</button>`
  ).join('');
}

function speakQuizWord() {
  const word = quizWords[quizIndex];
  if (word) {
    const textToSpeak = (word.allWords && word.allWords.length > 1) ? word.allWords.join(', ') : word.word;
    speak(textToSpeak);
  }
}

function generateOptions(correct, pool, count) {
  const filtered = pool.filter(item => item && item !== correct);
  const unique = [...new Set(filtered)];
  const shuffled = shuffleArray(unique).slice(0, count - 1);
  shuffled.push(correct);
  return shuffleArray(shuffled);
}

function selectQuizOption(btn) {
  if (quizAnswered) return;
  quizAnswered = true;
  
  const word = quizWords[quizIndex];
  const selected = btn.getAttribute('data-value');
  
  let correctAnswer;
  if (quizMode === 'en-vi') correctAnswer = word.meaning || '—';
  else correctAnswer = word.word;
  
  const isCorrect = selected === correctAnswer;
  
  // Disable all options
  document.querySelectorAll('.quiz-option').forEach(opt => {
    opt.classList.add('disabled');
    if (opt.getAttribute('data-value') === correctAnswer) {
      opt.classList.add('correct');
    }
  });
  
  if (isCorrect) {
    btn.classList.add('correct');
    quizScore++;
    document.getElementById('quiz-score').textContent = quizScore;
    recordWordResult(word.id, true);
  } else {
    btn.classList.add('wrong');
    quizWrongWords.push(word);
    recordWordResult(word.id, false);
  }
  
  // Show feedback
  const feedback = document.getElementById('quiz-feedback');
  feedback.classList.remove('hidden');
  document.getElementById('feedback-icon').textContent = isCorrect ? '✅' : '❌';
  
  if (isCorrect) {
    document.getElementById('feedback-text').textContent = 'Chính xác!';
  } else {
    document.getElementById('feedback-text').innerHTML = 
      `Đáp án đúng: <strong>${escapeHtml(correctAnswer)}</strong>`;
  }
  
  // Show next button
  document.getElementById('quiz-next-btn').classList.remove('hidden');
}

function speakQuizWord() {
  if (quizWords[quizIndex]) {
    speak(quizWords[quizIndex].word);
  }
}

function nextQuestion() {
  quizIndex++;
  renderQuizQuestion();
}

function showQuizResults() {
  showPage('page-results');
  
  const total = quizWords.length;
  const percent = Math.round(quizScore / total * 100);
  
  let icon, title;
  if (percent >= 90) { icon = '🏆'; title = 'Xuất sắc!'; }
  else if (percent >= 70) { icon = '🎉'; title = 'Tuyệt vời!'; }
  else if (percent >= 50) { icon = '💪'; title = 'Khá tốt!'; }
  else { icon = '📚'; title = 'Cần ôn thêm!'; }
  
  document.getElementById('results-icon').textContent = icon;
  document.getElementById('results-title').textContent = title;
  document.getElementById('results-score').textContent = `${quizScore}/${total}`;
  document.getElementById('results-details').textContent = 
    `Chính xác ${percent}% • ${quizWrongWords.length} từ sai`;
  
  // Render wrong words
  const wrongList = document.getElementById('results-wrong-list');
  if (quizWrongWords.length > 0) {
    wrongList.innerHTML = `
      <h3 style="margin-bottom: 12px; color: var(--text-secondary)">📝 Các từ cần ôn:</h3>
      ${quizWrongWords.map(w => `
        <div class="wrong-word-item">
          <span class="wrong-word-en">${escapeHtml(w.word)} <span style="color: var(--accent-1)">${w.pronunciation || ''}</span></span>
          <span class="wrong-word-vi">${escapeHtml(w.meaning || '')}</span>
        </div>
      `).join('')}
    `;
  } else {
    wrongList.innerHTML = '';
  }
}

function retryQuiz() {
  if (quizMode) {
    startQuiz(quizMode);
  } else if (typingWords.length) {
    startTyping();
  }
}

// ===== TYPING =====
function startTyping() {
  typingWords = shuffleArray([...currentLesson.words]);
  typingIndex = 0;
  typingScore = 0;
  typingWrongWords = [];
  typingAnswered = false;
  
  document.getElementById('typing-total').textContent = typingWords.length;
  document.getElementById('typing-score').textContent = '0';
  
  showPage('page-typing');
  renderTypingQuestion();
}

function renderTypingQuestion() {
  if (typingIndex >= typingWords.length) {
    quizScore = typingScore;
    quizWrongWords = typingWrongWords;
    quizWords = typingWords;
    quizMode = '';
    showQuizResults();
    return;
  }
  
  typingAnswered = false;
  const word = typingWords[typingIndex];
  
  document.getElementById('typing-current').textContent = typingIndex + 1;
  document.getElementById('typing-progress-bar').style.width = 
    ((typingIndex + 1) / typingWords.length * 100) + '%';
  
  document.getElementById('typing-prompt').textContent = word.meaning || '—';
  document.getElementById('typing-hint').textContent = word.pronunciation || '';
  
  const input = document.getElementById('typing-input');
  input.value = '';
  input.className = 'typing-input';
  input.disabled = false;
  input.focus();
  
  document.getElementById('typing-feedback').classList.add('hidden');
  document.getElementById('typing-next-btn').classList.add('hidden');
  document.getElementById('typing-check-btn').style.display = '';
}

function checkTyping() {
  if (typingAnswered) return;
  typingAnswered = true;
  
  const word = typingWords[typingIndex];
  const input = document.getElementById('typing-input');
  const userAns = input.value.trim().toLowerCase();
  
  // Accept user answer if it matches ANY word in allWords OR the combined word string
  const validAnswers = (word.allWords && word.allWords.length > 0)
    ? [...word.allWords.map(w => w.toLowerCase()), word.word.toLowerCase()]
    : [word.word.toLowerCase()];
    
  let matchedWord = null;
  let isClose = false;
  let closeTarget = null;
  
  for (const ans of validAnswers) {
    if (userAns === ans) {
      matchedWord = ans;
      break;
    }
    if (!isClose && ans.length > 4 && levenshtein(userAns, ans) <= 1) {
      isClose = true;
      closeTarget = ans;
    }
  }
  
  const isCorrect = matchedWord !== null;
  const feedback = document.getElementById('typing-feedback');
  feedback.classList.remove('hidden', 'correct', 'wrong');
  
  if (isCorrect) {
    input.classList.add('correct');
    feedback.classList.add('correct');
    if (word.allWords && word.allWords.length > 1) {
      const others = word.allWords.filter(w => w.toLowerCase() !== matchedWord);
      if (others.length > 0) {
        feedback.innerHTML = `✅ Chính xác! Các từ đồng nghĩa khác: <strong>${escapeHtml(others.join(', '))}</strong>`;
      } else {
        feedback.textContent = '✅ Chính xác!';
      }
    } else {
      feedback.textContent = '✅ Chính xác!';
    }
    typingScore++;
    document.getElementById('typing-score').textContent = typingScore;
    recordWordResult(word.id, true);
  } else if (isClose) {
    input.classList.add('correct');
    feedback.classList.add('correct');
    feedback.innerHTML = `✅ Gần đúng! Đáp án: <strong>${escapeHtml(word.word)}</strong>`;
    typingScore++;
    document.getElementById('typing-score').textContent = typingScore;
    recordWordResult(word.id, true);
  } else {
    input.classList.add('wrong');
    feedback.classList.add('wrong');
    feedback.innerHTML = `❌ Sai! Đáp án đúng: <strong>${escapeHtml(word.word)}</strong>`;
    typingWrongWords.push(word);
    recordWordResult(word.id, false);
  }
  
  input.disabled = true;
  document.getElementById('typing-check-btn').style.display = 'none';
  document.getElementById('typing-next-btn').classList.remove('hidden');
}

function nextTypingQuestion() {
  typingIndex++;
  renderTypingQuestion();
}

// Enter to submit typing
document.addEventListener('keydown', (e) => {
  const typingPage = document.getElementById('page-typing');
  if (typingPage.classList.contains('hidden')) return;
  
  if (e.key === 'Enter') {
    if (!typingAnswered) {
      checkTyping();
    } else {
      nextTypingQuestion();
    }
  }
});

// ===== MATCHING =====
function startMatching() {
  // Take 6 random words for matching (or all if less than 6)
  const count = Math.min(6, currentLesson.words.length);
  matchingWords = shuffleArray([...currentLesson.words]).slice(0, count);
  matchingSelected = null;
  matchingMatched = 0;
  matchingSeconds = 0;
  matchingAttempts = 0;
  
  if (matchingTimer) clearInterval(matchingTimer);
  
  showPage('page-matching');
  document.getElementById('matching-result').classList.add('hidden');
  
  // Render columns
  const leftCol = document.getElementById('matching-left');
  const rightCol = document.getElementById('matching-right');
  
  const shuffledEn = shuffleArray(matchingWords.map((w, i) => ({ text: w.word, index: i, side: 'en' })));
  const shuffledVi = shuffleArray(matchingWords.map((w, i) => ({ text: w.meaning || '—', index: i, side: 'vi' })));
  
  leftCol.innerHTML = shuffledEn.map(item => 
    `<div class="match-item" data-index="${item.index}" data-side="en" onclick="selectMatch(this)">${escapeHtml(item.text)}</div>`
  ).join('');
  
  rightCol.innerHTML = shuffledVi.map(item => 
    `<div class="match-item" data-index="${item.index}" data-side="vi" onclick="selectMatch(this)">${escapeHtml(item.text)}</div>`
  ).join('');
  
  // Start timer
  matchingTimer = setInterval(() => {
    matchingSeconds++;
    const m = Math.floor(matchingSeconds / 60);
    const s = matchingSeconds % 60;
    document.getElementById('matching-timer').textContent = 
      `⏱️ ${m}:${String(s).padStart(2, '0')}`;
  }, 1000);
}

function selectMatch(el) {
  if (el.classList.contains('matched')) return;
  
  const index = parseInt(el.getAttribute('data-index'));
  const side = el.getAttribute('data-side');
  
  if (matchingSelected === null) {
    // First selection
    matchingSelected = { el, index, side };
    el.classList.add('selected');
  } else if (matchingSelected.side === side) {
    // Same side — switch selection
    matchingSelected.el.classList.remove('selected');
    matchingSelected = { el, index, side };
    el.classList.add('selected');
  } else {
    // Different side — check match
    matchingAttempts++;
    
    if (matchingSelected.index === index) {
      // Correct match
      matchingSelected.el.classList.remove('selected');
      matchingSelected.el.classList.add('matched');
      el.classList.add('matched');
      matchingMatched++;
      
      recordWordResult(matchingWords[index].id, true);
      
      if (matchingMatched === matchingWords.length) {
        // All matched!
        clearInterval(matchingTimer);
        matchingTimer = null;
        
        setTimeout(() => {
          const result = document.getElementById('matching-result');
          result.classList.remove('hidden');
          const m = Math.floor(matchingSeconds / 60);
          const s = matchingSeconds % 60;
          result.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 16px">🎉</div>
            <h3 style="font-size: 24px; font-weight: 700; margin-bottom: 12px">Hoàn thành!</h3>
            <p style="color: var(--text-secondary); margin-bottom: 8px">
              Thời gian: <strong>${m}:${String(s).padStart(2, '0')}</strong>
            </p>
            <p style="color: var(--text-secondary); margin-bottom: 24px">
              Số lần thử: <strong>${matchingAttempts}</strong>
            </p>
            <button class="btn-primary" onclick="startMatching()">Chơi lại</button>
            <button class="btn-secondary" style="margin-left: 8px" onclick="goToLesson()">Quay lại</button>
          `;
        }, 500);
      }
    } else {
      // Wrong match
      matchingSelected.el.classList.remove('selected');
      el.classList.add('wrong-match');
      matchingSelected.el.classList.add('wrong-match');
      
      const prevEl = matchingSelected.el;
      setTimeout(() => {
        el.classList.remove('wrong-match');
        prevEl.classList.remove('wrong-match');
      }, 500);
    }
    
    matchingSelected = null;
  }
}

// ===== STARRED WORDS =====
function showStarred() {
  showPage('page-starred');
  
  const starredIds = getStarred();
  
  if (starredIds.length === 0) {
    document.getElementById('starred-list').innerHTML = `
      <div class="starred-empty">
        <div class="starred-empty-icon">⭐</div>
        <p>Chưa có từ nào được đánh dấu</p>
        <p style="font-size: 13px; margin-top: 8px">Nhấn ⭐ khi xem Flashcard để đánh dấu từ khó</p>
      </div>
    `;
    return;
  }
  
  // Find word details from data
  const allWords = vocabData.lessons.flatMap(l => l.words);
  const starredWords = starredIds.map(id => allWords.find(w => w.id === id)).filter(Boolean);
  
  document.getElementById('starred-list').innerHTML = starredWords.map(w => `
    <div class="starred-item">
      <span class="starred-word">${escapeHtml(w.word)}</span>
      <span class="starred-pronunciation">${w.pronunciation || ''}</span>
      <span class="starred-meaning">${escapeHtml(w.meaning || '')}</span>
      <button class="starred-remove" onclick="removeStarred('${w.id}')" title="Bỏ đánh dấu">✕</button>
    </div>
  `).join('');
}

function removeStarred(wordId) {
  toggleStarWord(wordId);
  showStarred(); // Re-render
  showToast('✓ Đã bỏ đánh dấu');
}

// ===== UTILITIES =====
function shuffleArray(arr) {
  const shuffled = [...arr];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function levenshtein(a, b) {
  const matrix = [];
  for (let i = 0; i <= b.length; i++) matrix[i] = [i];
  for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      matrix[i][j] = b.charAt(i - 1) === a.charAt(j - 1)
        ? matrix[i - 1][j - 1]
        : Math.min(matrix[i - 1][j - 1] + 1, matrix[i][j - 1] + 1, matrix[i - 1][j] + 1);
    }
  }
  return matrix[b.length][a.length];
}

// ===== INIT =====
async function init() {
  initTheme();
  updateStarredBadge();
  
  try {
    const response = await fetch('data/vocab.json');
    vocabData = await response.json();
    
    // Update hero subtitle dynamically
    document.querySelector('.hero-subtitle').textContent = 
      `${vocabData.totalWords} từ vựng • ${vocabData.totalLessons} bài học • Flashcard & Quiz tương tác`;
    
    handleRoute();
  } catch (error) {
    console.error('Failed to load vocab data:', error);
    document.getElementById('lesson-grid').innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted)">
        <p>⚠️ Không tải được dữ liệu từ vựng.</p>
        <p style="font-size: 13px; margin-top: 8px">Hãy chắc chắn file data/vocab.json tồn tại.</p>
      </div>
    `;
  }
}

// Route change handler
window.addEventListener('hashchange', handleRoute);

// Init on load
document.addEventListener('DOMContentLoaded', init);
