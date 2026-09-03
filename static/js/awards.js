function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getMedalSvg(rank) {
    if (rank === 1) {
        // 金牌冠军奖章 (无任何emoji，高端矢量高光图标)
        return `
            <div class="podium-badge-svg badge-gold" title="冠军">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                    <path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/>
                </svg>
            </div>
        `;
    } else if (rank === 2) {
        // 银牌亚军星芒奖章
        return `
            <div class="podium-badge-svg badge-silver" title="亚军">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
            </div>
        `;
    } else {
        // 铜牌季军荣誉奖章
        return `
            <div class="podium-badge-svg badge-bronze" title="季军">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                    <path d="M12 15a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm-6.2 3.8l3.6-1.5 1.5 3.6 1.1-3.9 1.1 3.9 1.5-3.6 3.6 1.5-2.6-4.2a6.9 6.9 0 0 1-7.1 0l-2.7 4.2z"/>
                </svg>
            </div>
        `;
    }
}

function renderPodiumSlot(rank, player) {
    const name = player ? escapeHtml(player.nickname) : '—';
    const score = player ? player.score : null;
    const emptyClass = player ? '' : ' podium-slot-empty';

    return `
        <div class="podium-slot podium-rank-${rank}${emptyClass}">
            <div class="podium-badge-wrap">
                ${getMedalSvg(rank)}
            </div>
            <div class="podium-name">${name}</div>
            ${score !== null ? `<div class="podium-score-pill"><span class="score-val">${score}</span><span class="score-lbl">分</span></div>` : ''}
            <div class="podium-stand podium-stand-${rank}">
                <span class="podium-place-label">${rank}</span>
                <div class="podium-stand-glow"></div>
            </div>
        </div>
    `;
}

function renderPodium(leaderboard, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const list = leaderboard || [];
    const byRank = {
        1: list.find(p => p.rank === 1),
        2: list.find(p => p.rank === 2),
        3: list.find(p => p.rank === 3),
    };

    container.innerHTML = `
        <div class="podium-stage" role="list" aria-label="前三名荣誉领奖台">
            ${[2, 1, 3].map(rank => renderPodiumSlot(rank, byRank[rank])).join('')}
        </div>
    `;
}

function renderLeaderboardList(leaderboard, containerId, startRank = 1) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const rows = (leaderboard || []).filter(p => p.rank >= startRank);
    if (rows.length === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = rows.map(p => `
        <div class="host-lb-row">
            <div class="host-lb-rank">#${p.rank}</div>
            <div class="host-lb-avatar">${p.nickname.slice(0, 1).toUpperCase()}</div>
            <div class="host-lb-name">${escapeHtml(p.nickname)}</div>
            <div class="host-lb-score">${p.score} <span class="score-unit">分</span></div>
        </div>
    `).join('');
}

function renderAwardsCeremony(leaderboard, podiumId, listId, titleId) {
    renderPodium(leaderboard, podiumId);
    const rest = (leaderboard || []).filter(p => p.rank >= 4);
    renderLeaderboardList(leaderboard, listId, 4);
    if (titleId) {
        const title = document.getElementById(titleId);
        if (title) {
            title.classList.toggle('hidden', rest.length === 0);
        }
    }
}
