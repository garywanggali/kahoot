(function () {
    const root = document.getElementById('kahoot-editor');
    if (!root) return;

    const quizId = root.dataset.quizId;
    const dashboardUrl = root.dataset.dashboardUrl || '/teacher/';
    const AUTO_SAVE_DEBOUNCE_MS = 900;
    const AUTO_SAVE_INTERVAL_MS = 60 * 1000;

    function _t(key, ...args) {
        if (typeof window !== 'undefined' && window.t) {
            return window.t(key, ...args);
        }
        return key;
    }

    let questions = Array.isArray(INITIAL_QUESTIONS) ? INITIAL_QUESTIONS.slice() : [];
    let activeIndex = questions.length > 0 ? 0 : -1;
    let correctKeys = new Set();
    let dirty = false;
    let autoSaveTimer = null;
    let saveInFlight = null;
    let localImagePreviewUrl = null;

    function normalizeImageUrl(url) {
        if (!url) return '';
        if (url.startsWith('blob:') || url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/')) {
            return url;
        }
        return '/' + url.replace(/^\/+/, '');
    }

    function revokeLocalImagePreview() {
        if (localImagePreviewUrl) {
            URL.revokeObjectURL(localImagePreviewUrl);
            localImagePreviewUrl = null;
        }
    }

    function showQuestionImage(url) {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const src = normalizeImageUrl(url);
        if (!src) {
            els.previewImage.removeAttribute('src');
            els.previewImage.onerror = null;
            els.previewImage.classList.add('hidden');
            if (els.mediaPlaceholder) els.mediaPlaceholder.classList.remove('hidden');
            els.removeImage.classList.add('hidden');
            return;
        }
        els.previewImage.onerror = () => {
            if (localImagePreviewUrl && localImagePreviewUrl !== src) {
                showQuestionImage(localImagePreviewUrl);
                return;
            }
            setSaveStatus(isEn ? 'Failed to load image, please re-upload' : '图片加载失败，请重新上传');
        };
        els.previewImage.onload = () => {
            if (src !== localImagePreviewUrl) {
                revokeLocalImagePreview();
            }
        };
        els.previewImage.src = src;
        els.previewImage.classList.remove('hidden');
        if (els.mediaPlaceholder) els.mediaPlaceholder.classList.add('hidden');
        els.removeImage.classList.remove('hidden');
    }

    const els = {
        list: document.getElementById('question-list'),
        previewNumber: document.getElementById('preview-number'),
        text: document.getElementById('field-text'),
        type: document.getElementById('field-type'),
        time: document.getElementById('field-time'),
        optionA: document.getElementById('field-option-a'),
        optionB: document.getElementById('field-option-b'),
        optionC: document.getElementById('field-option-c'),
        optionD: document.getElementById('field-option-d'),
        shortCorrect: document.getElementById('field-short-correct'),
        optionsPanel: document.getElementById('options-panel'),
        shortPanel: document.getElementById('short-panel'),
        wordPanel: document.getElementById('wordcloud-panel'),
        explanationPanel: document.getElementById('explanation-panel'),
        preview: document.getElementById('editor-preview'),
        mediaZone: document.getElementById('media-zone'),
        mediaPlaceholderText: document.getElementById('media-placeholder-text'),
        previewImage: document.getElementById('preview-image'),
        mediaPlaceholder: document.getElementById('media-placeholder'),
        imageInput: document.getElementById('image-input'),
        removeImage: document.getElementById('btn-remove-image'),
        saveStatus: document.getElementById('save-status'),
        typeHint: document.getElementById('type-hint'),
        quizTitle: document.getElementById('quiz-title-input'),
        modalQuizPublic: document.getElementById('modal-quiz-public'),
        modalSaveChanges: document.getElementById('modal-save-changes'),
    };

    function setSaveStatus(msg) {
        if (els.saveStatus) els.saveStatus.textContent = msg || '';
    }

    function csrfToken() {
        const input = document.querySelector('#kahoot-editor input[name=csrfmiddlewaretoken]');
        if (input && input.value) return input.value;
        const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    function appendCsrf(formData) {
        const token = csrfToken();
        if (token && formData instanceof FormData && !formData.has('csrfmiddlewaretoken')) {
            formData.append('csrfmiddlewaretoken', token);
        }
        return formData;
    }

    function typeLabel(t) {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        if (isEn) {
            const mapEn = {
                single: 'Single',
                multiple: 'Multiple',
                judgment: 'True/False',
                short_answer: 'Short Answer',
                word_cloud: 'Word Cloud',
                explanation: 'Explain',
            };
            return mapEn[t] || 'Single';
        }
        const map = {
            single: '单选',
            multiple: '多选',
            judgment: '判断',
            short_answer: '简答',
            word_cloud: '词云',
            explanation: '解释',
        };
        return map[t] || '单选';
    }

    function currentQuestion() {
        return activeIndex >= 0 ? questions[activeIndex] : null;
    }

    function markDirty() {
        dirty = true;
        scheduleDebouncedAutoSave();
    }

    function scheduleDebouncedAutoSave() {
        if (autoSaveTimer) clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(() => {
            if (dirty && currentQuestion() && canAutoSaveCurrentQuestion()) {
                void saveQuestion({ silent: true });
            }
        }, AUTO_SAVE_DEBOUNCE_MS);
    }

    function renderList() {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        els.list.innerHTML = '';
        questions.forEach((q, i) => {
            const li = document.createElement('li');
            li.className = 'kahoot-editor-q-item' + (i === activeIndex ? ' active' : '');
            const isExplanation = (q.question_type === 'explanation');
            const emptyLabel = isEn ? '(Untitled question)' : '（未填写题干）';
            const rawLabel = (q.text || '').trim();
            const label = isExplanation
                ? (isEn ? 'Full-screen image' : '全屏图片')
                : (rawLabel || emptyLabel);
            li.innerHTML = `<span class="kahoot-editor-q-num">${i + 1}</span>
                <span class="kahoot-editor-q-label">${typeLabel(q.question_type)} · ${label.slice(0, 28)}</span>`;
            li.onclick = () => { void selectQuestion(i); };
            els.list.appendChild(li);
        });
        if (questions.length === 0) {
            els.list.innerHTML = `<li class="kahoot-editor-q-empty">${isEn ? 'No questions, click "+ Add"' : '暂无题目，点击「+ 添加」'}</li>`;
        }
    }

    function updateCorrectMarks() {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const markTitle = isEn ? 'Mark as correct' : '标为正确答案';
        document.querySelectorAll('.kahoot-editor-mark-correct').forEach(btn => {
            const key = btn.dataset.key;
            btn.title = markTitle;
            btn.classList.toggle('is-correct', correctKeys.has(key));
        });
    }

    function loadCorrectFromQuestion(q) {
        correctKeys = new Set(q.correct_option_keys || []);
        if (q.question_type === 'single' || q.question_type === 'judgment') {
            const k = (q.correct_option || 'A').toUpperCase();
            correctKeys = new Set([k]);
        }
        updateCorrectMarks();
    }

    function applyTypeUi(type) {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const isShort = type === 'short_answer';
        const isWord = type === 'word_cloud';
        const isExplanation = type === 'explanation';
        const isJudgment = type === 'judgment';
        els.optionsPanel.classList.toggle('hidden', isShort || isWord || isExplanation);
        els.shortPanel.classList.toggle('hidden', !isShort);
        els.wordPanel.classList.toggle('hidden', !isWord);
        if (els.explanationPanel) els.explanationPanel.classList.add('hidden');
        els.text.classList.toggle('hidden', isExplanation);
        if (els.preview) els.preview.classList.toggle('preview-explanation', isExplanation);
        if (els.mediaZone) els.mediaZone.classList.toggle('media-explanation', isExplanation);
        if (els.previewNumber) els.previewNumber.classList.toggle('hidden', isExplanation);
        const timerBar = document.querySelector('.kahoot-editor-timer');
        if (timerBar) timerBar.classList.toggle('hidden', isExplanation);
        const timeGroup = document.getElementById('time-limit-group');
        if (timeGroup) timeGroup.classList.toggle('hidden', isExplanation);
        if (els.mediaPlaceholderText) {
            els.mediaPlaceholderText.textContent = isExplanation
                ? (isEn ? 'Click to upload explanation image (required, one image, fills the screen)' : '点击上传解释图片（必填，仅一张，上课铺满屏幕）')
                : (isEn ? 'Click to upload question image (optional)' : '点击上传题目图片（可选）');
        }
        const timeLabel = document.querySelector('label[for="field-time"]');
        if (timeLabel) {
            timeLabel.textContent = isEn ? 'Time limit' : '答题时限';
        }
        if (els.removeImage) {
            els.removeImage.textContent = isExplanation
                ? (isEn ? 'Replace image' : '更换图片')
                : (isEn ? 'Remove image' : '移除图片');
        }

        if (isJudgment) {
            els.optionA.placeholder = isEn ? 'True' : '正确';
            els.optionB.placeholder = isEn ? 'False' : '错误';
            els.optionC.parentElement.classList.add('hidden');
            els.optionD.parentElement.classList.add('hidden');
        } else if (!isShort && !isWord && !isExplanation) {
            els.optionA.placeholder = isEn ? 'Option A' : '选项 A';
            els.optionB.placeholder = isEn ? 'Option B' : '选项 B';
            els.optionC.parentElement.classList.remove('hidden');
            els.optionD.parentElement.classList.remove('hidden');
        }

        if (type === 'multiple') {
            els.typeHint.textContent = isEn ? 'Multiple: Click ✓ on multiple options (at least 2)' : '多选：可标记多个 ✓，须全部选对才得分';
        } else if (type === 'single') {
            els.typeHint.textContent = isEn ? 'Single: Click ✓ to mark the single correct answer' : '单选：点击 ✓ 标记唯一正确答案';
        } else if (type === 'judgment') {
            els.typeHint.textContent = isEn ? 'True/False: Option A is True, B is False. Click ✓ to mark' : '判断：标记正确项为 A 或 B';
        } else if (type === 'short_answer') {
            els.typeHint.textContent = isEn ? 'Short Answer: Enter accepted text (separate with |)' : '简答：填写参考答案（多个用 | 分隔）';
        } else if (type === 'explanation') {
            els.typeHint.textContent = isEn
                ? 'Explanation: Upload one image that fills the classroom screen. No timer — tap Next when you finish talking. Students do not see or answer it.'
                : '解释：只上传一张图片，上课铺满大屏；不限时，讲完后点下一题。学生不看、不作答';
        } else {
            els.typeHint.textContent = isEn ? 'Word Cloud: Students submit text live without scoring' : '词云：学生自由输入实时聚合展示';
        }
    }

    function fillForm(q) {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        els.text.value = q.text || '';
        els.type.value = q.question_type || 'single';
        els.time.value = String(q.time_limit || 20);
        els.optionA.value = q.question_type === 'judgment' ? (q.option_a || (isEn ? 'True' : '正确')) : (q.option_a || '');
        els.optionB.value = q.question_type === 'judgment' ? (q.option_b || (isEn ? 'False' : '错误')) : (q.option_b || '');
        els.optionC.value = q.option_c || '';
        els.optionD.value = q.option_d || '';
        els.shortCorrect.value = q.short_correct || q.option_a || '';
        applyTypeUi(els.type.value);
        loadCorrectFromQuestion(q);

        if (q.image_url) {
            showQuestionImage(q.image_url);
        } else {
            revokeLocalImagePreview();
            showQuestionImage('');
        }
        els.previewNumber.textContent = questions.length
            ? (isEn ? `Question ${activeIndex + 1} / ${questions.length} (Preview)` : `第 ${activeIndex + 1} / ${questions.length} 题（预览）`)
            : '';
        if (!saveInFlight) setSaveStatus('');
    }

    async function selectQuestion(index) {
        if (index === activeIndex) return;
        if (dirty && currentQuestion()) {
            await saveQuestion({ silent: true });
        }
        if (index < 0 || index >= questions.length) {
            activeIndex = -1;
            renderList();
            return;
        }
        activeIndex = index;
        dirty = false;
        renderList();
        fillForm(questions[activeIndex]);
    }

    function readFormToPayload() {
        const type = els.type.value;
        const payload = new FormData();
        const q = currentQuestion();
        if (q && q.id) payload.append('question_id', q.id);
        payload.append('text', els.text.value.trim());
        payload.append('question_type', type);
        payload.append('time_limit', type === 'explanation' ? '0' : els.time.value);
        payload.append('option_a', els.optionA.value.trim());
        payload.append('option_b', els.optionB.value.trim());
        payload.append('option_c', els.optionC.value.trim());
        payload.append('option_d', els.optionD.value.trim());

        if (type === 'short_answer') {
            payload.append('short_correct', els.shortCorrect.value.trim());
        } else if (type === 'multiple') {
            correctKeys.forEach(k => payload.append('correct_options', k));
        } else if (type === 'judgment') {
            const k = correctKeys.has('B') ? 'B' : 'A';
            payload.append('judgment_correct', k);
        } else if (type === 'single') {
            const k = [...correctKeys][0] || 'A';
            payload.append('correct_option', k);
        }

        if (els.imageInput.files[0]) {
            payload.append('image', els.imageInput.files[0]);
        }
        if (els.removeImage.dataset.pendingRemove === '1') {
            payload.append('remove_image', '1');
        }
        return payload;
    }

    async function apiPost(url, body) {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const token = csrfToken();
        const opts = {
            method: 'POST',
            credentials: 'same-origin',
            headers: {},
        };
        if (token) {
            opts.headers['X-CSRFToken'] = token;
        }
        if (body instanceof FormData) {
            appendCsrf(body);
            opts.body = body;
        } else {
            const params = new URLSearchParams(body);
            if (token) params.set('csrfmiddlewaretoken', token);
            opts.headers['Content-Type'] = 'application/x-www-form-urlencoded';
            opts.body = params;
        }
        const res = await fetch(url, opts);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const fallback = res.status === 403
                ? (isEn ? 'CSRF verification failed, please refresh' : 'CSRF 校验失败，请刷新页面重试')
                : (isEn ? `Request failed (${res.status})` : `请求失败 (${res.status})`);
            throw new Error(data.error || fallback);
        }
        return data;
    }

    async function saveQuestion(options = {}) {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const silent = options.silent;
        const force = options.force;

        if (saveInFlight) {
            await saveInFlight;
            if (!force && silent) {
                return true;
            }
        }

        const q = currentQuestion();
        if (!q) return true;

        const task = (async () => {
            if (!silent) setSaveStatus(isEn ? 'Saving…' : '保存中…');
            try {
                const data = await apiPost(
                    `/teacher/kahoot/${quizId}/questions/save/`,
                    readFormToPayload(),
                );
                questions[activeIndex] = data.question;
                els.imageInput.value = '';
                els.removeImage.dataset.pendingRemove = '0';
                dirty = false;
                fillForm(data.question);
                renderList();
                if (silent) {
                    setSaveStatus(isEn ? 'Auto-saved' : '已自动保存');
                    showTopSaveToast(isEn ? 'Saved' : '已快速保存');
                } else {
                    setSaveStatus(isEn ? 'Saved' : '已保存');
                    showTopSaveToast(isEn ? 'Saved' : '已保存');
                }
                return true;
            } catch (e) {
                setSaveStatus(e.message);
                if (!silent) throw e;
                return false;
            }
        })();

        saveInFlight = task;
        try {
            return await task;
        } finally {
            if (saveInFlight === task) {
                saveInFlight = null;
            }
        }
    }

    async function saveQuizMeta(options = {}) {
        const silent = options.silent;
        const includePublic = options.includePublic === true;
        const payload = {
            title: els.quizTitle.value.trim(),
        };
        if (includePublic) {
            payload.is_public = els.modalQuizPublic && els.modalQuizPublic.checked ? '1' : '0';
        }
        try {
            await apiPost(`/teacher/kahoot/${quizId}/meta/`, payload);
            return true;
        } catch (e) {
            if (!silent) throw e;
            setSaveStatus(e.message);
            return false;
        }
    }

    async function saveAllChanges(options = {}) {
        const silent = options.silent;
        const forceQuestion = options.forceQuestion;
        const includePublic = options.includePublic === true;
        let questionHandled = !currentQuestion();

        if (currentQuestion()) {
            const shouldSaveQuestion = forceQuestion || canAutoSaveCurrentQuestion();
            if (shouldSaveQuestion) {
                await saveQuestion({ silent, force: forceQuestion });
                questionHandled = true;
            }
        }

        await saveQuizMeta({ silent, includePublic });

        if (questionHandled || !currentQuestion()) {
            dirty = false;
        }
        return true;
    }

    async function addQuestion() {
        if (dirty && currentQuestion()) {
            await saveQuestion({ silent: true });
        }
        try {
            const data = await apiPost(`/teacher/kahoot/${quizId}/questions/add/`, new FormData());
            questions.push(data.question);
            activeIndex = questions.length - 1;
            dirty = false;
            renderList();
            fillForm(data.question);
        } catch (e) {
            alert(e.message);
        }
    }

    async function deleteQuestion() {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const q = currentQuestion();
        if (!q || !q.id) return;
        if (!confirm(isEn ? 'Are you sure you want to delete this question?' : '确定删除这道题？')) return;
        try {
            await apiPost(`/teacher/kahoot/${quizId}/questions/${q.id}/delete/`, new FormData());
            questions.splice(activeIndex, 1);
            dirty = false;
            if (questions.length === 0) {
                activeIndex = -1;
                renderList();
                return;
            }
            activeIndex = Math.min(activeIndex, questions.length - 1);
            renderList();
            fillForm(questions[activeIndex]);
        } catch (e) {
            alert(e.message);
        }
    }

    let toastTimer = null;
    function showTopSaveToast(msg = '已快速保存', duration = 2200) {
        const banner = document.getElementById('save-toast-banner');
        const textEl = document.getElementById('save-toast-text');
        if (!banner) return;
        if (textEl) textEl.textContent = msg;
        banner.classList.remove('hidden');

        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            banner.classList.add('hidden');
        }, duration);
    }

    async function saveOnly() {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const btn = document.getElementById('btn-save-quiz');
        const label = btn ? btn.textContent : '';
        if (btn) {
            btn.disabled = true;
            btn.textContent = isEn ? 'Saving…' : '保存中…';
        }
        setSaveStatus(isEn ? 'Saving changes…' : '正在保存…');
        try {
            await saveAllChanges({ silent: false, forceQuestion: true });
            setSaveStatus(isEn ? '✓ All changes saved' : '✓ 已保存全部更改');
            showTopSaveToast(isEn ? 'Saved' : '已保存');
            setTimeout(() => setSaveStatus(''), 2500);
        } catch (e) {
            const msg = e.message || (isEn ? 'Failed to save' : '保存失败');
            setSaveStatus((isEn ? 'Save failed: ' : '保存失败：') + msg);
            alert(msg);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = label;
            }
        }
    }

    async function saveCurrentQuestion() {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        try {
            await saveQuestion({ silent: false });
        } catch (e) {
            alert(e.message || (isEn ? 'Failed to save' : '保存失败'));
        }
    }

    const exitModal = document.getElementById('exit-modal');
    const btnSaveQuiz = document.getElementById('btn-save-quiz');
    const btnExitQuiz = document.getElementById('btn-exit-quiz');
    const btnCancelExit = document.getElementById('btn-cancel-exit');
    const btnConfirmExit = document.getElementById('btn-confirm-exit');
    const btnTopBack = document.getElementById('btn-top-back');

    function openExitModal(e) {
        if (e) e.preventDefault();
        if (els.modalSaveChanges) {
            els.modalSaveChanges.checked = dirty;
        }
        if (exitModal) exitModal.classList.remove('hidden');
    }

    function closeExitModal() {
        if (exitModal) exitModal.classList.add('hidden');
    }

    async function confirmLeave() {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const shouldSave = els.modalSaveChanges ? els.modalSaveChanges.checked : false;
        const label = btnConfirmExit ? btnConfirmExit.textContent : (isEn ? 'Confirm & Exit' : '确认离开');

        try {
            if (btnConfirmExit) {
                btnConfirmExit.disabled = true;
                btnConfirmExit.textContent = isEn ? 'Processing…' : '处理中…';
            }

            if (shouldSave) {
                await saveAllChanges({
                    silent: false,
                    forceQuestion: true,
                    includePublic: true,
                });
            } else {
                await saveQuizMeta({ silent: false, includePublic: true });
            }

            window.location.href = dashboardUrl;
        } catch (e) {
            alert((isEn ? 'Failed to exit: ' : '离开失败：') + (e.message || (isEn ? 'Action failed' : '操作失败')));
            if (btnConfirmExit) {
                btnConfirmExit.disabled = false;
                btnConfirmExit.textContent = label;
            }
        }
    }

    document.getElementById('btn-add-question').addEventListener('click', addQuestion);
    document.getElementById('btn-delete-question').addEventListener('click', deleteQuestion);
    if (btnSaveQuiz) btnSaveQuiz.addEventListener('click', () => { void saveOnly(); });
    if (btnExitQuiz) btnExitQuiz.addEventListener('click', openExitModal);
    if (btnTopBack) btnTopBack.addEventListener('click', openExitModal);
    if (btnCancelExit) btnCancelExit.addEventListener('click', closeExitModal);
    if (btnConfirmExit) btnConfirmExit.addEventListener('click', () => { void confirmLeave(); });

    const saveQuestionBtn = document.getElementById('btn-save-question');
    if (saveQuestionBtn) {
        saveQuestionBtn.addEventListener('click', () => { void saveCurrentQuestion(); });
    }

    if (exitModal) {
        exitModal.addEventListener('click', (e) => {
            if (e.target === exitModal) closeExitModal();
        });
    }

    const watchEls = [
        els.text, els.type, els.time,
        els.optionA, els.optionB, els.optionC, els.optionD,
        els.shortCorrect, els.quizTitle,
    ];
    watchEls.forEach(el => {
        if (!el) return;
        el.addEventListener('input', markDirty);
        el.addEventListener('change', markDirty);
    });

    els.type.addEventListener('change', () => {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        applyTypeUi(els.type.value);
        if (els.type.value === 'judgment') {
            if (!els.optionA.value) els.optionA.value = isEn ? 'True' : '正确';
            if (!els.optionB.value) els.optionB.value = isEn ? 'False' : '错误';
            correctKeys = new Set(['A']);
            updateCorrectMarks();
        } else if (els.type.value !== 'explanation' && els.text.value === '解释') {
            els.text.value = '';
        }
        markDirty();
    });

    document.querySelectorAll('.kahoot-editor-mark-correct').forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.key;
            const type = els.type.value;
            if (type === 'multiple') {
                if (correctKeys.has(key)) correctKeys.delete(key);
                else correctKeys.add(key);
            } else {
                correctKeys = new Set([key]);
            }
            updateCorrectMarks();
            markDirty();
        });
    });

    if (els.mediaZone) {
        els.mediaZone.addEventListener('click', (e) => {
            if (e.target.closest('#btn-remove-image')) return;
            els.imageInput.click();
        });
    }
    els.imageInput.addEventListener('change', () => {
        const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
        const file = els.imageInput.files[0];
        if (!file) return;
        if (file.size > MAX_IMAGE_MB * 1024 * 1024) {
            alert(isEn ? `Image cannot exceed ${MAX_IMAGE_MB}MB` : `图片不能超过 ${MAX_IMAGE_MB}MB`);
            return;
        }
        revokeLocalImagePreview();
        localImagePreviewUrl = URL.createObjectURL(file);
        showQuestionImage(localImagePreviewUrl);
        els.removeImage.dataset.pendingRemove = '0';
        markDirty();
        if (canAutoSaveCurrentQuestion()) {
            void saveQuestion({ silent: true });
        }
    });
    els.removeImage.addEventListener('click', (e) => {
        e.stopPropagation();
        if (els.type.value === 'explanation') {
            els.imageInput.click();
            return;
        }
        els.imageInput.value = '';
        revokeLocalImagePreview();
        showQuestionImage('');
        els.removeImage.dataset.pendingRemove = '1';
        markDirty();
    });

    function canAutoSaveCurrentQuestion() {
        if (!currentQuestion()) return false;
        if (els.type.value === 'explanation') {
            const hasFile = !!(els.imageInput.files && els.imageInput.files[0]);
            const keepExisting = !!(currentQuestion().image_url && els.removeImage.dataset.pendingRemove !== '1');
            return hasFile || keepExisting;
        }
        return true;
    }

    async function runPeriodicAutoSave() {
        if (!dirty) return;
        try {
            await saveAllChanges({ silent: true, forceQuestion: false });
        } catch {
            /* 定时保存失败不打断编辑 */
        }
    }

    setInterval(runPeriodicAutoSave, AUTO_SAVE_INTERVAL_MS);

    renderList();
    if (questions.length) {
        activeIndex = 0;
        fillForm(questions[0]);
    }
})();
