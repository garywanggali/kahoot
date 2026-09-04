/**
 * Shoot Match Analytics System
 * Provides multi-dimensional post-game review:
 * 1. By Question: see who got each question right and who got it wrong
 * 2. By Player: see which questions each player got right and which they got wrong
 */
(function (global) {
    'use strict';

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }

    function _t(key, ...args) {
        if (typeof window !== 'undefined' && window.t) {
            return window.t(key, ...args);
        }
        return key;
    }

    class AnalyticsRenderer {
        constructor(containerEl, data) {
            this.container = typeof containerEl === 'string' ? document.getElementById(containerEl) : containerEl;
            this.data = data;
            this.currentTab = 'question'; // 'question' or 'player'
            this.searchQuery = '';
            this.filterQuestionType = 'all';
            this.expandedQuestions = new Set();
            this.expandedPlayers = new Set();

            if (this.data && this.data.by_questions && this.data.by_questions.length > 0) {
                // By default expand first 2 questions and first 2 players
                this.expandedQuestions.add(this.data.by_questions[0].id);
                if (this.data.by_questions.length > 1) {
                    this.expandedQuestions.add(this.data.by_questions[1].id);
                }
            }
            if (this.data && this.data.by_players && this.data.by_players.length > 0) {
                this.expandedPlayers.add(this.data.by_players[0].id);
            }
        }

        render() {
            if (!this.container) return;
            const isEn = window.ShootI18n ? window.ShootI18n.isEn() : false;

            if (!this.data) {
                this.container.innerHTML = `
                    <div class="analytics-loading">
                        <div class="host-radar-wrap"><div class="host-radar-ping"></div></div>
                        <p>${isEn ? 'Calculating match analytics, please wait…' : '数据分析计算中，请稍候…'}</p>
                    </div>
                `;
                return;
            }

            const summary = this.data.summary || {};
            const html = `
                <div class="analytics-wrapper">
                    <!-- 1. KPI 概览指标条 -->
                    <div class="analytics-kpi-grid">
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">${_t('analytics.kpi_players')}</span>
                            <div class="kpi-value">${summary.total_players || 0}<span class="kpi-unit">${_t('analytics.unit_person')}</span></div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">${_t('analytics.kpi_accuracy')}</span>
                            <div class="kpi-value ${summary.has_scored_questions === false ? 'text-muted' : ((summary.overall_accuracy || 0) >= 60 ? 'text-success' : 'text-warning')}">${summary.has_scored_questions === false ? (isEn ? 'N/A' : '不适用') : `${summary.overall_accuracy || 0}%`}</div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">${_t('analytics.kpi_avg_score')}</span>
                            <div class="kpi-value">${summary.avg_score || 0}<span class="kpi-unit">${_t('analytics.unit_score')}</span></div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">${_t('analytics.kpi_max_score')}</span>
                            <div class="kpi-value text-accent">${summary.highest_score || 0}<span class="kpi-unit">${_t('analytics.unit_score')}</span></div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">${_t('analytics.kpi_questions')}</span>
                            <div class="kpi-value">${summary.total_questions || 0}<span class="kpi-unit">${_t('analytics.unit_question')}</span></div>
                        </div>
                    </div>

                    <!-- 2. 视角切换开关 (View Tabs) -->
                    <div class="analytics-tab-header">
                        <div class="analytics-tabs" role="tablist">
                            <button type="button" class="analytics-tab-btn ${this.currentTab === 'question' ? 'active' : ''}" data-tab="question">
                                <span>${_t('analytics.tab_by_question')}</span>
                            </button>
                            <button type="button" class="analytics-tab-btn ${this.currentTab === 'player' ? 'active' : ''}" data-tab="player">
                                <span>${_t('analytics.tab_by_player')}</span>
                            </button>
                        </div>

                        ${summary.hardest_question ? `
                            <div class="analytics-spotlight-pill" title="${isEn ? 'Question with lowest accuracy rate' : '全场得分率最低的易错题目'}">
                                <span>${_t('analytics.spotlight_hardest', summary.hardest_question.order, summary.hardest_question.accuracy)}</span>
                            </div>
                        ` : (summary.has_scored_questions === false ? `
                            <div class="analytics-spotlight-pill" title="${isEn ? 'No scored questions in this match' : '本场没有计分题'}">
                                <span>${isEn ? 'Explanation / interactive only — no accuracy stats' : '本场均为讲解/互动题，无正确率统计'}</span>
                            </div>
                        ` : '')}
                    </div>

                    <!-- 3. 主体分析内容区 -->
                    <div class="analytics-tab-body">
                        ${this.currentTab === 'question' ? this.renderQuestionView() : this.renderPlayerView()}
                    </div>
                </div>
            `;

            this.container.innerHTML = html;
            this.bindEvents();
        }

        renderQuestionView() {
            const list = this.data.by_questions || [];
            const isEn = window.ShootI18n ? window.ShootI18n.isEn() : false;

            if (list.length === 0) {
                return `<div class="analytics-empty">${isEn ? 'No question analytics data available' : '本房间暂无试题数据'}</div>`;
            }

            return `
                <div class="analytics-question-list">
                    ${list.map(q => {
                        const isExpanded = this.expandedQuestions.has(q.id);
                        const accRate = q.accuracy_percent;
                        let accClass = 'badge-success';
                        if (q.is_explanation || q.is_unscored) accClass = 'badge-neutral';
                        else if (accRate == null) accClass = 'badge-neutral';
                        else if (accRate < 50) accClass = 'badge-danger';
                        else if (accRate < 75) accClass = 'badge-warning';

                        const correctPlayers = q.correct_players || [];
                        const wrongPlayers = q.wrong_players || [];
                        const unansweredPlayers = q.unanswered_players || [];

                        const qIndexStr = isEn ? `Q${q.order}` : `第 ${q.order} 题`;
                        const typeLabel = (isEn && _t('qtype.label.' + q.question_type)) ? _t('qtype.label.' + q.question_type) : q.type_label;
                        const accBadgeText = q.is_explanation
                            ? (isEn ? 'Explanation' : '讲解')
                            : (q.is_word_cloud ? (isEn ? 'Interactive' : '互动题') : (isEn ? `Accuracy ${accRate ?? 0}%` : `正确率 ${accRate ?? 0}%`));
                        const countsText = q.is_explanation
                            ? (isEn ? 'Students do not answer' : '学生无需作答')
                            : (isEn
                                ? `${q.correct_count || 0} correct · ${(q.wrong_count || 0) + (q.unanswered_count || 0)} wrong/unanswered`
                                : `${q.correct_count || 0} 对 · ${(q.wrong_count || 0) + (q.unanswered_count || 0)} 错/未答`);
                        const foldBtnText = isExpanded
                            ? (isEn ? 'Collapse' : '收起')
                            : (isEn ? 'View Students' : '展开名单');

                        return `
                            <div class="analytics-card ${isExpanded ? 'is-expanded' : ''}" data-q-id="${q.id}">
                                <!-- 试题头部折叠栏 -->
                                <div class="analytics-card-header" data-toggle-q="${q.id}">
                                    <div class="q-header-left">
                                        <span class="q-index-pill">${qIndexStr}</span>
                                        <span class="q-type-badge">${escapeHtml(typeLabel)}</span>
                                        <h3 class="q-stem-title">${escapeHtml(q.text)}</h3>
                                    </div>
                                    <div class="q-header-right">
                                        <div class="q-acc-stat">
                                            <span class="q-acc-badge ${accClass}">${accBadgeText}</span>
                                            <span class="q-acc-count">${countsText}</span>
                                        </div>
                                        <button type="button" class="btn-toggle-fold" aria-label="${isEn ? 'Toggle details' : '展开或收起'}">
                                            ${foldBtnText}
                                        </button>
                                    </div>
                                </div>

                                <!-- 展开详情区 -->
                                ${isExpanded ? `
                                    <div class="analytics-card-content">
                                        ${q.is_explanation ? `
                                            <div class="q-correct-answer-strip">
                                                <span class="strip-label">${isEn ? 'Note: ' : '题型说明：'}</span>
                                                <span class="strip-value">${isEn ? 'Teacher explanation slide. Students do not see or answer it.' : '教师讲解知识点，学生端不显示、无需作答'}</span>
                                            </div>
                                            ${q.image_url ? `<div class="q-explanation-thumb"><img src="${escapeHtml(q.image_url)}" alt="${isEn ? 'Explanation image' : '讲解图片'}"></div>` : ''}
                                        ` : `
                                        <!-- 标准答案条 -->
                                        <div class="q-correct-answer-strip">
                                            <span class="strip-label">${isEn ? 'Correct Answer: ' : '标准答案：'}</span>
                                            <span class="strip-value">${escapeHtml(q.correct_answer_display || '—')}</span>
                                        </div>

                                        <!-- 学生正误对比两栏网格 -->
                                        <div class="q-split-grid">
                                            <!-- 左栏：答对学生名单 -->
                                            <div class="q-split-col col-correct">
                                                <div class="col-head">
                                                    <div class="col-title-group">
                                                        <strong>${isEn ? 'Correct Students' : '答对学生名单'}</strong>
                                                    </div>
                                                    <span class="col-badge badge-green">${correctPlayers.length} ${isEn ? 'players' : '人'}</span>
                                                </div>
                                                <div class="col-player-list">
                                                    ${correctPlayers.length === 0 ? `
                                                        <div class="col-empty text-muted">${isEn ? 'No students got this right' : '本题全员未答对'}</div>
                                                    ` : correctPlayers.map(p => this.renderPlayerAnswerChip(p, true, q.is_word_cloud)).join('')}
                                                </div>
                                            </div>

                                            <!-- 右栏：答错或未答学生名单 -->
                                            <div class="q-split-col col-wrong">
                                                <div class="col-head">
                                                    <div class="col-title-group">
                                                        <strong>${isEn ? 'Incorrect / Unanswered' : '答错 / 未答名单'}</strong>
                                                    </div>
                                                    <span class="col-badge badge-red">${wrongPlayers.length + unansweredPlayers.length} ${isEn ? 'players' : '人'}</span>
                                                </div>
                                                <div class="col-player-list">
                                                    ${(wrongPlayers.length + unansweredPlayers.length) === 0 ? `
                                                        <div class="col-empty text-success">${isEn ? 'All students answered correctly!' : '全员答对，表现优异'}</div>
                                                    ` : `
                                                        ${wrongPlayers.map(p => this.renderPlayerAnswerChip(p, false, false)).join('')}
                                                        ${unansweredPlayers.map(p => this.renderUnansweredPlayerChip(p)).join('')}
                                                    `}
                                                </div>
                                            </div>
                                        </div>
                                        `}
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        renderPlayerAnswerChip(p, isCorrect, isWordCloud) {
            const isEn = window.ShootI18n ? window.ShootI18n.isEn() : false;
            let avatarSvg = `<span class="chip-avatar-fallback">${escapeHtml((p.nickname || '?').slice(0, 1))}</span>`;
            try {
                if (window.AvatarSystem) {
                    avatarSvg = window.AvatarSystem.renderSvg(p.avatar, 30, { nickname: p.nickname });
                }
            } catch (err) {
                console.warn('Avatar render failed', err);
            }

            const optPrefix = isEn ? 'Option: ' : '选项：';
            const ptsUnit = isEn ? 'pts' : '分';
            const secUnit = isEn ? 's' : '秒';

            return `
                <div class="analytics-player-chip ${isCorrect ? 'chip-correct' : 'chip-wrong'}">
                    <div class="chip-left">
                        <div class="chip-avatar">${avatarSvg}</div>
                        <div class="chip-meta">
                            <span class="chip-name" title="${escapeHtml(p.nickname)}">${escapeHtml(p.nickname)}</span>
                            <span class="chip-selection" title="${isEn ? 'Selected: ' : '所选：'}${escapeHtml(p.selected_display || p.selected)}">
                                ${optPrefix}<strong>${escapeHtml(p.selected_display || p.selected || '—')}</strong>
                            </span>
                        </div>
                    </div>
                    <div class="chip-right">
                        ${isWordCloud ? '' : `<span class="chip-score ${isCorrect ? 'text-green' : 'text-gray'}">+${p.points}${ptsUnit}</span>`}
                        <span class="chip-time">${p.response_time_sec}${secUnit}</span>
                    </div>
                </div>
            `;
        }

        renderUnansweredPlayerChip(p) {
            const isEn = window.ShootI18n ? window.ShootI18n.isEn() : false;
            let avatarSvg = `<span class="chip-avatar-fallback">${escapeHtml((p.nickname || '?').slice(0, 1))}</span>`;
            try {
                if (window.AvatarSystem) {
                    avatarSvg = window.AvatarSystem.renderSvg(p.avatar, 28, { nickname: p.nickname });
                }
            } catch (err) {
                console.warn('Avatar render failed', err);
            }

            return `
                <div class="analytics-player-chip chip-unanswered">
                    <div class="chip-left">
                        <div class="chip-avatar">${avatarSvg}</div>
                        <div class="chip-meta">
                            <span class="chip-name">${escapeHtml(p.nickname)}</span>
                            <span class="chip-selection text-muted">${isEn ? 'Did not submit' : '未提交答案'}</span>
                        </div>
                    </div>
                    <div class="chip-right">
                        <span class="badge-unanswered">${isEn ? 'Unanswered' : '未作答'}</span>
                    </div>
                </div>
            `;
        }

        renderPlayerView() {
            const list = this.data.by_players || [];
            const isEn = window.ShootI18n ? window.ShootI18n.isEn() : false;

            if (list.length === 0) {
                return `<div class="analytics-empty">${isEn ? 'No participating players in this room' : '本房间暂无参与学生'}</div>`;
            }

            return `
                <div class="analytics-player-grid">
                    ${list.map(p => {
                        const isExpanded = this.expandedPlayers.has(p.id);
                        let avatarSvg = `<span class="player-big-avatar-fallback">${escapeHtml((p.nickname || '?').slice(0, 1))}</span>`;
                        try {
                            if (window.AvatarSystem) {
                                avatarSvg = window.AvatarSystem.renderSvg(p.avatar, 46, { nickname: p.nickname });
                            }
                        } catch (err) {
                            console.warn('Avatar render failed', err);
                        }

                        const rankIcon = p.rank === 1
                            ? (isEn ? '#1 Champion' : '第 1 名 (冠军)')
                            : (p.rank === 2
                                ? (isEn ? '#2 Runner-up' : '第 2 名 (亚军)')
                                : (p.rank === 3
                                    ? (isEn ? '#3 3rd Place' : '第 3 名 (季军)')
                                    : `#${p.rank}`));
                        const rankClass = p.rank === 1 ? 'rank-gold' : (p.rank === 2 ? 'rank-silver' : (p.rank === 3 ? 'rank-bronze' : ''));

                        const correctQs = p.correct_questions || [];
                        const wrongQs = p.wrong_questions || [];
                        const unansweredQs = p.unanswered_questions || [];

                        const scorePill = isEn ? `Score: <strong>${p.score}</strong>` : `总分 <strong>${p.score}</strong>`;
                        const accPill = (p.accuracy_percent == null || p.has_scored_questions === false)
                            ? (isEn ? 'Accuracy: <strong>N/A</strong>' : '正确率 <strong>不适用</strong>')
                            : (isEn ? `Accuracy: <strong>${p.accuracy_percent}%</strong>` : `正确率 <strong>${p.accuracy_percent}%</strong>`);
                        const countsPill = isEn
                            ? `${p.correct_count || 0} correct · ${(p.wrong_count || 0) + (p.unanswered_count || 0)} wrong`
                            : `${p.correct_count || 0} 对 · ${(p.wrong_count || 0) + (p.unanswered_count || 0)} 错`;
                        const foldBtnText = isExpanded
                            ? (isEn ? 'Collapse List' : '收起错对题单')
                            : (isEn ? 'View Performance' : '查看对题与错题');

                        return `
                            <div class="analytics-card player-card ${isExpanded ? 'is-expanded' : ''} ${rankClass}" data-p-id="${p.id}">
                                <!-- 学生卡片头部 -->
                                <div class="player-card-header" data-toggle-p="${p.id}">
                                    <div class="p-header-left">
                                        <div class="p-card-avatar">${avatarSvg}</div>
                                        <div class="p-card-info">
                                            <div class="p-name-row">
                                                <span class="p-card-rank">${rankIcon}</span>
                                                <h3 class="p-card-name">${escapeHtml(p.nickname)}</h3>
                                            </div>
                                            <div class="p-stat-badges">
                                                <span class="p-pill p-pill-score">${scorePill}</span>
                                                <span class="p-pill p-pill-acc">${accPill}</span>
                                                <span class="p-pill p-pill-counts">${countsPill}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="p-header-right">
                                        <button type="button" class="btn-toggle-fold">
                                            ${foldBtnText}
                                        </button>
                                    </div>
                                </div>

                                <!-- 学生答题错对展开清单 -->
                                ${isExpanded ? `
                                    <div class="player-card-body">
                                        <div class="player-two-cols">
                                            <!-- 答对的题目 -->
                                            <div class="p-col p-col-correct">
                                                <div class="p-col-title">
                                                    <span>${isEn ? `Correct Questions (${correctQs.length})` : `答对题目 (${correctQs.length})`}</span>
                                                </div>
                                                <div class="p-q-list">
                                                    ${correctQs.length === 0 ? `
                                                        <div class="p-q-empty text-muted">${isEn ? 'No correct questions in this match' : '本场未答对题目'}</div>
                                                    ` : correctQs.map(q => {
                                                        const qIdx = isEn ? `Q${q.order}` : `第 ${q.order} 题`;
                                                        const qType = (isEn && _t('qtype.label.' + q.question_type)) ? _t('qtype.label.' + q.question_type) : q.type_label;
                                                        const qScore = isEn ? `+${q.points}pts (${q.response_time_sec}s)` : `+${q.points}分 (${q.response_time_sec}s)`;
                                                        return `
                                                            <div class="p-q-item p-q-item-correct">
                                                                <div class="p-q-top">
                                                                    <span class="p-q-index">${qIdx}</span>
                                                                    <span class="p-q-type">${escapeHtml(qType)}</span>
                                                                    <span class="p-q-score">${qScore}</span>
                                                                </div>
                                                                <div class="p-q-stem">${escapeHtml(q.text)}</div>
                                                                <div class="p-q-ans">
                                                                    <span class="text-label">${isEn ? 'Answer: ' : '作答：'}</span>
                                                                    <span class="text-value">${escapeHtml(q.selected_display || q.selected)}</span>
                                                                </div>
                                                            </div>
                                                        `;
                                                    }).join('')}
                                                </div>
                                            </div>

                                            <!-- 答错或未作答的题目 -->
                                            <div class="p-col p-col-wrong">
                                                <div class="p-col-title">
                                                    <span>${isEn ? `Incorrect / Unanswered (${wrongQs.length + unansweredQs.length})` : `答错 / 未作答题目 (${wrongQs.length + unansweredQs.length})`}</span>
                                                </div>
                                                <div class="p-q-list">
                                                    ${(wrongQs.length + unansweredQs.length) === 0 ? `
                                                        <div class="p-q-empty text-success">${isEn ? 'Perfect score, all correct!' : '全部答对，无错题'}</div>
                                                    ` : `
                                                        ${wrongQs.map(q => {
                                                            const qIdx = isEn ? `Q${q.order}` : `第 ${q.order} 题`;
                                                            const qType = (isEn && _t('qtype.label.' + q.question_type)) ? _t('qtype.label.' + q.question_type) : q.type_label;
                                                            return `
                                                                <div class="p-q-item p-q-item-wrong">
                                                                    <div class="p-q-top">
                                                                        <span class="p-q-index">${qIdx}</span>
                                                                        <span class="p-q-type">${escapeHtml(qType)}</span>
                                                                        <span class="p-q-time">${q.response_time_sec}s</span>
                                                                    </div>
                                                                    <div class="p-q-stem">${escapeHtml(q.text)}</div>
                                                                    <div class="p-q-ans-compare">
                                                                        <div class="compare-row wrong-row">
                                                                            <span class="tag-wrong">${isEn ? 'Selected' : '所选'}</span>
                                                                            <span class="val-wrong">${escapeHtml(q.selected_display || q.selected)}</span>
                                                                        </div>
                                                                        <div class="compare-row right-row">
                                                                            <span class="tag-right">${isEn ? 'Correct' : '正解'}</span>
                                                                            <span class="val-right">${escapeHtml(q.correct_answer_display)}</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            `;
                                                        }).join('')}
                                                        ${unansweredQs.map(q => {
                                                            const qIdx = isEn ? `Q${q.order}` : `第 ${q.order} 题`;
                                                            const qType = (isEn && _t('qtype.label.' + q.question_type)) ? _t('qtype.label.' + q.question_type) : q.type_label;
                                                            return `
                                                                <div class="p-q-item p-q-item-unanswered">
                                                                    <div class="p-q-top">
                                                                        <span class="p-q-index">${qIdx}</span>
                                                                        <span class="p-q-type">${escapeHtml(qType)}</span>
                                                                        <span class="badge-unanswered">${isEn ? 'Unanswered' : '未作答'}</span>
                                                                    </div>
                                                                    <div class="p-q-stem">${escapeHtml(q.text)}</div>
                                                                    <div class="p-q-ans-compare">
                                                                        <div class="compare-row right-row">
                                                                            <span class="tag-right">${isEn ? 'Correct' : '正解'}</span>
                                                                            <span class="val-right">${escapeHtml(q.correct_answer_display)}</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            `;
                                                        }).join('')}
                                                     `}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        bindEvents() {
            // Tab Switch
            this.container.querySelectorAll('.analytics-tab-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const tab = btn.dataset.tab;
                    if (tab && tab !== this.currentTab) {
                        this.currentTab = tab;
                        this.render();
                    }
                });
            });

            // Toggle Question Fold
            this.container.querySelectorAll('[data-toggle-q]').forEach(el => {
                el.addEventListener('click', (e) => {
                    const qId = parseInt(el.dataset.toggleQ, 10);
                    if (this.expandedQuestions.has(qId)) {
                        this.expandedQuestions.delete(qId);
                    } else {
                        this.expandedQuestions.add(qId);
                    }
                    this.render();
                });
            });

            // Toggle Player Fold
            this.container.querySelectorAll('[data-toggle-p]').forEach(el => {
                el.addEventListener('click', (e) => {
                    const pId = parseInt(el.dataset.toggleP, 10);
                    if (this.expandedPlayers.has(pId)) {
                        this.expandedPlayers.delete(pId);
                    } else {
                        this.expandedPlayers.add(pId);
                    }
                    this.render();
                });
            });
        }
    }

    async function loadAndRenderAnalytics(containerId, apiUrl) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const isEn = window.ShootI18n ? window.ShootI18n.isEn() : false;
        const renderer = new AnalyticsRenderer(container, null);
        renderer.render();

        try {
            const resp = await fetch(apiUrl);
            if (!resp.ok) {
                throw new Error(isEn ? `Failed to load analytics (HTTP ${resp.status})` : `获取分析失败 (HTTP ${resp.status})`);
            }
            const data = await resp.json();
            renderer.data = data;
            renderer.render();
            return data;
        } catch (err) {
            container.innerHTML = `
                <div class="analytics-error">
                    <p>⚠️ ${escapeHtml(err.message || (isEn ? 'Failed to load match analytics' : '加载对战数据分析失败'))}</p>
                    <button type="button" class="btn btn-outline btn-sm" onclick="location.reload()">${isEn ? 'Reload' : '重新加载'}</button>
                </div>
            `;
            throw err;
        }
    }

    global.AnalyticsRenderer = AnalyticsRenderer;
    global.loadAndRenderAnalytics = loadAndRenderAnalytics;

})(typeof window !== 'undefined' ? window : this);
