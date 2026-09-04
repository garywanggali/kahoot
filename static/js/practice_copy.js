/**
 * Copy public-quiz practice codes (and a ready-to-send student message).
 */
(function () {
    'use strict';

    function t(key, fallback) {
        var args = Array.prototype.slice.call(arguments, 2);
        if (typeof window.t === 'function') {
            var translated = window.t.apply(null, [key].concat(args));
            if (translated && translated !== key) return translated;
        }
        if (!fallback) return key;
        var i = 0;
        return String(fallback).replace(/%s/g, function () {
            return args[i] !== undefined ? args[i++] : '';
        });
    }

    function shareText(code, title) {
        return t(
            'assign.share_text',
            '请同学们打开测验首页，输入练习码 %s，开始《%s》个人练习。',
            code,
            title,
        );
    }

    function writeClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        return new Promise(function (resolve, reject) {
            var area = document.createElement('textarea');
            area.value = text;
            area.setAttribute('readonly', '');
            area.style.position = 'fixed';
            area.style.left = '-9999px';
            document.body.appendChild(area);
            area.select();
            try {
                if (!document.execCommand('copy')) {
                    reject(new Error('copy failed'));
                } else {
                    resolve();
                }
            } catch (err) {
                reject(err);
            } finally {
                document.body.removeChild(area);
            }
        });
    }

    function showToast(message) {
        var el = document.getElementById('practice-copy-toast');
        if (!el) {
            el = document.createElement('div');
            el.id = 'practice-copy-toast';
            el.className = 'practice-copy-toast';
            el.setAttribute('role', 'status');
            document.body.appendChild(el);
        }
        el.textContent = message;
        el.classList.remove('hidden');
        clearTimeout(showToast._timer);
        showToast._timer = setTimeout(function () {
            el.classList.add('hidden');
        }, 1800);
    }

    document.addEventListener('click', function (event) {
        var btn = event.target.closest('[data-practice-code]');
        if (!btn) return;
        event.preventDefault();
        var code = (btn.getAttribute('data-practice-code') || '').trim();
        if (!code) return;
        var title = (btn.getAttribute('data-quiz-title') || '').trim();
        var kind = btn.getAttribute('data-copy-kind') || 'code';
        var text = kind === 'share' ? shareText(code, title) : code;
        writeClipboard(text).then(function () {
            showToast(kind === 'share'
                ? t('assign.copied_share', '已复制发给学生的文案')
                : t('assign.copied_code', '已复制练习码 %s', code));
        }).catch(function () {
            showToast(t('status.error', '操作失败'));
        });
    });
})();
