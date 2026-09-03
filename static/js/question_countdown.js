/**
 * Full-screen 3-2-1 question intro used by host projector and student play.
 * Remaining time comes from the server so late joiners stay in sync.
 */
(function (global) {
    'use strict';

    var GO_MS = 280;
    var SKIP_MS = 60;

    function t(key, fallback) {
        var args = Array.prototype.slice.call(arguments, 2);
        if (typeof global.t === 'function') {
            var translated = global.t.apply(null, [key].concat(args));
            if (translated && translated !== key) return translated;
        }
        return fallback;
    }

    function remainingMsFromState(state) {
        if (!state) return 0;
        var remaining = Number(state.countdown_remaining_ms);
        if (Number.isFinite(remaining)) return Math.max(0, remaining);
        var seconds = Number(state.countdown_seconds);
        if (Number.isFinite(seconds) && seconds > 0) return seconds * 1000;
        return 0;
    }

    function create(overlayId) {
        var timer = null;
        var token = 0;

        function overlayEl() {
            return document.getElementById(overlayId);
        }

        function clearTimer() {
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
        }

        function hide() {
            var el = overlayEl();
            if (!el) return;
            el.classList.add('hidden');
            el.classList.remove('is-go', 'is-n3', 'is-n2', 'is-n1');
            el.setAttribute('aria-hidden', 'true');
        }

        function cancel() {
            token += 1;
            clearTimer();
            hide();
        }

        function restartAnim(node, className) {
            if (!node) return;
            node.classList.remove(className);
            void node.offsetWidth;
            node.classList.add(className);
        }

        function paint(el, value, isGo) {
            var numEl = el.querySelector('.q-countdown-num');
            var hintEl = el.querySelector('.q-countdown-hint');
            var ringEl = el.querySelector('.q-countdown-ring');
            el.classList.remove('is-n3', 'is-n2', 'is-n1', 'is-go');
            if (isGo) {
                el.classList.add('is-go');
                if (numEl) numEl.textContent = t('countdown.go', 'GO!');
                if (hintEl) hintEl.textContent = '';
            } else {
                el.classList.add('is-n' + value);
                if (numEl) numEl.textContent = String(value);
                if (hintEl) hintEl.textContent = t('countdown.get_ready', '准备');
            }
            restartAnim(numEl, 'q-countdown-pop');
            restartAnim(ringEl, 'q-countdown-pulse');
        }

        function run(state, onDone) {
            cancel();
            var my = token;
            var remaining = remainingMsFromState(state);
            var el = overlayEl();
            var finish = function () {
                if (my !== token) return;
                hide();
                if (typeof onDone === 'function') onDone();
            };

            if (!el || remaining <= SKIP_MS) {
                finish();
                return;
            }

            var metaEl = el.querySelector('.q-countdown-meta');
            if (metaEl) {
                var idx = (Number(state.current_question_index) || 0) + 1;
                var total = Number(state.total_questions) || 0;
                metaEl.textContent = t('play.question_num', '第 %s / %s 题', idx, total);
            }

            el.classList.remove('hidden');
            el.setAttribute('aria-hidden', 'false');
            var endsAt = Date.now() + remaining;

            function tick() {
                if (my !== token) return;
                var left = endsAt - Date.now();
                if (left <= 0) {
                    finish();
                    return;
                }
                if (left <= GO_MS) {
                    paint(el, 0, true);
                    timer = setTimeout(tick, left);
                    return;
                }
                var n = Math.max(1, Math.ceil(left / 1000));
                paint(el, n, false);
                var nextBoundary = endsAt - (n - 1) * 1000;
                var goAt = endsAt - GO_MS;
                var nextAt = n === 1 ? Math.min(nextBoundary, goAt) : nextBoundary;
                timer = setTimeout(tick, Math.max(16, nextAt - Date.now()));
            }

            tick();
        }

        return { run: run, cancel: cancel, hide: hide };
    }

    global.QuestionCountdown = {
        create: create,
        remainingMsFromState: remainingMsFromState,
    };
})(window);
