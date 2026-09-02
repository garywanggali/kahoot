(function () {
    const root = document.getElementById('kahoot-editor');
    if (!root) return;

    const quizId = root.dataset.quizId;
    let questions = Array.isArray(INITIAL_QUESTIONS) ? INITIAL_QUESTIONS.slice() : [];
    let activeIndex = questions.length > 0 ? 0 : -1;
    let correctKeys = new Set();

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
        previewImage: document.getElementById('preview-image'),
        mediaPlaceholder: document.getElementById('media-placeholder'),
        imageInput: document.getElementById('image-input'),
        removeImage: document.getElementById('btn-remove-image'),
        saveStatus: document.getElementById('save-status'),
        typeHint: document.getElementById('type-hint'),
        quizTitle: document.getElementById('quiz-title-input'),
        quizPublic: document.getElementById('quiz-public-input'),
    };

    function csrfToken() {
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    function typeLabel(t) {
        const map = {
            single: '单选',
            multiple: '多选',
            judgment: '判断',
            short_answer: '简答',
            word_cloud: '词云',
        };
        return map[t] || '单选';
    }

    function currentQuestion() {
        return activeIndex >= 0 ? questions[activeIndex] : null;
    }

    function renderList() {
        els.list.innerHTML = '';
        questions.forEach((q, i) => {
            const li = document.createElement('li');
            li.className = 'kahoot-editor-q-item' + (i === activeIndex ? ' active' : '');
            const label = (q.text || '').trim() || '（未填写题干）';
            li.innerHTML = `<span class="kahoot-editor-q-num">${i + 1}</span>
                <span class="kahoot-editor-q-label">${typeLabel(q.question_type)} · ${label.slice(0, 28)}</span>`;
            li.onclick = () => selectQuestion(i);
            els.list.appendChild(li);
        });
        if (questions.length === 0) {
            els.list.innerHTML = '<li class="kahoot-editor-q-empty">暂无题目，点击「+ 添加」</li>';
        }
    }

    function updateCorrectMarks() {
        document.querySelectorAll('.kahoot-editor-mark-correct').forEach(btn => {
            const key = btn.dataset.key;
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
        const isShort = type === 'short_answer';
        const isWord = type === 'word_cloud';
        const isJudgment = type === 'judgment';
        els.optionsPanel.classList.toggle('hidden', isShort || isWord);
        els.shortPanel.classList.toggle('hidden', !isShort);
        els.wordPanel.classList.toggle('hidden', !isWord);

        if (isJudgment) {
            els.optionA.placeholder = '正确';
            els.optionB.placeholder = '错误';
            els.optionC.parentElement.classList.add('hidden');
            els.optionD.parentElement.classList.add('hidden');
        } else if (!isShort && !isWord) {
            els.optionA.placeholder = '选项 A';
            els.optionB.placeholder = '选项 B';
            els.optionC.parentElement.classList.remove('hidden');
            els.optionD.parentElement.classList.remove('hidden');
        }

        if (type === 'multiple') {
            els.typeHint.textContent = '多选：可标记多个 ✓，须全部选对才得分';
        } else if (type === 'single') {
            els.typeHint.textContent = '单选：点击 ✓ 标记唯一正确答案';
        } else if (type === 'judgment') {
            els.typeHint.textContent = '判断：标记正确项为 A 或 B';
        } else if (type === 'short_answer') {
            els.typeHint.textContent = '简答：填写参考答案';
        } else {
            els.typeHint.textContent = '词云：学生自由输入';
        }
    }

    function fillForm(q) {
        els.text.value = q.text || '';
        els.type.value = q.question_type || 'single';
        els.time.value = String(q.time_limit || 20);
        els.optionA.value = q.question_type === 'judgment' ? (q.option_a || '正确') : (q.option_a || '');
        els.optionB.value = q.question_type === 'judgment' ? (q.option_b || '错误') : (q.option_b || '');
        els.optionC.value = q.option_c || '';
        els.optionD.value = q.option_d || '';
        els.shortCorrect.value = q.short_correct || q.option_a || '';
        applyTypeUi(els.type.value);
        loadCorrectFromQuestion(q);

        if (q.image_url) {
            els.previewImage.src = q.image_url;
            els.previewImage.classList.remove('hidden');
            els.mediaPlaceholder.classList.add('hidden');
            els.removeImage.classList.remove('hidden');
        } else {
            els.previewImage.removeAttribute('src');
            els.previewImage.classList.add('hidden');
            els.mediaPlaceholder.classList.remove('hidden');
            els.removeImage.classList.add('hidden');
        }
        els.previewNumber.textContent = questions.length
            ? `第 ${activeIndex + 1} / ${questions.length} 题（预览）`
            : '';
        els.saveStatus.textContent = '';
    }

    function selectQuestion(index) {
        if (index < 0 || index >= questions.length) {
            activeIndex = -1;
            renderList();
            return;
        }
        activeIndex = index;
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
        payload.append('time_limit', els.time.value);
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
        const opts = {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrfToken() },
        };
        if (body instanceof FormData) {
            opts.body = body;
        } else {
            opts.headers['Content-Type'] = 'application/x-www-form-urlencoded';
            opts.body = new URLSearchParams(body);
        }
        const res = await fetch(url, opts);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || '请求失败');
        }
        return data;
    }

    async function saveQuestion() {
        const q = currentQuestion();
        if (!q) return;
        els.saveStatus.textContent = '保存中…';
        try {
            const data = await apiPost(`/teacher/kahoot/${quizId}/questions/save/`, readFormToPayload());
            questions[activeIndex] = data.question;
            els.imageInput.value = '';
            els.removeImage.dataset.pendingRemove = '0';
            fillForm(data.question);
            renderList();
            els.saveStatus.textContent = '已保存';
        } catch (e) {
            els.saveStatus.textContent = e.message;
        }
    }

    async function addQuestion() {
        try {
            const data = await apiPost(`/teacher/kahoot/${quizId}/questions/add/`, new FormData());
            questions.push(data.question);
            selectQuestion(questions.length - 1);
        } catch (e) {
            alert(e.message);
        }
    }

    async function deleteQuestion() {
        const q = currentQuestion();
        if (!q || !q.id) return;
        if (!confirm('确定删除这道题？')) return;
        try {
            await apiPost(`/teacher/kahoot/${quizId}/questions/${q.id}/delete/`, new FormData());
            questions.splice(activeIndex, 1);
            selectQuestion(Math.min(activeIndex, questions.length - 1));
        } catch (e) {
            alert(e.message);
        }
    }

    async function saveMeta() {
        try {
            await apiPost(`/teacher/kahoot/${quizId}/meta/`, {
                title: els.quizTitle.value.trim(),
                is_public: els.quizPublic.checked ? '1' : '0',
            });
            els.saveStatus.textContent = '套题设置已保存';
        } catch (e) {
            alert(e.message);
        }
    }

    document.getElementById('btn-add-question').addEventListener('click', addQuestion);
    document.getElementById('btn-save-question').addEventListener('click', saveQuestion);
    document.getElementById('btn-delete-question').addEventListener('click', deleteQuestion);
    document.getElementById('btn-save-meta').addEventListener('click', saveMeta);

    els.type.addEventListener('change', () => {
        applyTypeUi(els.type.value);
        if (els.type.value === 'judgment') {
            if (!els.optionA.value) els.optionA.value = '正确';
            if (!els.optionB.value) els.optionB.value = '错误';
            correctKeys = new Set(['A']);
            updateCorrectMarks();
        }
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
        });
    });

    els.mediaPlaceholder.addEventListener('click', () => els.imageInput.click());
    els.imageInput.addEventListener('change', () => {
        const file = els.imageInput.files[0];
        if (!file) return;
        if (file.size > MAX_IMAGE_MB * 1024 * 1024) {
            alert(`图片不能超过 ${MAX_IMAGE_MB}MB`);
            return;
        }
        els.previewImage.src = URL.createObjectURL(file);
        els.previewImage.classList.remove('hidden');
        els.mediaPlaceholder.classList.add('hidden');
        els.removeImage.classList.remove('hidden');
        els.removeImage.dataset.pendingRemove = '0';
    });
    els.removeImage.addEventListener('click', (e) => {
        e.stopPropagation();
        els.imageInput.value = '';
        els.previewImage.removeAttribute('src');
        els.previewImage.classList.add('hidden');
        els.mediaPlaceholder.classList.remove('hidden');
        els.removeImage.classList.add('hidden');
        els.removeImage.dataset.pendingRemove = '1';
    });

    renderList();
    if (questions.length) selectQuestion(0);
})();
