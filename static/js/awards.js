function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getMedalSvg(rank) {
    const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
    const title = rank === 1
        ? (isEn ? 'Champion' : '冠军')
        : (rank === 2 ? (isEn ? '2nd Place' : '亚军') : (isEn ? '3rd Place' : '季军'));

    if (rank === 1) {
        // 金牌冠军奖章 (矢量高光图标)
        return `
            <div class="podium-badge-svg badge-gold" title="${title}">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                    <path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3c0 .6-.4 1-1 1H6c-.6 0-1-.4-1-1v-1h14v1z"/>
                </svg>
            </div>
        `;
    } else if (rank === 2) {
        // 银牌亚军星芒奖章
        return `
            <div class="podium-badge-svg badge-silver" title="${title}">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
            </div>
        `;
    } else {
        // 铜牌季军荣誉奖章
        return `
            <div class="podium-badge-svg badge-bronze" title="${title}">
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
    const ptsUnit = window.t ? t('awards.pts_unit') : '分';

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
            <div class="podium-name" title="${name}">${name}</div>
            ${score !== null ? `<div class="podium-score-pill"><span class="score-val">${score}</span><span class="score-lbl">${ptsUnit}</span></div>` : ''}
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

    const podiumAria = window.t ? t('awards.ceremony') : '前三名荣誉领奖台';

    container.innerHTML = `
        <div class="podium-stage" role="list" aria-label="${podiumAria}">
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

    const ptsUnit = window.t ? t('awards.pts_unit') : '分';

    container.innerHTML = rows.map(p => {
        const avatarSvg = window.AvatarSystem
            ? window.AvatarSystem.renderSvg(p.avatar, 32, { nickname: p.nickname })
            : `<span class="player-chip-avatar-fallback">${escapeHtml(p.nickname.slice(0, 1).toUpperCase())}</span>`;

        return `
            <div class="host-lb-row">
                <div class="host-lb-rank">#${p.rank}</div>
                <div class="host-lb-avatar">${avatarSvg}</div>
                <div class="host-lb-name">${escapeHtml(p.nickname)}</div>
                <div class="host-lb-score">${p.score} <span class="score-unit">${ptsUnit}</span></div>
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
            if (window.t) {
                title.textContent = t('awards.full_ranking');
            }
        }
    }
}
