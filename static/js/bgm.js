(function () {
    const STORAGE_KEY = 'kahoot_bgm';
    const audio = document.getElementById('global-bgm');
    if (!audio) return;

    function readState() {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    }

    function writeState() {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
                time: audio.currentTime,
                at: Date.now(),
                duration: audio.duration || 0,
            }));
        } catch {
            /* ignore quota / private mode */
        }
    }

    function getResumeTime() {
        const state = readState();
        if (!state || typeof state.time !== 'number') return 0;
        const elapsed = (Date.now() - state.at) / 1000;
        const duration = audio.duration || state.duration || 0;
        if (duration > 0) {
            return (state.time + elapsed) % duration;
        }
        return state.time + elapsed;
    }

    function tryResume() {
        const target = getResumeTime();
        if (target > 0.05) {
            try {
                audio.currentTime = target;
            } catch {
                /* not seekable yet */
            }
        }
    }

    function play() {
        if (audio.paused) {
            audio.play().catch(() => {});
        }
    }

    function optOutTurboForHeavyPages() {
        document.querySelectorAll('a[href]').forEach((anchor) => {
            const href = anchor.getAttribute('href') || '';
            if (
                href.includes('/play/')
                || href.includes('/practice/')
                || href.includes('/edit/')
                || /\/teacher\/rooms\/\d+/.test(href)
            ) {
                anchor.setAttribute('data-turbo', 'false');
            }
            anchor.setAttribute('data-turbo-prefetch', 'false');
        });
    }

    function disableTurboOnForms() {
        document.querySelectorAll('form').forEach((form) => {
            form.setAttribute('data-turbo', 'false');
        });
    }

    function recoverStuckTurbo() {
        try {
            const visit = window.Turbo && window.Turbo.navigator && window.Turbo.navigator.currentVisit;
            if (visit && typeof visit.cancel === 'function') {
                visit.cancel();
            }
        } catch {
            /* ignore */
        }
        document.documentElement.removeAttribute('aria-busy');
        document.documentElement.removeAttribute('busy');
    }

    let busyTimer = null;
    function armBusyWatch() {
        clearTimeout(busyTimer);
        busyTimer = setTimeout(recoverStuckTurbo, 2000);
    }
    function clearBusyWatch() {
        clearTimeout(busyTimer);
        busyTimer = null;
        document.documentElement.removeAttribute('aria-busy');
        document.documentElement.removeAttribute('busy');
    }

    if (!audio.dataset.bgmInit) {
        audio.dataset.bgmInit = '1';
        audio.volume = 0.35;

        let saveTimer = null;
        audio.addEventListener('timeupdate', () => {
            if (saveTimer) return;
            saveTimer = setTimeout(() => {
                saveTimer = null;
                writeState();
            }, 400);
        });

        audio.addEventListener('loadedmetadata', tryResume);

        audio.addEventListener('canplay', () => {
            tryResume();
            play();
        }, { once: true });

        window.addEventListener('pagehide', writeState);

        document.addEventListener('pointerdown', () => play(), { once: true });
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) play();
        });

        document.addEventListener('turbo:load', () => {
            optOutTurboForHeavyPages();
            disableTurboOnForms();
            clearBusyWatch();
            play();
        });
        document.addEventListener('turbo:render', clearBusyWatch);
        document.addEventListener('turbo:submit-end', clearBusyWatch);
        document.addEventListener('turbo:fetch-request-error', clearBusyWatch);
        document.addEventListener('turbo:before-fetch-request', armBusyWatch);
        document.addEventListener('DOMContentLoaded', () => {
            optOutTurboForHeavyPages();
            disableTurboOnForms();
        });

        if (audio.readyState >= HTMLMediaElement.HAVE_METADATA) {
            tryResume();
            play();
        }
    } else {
        play();
    }

    optOutTurboForHeavyPages();
    disableTurboOnForms();
})();
