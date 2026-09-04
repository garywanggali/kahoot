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
        },
        {
            id: 8,
            name: '爱心眼',
            description: '粉红爱心瞳孔与甜蜜酒窝',
            render() {
                return `
                    <ellipse cx="27" cy="58" rx="6" ry="3.2" fill="#FF7675" opacity="0.55"/>
                    <ellipse cx="73" cy="58" rx="6" ry="3.2" fill="#FF7675" opacity="0.55"/>
                    <path d="M 28 46 C 28 41, 34 41, 35 45 C 36 41, 42 41, 42 46 C 42 52, 35 57, 35 57 C 35 57, 28 52, 28 46 Z" fill="#E11D48"/>
                    <path d="M 58 46 C 58 41, 64 41, 65 45 C 66 41, 72 41, 72 46 C 72 52, 65 57, 65 57 C 65 57, 58 52, 58 46 Z" fill="#E11D48"/>
                    <path d="M 31 46 L 33 44" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round"/>
                    <path d="M 61 46 L 63 44" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round"/>
                    <path d="M 40 66 Q 50 74 60 66" fill="none" stroke="#111111" stroke-width="3.6" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 9,
            name: '哈欠犯困',
            description: '半垂眼皮与飘着的 Zzz',
            render() {
                return `
                    <path d="M 26 44 Q 35 40 42 46" fill="none" stroke="#111111" stroke-width="3.4" stroke-linecap="round"/>
                    <path d="M 58 46 Q 65 40 74 44" fill="none" stroke="#111111" stroke-width="3.4" stroke-linecap="round"/>
                    <line x1="27" y1="50" x2="42" y2="50" stroke="#111111" stroke-width="4" stroke-linecap="round"/>
                    <line x1="58" y1="50" x2="73" y2="50" stroke="#111111" stroke-width="4" stroke-linecap="round"/>
                    <ellipse cx="50" cy="66" rx="7" ry="8" fill="#111111"/>
                    <ellipse cx="50" cy="68" rx="4.5" ry="4" fill="#FF6B81"/>
                    <text x="76" y="28" font-size="9" font-weight="900" fill="#111111" font-family="ui-sans-serif,sans-serif">z</text>
                    <text x="82" y="20" font-size="12" font-weight="900" fill="#111111" font-family="ui-sans-serif,sans-serif">z</text>
                    <text x="90" y="10" font-size="14" font-weight="900" fill="#111111" font-family="ui-sans-serif,sans-serif">Z</text>
                `;
            }
        },
        {
            id: 10,
            name: '怒气喷发',
            description: '倒八字眉、咬牙与蒸汽',
            render() {
                return `
                    <path d="M 24 36 L 42 44" stroke="#111111" stroke-width="4.2" stroke-linecap="round"/>
                    <path d="M 76 36 L 58 44" stroke="#111111" stroke-width="4.2" stroke-linecap="round"/>
                    <rect x="28" y="47" width="16" height="8" rx="2" fill="#111111"/>
                    <rect x="56" y="47" width="16" height="8" rx="2" fill="#111111"/>
                    <rect x="31" y="49" width="5" height="4" rx="1" fill="#FFFFFF"/>
                    <rect x="59" y="49" width="5" height="4" rx="1" fill="#FFFFFF"/>
                    <rect x="40" y="62" width="20" height="8" rx="2" fill="#FFFFFF" stroke="#111111" stroke-width="3"/>
                    <line x1="45" y1="62" x2="45" y2="70" stroke="#111111" stroke-width="2"/>
                    <line x1="50" y1="62" x2="50" y2="70" stroke="#111111" stroke-width="2"/>
                    <line x1="55" y1="62" x2="55" y2="70" stroke="#111111" stroke-width="2"/>
                    <path d="M 16 30 Q 12 22 18 18" fill="none" stroke="#FF4F00" stroke-width="3" stroke-linecap="round"/>
                    <path d="M 22 26 Q 18 16 26 14" fill="none" stroke="#FF4F00" stroke-width="2.4" stroke-linecap="round"/>
                    <path d="M 84 30 Q 88 22 82 18" fill="none" stroke="#FF4F00" stroke-width="3" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 11,
            name: '忍者面罩',
            description: '只露锐利双眼的蒙面',
            render() {
                return `
                    <path d="M 18 52 Q 50 46 82 52 L 80 82 Q 50 90 20 82 Z" fill="#18181B"/>
                    <path d="M 22 54 Q 50 50 78 54 L 76 62 Q 50 58 24 62 Z" fill="#27272A"/>
                    <path d="M 28 46 Q 35 42 42 46 Q 35 50 28 46 Z" fill="#111111"/>
                    <path d="M 58 46 Q 65 42 72 46 Q 65 50 58 46 Z" fill="#111111"/>
                    <circle cx="35" cy="46" r="2.2" fill="#00F0FF"/>
                    <circle cx="65" cy="46" r="2.2" fill="#00F0FF"/>
                    <rect x="46" y="58" width="8" height="4" rx="1" fill="#3F3F46"/>
                `;
            }
        },
        {
            id: 12,
            name: '星星眼',
            description: '四角星瞳孔与闪光雀跃',
            render() {
                return `
                    <ellipse cx="26" cy="58" rx="5.5" ry="3" fill="#FDE047" opacity="0.7"/>
                    <ellipse cx="74" cy="58" rx="5.5" ry="3" fill="#FDE047" opacity="0.7"/>
                    <path d="M 34 38 L 36.5 45 L 44 46 L 38 51 L 40 58 L 34 54 L 28 58 L 30 51 L 24 46 L 31.5 45 Z" fill="#111111"/>
                    <path d="M 66 38 L 68.5 45 L 76 46 L 70 51 L 72 58 L 66 54 L 60 58 L 62 51 L 56 46 L 63.5 45 Z" fill="#111111"/>
                    <path d="M 34 44 L 34 48" stroke="#FDE047" stroke-width="2" stroke-linecap="round"/>
                    <path d="M 66 44 L 66 48" stroke="#FDE047" stroke-width="2" stroke-linecap="round"/>
                    <path d="M 38 64 Q 50 78 62 64 Q 50 70 38 64 Z" fill="#111111"/>
                    <path d="M 42 66 Q 50 70 58 66" fill="none" stroke="#FFFFFF" stroke-width="2"/>
                    <path d="M 80 32 L 82 36 L 86 34 L 83 38 L 86 42 L 80 40 L 76 44 L 78 38 L 72 36 L 78 34 Z" fill="#FACC15"/>
                `;
            }
        },
        {
            id: 13,
            name: '泪奔大哭',
            description: '汪汪泪眼与往下淌的泪珠',
            render() {
                return `
                    <circle cx="34" cy="48" r="8" fill="#111111"/>
                    <circle cx="66" cy="48" r="8" fill="#111111"/>
                    <circle cx="32" cy="46" r="2.4" fill="#FFFFFF"/>
                    <circle cx="64" cy="46" r="2.4" fill="#FFFFFF"/>
                    <path d="M 30 56 Q 32 72 28 78" fill="none" stroke="#38BDF8" stroke-width="4" stroke-linecap="round"/>
                    <path d="M 38 56 Q 40 70 42 80" fill="none" stroke="#38BDF8" stroke-width="3.2" stroke-linecap="round"/>
                    <path d="M 62 56 Q 60 70 58 80" fill="none" stroke="#38BDF8" stroke-width="3.2" stroke-linecap="round"/>
                    <path d="M 70 56 Q 68 72 72 78" fill="none" stroke="#38BDF8" stroke-width="4" stroke-linecap="round"/>
                    <circle cx="28" cy="80" r="3.2" fill="#38BDF8"/>
                    <circle cx="72" cy="80" r="3.2" fill="#38BDF8"/>
                    <path d="M 42 64 Q 50 62 58 64 Q 50 72 42 64 Z" fill="#111111"/>
                `;
            }
        },
        {
            id: 14,
            name: '猫须喵喵',
            description: '竖瞳孔、胡须与三角小嘴',
            render() {
                return `
                    <ellipse cx="34" cy="48" rx="8" ry="9" fill="#111111"/>
                    <ellipse cx="66" cy="48" rx="8" ry="9" fill="#111111"/>
                    <ellipse cx="34" cy="48" rx="2.2" ry="6" fill="#FDE047"/>
                    <ellipse cx="66" cy="48" rx="2.2" ry="6" fill="#FDE047"/>
                    <line x1="12" y1="54" x2="28" y2="58" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
                    <line x1="12" y1="60" x2="28" y2="61" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
                    <line x1="88" y1="54" x2="72" y2="58" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
                    <line x1="88" y1="60" x2="72" y2="61" stroke="#111111" stroke-width="2.4" stroke-linecap="round"/>
                    <path d="M 50 62 L 46 70 L 54 70 Z" fill="#111111"/>
                    <path d="M 50 70 Q 50 76 46 78" fill="none" stroke="#FF6B81" stroke-width="2.4" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 15,
            name: 'WLR 吸血鬼',
            description: '细长睡眼、獠牙、额头十字与面纹',
            render() {
                return `
                    <path d="M 24 40 L 42 44" stroke="#111111" stroke-width="3.2" stroke-linecap="round"/>
                    <path d="M 76 40 L 58 44" stroke="#111111" stroke-width="3.2" stroke-linecap="round"/>
                    <ellipse cx="34" cy="50" rx="9" ry="6" fill="#111111"/>
                    <ellipse cx="66" cy="50" rx="9" ry="6" fill="#111111"/>
                    <rect x="26" y="49" width="16" height="3.2" rx="1" fill="#F43F5E"/>
                    <rect x="58" y="49" width="16" height="3.2" rx="1" fill="#F43F5E"/>
                    <ellipse cx="34" cy="50.5" rx="6" ry="1.6" fill="#FAFAFA"/>
                    <ellipse cx="66" cy="50.5" rx="6" ry="1.6" fill="#FAFAFA"/>
                    <path d="M 50 18 L 50 30" stroke="#111111" stroke-width="3.2" stroke-linecap="round"/>
                    <path d="M 44 24 L 56 24" stroke="#111111" stroke-width="3.2" stroke-linecap="round"/>
                    <path d="M 22 56 L 26 62 L 22 62 Z" fill="#111111"/>
                    <path d="M 78 34 L 80 38 L 82 34 L 80 32 Z" fill="#111111"/>
                    <circle cx="78" cy="58" r="1.6" fill="#111111"/>
                    <path d="M 42 64 L 46 72 L 50 64 L 54 72 L 58 64" fill="none" stroke="#111111" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M 44 64 L 44 74" fill="#FAFAFA" stroke="#111111" stroke-width="1.6"/>
                    <path d="M 56 64 L 56 74" fill="#FAFAFA" stroke="#111111" stroke-width="1.6"/>
                    <path d="M 43 66 Q 50 70 57 66" fill="none" stroke="#9F1239" stroke-width="2.4" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 16,
            name: '搞怪吐舌',
            description: '歪眨眼、大眼珠与侧吐大舌头',
            render() {
                return `
                    <ellipse cx="24" cy="58" rx="6" ry="3.5" fill="#FF7675" opacity="0.6"/>
                    <ellipse cx="76" cy="58" rx="6" ry="3.5" fill="#FF7675" opacity="0.6"/>
                    <!-- 左俏皮眨眼 > -->
                    <path d="M 26 44 L 38 49 L 26 54" fill="none" stroke="#111111" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- 右搞怪大圆眼 -->
                    <circle cx="66" cy="46" r="8" fill="#111111"/>
                    <circle cx="63" cy="43" r="3.2" fill="#FFFFFF"/>
                    <circle cx="68" cy="49" r="1.5" fill="#FFFFFF"/>
                    <!-- 张口吐舌 -->
                    <path d="M 38 60 Q 50 63 64 60 Q 60 76 38 60 Z" fill="#111111"/>
                    <path d="M 48 62 C 48 76, 64 76, 62 62 Z" fill="#FF4757" stroke="#111111" stroke-width="2.2"/>
                `;
            }
        },
        {
            id: 17,
            name: '暴富金币眼',
            description: '闪闪发光的美元符号与金牙咧嘴',
            render() {
                return `
                    <polygon points="50,26 52,32 58,34 52,36 50,42 48,36 42,34 48,32" fill="#FACC15"/>
                    <polygon points="82,36 83.5,40 88,41 83.5,42 82,46 80.5,42 76,41 80.5,40" fill="#FACC15"/>
                    <!-- 左金币眼 -->
                    <circle cx="34" cy="48" r="9" fill="#FEF08A" stroke="#CA8A04" stroke-width="2.2"/>
                    <text x="34" y="52.5" font-size="12" font-weight="900" fill="#15803D" text-anchor="middle" font-family="ui-sans-serif,system-ui,sans-serif">$</text>
                    <!-- 右金币眼 -->
                    <circle cx="66" cy="48" r="9" fill="#FEF08A" stroke="#CA8A04" stroke-width="2.2"/>
                    <text x="66" y="52.5" font-size="12" font-weight="900" fill="#15803D" text-anchor="middle" font-family="ui-sans-serif,system-ui,sans-serif">$</text>
                    <!-- 灿烂大笑与金牙 -->
                    <path d="M 36 63 Q 50 76 64 63 Z" fill="#111111"/>
                    <path d="M 38 63 Q 50 66 62 63 L 62 65 Q 50 68 38 65 Z" fill="#FFFFFF"/>
                    <polygon points="40,63 46,63 45,68 40,68" fill="#FACC15" stroke="#CA8A04" stroke-width="0.8"/>
                `;
            }
        },
        {
            id: 18,
            name: '晕乎圈圈眼',
            description: '蚊香催眠眼、波浪嘴与冷汗',
            render() {
                return `
                    <path d="M 78 30 C 78 26, 82 20, 82 20 C 82 20, 86 26, 86 30 C 86 33, 84 35, 82 35 C 80 35, 78 33, 78 30 Z" fill="#38BDF8"/>
                    <!-- 左同心圈圈眼 -->
                    <circle cx="34" cy="48" r="9" fill="none" stroke="#111111" stroke-width="2.6"/>
                    <circle cx="34" cy="48" r="5" fill="none" stroke="#111111" stroke-width="2.6"/>
                    <circle cx="34" cy="48" r="1.8" fill="#111111"/>
                    <!-- 右同心圈圈眼 -->
                    <circle cx="66" cy="48" r="9" fill="none" stroke="#111111" stroke-width="2.6"/>
                    <circle cx="66" cy="48" r="5" fill="none" stroke="#111111" stroke-width="2.6"/>
                    <circle cx="66" cy="48" r="1.8" fill="#111111"/>
                    <!-- 晕乎波浪嘴 -->
                    <path d="M 40 66 Q 45 61 50 66 Q 55 71 60 66" fill="none" stroke="#111111" stroke-width="3.5" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 19,
            name: '害羞红晕',
            description: '软萌害羞的大红晕与小波浪嘴',
            render() {
                return `
                    <!-- 害羞红晕斜线 -->
                    <ellipse cx="27" cy="58" rx="8" ry="4.5" fill="#FB7185" opacity="0.75"/>
                    <ellipse cx="73" cy="58" rx="8" ry="4.5" fill="#FB7185" opacity="0.75"/>
                    <path d="M 23 57 L 27 61 M 28 56 L 32 60" stroke="#E11D48" stroke-width="1.6" stroke-linecap="round"/>
                    <path d="M 69 57 L 73 61 M 74 56 L 78 60" stroke="#E11D48" stroke-width="1.6" stroke-linecap="round"/>
                    <!-- 羞怯下垂眼 -->
                    <circle cx="35" cy="49" r="4.5" fill="#111111"/>
                    <circle cx="33.5" cy="47.5" r="1.6" fill="#FFFFFF"/>
                    <circle cx="65" cy="49" r="4.5" fill="#111111"/>
                    <circle cx="63.5" cy="47.5" r="1.6" fill="#FFFFFF"/>
                    <!-- 羞怯小嘴 -->
                    <path d="M 44 65 Q 47 62 50 65 Q 53 62 56 65" fill="none" stroke="#111111" stroke-width="3" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 20,
            name: '绅士单片镜',
            description: '金丝单片眼镜、八字胡与优雅微笑',
            render() {
                return `
                    <!-- 左眼 -->
                    <circle cx="34" cy="48" r="5" fill="#111111"/>
                    <circle cx="32.5" cy="46" r="1.8" fill="#FFFFFF"/>
                    <!-- 右眼金丝单片镜 -->
                    <circle cx="66" cy="48" r="10.5" fill="rgba(254,240,138,0.25)" stroke="#EAB308" stroke-width="3"/>
                    <circle cx="66" cy="48" r="5" fill="#111111"/>
                    <circle cx="64.5" cy="46" r="1.8" fill="#FFFFFF"/>
                    <path d="M 76 48 Q 82 62 76 76" fill="none" stroke="#EAB308" stroke-width="2" stroke-dasharray="2,2"/>
                    <!-- 八字胡 -->
                    <path d="M 50 61 C 46 56, 38 56, 34 60 C 31 63, 29 61, 30 59 C 32 54, 38 52, 44 56 C 48 59, 50 61, 50 61 C 50 61, 52 59, 56 56 C 62 52, 68 54, 70 59 C 71 61, 69 63, 66 60 C 62 56, 54 56, 50 61 Z" fill="#18181B"/>
                    <!-- 微笑 -->
                    <path d="M 44 69 Q 50 73 56 69" fill="none" stroke="#111111" stroke-width="3" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 21,
            name: '赛博机械面',
            description: '发光 HUD 准星眼与电路机械装甲',
            render() {
                return `
                    <!-- 左眼与赛博面纹 -->
                    <path d="M 24 57 L 38 57 L 42 61" fill="none" stroke="#06B6D4" stroke-width="2.2" stroke-linecap="round"/>
                    <circle cx="34" cy="48" r="6" fill="#111111"/>
                    <circle cx="32" cy="46" r="2" fill="#FFFFFF"/>
                    <!-- 右侧赛博机械装甲 -->
                    <path d="M 54 36 L 78 36 L 80 60 L 56 60 Z" fill="#1E293B" opacity="0.8" stroke="#06B6D4" stroke-width="1.6"/>
                    <circle cx="66" cy="48" r="8.5" fill="#0F172A" stroke="#22D3EE" stroke-width="2.5"/>
                    <circle cx="66" cy="48" r="3.5" fill="#F43F5E"/>
                    <line x1="55" y1="48" x2="77" y2="48" stroke="#22D3EE" stroke-width="1.4" stroke-dasharray="2,2"/>
                    <line x1="66" y1="37" x2="66" y2="59" stroke="#22D3EE" stroke-width="1.4" stroke-dasharray="2,2"/>
                    <!-- 机械冷酷歪嘴 -->
                    <path d="M 44 68 L 58 66" fill="none" stroke="#111111" stroke-width="3.6" stroke-linecap="round"/>
                `;
            }
        },
        {
            id: 22,
            name: '仓鼠鼓腮',
            description: '塞满零食圆滚滚的腮帮子与咪咪眼',
            render() {
                return `
                    <!-- 鼓鼓的脸颊大圆 -->
                    <circle cx="23" cy="56" r="10" fill="#FECDD3" opacity="0.85"/>
                    <circle cx="77" cy="56" r="10" fill="#FECDD3" opacity="0.85"/>
                    <!-- 满足的眯眯眼 ^ ^ -->
                    <path d="M 27 47 Q 34 39 41 47" fill="none" stroke="#111111" stroke-width="4.2" stroke-linecap="round"/>
                    <path d="M 59 47 Q 66 39 73 47" fill="none" stroke="#111111" stroke-width="4.2" stroke-linecap="round"/>
                    <!-- 嚼吧小饼干 -->
                    <circle cx="48" cy="65" r="5.5" fill="#D97706" stroke="#92400E" stroke-width="1.2"/>
                    <circle cx="46" cy="63" r="0.9" fill="#78350F"/>
                    <circle cx="49" cy="66" r="0.9" fill="#78350F"/>
                    <!-- 嚼吧嚼吧嘴巴 -->
                    <path d="M 43 65 Q 50 71 57 65" fill="none" stroke="#111111" stroke-width="3.5" stroke-linecap="round"/>
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
        },
        {
            id: 8,
            name: '双麻花辫',
            description: '两侧垂下的粗编织麻花',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <path d="M 20 38 C 18 16, 38 8, 50 8 C 62 8, 82 16, 80 38 C 72 26, 62 24, 50 24 C 38 24, 28 26, 20 38 Z" fill="${color}"/>
                        <path d="M 22 34 Q 18 48 16 62 Q 22 58 24 46 Q 26 56 20 70 Q 28 64 28 50 Z" fill="${color}"/>
                        <path d="M 78 34 Q 82 48 84 62 Q 78 58 76 46 Q 74 56 80 70 Q 72 64 72 50 Z" fill="${color}"/>
                        <circle cx="18" cy="72" r="5" fill="${color}"/>
                        <circle cx="82" cy="72" r="5" fill="${color}"/>
                        <circle cx="18" cy="72" r="2.2" fill="#F472B6"/>
                        <circle cx="82" cy="72" r="2.2" fill="#F472B6"/>
                        <path d="M 32 26 Q 40 34 38 28" stroke="${color}" stroke-width="5" fill="none" stroke-linecap="round"/>
                        <path d="M 62 28 Q 60 34 68 26" stroke="${color}" stroke-width="5" fill="none" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 9,
            name: '武士顶髻',
            description: '两侧利落、头顶束成发髻',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <path d="M 22 36 C 22 22, 34 16, 50 16 C 66 16, 78 22, 78 36 C 70 28, 60 26, 50 26 C 40 26, 30 28, 22 36 Z" fill="${color}"/>
                        <ellipse cx="50" cy="6" rx="11" ry="10" fill="${color}"/>
                        <rect x="47" y="12" width="6" height="8" rx="2" fill="${color}"/>
                        <path d="M 42 4 Q 50 -2 58 4" stroke="#FFFFFF" opacity="0.28" stroke-width="2" fill="none"/>
                        <rect x="44" y="14" width="12" height="3" rx="1.5" fill="#DC2626"/>
                    </g>
                `;
            }
        },
        {
            id: 10,
            name: '刺猬刺毛',
            description: '四面八方扎起的尖刺发型',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <path d="M 50 10 L 56 28 L 44 28 Z" fill="${color}"/>
                        <path d="M 28 16 L 42 30 L 32 34 Z" fill="${color}"/>
                        <path d="M 72 16 L 68 34 L 58 30 Z" fill="${color}"/>
                        <path d="M 14 32 L 30 38 L 22 46 Z" fill="${color}"/>
                        <path d="M 86 32 L 78 46 L 70 38 Z" fill="${color}"/>
                        <path d="M 18 18 L 34 28 L 26 22 Z" fill="${color}"/>
                        <path d="M 82 18 L 74 22 L 66 28 Z" fill="${color}"/>
                        <path d="M 50 4 L 54 22 L 46 22 Z" fill="${color}"/>
                        <path d="M 22 40 C 24 22, 40 16, 50 16 C 60 16, 76 22, 78 40 C 68 30, 58 28, 50 28 C 42 28, 32 30, 22 40 Z" fill="${color}"/>
                    </g>
                `;
            }
        },
        {
            id: 11,
            name: '长波浪披肩',
            description: '披到肩下的大卷波浪长发',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <path d="M 16 40 C 10 18, 32 4, 50 4 C 68 4, 90 18, 84 40
                                 C 90 48, 92 70, 86 88 C 80 76, 76 58, 78 44
                                 C 70 28, 58 22, 50 22 C 42 22, 30 28, 22 44
                                 C 24 58, 20 76, 14 88 C 8 70, 10 48, 16 40 Z" fill="${color}"/>
                        <path d="M 24 36 Q 38 28 50 32 Q 62 28 76 36 Q 68 30 50 28 Q 32 30 24 36 Z" fill="${color}"/>
                        <path d="M 20 58 Q 16 70 22 82" stroke="#FFFFFF" opacity="0.18" stroke-width="3" fill="none"/>
                        <path d="M 80 58 Q 84 70 78 82" stroke="#FFFFFF" opacity="0.18" stroke-width="3" fill="none"/>
                    </g>
                `;
            }
        },
        {
            id: 12,
            name: '狼尾短切',
            description: '头顶短、脑后拖一条狼尾',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <path d="M 22 38 C 20 18, 36 10, 50 10 C 64 10, 80 18, 78 38 C 70 28, 60 26, 50 26 C 40 26, 30 28, 22 38 Z" fill="${color}"/>
                        <path d="M 58 32 C 72 40, 78 58, 74 86 C 66 70, 62 52, 54 38 Z" fill="${color}"/>
                        <path d="M 28 32 Q 40 22 62 28" stroke="#FFFFFF" opacity="0.22" stroke-width="2.4" fill="none"/>
                    </g>
                `;
            }
        },
        {
            id: 13,
            name: '单股长辫',
            description: '脑后一条垂到身侧的粗长辫',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <path d="M 20 38 C 18 16, 36 8, 50 8 C 64 8, 82 16, 80 38 C 72 26, 60 24, 50 24 C 40 24, 28 26, 20 38 Z" fill="${color}"/>
                        <path d="M 54 30 C 68 42, 70 58, 66 74 C 62 86, 58 94, 62 100 C 48 92, 52 78, 56 64 C 58 50, 50 40, 46 34 Z" fill="${color}"/>
                        <path d="M 60 48 Q 66 56 62 66" stroke="#FFFFFF" opacity="0.2" stroke-width="2" fill="none"/>
                        <rect x="58" y="96" width="10" height="5" rx="2" fill="#F59E0B"/>
                    </g>
                `;
            }
        },
        {
            id: 14,
            name: '血红脏辫',
            description: 'WLR 标志性红黑长脏辫与垂坠发束',
            render() {
                const c = '#9F1239';
                const dark = '#4C0519';
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.35))">
                        <path d="M 12 36 C 14 8, 34 -2, 50 0 C 66 -2, 86 8, 88 36
                                 C 92 48, 94 78, 90 102 C 82 86, 80 60, 82 42
                                 C 74 22, 62 16, 50 16 C 38 16, 26 22, 18 42
                                 C 20 60, 18 86, 10 102 C 6 78, 8 48, 12 36 Z" fill="${c}"/>
                        <path d="M 18 40 Q 14 62 16 88" stroke="${dark}" stroke-width="5" fill="none" stroke-linecap="round"/>
                        <path d="M 26 38 Q 22 66 24 92" stroke="${dark}" stroke-width="4.5" fill="none" stroke-linecap="round"/>
                        <path d="M 82 40 Q 86 62 84 88" stroke="${dark}" stroke-width="5" fill="none" stroke-linecap="round"/>
                        <path d="M 74 38 Q 78 66 76 92" stroke="${dark}" stroke-width="4.5" fill="none" stroke-linecap="round"/>
                        <path d="M 34 22 Q 28 48 32 86" stroke="${dark}" stroke-width="4" fill="none" stroke-linecap="round"/>
                        <path d="M 66 22 Q 72 48 68 86" stroke="${dark}" stroke-width="4" fill="none" stroke-linecap="round"/>
                        <path d="M 22 28 Q 40 36 48 30 Q 42 42 30 44 Z" fill="${c}"/>
                        <path d="M 78 28 Q 60 36 52 30 Q 58 42 70 44 Z" fill="${c}"/>
                        <path d="M 28 32 Q 50 24 72 32 L 70 40 Q 50 34 30 40 Z" fill="${c}"/>
                        <path d="M 24 18 Q 22 8 28 6" fill="none" stroke="${c}" stroke-width="3" stroke-linecap="round"/>
                        <path d="M 76 18 Q 78 8 72 6" fill="none" stroke="${c}" stroke-width="3" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 15,
            name: '活力双马尾',
            description: '两侧元气俏皮的高翘双马尾',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <!-- 左马尾 -->
                        <path d="M 22 24 C 6 12, -4 30, -2 58 C 4 64, 12 50, 14 36 Z" fill="${color}"/>
                        <!-- 右马尾 -->
                        <path d="M 78 24 C 94 12, 104 30, 102 58 C 96 64, 88 50, 86 36 Z" fill="${color}"/>
                        <!-- 红色发圈 -->
                        <circle cx="20" cy="24" r="4.5" fill="#F43F5E"/>
                        <circle cx="80" cy="24" r="4.5" fill="#F43F5E"/>
                        <!-- 顶盖发 -->
                        <path d="M 18 36 C 16 16, 34 8, 50 8 C 66 8, 84 16, 82 36 C 74 24, 60 22, 50 22 C 40 22, 26 24, 18 36 Z" fill="${color}"/>
                        <path d="M 26 30 Q 34 38 42 32" stroke="${color}" stroke-width="4.5" stroke-linecap="round" fill="none"/>
                        <path d="M 74 30 Q 66 38 58 32" stroke="${color}" stroke-width="4.5" stroke-linecap="round" fill="none"/>
                    </g>
                `;
            }
        },
        {
            id: 16,
            name: '潮流鲻鱼头',
            description: '层次碎发刘海与微扬后脖发',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 2px rgba(0,0,0,0.25))">
                        <!-- 颈部向外翘发 -->
                        <path d="M 16 46 C 8 62, 12 84, 18 94 C 24 82, 24 64, 22 50 Z" fill="${color}"/>
                        <path d="M 84 46 C 92 62, 88 84, 82 94 C 76 82, 76 64, 78 50 Z" fill="${color}"/>
                        <!-- 头顶与碎发 -->
                        <path d="M 18 38 C 16 14, 38 4, 50 4 C 62 4, 84 14, 82 38 C 76 26, 68 22, 50 22 C 32 22, 24 26, 18 38 Z" fill="${color}"/>
                        <path d="M 32 22 L 40 34 L 48 24 L 56 34 L 64 22" stroke="${color}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </g>
                `;
            }
        },
        {
            id: 17,
            name: '复古名媛卷',
            description: '优雅侧分大波浪与温婉垂卷',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <!-- 侧分顶部大弧度 -->
                        <path d="M 16 38 C 12 12, 36 2, 58 2 C 78 2, 88 18, 86 38 C 78 22, 60 16, 44 20 C 30 24, 20 30, 16 38 Z" fill="${color}"/>
                        <!-- 垂挂右侧的大波浪卷 -->
                        <path d="M 80 34 C 92 46, 96 68, 88 88 C 80 94, 74 84, 76 72 C 80 62, 78 48, 76 38 Z" fill="${color}"/>
                        <path d="M 32 10 Q 52 4 72 12" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.35"/>
                    </g>
                `;
            }
        },
        {
            id: 18,
            name: '街头渔夫帽',
            description: '潮牌深灰渔夫帽与微露发梢',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.3))">
                        <!-- 底部露出发梢 -->
                        <path d="M 18 42 C 14 56, 14 70, 20 80 C 24 70, 26 56, 24 44 Z" fill="${color}"/>
                        <path d="M 82 42 C 86 56, 86 70, 80 80 C 76 70, 74 56, 76 44 Z" fill="${color}"/>
                        <!-- 帽子梯形筒 -->
                        <path d="M 28 26 L 34 6 L 66 6 L 72 26 Z" fill="#334155"/>
                        <ellipse cx="50" cy="6" rx="16" ry="4" fill="#1E293B"/>
                        <!-- 帽檐 -->
                        <ellipse cx="50" cy="27" rx="36" ry="10" fill="#475569"/>
                        <!-- 标牌 -->
                        <rect x="44" y="14" width="12" height="6" rx="2" fill="#F43F5E"/>
                        <rect x="46" y="16" width="8" height="2" fill="#FFFFFF"/>
                    </g>
                `;
            }
        },
        {
            id: 19,
            name: '浪漫贝雷帽',
            description: '法式酒红歪戴贝雷帽',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <path d="M 20 40 C 18 20, 36 12, 50 12 C 64 12, 82 20, 80 40 C 74 30, 60 26, 50 26 C 40 26, 26 30, 20 40 Z" fill="${color}"/>
                        <!-- 歪戴贝雷帽 -->
                        <path d="M 12 28 C 10 10, 38 -2, 68 4 C 88 8, 92 24, 76 34 C 54 38, 22 36, 12 28 Z" fill="#991B1B"/>
                        <path d="M 26 12 Q 52 4 72 10" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" fill="none" opacity="0.3"/>
                        <path d="M 52 2 L 54 -4" stroke="#7F1D1D" stroke-width="3" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 20,
            name: '赛博莫西干',
            description: '电光青刺边与极简渐变铲青',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.3))">
                        <path d="M 20 36 C 24 24, 34 18, 42 16 L 42 32 Z" fill="${color}" opacity="0.35"/>
                        <path d="M 80 36 C 76 24, 66 18, 58 16 L 58 32 Z" fill="${color}" opacity="0.35"/>
                        <path d="M 38 28 L 44 8 L 48 18 L 52 -2 L 56 16 L 62 6 L 60 28 Z" fill="${color}"/>
                        <path d="M 44 8 L 48 18 L 52 -2 L 56 16 L 62 6" stroke="#00F0FF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </g>
                `;
            }
        },
        {
            id: 21,
            name: '丝滑黑长直',
            description: '顺滑如瀑及腰长发与中分刘海',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 3px rgba(0,0,0,0.25))">
                        <!-- 垂坠后背长发 -->
                        <path d="M 14 36 C 8 55, 6 80, 10 106 C 18 106, 24 82, 22 50 C 30 24, 70 24, 78 50 C 76 82, 82 106, 90 106 C 94 80, 92 55, 86 36 C 80 14, 66 6, 50 6 C 34 6, 20 14, 14 36 Z" fill="${color}"/>
                        <!-- 前额中分 -->
                        <path d="M 22 36 Q 34 26 48 30 L 46 22 Q 32 20 22 36 Z" fill="${color}"/>
                        <path d="M 78 36 Q 66 26 52 30 L 54 22 Q 68 20 78 36 Z" fill="${color}"/>
                        <path d="M 16 60 Q 14 78 18 96" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" fill="none" opacity="0.22"/>
                        <path d="M 84 60 Q 86 78 82 96" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" fill="none" opacity="0.22"/>
                    </g>
                `;
            }
        },
        {
            id: 22,
            name: '宇航太空盔',
            description: '圆润透明太空头盔与反光弧',
            render(color) {
                return `
                    <g filter="drop-shadow(0px 3px 4px rgba(0,0,0,0.3))">
                        <path d="M 26 36 C 24 22, 38 16, 50 16 C 62 16, 76 22, 74 36 Z" fill="${color}"/>
                        <!-- 气泡透明外罩 -->
                        <ellipse cx="50" cy="46" rx="46" ry="44" fill="rgba(6,182,212,0.12)" stroke="#0284C7" stroke-width="3"/>
                        <path d="M 20 32 A 38 38 0 0 1 76 14" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" fill="none" opacity="0.65"/>
                        <!-- 颈圈 -->
                        <rect x="22" y="86" width="56" height="10" rx="4" fill="#CBD5E1" stroke="#475569" stroke-width="2"/>
                        <rect x="38" y="88" width="24" height="6" rx="2" fill="#0284C7"/>
                    </g>
                `;
            }
        }
    ];

    const ACCESSORIES = [
        {
            id: 0,
            name: '无配饰',
            description: '素颜不戴配件',
            render() { return ''; }
        },
        {
            id: 1,
            name: '猫耳发箍',
            description: '粉内里三角猫耳',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.25))">
                        <path d="M 18 22 L 28 4 L 40 24 Z" fill="#18181B" stroke="#111" stroke-width="2"/>
                        <path d="M 60 24 L 72 4 L 82 22 Z" fill="#18181B" stroke="#111" stroke-width="2"/>
                        <path d="M 23 20 L 28 10 L 36 22 Z" fill="#FB7185"/>
                        <path d="M 64 22 L 72 10 L 77 20 Z" fill="#FB7185"/>
                        <path d="M 30 22 Q 50 16 70 22" fill="none" stroke="#18181B" stroke-width="4" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 2,
            name: '恶魔弯角',
            description: '两侧上弯的暗红魔角',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.3))">
                        <path d="M 22 28 C 8 22, 6 4, 20 -2 C 16 10, 22 18, 30 24 Z" fill="#7F1D1D" stroke="#111" stroke-width="2"/>
                        <path d="M 78 28 C 92 22, 94 4, 80 -2 C 84 10, 78 18, 70 24 Z" fill="#7F1D1D" stroke="#111" stroke-width="2"/>
                        <path d="M 16 10 Q 18 4 22 6" fill="none" stroke="#FECACA" stroke-width="2"/>
                    </g>
                `;
            }
        },
        {
            id: 3,
            name: '天使光环',
            description: '头顶悬浮金环',
            render() {
                return `
                    <ellipse cx="50" cy="2" rx="22" ry="7" fill="none" stroke="#F59E0B" stroke-width="5"/>
                    <ellipse cx="50" cy="2" rx="22" ry="7" fill="none" stroke="#FEF3C7" stroke-width="2"/>
                    <ellipse cx="62" cy="-1" rx="4" ry="1.6" fill="#FFFFFF" opacity="0.7"/>
                `;
            }
        },
        {
            id: 4,
            name: '头戴耳机',
            description: '罩耳大耳机与头梁',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.3))">
                        <path d="M 22 40 Q 50 4 78 40" fill="none" stroke="#18181B" stroke-width="6" stroke-linecap="round"/>
                        <path d="M 22 40 Q 50 8 78 40" fill="none" stroke="#3F3F46" stroke-width="2.5"/>
                        <rect x="8" y="38" width="16" height="28" rx="8" fill="#18181B" stroke="#111" stroke-width="2"/>
                        <rect x="76" y="38" width="16" height="28" rx="8" fill="#18181B" stroke="#111" stroke-width="2"/>
                        <rect x="11" y="44" width="10" height="16" rx="5" fill="#FF4F00"/>
                        <rect x="79" y="44" width="10" height="16" rx="5" fill="#FF4F00"/>
                    </g>
                `;
            }
        },
        {
            id: 5,
            name: '侧边大蝴蝶结',
            description: '歪戴在耳侧的巨大蝴蝶结',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.25))">
                        <path d="M 64 8 L 86 2 L 80 22 L 70 16 Z" fill="#DB2777" stroke="#111" stroke-width="2"/>
                        <path d="M 70 18 L 96 28 L 78 40 L 68 26 Z" fill="#F472B6" stroke="#111" stroke-width="2"/>
                        <circle cx="72" cy="22" r="6" fill="#9D174D" stroke="#111" stroke-width="2"/>
                        <circle cx="72" cy="22" r="2" fill="#FECDD3"/>
                    </g>
                `;
            }
        },
        {
            id: 6,
            name: '海盗眼罩',
            description: '斜跨头带与单眼罩',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.3))">
                        <path d="M 12 32 L 88 58" stroke="#18181B" stroke-width="6" stroke-linecap="round"/>
                        <ellipse cx="34" cy="48" rx="13" ry="11" fill="#18181B" stroke="#111" stroke-width="2"/>
                        <path d="M 28 44 L 40 52" stroke="#52525B" stroke-width="2"/>
                    </g>
                `;
            }
        },
        {
            id: 7,
            name: '迷你皇冠',
            description: '歪戴的小金冠与宝石',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.3))">
                        <path d="M 30 18 L 34 4 L 42 14 L 50 0 L 58 14 L 66 4 L 70 18 Z" fill="#F59E0B" stroke="#111" stroke-width="2.2" stroke-linejoin="round"/>
                        <rect x="30" y="16" width="40" height="6" rx="1.5" fill="#D97706" stroke="#111" stroke-width="2"/>
                        <circle cx="50" cy="10" r="3.2" fill="#EF4444"/>
                        <circle cx="38" cy="14" r="2.2" fill="#38BDF8"/>
                        <circle cx="62" cy="14" r="2.2" fill="#A3E635"/>
                    </g>
                `;
            }
        },
        {
            id: 8,
            name: '针织围脖',
            description: '堆在脖子上的条纹围巾',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.25))">
                        <path d="M 22 72 Q 50 86 78 72 L 80 92 Q 50 102 20 92 Z" fill="#2563EB" stroke="#111" stroke-width="2.2"/>
                        <path d="M 24 80 L 76 80" stroke="#FDE047" stroke-width="3"/>
                        <path d="M 26 86 L 74 86" stroke="#FDE047" stroke-width="3"/>
                        <path d="M 64 88 L 78 108 L 70 108 L 60 92 Z" fill="#1D4ED8" stroke="#111" stroke-width="2"/>
                        <path d="M 68 96 L 76 108" stroke="#FDE047" stroke-width="2"/>
                    </g>
                `;
            }
        },
        {
            id: 9,
            name: 'WLR 十字架链',
            description: '铆钉项圈与垂坠十字架',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.35))">
                        <path d="M 28 78 Q 50 90 72 78" fill="none" stroke="#111111" stroke-width="5" stroke-linecap="round"/>
                        <circle cx="32" cy="80" r="2.4" fill="#A1A1AA"/>
                        <circle cx="40" cy="84" r="2.4" fill="#A1A1AA"/>
                        <circle cx="50" cy="86" r="2.4" fill="#A1A1AA"/>
                        <circle cx="60" cy="84" r="2.4" fill="#A1A1AA"/>
                        <circle cx="68" cy="80" r="2.4" fill="#A1A1AA"/>
                        <path d="M 50 86 L 50 108" stroke="#D4D4D8" stroke-width="3.2" stroke-linecap="round"/>
                        <path d="M 50 94 L 50 112" stroke="#E11D48" stroke-width="5.5" stroke-linecap="round"/>
                        <path d="M 40 102 L 60 102" stroke="#E11D48" stroke-width="5.5" stroke-linecap="round"/>
                        <path d="M 50 94 L 50 112" stroke="#111" stroke-width="2"/>
                        <path d="M 40 102 L 60 102" stroke="#111" stroke-width="2"/>
                    </g>
                `;
            }
        },
        {
            id: 10,
            name: '赛博VR目镜',
            description: '科技感发光青粉扫描视窗',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 3px rgba(0,0,0,0.35))">
                        <rect x="14" y="38" width="72" height="20" rx="5" fill="#0F172A" stroke="#06B6D4" stroke-width="2.5"/>
                        <rect x="18" y="42" width="64" height="12" rx="3" fill="#164E63"/>
                        <path d="M 20 48 L 80 48" stroke="#22D3EE" stroke-width="2" stroke-dasharray="6,3" opacity="0.9"/>
                        <circle cx="24" cy="48" r="2.5" fill="#F43F5E"/>
                        <circle cx="76" cy="48" r="2.5" fill="#22D3EE"/>
                    </g>
                `;
            }
        },
        {
            id: 11,
            name: '派对彩条帽',
            description: '粉黄条纹尖顶帽与绒球',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 3px rgba(0,0,0,0.25))">
                        <polygon points="32,24 68,24 50,-10" fill="#EC4899" stroke="#BE185D" stroke-width="2"/>
                        <polygon points="37,16 63,16 58,8 42,8" fill="#FACC15"/>
                        <polygon points="45,2 55,2 50,-8" fill="#06B6D4"/>
                        <circle cx="50" cy="-11" r="5" fill="#FACC15"/>
                        <path d="M 30 24 Q 35 28 40 24 Q 45 28 50 24 Q 55 28 60 24 Q 65 28 70 24" fill="none" stroke="#F43F5E" stroke-width="4" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 12,
            name: '头顶小黄鸭',
            description: '趴在头顶上的呆萌洗澡小黄鸭',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.25))">
                        <ellipse cx="50" cy="4" rx="14" ry="10" fill="#FACC15" stroke="#CA8A04" stroke-width="2"/>
                        <circle cx="59" cy="-2" r="8" fill="#FACC15" stroke="#CA8A04" stroke-width="2"/>
                        <polygon points="66,-2 74,-1 66,2" fill="#F97316" stroke="#C2410C" stroke-width="1.2"/>
                        <circle cx="61" cy="-4" r="1.8" fill="#111111"/>
                        <circle cx="60.5" cy="-4.5" r="0.6" fill="#FFFFFF"/>
                        <path d="M 44 4 Q 49 10 54 4" fill="none" stroke="#CA8A04" stroke-width="2" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 13,
            name: '创可贴贴纸',
            description: '脸颊十字交叉创可贴与鼻梁贴',
            render() {
                return `
                    <g filter="drop-shadow(0px 1px 2px rgba(0,0,0,0.2))">
                        <!-- 鼻梁创口贴 -->
                        <rect x="42" y="52" width="16" height="6" rx="2" fill="#FDE68A" stroke="#D97706" stroke-width="1.5" transform="rotate(-8 50 55)"/>
                        <circle cx="50" cy="55" r="1.2" fill="#EF4444"/>
                        <!-- 脸颊粉色十字贴 -->
                        <rect x="22" y="58" width="14" height="5" rx="1.5" fill="#FBCFE8" stroke="#DB2777" stroke-width="1.2" transform="rotate(40 29 60)"/>
                        <rect x="22" y="58" width="14" height="5" rx="1.5" fill="#FBCFE8" stroke="#DB2777" stroke-width="1.2" transform="rotate(-40 29 60)"/>
                    </g>
                `;
            }
        },
        {
            id: 14,
            name: '复古黑框方镜',
            description: '潮酷大黑框方形眼镜与透亮反光',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.3))">
                        <line x1="44" y1="46" x2="56" y2="46" stroke="#18181B" stroke-width="3.5" stroke-linecap="round"/>
                        <rect x="22" y="38" width="22" height="18" rx="4" fill="rgba(255,255,255,0.2)" stroke="#18181B" stroke-width="3.5"/>
                        <rect x="56" y="38" width="22" height="18" rx="4" fill="rgba(255,255,255,0.2)" stroke="#18181B" stroke-width="3.5"/>
                        <line x1="26" y1="42" x2="34" y2="42" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                        <line x1="60" y1="42" x2="68" y2="42" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                    </g>
                `;
            }
        },
        {
            id: 15,
            name: '闪亮珍珠项圈',
            description: '华丽珍珠链与红宝石吊坠',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.25))">
                        <path d="M 28 80 Q 50 92 72 80" fill="none" stroke="#E2E8F0" stroke-width="7" stroke-linecap="round"/>
                        <circle cx="30" cy="80" r="3.2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <circle cx="37" cy="83" r="3.2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <circle cx="44" cy="85" r="3.2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <circle cx="50" cy="86" r="3.6" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <circle cx="56" cy="85" r="3.2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <circle cx="63" cy="83" r="3.2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <circle cx="70" cy="80" r="3.2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
                        <polygon points="50,88 54,94 50,100 46,94" fill="#E11D48" stroke="#9F1239" stroke-width="1.2"/>
                        <circle cx="50" cy="94" r="1.2" fill="#FFFFFF"/>
                    </g>
                `;
            }
        },
        {
            id: 16,
            name: '头顶萌芽发夹',
            description: '绿油油的双叶破土小嫩芽发卡',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.2))">
                        <path d="M 50 16 Q 48 4 50 -4" fill="none" stroke="#22C55E" stroke-width="3" stroke-linecap="round"/>
                        <path d="M 50 -2 C 40 -8, 38 4, 50 -2 Z" fill="#4ADE80" stroke="#16A34A" stroke-width="1.5"/>
                        <path d="M 50 -4 C 60 -10, 62 2, 50 -4 Z" fill="#4ADE80" stroke="#16A34A" stroke-width="1.5"/>
                        <rect x="42" y="14" width="16" height="4" rx="2" fill="#EC4899"/>
                    </g>
                `;
            }
        },
        {
            id: 17,
            name: '暗夜小蝙蝠翼',
            description: '耳侧张开的暗黑小恶魔蝙蝠翼',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 2px rgba(0,0,0,0.3))">
                        <path d="M 22 36 C 10 24, -4 28, -6 40 C -2 42, 6 42, 4 48 C 10 48, 16 48, 14 54 C 20 50, 24 44, 22 36 Z" fill="#18181B" stroke="#09090B" stroke-width="1.8" stroke-linejoin="round"/>
                        <path d="M 20 38 L 0 34" stroke="#52525B" stroke-width="1.2"/>
                        <path d="M 78 36 C 90 24, 104 28, 106 40 C 102 42, 94 42, 96 48 C 90 48, 84 48, 86 54 C 80 50, 76 44, 78 36 Z" fill="#18181B" stroke="#09090B" stroke-width="1.8" stroke-linejoin="round"/>
                        <path d="M 80 38 L 100 34" stroke="#52525B" stroke-width="1.2"/>
                    </g>
                `;
            }
        },
        {
            id: 18,
            name: '冠军金牌',
            description: '第一名金色闪耀奖牌与红蓝织带',
            render() {
                return `
                    <g filter="drop-shadow(0px 2px 3px rgba(0,0,0,0.3))">
                        <path d="M 38 80 L 48 96 L 44 96 L 36 80 Z" fill="#EF4444"/>
                        <path d="M 62 80 L 52 96 L 56 96 L 64 80 Z" fill="#3B82F6"/>
                        <circle cx="50" cy="102" r="11" fill="#FACC15" stroke="#CA8A04" stroke-width="2"/>
                        <circle cx="50" cy="102" r="9" fill="none" stroke="#EAB308" stroke-width="1" stroke-dasharray="2,1"/>
                        <text x="50" y="106" font-size="11" font-weight="900" fill="#78350F" text-anchor="middle" font-family="ui-sans-serif,system-ui,sans-serif">1</text>
                    </g>
                `;
            }
        }
    ];

    const LOOKS = [
        { id: 'wlr', face: 15, hair: 14, acc: 9 }
    ];

    const WLR_FACE_ID = 15;
    const WLR_HAIR_ID = 14;

    function clampIndex(value, length) {
        const n = parseInt(value, 10);
        if (isNaN(n) || n < 0 || n >= length) return 0;
        return n;
    }

    function normalizeAvatar(raw) {
        if (!raw || typeof raw !== 'object') {
            return { face: 0, hair: 0, acc: 0 };
        }
        return {
            face: clampIndex(raw.face, FACES.length),
            hair: clampIndex(raw.hair, HAIRS.length),
            acc: clampIndex(raw.acc != null ? raw.acc : raw.accessory, ACCESSORIES.length),
        };
    }

    function getPalette(avatar, nickname = '') {
        const f = avatar.face;
        const h = avatar.hair;
        const a = avatar.acc || 0;
        let seed = (f * 5 + h * 11 + a * 17);
        if (nickname) {
            for (let i = 0; i < nickname.length; i++) {
                seed += nickname.charCodeAt(i);
            }
        }
        const bodyIndex = Math.abs(seed) % BODY_COLORS.length;
        const hairIndex = Math.abs(seed + 3) % HAIR_COLORS.length;
        const palette = {
            body: BODY_COLORS[bodyIndex],
            hair: HAIR_COLORS[hairIndex],
        };
        if (h === WLR_HAIR_ID) {
            palette.hair = '#9F1239';
        }
        if (f === WLR_FACE_ID) {
            palette.body = { bg: '#F4E7D4', shadow: '#C4A484' };
        }
        return palette;
    }

    function renderSvg(avatarRaw, size = 64, options = {}) {
        const avatar = normalizeAvatar(avatarRaw);
        const nickname = options.nickname || '';
        const palette = getPalette(avatar, nickname);

        const faceObj = FACES[avatar.face] || FACES[0];
        const hairObj = HAIRS[avatar.hair] || HAIRS[0];
        const accObj = ACCESSORIES[avatar.acc] || ACCESSORIES[0];

        const width = size;
        const height = size;
        const className = options.className || 'kahoot-avatar-svg';

        return `
            <svg class="${className}" width="${width}" height="${height}" viewBox="-8 -14 116 128" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="头像" style="overflow: visible; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.12));">
                <g class="avatar-body-layer">
                    <rect x="14" y="14" width="72" height="72" rx="36" fill="${palette.body.bg}"/>
                    <path d="M 16 60 Q 50 92 84 60 A 36 36 0 0 1 16 60 Z" fill="${palette.body.shadow}" opacity="0.35"/>
                    <rect x="14" y="14" width="72" height="72" rx="36" stroke="rgba(0,0,0,0.15)" stroke-width="2.5"/>
                </g>
                <g class="avatar-face-layer">
                    ${faceObj.render(palette.body.bg)}
                </g>
                <g class="avatar-hair-layer">
                    ${hairObj.render(palette.hair)}
                </g>
                <g class="avatar-acc-layer">
                    ${accObj.render()}
                </g>
            </svg>
        `.trim();
    }

    function getRandomAvatar() {
        return {
            face: Math.floor(Math.random() * FACES.length),
            hair: Math.floor(Math.random() * HAIRS.length),
            acc: Math.floor(Math.random() * ACCESSORIES.length),
        };
    }

    function applyLook(lookId) {
        const look = LOOKS.find((item) => item.id === lookId) || LOOKS[0];
        return { face: look.face, hair: look.hair, acc: look.acc };
    }

    function localizedName(prefix, item) {
        if (window.t) {
            const translated = window.t(prefix + item.id);
            if (translated && translated !== prefix + item.id) return translated;
        }
        return item.name;
    }

    function getFaceName(index) {
        return localizedName('face.', FACES[typeof index === 'number' ? index : 0] || FACES[0]);
    }

    function getHairName(index) {
        return localizedName('hair.', HAIRS[typeof index === 'number' ? index : 0] || HAIRS[0]);
    }

    function getAccName(index) {
        return localizedName('acc.', ACCESSORIES[typeof index === 'number' ? index : 0] || ACCESSORIES[0]);
    }

    const AvatarSystem = {
        FACES,
        HAIRS,
        ACCESSORIES,
        LOOKS,
        normalize: normalizeAvatar,
        renderSvg,
        random: getRandomAvatar,
        applyLook,
        getPalette,
        getFaceName,
        getHairName,
        getAccName,
    };

    global.AvatarSystem = AvatarSystem;

})(typeof window !== 'undefined' ? window : this);

