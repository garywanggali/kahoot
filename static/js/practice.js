/**
 * Solo practice mode: no teacher, no live ranking, no option stats.
 * Scores each answer on the server and shows a quiz-set leaderboard at the end.
 */
(function () {
    'use strict';

    function t(key, fallback) {
        var args = Array.prototype.slice.call(arguments, 2);
        if (typeof window.t === 'function') {
            var translated = window.t.apply(null, [key].concat(args));
            if (translated && translated !== key) return translated;
        }
        return fallback;
    }

    function csrfToken() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        if (meta && meta.getAttribute('content')) return meta.getAttribute('content');
        var input = document.querySelector('input[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    var boot = window.PRACTICE_BOOT || {};
    var quiz = boot.quiz || { questions: [] };
    var nickname = boot.nickname || '';
    var token = '';
    var index = 0;
    var score = 0;
    var hasAnswered = false;
    var submitInFlight = false;
    var selectedOptions = new Set();
    var questionStartTime = 0;
    var timerInterval = null;
    var countdown = window.QuestionCountdown ? window.QuestionCountdown.create('question-countdown') : null;

    var STORAGE_AVATAR_KEY = 'kahoot_player_avatar';
    var myAvatar = (function () {
        try {
            var saved = localStorage.getItem(STORAGE_AVATAR_KEY);
            if (saved && window.AvatarSystem) {
                return window.AvatarSystem.normalize(JSON.parse(saved));
            }
        } catch (e) {}
        return window.AvatarSystem ? window.AvatarSystem.random() : { face: 0, hair: 0 };
    })();

    function saveAvatar() {
        try {
            localStorage.setItem(STORAGE_AVATAR_KEY, JSON.stringify(myAvatar));
        } catch (e) {}
    }

    function updateAvatarUi() {
        if (!window.AvatarSystem) return;
        var preview = document.getElementById('lobby-avatar-preview');
        if (preview) {
            preview.innerHTML = window.AvatarSystem.renderSvg(myAvatar, 140, {
                nickname: nickname,
                className: 'lobby-avatar-bounce-svg',
            });
        }
        var faceEl = document.getElementById('picker-face-name');
        var hairEl = document.getElementById('picker-hair-name');
        if (faceEl && window.AvatarSystem.getFaceName) {
            faceEl.textContent = window.AvatarSystem.getFaceName(myAvatar.face);
        }
        if (hairEl && window.AvatarSystem.getHairName) {
            hairEl.textContent = window.AvatarSystem.getHairName(myAvatar.hair);
        }
    }

    window.randomizeAvatar = function () {
        if (!window.AvatarSystem) return;
        myAvatar = window.AvatarSystem.random();
        saveAvatar();
        updateAvatarUi();
    };
    window.cycleFace = function (delta) {
        if (!window.AvatarSystem) return;
        var total = window.AvatarSystem.FACES.length;
        myAvatar.face = (myAvatar.face + delta + total) % total;
        saveAvatar();
        updateAvatarUi();
    };
    window.cycleHair = function (delta) {
        if (!window.AvatarSystem) return;
        var total = window.AvatarSystem.HAIRS.length;
        myAvatar.hair = (myAvatar.hair + delta + total) % total;
        saveAvatar();
        updateAvatarUi();
    };

    function showScreen(id) {
        ['waiting-screen', 'play-screen', 'ended-screen'].forEach(function (name) {
            var el = document.getElementById(name);
            if (el) el.classList.toggle('hidden', name !== id);
        });
    }

    function postJson(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(body || {}),
        }).then(function (resp) {
            return resp.json().then(function (data) {
                if (!resp.ok || data.ok === false) {
                    throw new Error(data.error || t('status.error', '操作失败'));
                }
                return data;
            });
        });
    }

    function currentQuestion() {
        return (quiz.questions || [])[index] || null;
    }

    function hideFeedback() {
        var stage = document.getElementById('feedback-stage');
        if (stage) stage.classList.add('hidden');
    }

    function showFeedback(type, title, detail) {
        var stage = document.getElementById('feedback-stage');
        var card = document.getElementById('feedback-card');
        var titleEl = document.getElementById('answer-feedback');
        var detailEl = document.getElementById('answer-detail');
        if (!stage) return;
        if (card) card.className = 'feedback-card' + (type ? ' card-' + type : '');
        stage.className = 'play-feedback-stage' + (type ? ' stage-' + type : '');
        if (titleEl) titleEl.textContent = title || '';
        if (detailEl) {
            detailEl.textContent = detail || '';
            detailEl.classList.toggle('hidden', !detail);
        }
        stage.classList.remove('hidden');
    }

    function lockAnswerUi() {
        document.querySelectorAll('.option-btn').forEach(function (b) { b.disabled = true; });
        var textInput = document.getElementById('text-answer-input');
        var textBtn = document.getElementById('submit-text-btn');
        var multi = document.getElementById('submit-multi-btn');
        if (textInput) textInput.disabled = true;
        if (textBtn) textBtn.disabled = true;
        if (multi) multi.disabled = true;
    }

    function clearTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    function startTimer(seconds) {
        clearTimer();
        var fill = document.getElementById('timer-fill');
        var bar = document.getElementById('timer-bar');
        if (!seconds || seconds <= 0) {
            if (bar) bar.classList.add('hidden');
            return;
        }
        if (bar) bar.classList.remove('hidden');
        if (fill) fill.style.width = '100%';
        var remaining = seconds;
        timerInterval = setInterval(function () {
            remaining -= 0.1;
            if (fill) fill.style.width = Math.max(0, (remaining / seconds) * 100) + '%';
            if (remaining <= 0) {
                clearTimer();
                if (!hasAnswered) submitCurrent('');
            }
        }, 100);
    }

    function renderQuestion() {
        var q = currentQuestion();
        if (!q) {
            finishPractice();
            return;
        }
        hasAnswered = false;
        submitInFlight = false;
        selectedOptions = new Set();
        questionStartTime = Date.now();
        hideFeedback();

        var total = quiz.total_questions || (quiz.questions || []).length;
        var numEl = document.getElementById('question-number');
        if (numEl) numEl.textContent = t('play.question_num', '第 %s / %s 题', index + 1, total);

        var textEl = document.getElementById('question-text');
        if (textEl) {
            textEl.textContent = q.text || '';
            textEl.classList.toggle('hidden', !q.text);
        }

        var imgWrap = document.getElementById('question-image-wrap');
        var imgEl = document.getElementById('question-image');
        if (q.image_url && imgWrap && imgEl) {
            imgEl.src = q.image_url;
            imgWrap.classList.remove('hidden');
        } else if (imgWrap && imgEl) {
            imgEl.removeAttribute('src');
            imgWrap.classList.add('hidden');
        }

        var isChoice = q.question_type === 'single' || q.question_type === 'multiple' || q.question_type === 'judgment';
        var isText = q.question_type === 'short_answer' || q.question_type === 'word_cloud';
        var isExplain = q.question_type === 'explanation';

        var container = document.getElementById('options-container');
        container.innerHTML = '';
        container.classList.toggle('hidden', !isChoice);
        container.classList.toggle('judgment-options', q.question_type === 'judgment');
        if (isChoice && q.options) {
            var colors = ['option-a', 'option-b', 'option-c', 'option-d'];
            q.options.forEach(function (opt, i) {
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'option-btn ' + colors[i];
                btn.textContent = opt.text;
                btn.dataset.key = opt.key;
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    if (q.question_type === 'multiple') {
                        if (selectedOptions.has(opt.key)) {
                            selectedOptions.delete(opt.key);
                            btn.classList.remove('selected');
                        } else {
                            selectedOptions.add(opt.key);
                            btn.classList.add('selected');
                        }
                    } else {
                        submitCurrent(opt.key);
                    }
                });
                container.appendChild(btn);
            });
        }

        var textGroup = document.getElementById('text-answer-group');
        var textInput = document.getElementById('text-answer-input');
        if (textGroup) textGroup.classList.toggle('hidden', !isText);
        if (textInput) {
            textInput.value = '';
            textInput.disabled = false;
        }
        var textBtn = document.getElementById('submit-text-btn');
        if (textBtn) textBtn.disabled = false;

        var multi = document.getElementById('submit-multi-btn');
        if (multi) {
            multi.disabled = false;
            multi.classList.toggle('hidden', q.question_type !== 'multiple');
        }
        var skip = document.getElementById('btn-skip-explanation');
        if (skip) skip.classList.toggle('hidden', !isExplain);

        var playScreen = document.getElementById('play-screen');
        if (playScreen) {
            playScreen.classList.toggle('play-show-stem', true);
            playScreen.classList.remove('play-hide-stem');
        }

        startTimer(isExplain ? 0 : q.time_limit);
    }

    function afterCountdown() {
        questionStartTime = Date.now();
        renderQuestion();
    }

    function beginQuestion() {
        var q = currentQuestion();
        if (!q) {
            finishPractice();
            return;
        }
        showScreen('play-screen');
        hideFeedback();
        if (countdown && q.uses_countdown) {
            countdown.run({
                countdown_remaining_ms: (quiz.countdown_seconds || 3) * 1000,
                current_question_index: index,
                total_questions: quiz.total_questions || quiz.questions.length,
            }, afterCountdown);
        } else {
            afterCountdown();
        }
    }

    function submitCurrent(selected) {
        if (hasAnswered || submitInFlight) return;
        var q = currentQuestion();
        if (!q) return;
        if (q.question_type === 'multiple' && !selected) {
            selected = Array.from(selectedOptions).sort().join(',');
            if (!selected) return;
        }
        if ((q.question_type === 'short_answer' || q.question_type === 'word_cloud') && !selected) {
            var input = document.getElementById('text-answer-input');
            selected = input ? input.value.trim() : '';
            if (!selected && q.question_type === 'short_answer') return;
        }
        hasAnswered = true;
        submitInFlight = true;
        lockAnswerUi();
        clearTimer();
        var elapsed = Date.now() - (questionStartTime || Date.now());
        postJson(boot.urls.answer, {
            token: token,
            question_id: q.id,
            selected: selected || '',
            response_time_ms: elapsed,
        }).then(function (data) {
            score = data.score || score;
            submitInFlight = false;
            var type = data.no_score ? 'submitted' : (data.is_correct ? 'correct' : (selected ? 'wrong' : 'timeup'));
            var title = data.no_score
                ? t('fb.submitted', '已提交')
                : (data.is_correct ? t('fb.correct', '对') : (selected ? t('fb.wrong', '错') : t('fb.timeup', '时间到')));
            var detail = data.no_score ? '' : ('+' + (data.points || 0) + ' · ' + t('practice.score_now', '总分 %s', score));
            showFeedback(type, title, detail);
            setTimeout(function () {
                index += 1;
                beginQuestion();
            }, 1200);
        }).catch(function () {
            submitInFlight = false;
            hasAnswered = false;
        });
    }

    function finishPractice() {
        clearTimer();
        if (countdown) countdown.hide();
        postJson(boot.urls.finish, { token: token }).then(function (data) {
            showScreen('ended-screen');
            var scoreEl = document.getElementById('practice-final-score');
            if (scoreEl) {
                var rank = data.rank ? t('practice.your_rank', '第 %s 名', data.rank) : '';
                scoreEl.textContent = t('practice.final_score', '总分 %s', data.score) + (rank ? ' · ' + rank : '');
            }
            if (typeof window.renderAwardsCeremony === 'function') {
                window.renderAwardsCeremony(
                    data.leaderboard || [],
                    'practice-podium',
                    'practice-leaderboard',
                    'practice-rank-title',
                );
            }
        });
    }

    function startPractice() {
        var btn = document.getElementById('btn-start-practice');
        if (btn) btn.disabled = true;
        postJson(boot.urls.start, { avatar: myAvatar }).then(function (data) {
            token = data.token;
            quiz = data.quiz || quiz;
            index = 0;
            score = 0;
            beginQuestion();
        }).catch(function () {
            if (btn) btn.disabled = false;
        });
    }

    document.getElementById('btn-start-practice').addEventListener('click', startPractice);
    document.getElementById('submit-text-btn').addEventListener('click', function () {
        submitCurrent('');
    });
    document.getElementById('submit-multi-btn').addEventListener('click', function () {
        submitCurrent('');
    });
    document.getElementById('btn-skip-explanation').addEventListener('click', function () {
        submitCurrent('');
    });
    document.getElementById('text-answer-input').addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            submitCurrent('');
        }
    });

    updateAvatarUi();
})();
