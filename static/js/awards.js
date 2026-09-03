function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function _tr(key, fallback) {
    if (window._t) {
        const val = _t(key);
        if (val && val !== key) return val;
    }
    if (window.t) {
        const val = t(key);
        if (val && val !== key) return val;
    }
    return fallback;
}

function getRankBadge(rank) {
    const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
    if (rank === 1) {
        return {
            emoji: '👑',
            title: isEn ? '1st' : '第 1 名',
            label: '1st',
            colorClass: 'rank-badge-orange'
        };
    } else if (rank === 2) {
        return {
            emoji: '🥈',
            title: isEn ? '2nd' : '第 2 名',
            label: '2nd',
            colorClass: 'rank-badge-blue'
        };
    } else {
        return {
            emoji: '🥉',
            title: isEn ? '3rd' : '第 3 名',
            label: '3rd',
            colorClass: 'rank-badge-amber'
        };
    }
}

function renderPodiumSlot(rank, player) {
    const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
    const badge = getRankBadge(rank);
    const ptsUnit = isEn ? 'PTS' : '分';
    const emptyText = isEn ? 'Awaiting Winner' : '虚位以待';

    if (!player) {
        return `
            <div class="podium-slot podium-rank-${rank} podium-slot-empty">
                <div class="podium-slot-ghost-wrap">
                    <div class="podium-ghost-badge">${badge.emoji}</div>
                    <div class="podium-ghost-title">${badge.title}</div>
                    <div class="podium-ghost-hint">${emptyText}</div>
                </div>
                <div class="podium-stand podium-stand-${rank}">
                    <span class="podium-place-label">${rank}</span>
                </div>
            </div>
        `;
    }

    const name = escapeHtml(player.nickname);
    const score = player.score !== undefined ? player.score : 0;
    const avatarHtml = window.AvatarSystem
        ? `<div class="podium-avatar-wrap podium-avatar-rank-${rank}">
            ${window.AvatarSystem.renderSvg(player.avatar, rank === 1 ? 92 : 76, {
                nickname: player.nickname,
                podium: true,
                rank: rank,
            })}
           </div>`
        : `<div class="podium-avatar-fallback">${name.slice(0, 1).toUpperCase()}</div>`;

    return `
        <div class="podium-slot podium-rank-${rank}">
            <div class="podium-slot-hero-top">
                <div class="podium-crown-badge ${badge.colorClass}">
                    <span>${badge.emoji}</span>
                    <span>${badge.title}</span>
                </div>
                ${avatarHtml}
                <div class="podium-name" title="${name}">${name}</div>
                <div class="podium-score-pill">
                    <span class="score-val">${score}</span>
                    <span class="score-lbl">${ptsUnit}</span>
                </div>
            </div>
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

    const isEn = window.KahootI18n ? window.KahootI18n.isEn() : false;
    const podiumAria = isEn ? 'Top 3 Champions Podium' : '前三名荣誉领奖台';

    container.innerHTML = `
        <div class="podium-stage" role="list" aria-label="${podiumAria}">
            ${[2, 1, 3].map(rank => renderPodiumSlot(rank, byRank[rank])).join('')}
        </div>
    `;
}

function renderLeaderboardList(leaderboard, containerId, startRank = 1, options) {
    const container = document.getElementById(containerId);
    if (!container) return;

    options = options || {};
    const highlightNickname = options.highlightNickname || '';
    const maxRows = options.maxRows || 0;
    let rows = (leaderboard || []).filter(p => p.rank >= startRank);
    if (maxRows > 0) {
        const top = rows.slice(0, maxRows);
        if (highlightNickname) {
            const me = rows.find(p => p.nickname === highlightNickname);
            if (me && !top.some(p => p.nickname === me.nickname)) {
                top.push(me);
            }
        }
        rows = top;
    }
    if (rows.length === 0) {
        container.innerHTML = '';
        return;
    }

    const ptsUnit = window.t ? t('awards.pts_unit') : '分';

    container.innerHTML = rows.map(p => {
        const avatarSvg = window.AvatarSystem
            ? window.AvatarSystem.renderSvg(p.avatar, 32, { nickname: p.nickname })
            : `<span class="player-chip-avatar-fallback">${escapeHtml(p.nickname.slice(0, 1).toUpperCase())}</span>`;
        const meClass = highlightNickname && p.nickname === highlightNickname ? ' is-me' : '';
        const rankClass = p.rank <= 3 ? ` rank-${p.rank}` : '';

        return `
            <div class="host-lb-row${rankClass}${meClass}">
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
