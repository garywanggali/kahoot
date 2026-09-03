function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderPodiumSlot(rank, player) {
    const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };
    const name = player ? escapeHtml(player.nickname) : '—';
    const score = player ? player.score : '';
    const emptyClass = player ? '' : ' podium-slot-empty';

    const avatarHtml = (player && window.AvatarSystem)
        ? `<div class="podium-avatar-wrap podium-avatar-rank-${rank}">
            ${window.AvatarSystem.renderSvg(player.avatar, rank === 1 ? 84 : 68, {
                nickname: player.nickname,
                podium: true,
                rank: rank,
            })}
           </div>`
        : '';

    return `
        <div class="podium-slot podium-rank-${rank}${emptyClass}">
            ${avatarHtml}
            <div class="podium-medal" aria-hidden="true">${medals[rank]}</div>
            <div class="podium-name" title="${name}">${name}</div>
            ${player ? `<div class="podium-score">${score} 分</div>` : ''}
            <div class="podium-stand podium-stand-${rank}">
                <span class="podium-place-label">${rank}</span>
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
        <div class="podium-stage" role="list" aria-label="前三名领奖台">
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

    container.innerHTML = rows.map(p => {
        const avatarSvg = window.AvatarSystem
            ? window.AvatarSystem.renderSvg(p.avatar, 30, { nickname: p.nickname })
            : `<span class="leaderboard-avatar-initial">${escapeHtml(p.nickname.slice(0, 1))}</span>`;

        return `
            <div class="leaderboard-item">
                <span class="leaderboard-rank">#${p.rank}</span>
                <span class="leaderboard-avatar-mini">${avatarSvg}</span>
                <span class="leaderboard-name">${escapeHtml(p.nickname)}</span>
                <span class="leaderboard-score">${p.score}</span>
            </div>
        `;
    }).join('');
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
