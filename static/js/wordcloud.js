function renderWordCloud(containerId, words) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.classList.add('word-cloud-display');

    if (!words || words.length === 0) {
        const emptyMsg = window.t ? t('host.word_cloud_empty') : '暂无回答，等待大家提交...';
        container.innerHTML = `<p class="word-cloud-empty">${escapeWordCloudText(emptyMsg)}</p>`;
        return;
    }

    const maxCount = Math.max(...words.map(w => w.count), 1);
    container.innerHTML = words.map((item) => {
        const ratio = item.count / maxCount;
        const size = 1.05 + ratio * 2.05;
        const weight = ratio > 0.66 ? 900 : (ratio > 0.33 ? 800 : 700);
        const color = wordCloudColorClass(item.text);
        const tilt = wordCloudTilt(item.text);
        const count = Number(item.count) || 0;
        return `<span class="word-cloud-tag ${color}" style="font-size:${size}rem;font-weight:${weight};--wc-tilt:${tilt}deg">${escapeWordCloudText(item.text)}<sub>${count}</sub></span>`;
    }).join('');
}

function wordCloudColorClass(text) {
    return 'wc-c' + (wordCloudHash(text) % 6);
}

function wordCloudTilt(text) {
    return ((wordCloudHash(text + '#') % 7) - 3) * 3;
}

function wordCloudHash(text) {
    const value = String(text || '');
    let hash = 0;
    for (let i = 0; i < value.length; i += 1) {
        hash = ((hash << 5) - hash) + value.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash);
}

function escapeWordCloudText(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
