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

    var boot = {};
    var quiz = { questions: [] };
    var nickname = '';

    function getBoot() {
        var next = window.PRACTICE_BOOT || {};
        boot = next;
        if (next.quiz) quiz = next.quiz;
        if (next.nickname) nickname = next.nickname;
        return next;
    }
    var token = '';
    var index = 0;
    var score = 0;
    var hasAnswered = false;
    var submitInFlight = false;
    var selectedOptions = new Set();
    var questionStartTime = 0;
    var timerInterval = null;

    var STORAGE_AVATAR_KEY = 'shoot_player_avatar';
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
        if (!url) {
            return Promise.reject(new Error(t('status.error', '操作失败')));
        }
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

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }

    function hidePracticeWordCloud() {
        var wrap = document.getElementById('practice-word-cloud-wrap');
        if (wrap) wrap.classList.add('hidden');
    }

    function showPracticeWordCloud(words) {
        var wrap = document.getElementById('practice-word-cloud-wrap');
        var title = wrap ? wrap.querySelector('.word-cloud-title') : null;
        if (title) title.textContent = t('practice.word_cloud_title', '本题词云');
        if (wrap) wrap.classList.remove('hidden');
        if (typeof renderWordCloud === 'function') {
            renderWordCloud('practice-word-cloud-display', words || []);
        }
    }

    function renderPracticeResultClouds(clouds) {
        var cloudsEl = document.getElementById('practice-word-clouds');
        if (!cloudsEl) return;
        if (!clouds || !clouds.length || typeof renderWordCloud !== 'function') {
            cloudsEl.classList.add('hidden');
            cloudsEl.innerHTML = '';
            return;
        }
        cloudsEl.classList.remove('hidden');
        cloudsEl.innerHTML = clouds.map(function (item, i) {
            return '<div class="word-cloud-wrap practice-result-cloud">' +
                '<p class="word-cloud-title">' + escapeHtml(t('practice.word_cloud_title', '本题词云')) + '</p>' +
                '<p class="word-cloud-question">' + escapeHtml(item.text || '') + '</p>' +
                '<div id="practice-result-cloud-' + i + '" class="word-cloud-display"></div>' +
                '</div>';
        }).join('');
        clouds.forEach(function (item, i) {
            renderWordCloud('practice-result-cloud-' + i, item.words || []);
        });
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

    function unlockAnswerUi() {
        document.querySelectorAll('.option-btn').forEach(function (b) { b.disabled = false; });
        var textInput = document.getElementById('text-answer-input');
        var textBtn = document.getElementById('submit-text-btn');
        var multi = document.getElementById('submit-multi-btn');
        if (textInput) textInput.disabled = false;
        if (textBtn) textBtn.disabled = false;
        if (multi) multi.disabled = false;
    }

    function clearTimer() {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
    }

    function hideTimerBar() {
        clearTimer();
        var bar = document.getElementById('timer-bar');
        if (bar) bar.classList.add('hidden');
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
        hidePracticeWordCloud();
        hideTimerBar();

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
            textInput.maxLength = q.question_type === 'word_cloud' ? 40 : 100;
            textInput.placeholder = q.question_type === 'word_cloud'
                ? t('play.text_placeholder_wordcloud', '输入一个词或短语...')
                : t('play.text_placeholder', '在此输入你的答案...');
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
    }

    function beginQuestion() {
        var q = currentQuestion();
        if (!q) {
            finishPractice();
            return;
        }
        showScreen('play-screen');
        hideFeedback();
        renderQuestion();
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
            if (!selected) {
                if (q.question_type === 'word_cloud') {
                    showFeedback('wrong', t('play.word_cloud_need_word', '请输入一个词'));
                }
                return;
            }
        }
        hasAnswered = true;
        submitInFlight = true;
        lockAnswerUi();
        clearTimer();
        var elapsed = Date.now() - (questionStartTime || Date.now());
        var urls = (getBoot().urls || {});
        postJson(urls.answer, {
            token: token,
            question_id: q.id,
            selected: selected || '',
            response_time_ms: elapsed,
        }).then(function (data) {
            score = data.score || score;
            submitInFlight = false;
            var waitMs = 1200;
            if (q.question_type === 'word_cloud') {
                hideFeedback();
                var textGroup = document.getElementById('text-answer-group');
                if (textGroup) textGroup.classList.add('hidden');
                showPracticeWordCloud(data.word_cloud || []);
                waitMs = 2600;
            } else {
                var type = data.no_score ? 'submitted' : (data.is_correct ? 'correct' : (selected ? 'wrong' : 'timeup'));
                var title = data.no_score
                    ? t('fb.submitted', '已提交')
                    : (data.is_correct ? t('fb.correct', '对') : (selected ? t('fb.wrong', '错') : t('fb.timeup', '时间到')));
                var detail = data.no_score ? '' : ('+' + (data.points || 0) + ' · ' + t('practice.score_now', '总分 %s', score));
                showFeedback(type, title, detail);
            }
            setTimeout(function () {
                index += 1;
                beginQuestion();
            }, waitMs);
        }).catch(function (err) {
            submitInFlight = false;
            hasAnswered = false;
            unlockAnswerUi();
            showFeedback(
                'wrong',
                (err && err.message) || t('status.error', '操作失败'),
            );
        });
    }

    function finishPractice() {
        clearTimer();
        var urls = (getBoot().urls || {});
        postJson(urls.finish, { token: token }).then(function (data) {
            showScreen('ended-screen');
            var scoreEl = document.getElementById('practice-final-score');
            if (scoreEl) {
                var rank = data.rank ? t('practice.your_rank', '第 %s 名', data.rank) : '';
                scoreEl.textContent = t('practice.final_score', '总分 %s', data.score) + (rank ? ' · ' + rank : '');
            }
            renderPracticeResultClouds(data.word_clouds || []);
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
        var urls = (getBoot().urls || {});
        if (!urls.start) {
            return;
        }
        if (btn) btn.disabled = true;
        postJson(urls.start, { avatar: myAvatar }).then(function (data) {
            token = data.token;
            quiz = data.quiz || quiz;
            index = 0;
            score = 0;
            beginQuestion();
        }).catch(function () {
            if (btn) btn.disabled = false;
        });
    }

    window.startPractice = startPractice;

    function bindClick(id, handler) {
        var el = document.getElementById(id);
        if (el) el.addEventListener('click', handler);
    }

    getBoot();
    bindClick('btn-start-practice', startPractice);
    bindClick('submit-text-btn', function () { submitCurrent(''); });
    bindClick('submit-multi-btn', function () { submitCurrent(''); });
    bindClick('btn-skip-explanation', function () { submitCurrent(''); });
    var textInput = document.getElementById('text-answer-input');
    if (textInput) {
        textInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitCurrent('');
            }
        });
    }

    updateAvatarUi();
})();
