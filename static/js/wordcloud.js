function renderWordCloud(containerId, words) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!words || words.length === 0) {
        const emptyMsg = window.t ? t('host.word_cloud_empty') : '暂无回答，等待大家提交...';
        container.innerHTML = `<p class="text-muted-block">${escapeWordCloudText(emptyMsg)}</p>`;
        return;
    }

    const maxCount = Math.max(...words.map(w => w.count), 1);
    container.innerHTML = words.map(item => {
        const ratio = item.count / maxCount;
        const size = 0.85 + ratio * 1.35;
        const opacity = 0.65 + ratio * 0.35;
        return `<span class="word-cloud-tag" style="font-size:${size}rem;opacity:${opacity}">${escapeWordCloudText(item.text)}<sub>${item.count}</sub></span>`;
    }).join('');
}

function escapeWordCloudText(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
