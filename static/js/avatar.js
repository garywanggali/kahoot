/**
 * Kahoot-inspired Modular Avatar System (Industrial Craft Edition)
 * Currently supports: Face (expressions) & Hair (hairstyles)
 */
(function (global) {
    'use strict';

    const BODY_COLORS = [
        { bg: '#FF5E00', shadow: '#D04500' }, // Safety Orange
        { bg: '#0066FF', shadow: '#0047B3' }, // Electric Blue
        { bg: '#8E44AD', shadow: '#6C3483' }, // Cyber Violet
        { bg: '#00B341', shadow: '#008530' }, // Mint Green
        { bg: '#E84393', shadow: '#B82B70' }, // Candy Pink
        { bg: '#18181B', shadow: '#09090B' }, // Matte Black
        { bg: '#FFB800', shadow: '#CC9300' }, // Industrial Amber
        { bg: '#00CEC9', shadow: '#009F9B' }, // Cyan Teal
    ];

    const HAIR_COLORS = [
        '#1E1E24', // Jet Black
        '#6D4C41', // Deep Brown
        '#F39C12', // Golden Blonde
        '#D35400', // Crimson Auburn
        '#2C3E50', // Navy Blue
        '#8E44AD', // Grape Purple
        '#00B894', // Emerald Green
        '#E17055', // Coral Orange
    ];

    const FACES = [
        {
            id: 0,
            name: '元气微笑',
            description: '圆润大眼与温暖微笑',
            render(c) {
                return `
                    <!-- 腮红 -->
                    <ellipse cx="28" cy="58" rx="6" ry="3.5" fill="#FF7675" opacity="0.6"/>
                    <ellipse cx="72" cy="58" rx="6" ry="3.5" fill="#FF7675" opacity="0.6"/>
                    <!-- 左眼 -->
                    <circle cx="34" cy="48" r="6.5" fill="#111111"/>
                    <circle cx="32" cy="46" r="2.2" fill="#FFFFFF"/>
                    <!-- 右眼 -->
                    <circle cx="66" cy="48" r="6.5" fill="#111111"/>
                    <circle cx="64" cy="46" r="2.2" fill="#FFFFFF"/>
                    <!-- 微笑嘴巴 -->
                    <path d="M 40 60 Q 50 71 60 60" fill="none" stroke="#111111" stroke-width="4" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 1,
            name: '酷炫墨镜',
            description: '前卫太阳镜与自信嘴角',
            render(c) {
                return `
                    <!-- 墨镜框体与镜片 -->
                    <g filter="drop-shadow(0px 3px 4px rgba(0,0,0,0.35))">
                        <path d="M 18 43 Q 50 39 82 43 L 80 54 Q 78 60 67 60 Q 56 60 53 52 L 47 52 Q 44 60 33 60 Q 22 60 20 54 Z" fill="#111111"/>
                        <!-- 镜片科技反光条 -->
                        <polygon points="26,45 34,45 28,57 23,57" fill="#00FFFF" opacity="0.8"/>
                        <polygon points="37,45 42,45 36,57 32,57" fill="#FFFFFF" opacity="0.75"/>
                        <polygon points="58,45 66,45 60,57 55,57" fill="#00FFFF" opacity="0.8"/>
                        <polygon points="69,45 74,45 68,57 64,57" fill="#FFFFFF" opacity="0.75"/>
                    </g>
                    <!-- 歪嘴自信笑 -->
                    <path d="M 44 68 Q 54 71 62 65" fill="none" stroke="#111111" stroke-width="3.8" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 2,
            name: '眯眼大笑',
            description: '开怀大笑与幸福弧线',
            render(c) {
                return `
                    <!-- 腮红 -->
                    <ellipse cx="26" cy="56" rx="6" ry="3.5" fill="#FF7675" opacity="0.65"/>
                    <ellipse cx="74" cy="56" rx="6" ry="3.5" fill="#FF7675" opacity="0.65"/>
                    <!-- 快乐眯眯眼 ^ ^ -->
                    <path d="M 28 49 Q 35 41 42 49" fill="none" stroke="#111111" stroke-width="4.5" stroke-linecap="round"/>
                    <path d="M 58 49 Q 65 41 72 49" fill="none" stroke="#111111" stroke-width="4.5" stroke-linecap="round"/>
                    <!-- 张口大笑与舌头 -->
                    <path d="M 37 59 Q 50 59 63 59 Q 63 76 50 76 Q 37 76 37 59 Z" fill="#111111"/>
                    <!-- 小白牙 -->
                    <path d="M 40 60 Q 50 63 60 60 L 60 63 Q 50 65 40 63 Z" fill="#FFFFFF"/>
                    <!-- 舌头 -->
                    <path d="M 43 73 Q 50 67 57 73 Q 50 78 43 73 Z" fill="#FF6B81"/>
                `;
            }
        },
        {
            id: 3,
            name: '俏皮眨眼',
            description: '单眼眨眨与微吐小舌头',
            render(c) {
                return `
                    <!-- 腮红 -->
                    <ellipse cx="27" cy="57" rx="5.5" ry="3.5" fill="#FF7675" opacity="0.6"/>
                    <ellipse cx="73" cy="57" rx="5.5" ry="3.5" fill="#FF7675" opacity="0.6"/>
                    <!-- 左眨眼 > -->
                    <path d="M 28 44 L 38 49 L 28 54" fill="none" stroke="#111111" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- 右大眼 -->
                    <circle cx="66" cy="48" r="7" fill="#111111"/>
                    <circle cx="64" cy="45" r="2.5" fill="#FFFFFF"/>
                    <circle cx="68" cy="51" r="1.2" fill="#FFFFFF"/>
                    <!-- 吐舌小嘴 -->
                    <path d="M 43 62 Q 50 68 57 62" fill="none" stroke="#111111" stroke-width="3.5" stroke-linecap="round"/>
                    <path d="M 48 64 C 48 71, 56 71, 56 64 Z" fill="#FF4757" stroke="#111111" stroke-width="2.5"/>
                `;
            }
        },
        {
            id: 4,
            name: '呆萌大眼',
            description: '同心圆无辜大眼神',
            render(c) {
                return `
                    <!-- 左无辜眼 -->
                    <circle cx="34" cy="48" r="9" fill="#111111"/>
                    <circle cx="34" cy="48" r="4.5" fill="#FFFFFF"/>
                    <circle cx="35" cy="48" r="2.2" fill="#111111"/>
                    <!-- 右无辜眼 -->
                    <circle cx="66" cy="48" r="9" fill="#111111"/>
                    <circle cx="66" cy="48" r="4.5" fill="#FFFFFF"/>
                    <circle cx="67" cy="48" r="2.2" fill="#111111"/>
                    <!-- 波浪呆萌嘴 ~ -->
                    <path d="M 43 65 Q 47 62 50 65 Q 53 68 57 65" fill="none" stroke="#111111" stroke-width="3.8" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 5,
            name: '学霸眼镜',
            description: '圆框镜架与睿智微笑',
            render(c) {
                return `
                    <!-- 眉毛 -->
                    <path d="M 27 36 Q 34 33 41 37" fill="none" stroke="#111111" stroke-width="3" stroke-linecap="round"/>
                    <path d="M 59 37 Q 66 33 73 36" fill="none" stroke="#111111" stroke-width="3" stroke-linecap="round"/>
                    <!-- 圆框眼镜与横梁 -->
                    <line x1="42" y1="48" x2="58" y2="48" stroke="#111111" stroke-width="3.5" stroke-linecap="round"/>
                    <circle cx="33" cy="48" r="10.5" fill="rgba(255,255,255,0.3)" stroke="#111111" stroke-width="3.5"/>
                    <circle cx="67" cy="48" r="10.5" fill="rgba(255,255,255,0.3)" stroke="#111111" stroke-width="3.5"/>
                    <!-- 镜片反光 -->
                    <path d="M 28 42 L 34 42" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
                    <path d="M 62 42 L 68 42" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
                    <!-- 眼睛 -->
                    <circle cx="33" cy="48" r="4.5" fill="#111111"/>
                    <circle cx="67" cy="48" r="4.5" fill="#111111"/>
                    <!-- 微笑 -->
                    <path d="M 43 66 Q 50 71 57 66" fill="none" stroke="#111111" stroke-width="3.5" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 6,
            name: '惊讶张嘴',
            description: '惊叹大眼睛与圆圆嘴',
            render(c) {
                return `
                    <!-- 挑眉 -->
                    <path d="M 29 35 Q 35 30 42 34" fill="none" stroke="#111111" stroke-width="3" stroke-linecap="round"/>
                    <path d="M 58 34 Q 65 30 71 35" fill="none" stroke="#111111" stroke-width="3" stroke-linecap="round"/>
                    <!-- 惊讶大圆眼 -->
                    <ellipse cx="35" cy="46" rx="6.5" ry="8" fill="#111111"/>
                    <circle cx="33" cy="43" r="2.5" fill="#FFFFFF"/>
                    <ellipse cx="65" cy="46" rx="6.5" ry="8" fill="#111111"/>
                    <circle cx="63" cy="43" r="2.5" fill="#FFFFFF"/>
                    <!-- 圆圆张嘴 O -->
                    <ellipse cx="50" cy="65" rx="6.5" ry="8.5" fill="#111111"/>
                    <ellipse cx="50" cy="67" rx="4.5" ry="4" fill="#FF6B81"/>
                `;
            }
        },
        {
            id: 7,
            name: '坚定斗志',
            description: '充满胜负欲的专注目光',
            render(c) {
                return `
                    <!-- 倒八字斗志粗眉 -->
                    <path d="M 27 38 L 42 42" fill="none" stroke="#111111" stroke-width="4" stroke-linecap="round"/>
                    <path d="M 73 38 L 58 42" fill="none" stroke="#111111" stroke-width="4" stroke-linecap="round"/>
                    <!-- 眼神 -->
                    <circle cx="35" cy="49" r="6" fill="#111111"/>
                    <circle cx="33" cy="47" r="2" fill="#FFFFFF"/>
                    <circle cx="65" cy="49" r="6" fill="#111111"/>
                    <circle cx="63" cy="47" r="2" fill="#FFFFFF"/>
                    <!-- 咬牙咧嘴自信笑 -->
                    <rect x="42" y="62" width="16" height="7" rx="3.5" fill="#FFFFFF" stroke="#111111" stroke-width="3"/>
                    <line x1="50" y1="62" x2="50" y2="69" stroke="#111111" stroke-width="2"/>
                `;
            }
        }
    ];

    const HAIRS = [
        {
            id: 0,
            name: '动感短发',
            description: '帅气侧分斜刘海短发',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <!-- 发束主体 -->
                        <path d="M 18 36 C 18 14, 45 6, 75 14 C 84 17, 85 28, 83 38 C 77 31, 68 28, 56 28 C 42 28, 30 33, 24 40 C 20 40, 18 38, 18 36 Z"
                              fill="${color}"/>
                        <!-- 斜向发尖刘海 -->
                        <path d="M 23 37 Q 35 24 58 29 Q 45 36 34 45 Q 26 43 23 37 Z" fill="${color}"/>
                        <path d="M 44 28 Q 60 25 78 35 Q 67 36 57 41 Q 48 35 44 28 Z" fill="${color}"/>
                    </g>
                `;
            }
        },
        {
            id: 1,
            name: '朋克飞机头',
            description: '赛博高耸的莫西干飞机头',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <path d="M 32 30 C 30 18, 42 2, 50 -1 C 58 2, 70 18, 68 30 C 62 25, 55 24, 50 24 C 45 24, 38 25, 32 30 Z" fill="${color}"/>
                        <!-- 侧翼细节发缕 -->
                        <path d="M 42 16 L 50 3 L 53 14 L 62 8 L 59 22 Z" fill="#FFFFFF" opacity="0.25"/>
                    </g>
                `;
            }
        },
        {
            id: 2,
            name: '蓬松爆炸头',
            description: '圆滚滚可爱的云朵爆炸卷发',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 4px 4px rgba(0,0,0,0.25))">
                        <!-- 由多个饱满的圆形弧构成的爆炸头发型 -->
                        <path d="M 16 42 
                                 A 13 13 0 0 1 18 24 
                                 A 14 14 0 0 1 33 13 
                                 A 15 15 0 0 1 50 8 
                                 A 15 15 0 0 1 67 13 
                                 A 14 14 0 0 1 82 24 
                                 A 13 13 0 0 1 84 42 
                                 Q 76 31 50 31 
                                 Q 24 31 16 42 Z"
                              fill="${color}"/>
                        <circle cx="34" cy="19" r="3" fill="#FFFFFF" opacity="0.2"/>
                        <circle cx="66" cy="19" r="3" fill="#FFFFFF" opacity="0.2"/>
                    </g>
                `;
            }
        },
        {
            id: 3,
            name: '双丸子头',
            description: '元气双丸子丸子发髻',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <!-- 左丸子 -->
                        <circle cx="17" cy="18" r="13" fill="${color}"/>
                        <circle cx="15" cy="16" r="4" fill="#FFFFFF" opacity="0.25"/>
                        <!-- 右丸子 -->
                        <circle cx="83" cy="18" r="13" fill="${color}"/>
                        <circle cx="81" cy="16" r="4" fill="#FFFFFF" opacity="0.25"/>
                        <!-- 头顶平贴发与可爱刘海 -->
                        <path d="M 21 34 Q 50 18 79 34 Q 68 28 50 28 Q 32 28 21 34 Z" fill="${color}"/>
                        <path d="M 38 28 Q 43 36 47 31" stroke="${color}" stroke-width="4" stroke-linecap="round" fill="none"/>
                        <path d="M 52 31 Q 56 36 61 28" stroke="${color}" stroke-width="4" stroke-linecap="round" fill="none"/>
                    </g>
                `;
            }
        },
        {
            id: 4,
            name: '齐刘海妹妹头',
            description: '文静整齐的波波头与刘海',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.22))">
                        <!-- 顶盖发 -->
                        <path d="M 18 42 C 16 20, 32 10, 50 10 C 68 10, 84 20, 82 42 C 78 30, 68 26, 50 26 C 32 26, 22 30, 18 42 Z" fill="${color}"/>
                        <!-- 整齐垂坠刘海 -->
                        <rect x="23" y="26" width="54" height="11" rx="4" fill="${color}"/>
                        <path d="M 23 37 Q 35 34 50 37 Q 65 34 77 37 L 77 48 Q 72 38 70 34 L 30 34 Q 28 38 23 48 Z" fill="${color}"/>
                    </g>
                `;
            }
        },
        {
            id: 5,
            name: '反戴棒球帽',
            description: '街头潮酷反戴鸭舌帽',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.3))">
                        <!-- 帽子圆弧圆顶 -->
                        <path d="M 18 36 C 20 12, 40 8, 50 8 C 60 8, 80 12, 82 36 Z" fill="${color}"/>
                        <!-- 帽子反戴后的鸭舌向后微翘 -->
                        <path d="M 28 10 Q 50 -2 72 10 L 68 12 Q 50 4 32 12 Z" fill="${color}" filter="brightness(0.85)"/>
                        <!-- 帽子下边缘帽圈 -->
                        <rect x="17" y="32" width="66" height="8" rx="4" fill="#111111"/>
                        <!-- 后脑勺调节扣开孔与搭扣 -->
                        <ellipse cx="50" cy="33" rx="6" ry="4" fill="#FFFFFF" opacity="0.3"/>
                        <rect x="47" y="35" width="6" height="3" rx="1" fill="#FFFFFF"/>
                    </g>
                `;
            }
        },
        {
            id: 6,
            name: '高贵大背头',
            description: '整洁利落的大背头分缝',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <path d="M 19 35 C 18 16, 36 6, 54 6 C 74 6, 83 18, 82 35 C 75 25, 62 22, 50 22 C 34 22, 24 26, 19 35 Z" fill="${color}"/>
                        <!-- 纹理发流高光线条 -->
                        <path d="M 30 18 Q 45 12 62 13" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.3"/>
                        <path d="M 33 24 Q 48 18 68 19" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.25"/>
                    </g>
                `;
            }
        },
        {
            id: 7,
            name: '呆毛小光头',
            description: '圆润光洁与顽皮小发苗',
            render(color) {
                return `
                    <g>
                        <!-- 一根顽皮卷曲向上的小呆毛 -->
                        <path d="M 50 16 C 50 6, 42 2, 45 -1 C 49 1, 57 7, 54 16 Z" fill="${color}"/>
                        <circle cx="45" cy="0" r="2" fill="${color}"/>
                    </g>
                `;
            }
        }
    ];

    function normalizeAvatar(raw) {
        if (!raw || typeof raw !== 'object') {
            return { face: 0, hair: 0 };
        }
        let face = parseInt(raw.face, 10);
        let hair = parseInt(raw.hair, 10);
        if (isNaN(face) || face < 0 || face >= FACES.length) face = 0;
        if (isNaN(hair) || hair < 0 || hair >= HAIRS.length) hair = 0;
        return { face, hair };
    }

    function getPalette(avatar, nickname = '') {
        const f = avatar.face;
        const h = avatar.hair;
        let seed = (f * 5 + h * 11);
        if (nickname) {
            for (let i = 0; i < nickname.length; i++) {
                seed += nickname.charCodeAt(i);
            }
        }
        const bodyIndex = Math.abs(seed) % BODY_COLORS.length;
        const hairIndex = Math.abs(seed + 3) % HAIR_COLORS.length;
        return {
            body: BODY_COLORS[bodyIndex],
            hair: HAIR_COLORS[hairIndex],
        };
    }

    function renderSvg(avatarRaw, size = 64, options = {}) {
        const avatar = normalizeAvatar(avatarRaw);
        const nickname = options.nickname || '';
        const palette = getPalette(avatar, nickname);

        const faceObj = FACES[avatar.face] || FACES[0];
        const hairObj = HAIRS[avatar.hair] || HAIRS[0];

        const width = size;
        const height = size;
        const className = options.className || 'kahoot-avatar-svg';
        const isPodium = options.podium || false;
        const rank = options.rank || 0;

        let medalBadge = '';
        if (isPodium && rank >= 1 && rank <= 3) {
            const crownColor = rank === 1 ? '#FFD700' : (rank === 2 ? '#E0E0E0' : '#CD7F32');
            medalBadge = `
                <!-- 颁奖专属头饰皇冠 (只在冠军时显现) -->
                ${rank === 1 ? `
                    <g transform="translate(36, -14) scale(0.28)">
                        <path d="M 0 50 L 20 15 L 50 38 L 80 15 L 100 50 Z" fill="#FFD700" stroke="#B8860B" stroke-width="6"/>
                        <circle cx="20" cy="15" r="7" fill="#FF4757"/>
                        <circle cx="50" cy="38" r="7" fill="#00D2D3"/>
                        <circle cx="80" cy="15" r="7" fill="#5F27CD"/>
                    </g>
                ` : ''}
            `;
        }

        return `
            <svg class="${className}" width="${width}" height="${height}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="头像">
                <defs>
                    <!-- 身体光泽高光 -->
                    <radialGradient id="kh-av-glow-${avatar.face}-${avatar.hair}" cx="35%" cy="30%" r="65%">
                        <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.32"/>
                        <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
                    </radialGradient>
                    <!-- 投影底盘 -->
                    <filter id="kh-av-shadow" x="-10%" y="-10%" width="120%" height="120%">
                        <feDropShadow dx="0" dy="4" stdDeviation="3" flood-color="#000000" flood-opacity="0.18"/>
                    </filter>
                </defs>

                ${medalBadge}

                <!-- 卡通圆形主身躯 (Kahoot 标志性圆润角色) -->
                <g filter="url(#kh-av-shadow)">
                    <!-- 身体底色 -->
                    <rect x="14" y="14" width="72" height="72" rx="36" fill="${palette.body.bg}"/>
                    <!-- 立体底阴影微弧 -->
                    <path d="M 16 60 Q 50 92 84 60 A 36 36 0 0 1 16 60 Z" fill="${palette.body.shadow}" opacity="0.3"/>
                    <!-- 顶光高光层 -->
                    <rect x="14" y="14" width="72" height="72" rx="36" fill="url(#kh-av-glow-${avatar.face}-${avatar.hair})"/>
                    <!-- 边框收边 (MK-78 精密手感) -->
                    <rect x="14" y="14" width="72" height="72" rx="36" stroke="rgba(0,0,0,0.18)" stroke-width="2.5"/>
                </g>

                <!-- 脸部表情层 (眼睛、腮红、嘴巴) -->
                <g class="avatar-face-layer">
                    ${faceObj.render(palette.body.bg)}
                </g>

                <!-- 头发发型层 (覆盖在额头和头顶) -->
                <g class="avatar-hair-layer">
                    ${hairObj.render(palette.hair)}
                </g>
            </svg>
        `.trim();
    }

    function getRandomAvatar() {
        return {
            face: Math.floor(Math.random() * FACES.length),
            hair: Math.floor(Math.random() * HAIRS.length),
        };
    }

    const AvatarSystem = {
        FACES,
        HAIRS,
        normalize: normalizeAvatar,
        renderSvg,
        random: getRandomAvatar,
        getPalette,
    };

    global.AvatarSystem = AvatarSystem;

})(typeof window !== 'undefined' ? window : this);
