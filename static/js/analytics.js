/**
 * Kahoot Match Analytics System
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
            if (!this.data) {
                this.container.innerHTML = `
                    <div class="analytics-loading">
                        <div class="host-radar-wrap"><div class="host-radar-ping"></div></div>
                        <p>数据分析计算中，请稍候…</p>
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
                            <span class="kpi-label">参战学生</span>
                            <div class="kpi-value">${summary.total_players || 0}<span class="kpi-unit">人</span></div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">全场综合正确率</span>
                            <div class="kpi-value ${summary.overall_accuracy >= 60 ? 'text-success' : 'text-warning'}">${summary.overall_accuracy || 0}%</div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">平均积分</span>
                            <div class="kpi-value">${summary.avg_score || 0}<span class="kpi-unit">分</span></div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">最高得分</span>
                            <div class="kpi-value text-accent">${summary.highest_score || 0}<span class="kpi-unit">分</span></div>
                        </div>
                        <div class="analytics-kpi-card">
                            <span class="kpi-label">试题总数</span>
                            <div class="kpi-value">${summary.total_questions || 0}<span class="kpi-unit">题</span></div>
                        </div>
                    </div>

                    <!-- 2. 视角切换开关 (View Tabs) -->
                    <div class="analytics-tab-header">
                        <div class="analytics-tabs" role="tablist">
                            <button type="button" class="analytics-tab-btn ${this.currentTab === 'question' ? 'active' : ''}" data-tab="question">
                                <span>按题目分析 (正误名单)</span>
                            </button>
                            <button type="button" class="analytics-tab-btn ${this.currentTab === 'player' ? 'active' : ''}" data-tab="player">
                                <span>按学生分析 (错对题单)</span>
                            </button>
                        </div>

                        ${summary.hardest_question ? `
                            <div class="analytics-spotlight-pill" title="全场得分率最低的易错题目">
                                <span>易错题：第 ${summary.hardest_question.order} 题 (正确率 ${summary.hardest_question.accuracy}%)</span>
                            </div>
                        ` : ''}
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
            if (list.length === 0) {
                return '<div class="analytics-empty">本房间暂无试题数据</div>';
            }

            return `
                <div class="analytics-question-list">
                    ${list.map(q => {
                        const isExpanded = this.expandedQuestions.has(q.id);
                        const accRate = q.accuracy_percent;
                        let accClass = 'badge-success';
                        if (accRate < 50) accClass = 'badge-danger';
                        else if (accRate < 75) accClass = 'badge-warning';

                        const correctPlayers = q.correct_players || [];
                        const wrongPlayers = q.wrong_players || [];
                        const unansweredPlayers = q.unanswered_players || [];

                        return `
                            <div class="analytics-card ${isExpanded ? 'is-expanded' : ''}" data-q-id="${q.id}">
                                <!-- 试题头部折叠栏 -->
                                <div class="analytics-card-header" data-toggle-q="${q.id}">
                                    <div class="q-header-left">
                                        <span class="q-index-pill">第 ${q.order} 题</span>
                                        <span class="q-type-badge">${escapeHtml(q.type_label)}</span>
                                        <h3 class="q-stem-title">${escapeHtml(q.text)}</h3>
                                    </div>
                                    <div class="q-header-right">
                                        <div class="q-acc-stat">
                                            <span class="q-acc-badge ${accClass}">${q.is_word_cloud ? '互动题' : `正确率 ${accRate}%`}</span>
                                            <span class="q-acc-count">${q.correct_count} 对 · ${q.wrong_count + q.unanswered_count} 错/未答</span>
                                        </div>
                                        <button type="button" class="btn-toggle-fold" aria-label="展开或收起">
                                            ${isExpanded ? '收起' : '展开名单'}
                                        </button>
                                    </div>
                                </div>

                                <!-- 展开详情区 -->
                                ${isExpanded ? `
                                    <div class="analytics-card-content">
                                        <!-- 标准答案条 -->
                                        <div class="q-correct-answer-strip">
                                            <span class="strip-label">标准答案：</span>
                                            <span class="strip-value">${escapeHtml(q.correct_answer_display || '—')}</span>
                                        </div>

                                        <!-- 学生正误对比两栏网格 -->
                                        <div class="q-split-grid">
                                            <!-- 左栏：答对学生名单 -->
                                            <div class="q-split-col col-correct">
                                                <div class="col-head">
                                                    <div class="col-title-group">
                                                        <strong>答对学生名单</strong>
                                                    </div>
                                                    <span class="col-badge badge-green">${correctPlayers.length} 人</span>
                                                </div>
                                                <div class="col-player-list">
                                                    ${correctPlayers.length === 0 ? `
                                                        <div class="col-empty text-muted">本题全员未答对</div>
                                                    ` : correctPlayers.map(p => this.renderPlayerAnswerChip(p, true, q.is_word_cloud)).join('')}
                                                </div>
                                            </div>

                                            <!-- 右栏：答错或未答学生名单 -->
                                            <div class="q-split-col col-wrong">
                                                <div class="col-head">
                                                    <div class="col-title-group">
                                                        <strong>答错 / 未答名单</strong>
                                                    </div>
                                                    <span class="col-badge badge-red">${wrongPlayers.length + unansweredPlayers.length} 人</span>
                                                </div>
                                                <div class="col-player-list">
                                                    ${(wrongPlayers.length + unansweredPlayers.length) === 0 ? `
                                                        <div class="col-empty text-success">全员答对，表现优异</div>
                                                    ` : `
                                                        ${wrongPlayers.map(p => this.renderPlayerAnswerChip(p, false, false)).join('')}
                                                        ${unansweredPlayers.map(p => this.renderUnansweredPlayerChip(p)).join('')}
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

        renderPlayerAnswerChip(p, isCorrect, isWordCloud) {
            const avatarSvg = window.AvatarSystem
                ? window.AvatarSystem.renderSvg(p.avatar, 30, { nickname: p.nickname })
                : `<span class="chip-avatar-fallback">${escapeHtml(p.nickname.slice(0, 1))}</span>`;

            return `
                <div class="analytics-player-chip ${isCorrect ? 'chip-correct' : 'chip-wrong'}">
                    <div class="chip-left">
                        <div class="chip-avatar">${avatarSvg}</div>
                        <div class="chip-meta">
                            <span class="chip-name" title="${escapeHtml(p.nickname)}">${escapeHtml(p.nickname)}</span>
                            <span class="chip-selection" title="所选：${escapeHtml(p.selected_display || p.selected)}">
                                选项：<strong>${escapeHtml(p.selected_display || p.selected || '—')}</strong>
                            </span>
                        </div>
                    </div>
                    <div class="chip-right">
                        ${isWordCloud ? '' : `<span class="chip-score ${isCorrect ? 'text-green' : 'text-gray'}">+${p.points}分</span>`}
                        <span class="chip-time">${p.response_time_sec}秒</span>
                    </div>
                </div>
            `;
        }

        renderUnansweredPlayerChip(p) {
            const avatarSvg = window.AvatarSystem
                ? window.AvatarSystem.renderSvg(p.avatar, 28, { nickname: p.nickname })
                : `<span class="chip-avatar-fallback">${escapeHtml(p.nickname.slice(0, 1))}</span>`;

            return `
                <div class="analytics-player-chip chip-unanswered">
                    <div class="chip-left">
                        <div class="chip-avatar">${avatarSvg}</div>
                        <div class="chip-meta">
                            <span class="chip-name">${escapeHtml(p.nickname)}</span>
                            <span class="chip-selection text-muted">未提交答案</span>
                        </div>
                    </div>
                    <div class="chip-right">
                        <span class="badge-unanswered">未作答</span>
                    </div>
                </div>
            `;
        }

        renderPlayerView() {
            const list = this.data.by_players || [];
            if (list.length === 0) {
                return '<div class="analytics-empty">本房间暂无参与学生</div>';
            }

            return `
                <div class="analytics-player-grid">
                    ${list.map(p => {
                        const isExpanded = this.expandedPlayers.has(p.id);
                        const avatarSvg = window.AvatarSystem
                            ? window.AvatarSystem.renderSvg(p.avatar, 46, { nickname: p.nickname })
                            : `<span class="player-big-avatar-fallback">${escapeHtml(p.nickname.slice(0, 1))}</span>`;

                        const rankIcon = p.rank === 1 ? '第 1 名 (冠军)' : (p.rank === 2 ? '第 2 名 (亚军)' : (p.rank === 3 ? '第 3 名 (季军)' : `#${p.rank}`));
                        const rankClass = p.rank === 1 ? 'rank-gold' : (p.rank === 2 ? 'rank-silver' : (p.rank === 3 ? 'rank-bronze' : ''));

                        const correctQs = p.correct_questions || [];
                        const wrongQs = p.wrong_questions || [];
                        const unansweredQs = p.unanswered_questions || [];

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
                                                <span class="p-pill p-pill-score">总分 <strong>${p.score}</strong></span>
                                                <span class="p-pill p-pill-acc">正确率 <strong>${p.accuracy_percent}%</strong></span>
                                                <span class="p-pill p-pill-counts">${p.correct_count} 对 · ${p.wrong_count + p.unanswered_count} 错</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="p-header-right">
                                        <button type="button" class="btn-toggle-fold">
                                            ${isExpanded ? '收起错对题单' : '查看对题与错题'}
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
                                                    <span>答对题目 (${correctQs.length})</span>
                                                </div>
                                                <div class="p-q-list">
                                                    ${correctQs.length === 0 ? `
                                                        <div class="p-q-empty text-muted">本场未答对题目</div>
                                                    ` : correctQs.map(q => `
                                                        <div class="p-q-item p-q-item-correct">
                                                            <div class="p-q-top">
                                                                <span class="p-q-index">第 ${q.order} 题</span>
                                                                <span class="p-q-type">${escapeHtml(q.type_label)}</span>
                                                                <span class="p-q-score">+${q.points}分 (${q.response_time_sec}s)</span>
                                                            </div>
                                                            <div class="p-q-stem">${escapeHtml(q.text)}</div>
                                                            <div class="p-q-ans">
                                                                <span class="text-label">作答：</span>
                                                                <span class="text-value">${escapeHtml(q.selected_display || q.selected)}</span>
                                                            </div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>

                                            <!-- 答错或未作答的题目 -->
                                            <div class="p-col p-col-wrong">
                                                <div class="p-col-title">
                                                    <span>答错 / 未作答题目 (${wrongQs.length + unansweredQs.length})</span>
                                                </div>
                                                <div class="p-q-list">
                                                    ${(wrongQs.length + unansweredQs.length) === 0 ? `
                                                        <div class="p-q-empty text-success">全部答对，无错题</div>
                                                    ` : `
                                                        ${wrongQs.map(q => `
                                                            <div class="p-q-item p-q-item-wrong">
                                                                <div class="p-q-top">
                                                                    <span class="p-q-index">第 ${q.order} 题</span>
                                                                    <span class="p-q-type">${escapeHtml(q.type_label)}</span>
                                                                    <span class="p-q-time">${q.response_time_sec}s</span>
                                                                </div>
                                                                <div class="p-q-stem">${escapeHtml(q.text)}</div>
                                                                <div class="p-q-ans-compare">
                                                                    <div class="compare-row wrong-row">
                                                                        <span class="tag-wrong">所选</span>
                                                                        <span class="val-wrong">${escapeHtml(q.selected_display || q.selected)}</span>
                                                                    </div>
                                                                    <div class="compare-row right-row">
                                                                        <span class="tag-right">正解</span>
                                                                        <span class="val-right">${escapeHtml(q.correct_answer_display)}</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        `).join('')}
                                                        ${unansweredQs.map(q => `
                                                            <div class="p-q-item p-q-item-unanswered">
                                                                <div class="p-q-top">
                                                                    <span class="p-q-index">第 ${q.order} 题</span>
                                                                    <span class="p-q-type">${escapeHtml(q.type_label)}</span>
                                                                    <span class="badge-unanswered">未作答</span>
                                                                </div>
                                                                <div class="p-q-stem">${escapeHtml(q.text)}</div>
                                                                <div class="p-q-ans-compare">
                                                                    <div class="compare-row right-row">
                                                                        <span class="tag-right">正解</span>
                                                                        <span class="val-right">${escapeHtml(q.correct_answer_display)}</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        `).join('')}
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
        const renderer = new AnalyticsRenderer(container, null);
        renderer.render();

        try {
            const resp = await fetch(apiUrl);
            if (!resp.ok) {
                throw new Error(`获取分析失败 (HTTP ${resp.status})`);
            }
            const data = await resp.json();
            renderer.data = data;
            renderer.render();
            return data;
        } catch (err) {
            container.innerHTML = `
                <div class="analytics-error">
                    <p>⚠️ ${escapeHtml(err.message || '加载对战数据分析失败')}</p>
                    <button type="button" class="btn btn-outline btn-sm" onclick="location.reload()">重新加载</button>
                </div>
            `;
            throw err;
        }
    }

    global.AnalyticsRenderer = AnalyticsRenderer;
    global.loadAndRenderAnalytics = loadAndRenderAnalytics;

})(typeof window !== 'undefined' ? window : this);
