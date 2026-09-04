/**
 * Shoot Studio Frontend Internationalization (i18n) Engine
 * Supports seamless bilingual switching between 简体中文 (zh-hans) & English (en)
 */
(function (global) {
    'use strict';

    const DICT_ZH = {
        // --- 通用 / General ---
        'app.title': 'Shoot Studio',
        'lang.name': '简体中文',
        'lang.switch': 'English',
        'btn.back': '返回',
        'btn.save': '保存',
        'btn.exit': '离开',
        'btn.cancel': '取消',
        'btn.confirm': '确认',
        'btn.delete': '删除',
        'btn.edit': '编辑',
        'btn.close': '收起',
        'btn.home': '返回首页',
        'btn.dashboard': '返回控制台',
        'status.loading': '加载中…',
        'status.saving': '正在保存…',
        'status.saved': '已保存',
        'status.error': '操作失败',
        'conn.connecting': '连接中，操作将稍后发送...',
        'conn.connected': '已连接',
        'conn.error': '连接异常，正在重试...',
        'conn.closed': '连接断开，正在重连...',

        // --- 首页 / Landing ---
        'landing.headline_1': 'every question.',
        'landing.headline_2': 'every answer.',
        'landing.student_title': '学生加入',
        'landing.room_code': '房间号 / 练习码',
        'landing.room_code_placeholder': '6位数字 / 字母PIN',
        'landing.join_hint': '',
        'landing.nickname': '昵称',
        'landing.nickname_placeholder': '输入你的昵称',
        'landing.btn_join': '进入游戏',
        'landing.switch_to_teacher': '你是出题人？<strong>切换至老师端 ↻</strong>',
        'landing.switch_to_student': '← <strong>返回学生加入</strong>',
        'landing.teacher_title': '老师登录',
        'landing.username': '用户名',
        'landing.username_placeholder': '输入老师用户名',
        'landing.password': '密码',
        'landing.password_placeholder': '注册时设置的密码（不是邀请码）',
        'landing.btn_teacher_login': '登录老师控制台',
        'landing.no_account': '还没有账号？邀请码注册 →',

        // --- 老师控制台 / Teacher Dashboard ---
        'dash.title': '老师控制台',
        'dash.current_user': '当前账号：%s',
        'dash.logout': '退出登录',
        'dash.create_room_title': '创建互动房间',
        'dash.create_room_desc': '挑选一套测验题库，一键生成 6 位房间号并投屏至大屏，组织学生手机连线极速竞答。',
        'dash.btn_create_room': '+ 发起新房间',
        'dash.btn_assign_practice': '布置练习',
        'assign.share_text': '请同学们打开测验首页，输入练习码 %s，开始《%s》个人练习。',
        'assign.copied_code': '已复制练习码 %s',
        'assign.copied_share': '已复制发给学生的文案',
        'dash.quiz_bank_title': '新建 Shoot / 我的题库',
        'dash.quiz_bank_desc': '支持手动编排或使用 AI 智能批量出题，自由配置单选、多选、判断与配图题型。',
        'dash.btn_new_shoot': '+ 新建 Shoot',
        'dash.btn_manage_bank': '管理我的题库 (%s)',
        'dash.settings': '账号设置',
        'dash.settings_hint': '管理头像、性别与登录信息',
        'dash.display_name': '显示名',
        'dash.username': '登录用户名',
        'dash.gender': '性别',
        'dash.gender.unspecified': '保密',
        'dash.gender.female': '女',
        'dash.gender.male': '男',
        'dash.gender.other': '其他',
        'dash.current_password': '当前密码',
        'dash.new_password': '新密码',
        'dash.new_password_confirm': '确认新密码',
        'dash.password_hint': '更改用户名或密码时需填写当前密码；新密码留空则不修改。',
        'dash.btn_save_settings': '保存设置',
        'dash.settings_saved': '已保存',
        'dash.avatar_random': '随机换装',

        // --- 题库向导 / Wizard ---
        'wizard.title': '新建测验题库',
        'wizard.step_1_indicator': '1. 命名题库',
        'wizard.step_2_indicator': '2. 选择出题方式',
        'wizard.back_dashboard': '返回控制台',
        'wizard.back_step_1': '返回修改名称',
        'wizard.step_1_title': '第一步：命名这套测验题库',
        'wizard.step_1_desc': '每次新建都会保存为<strong>一套独立的测验套题</strong>，可在题库中随时复用，也可直接一键发起大屏互动。',
        'wizard.quiz_name_label': '题库名称',
        'wizard.quiz_name_placeholder': '例如：初一地理期末总复习 / 细胞生物学专题测验',
        'wizard.btn_goto_step_2': '下一步：选择出题方式',
        'wizard.step_2_title': '第二步：选择出题方式',
        'wizard.step_2_desc': '选择最适合你的出题模式，选定后即可直接进入试题编辑或批量生成。',
        'wizard.mode_manual_title': '手动编辑出题',
        'wizard.mode_manual_desc': '逐题编写题干与选项，自由配置单选、多选、判断、简答与配图。',
        'wizard.mode_manual_btn': '开始手动出题 →',
        'wizard.mode_ai_title': 'AI 智能生成',
        'wizard.mode_ai_desc': '输入学科主题、年级与题型配比，由大模型自动出题并填入。',
        'wizard.mode_ai_btn': '使用 AI 生成 →',
        'wizard.mode_excel_title': 'Excel 批量导入',
        'wizard.mode_excel_desc': '下载标准表格模板，按固定格式批量上传 .xlsx 文件快速导入试题。',
        'wizard.mode_excel_btn': '上传 Excel 导入 →',
        'wizard.mode_public_title': '从公共题库选用',
        'wizard.mode_public_desc': '浏览其他老师公开的精选套题，一键选用或二次编辑修改。',
        'wizard.mode_public_btn': '浏览公共题库 →',

        // --- 学生游戏端 / Play Screen ---
        'play.room_pin': '房间号',
        'play.player': '玩家',
        'play.connected_count': '已连线 <strong id="player-count">%s</strong> 人',
        'play.random_avatar': '随机换装',
        'play.face': '表情',
        'play.hair': '发型',
        'play.waiting_host': '等待老师开始游戏',
        'play.question_num': '第 %s / %s 题',
        'play.text_placeholder': '在此输入你的答案...',
        'play.text_placeholder_wordcloud': '输入一个词或短语...',
        'play.word_cloud_title': '大家正在说',
        'play.word_cloud_need_word': '请输入一个词',
        'play.btn_submit': '提交答案',
        'play.waiting_next': '等待下一题...',
        'play.explanation_title': '老师正在讲解',
        'play.explanation_detail': '请看教室大屏，本题无需作答',
        'play.live_ranking': '实时积分榜',
        'play.your_rank_score': '第 %s 名 · 总分 %s',
        'play.danmaku_send': '发送',
        'play.danmaku_btn': '发弹幕',
        'countdown.get_ready': '准备答题',
        'countdown.go': 'GO!',
        'countdown.go_hint': '开始抢答！',

        // 反馈卡片状态
        'fb.correct': '对',
        'fb.wrong': '错',
        'fb.timeup': '时间到，等待揭晓',
        'fb.submitted': '已提交，等待揭晓',
        'fb.submitted_short': '已提交',
        'fb.question_ended': '本题已结束',
        'fb.get_ready': '请准备',

        // 最终结算与领奖台
        'awards.ceremony': '颁奖典礼',
        'awards.full_ranking': '完整排名',
        'awards.btn_analytics': '查看数据分析',
        'awards.back_to_podium': '← 返回荣誉领奖台',
        'awards.champion': '冠军',
        'awards.runner_up': '亚军',
        'awards.third_place': '季军',
        'awards.rank_n': '第 %s 名',
        'awards.final_score': '最终积分: <strong>%s</strong> 分',
        'awards.pts_unit': '分',
        'awards.pts_gain': '+%s',

        // --- 头像表情、发型与配饰 / Avatar System ---
        'face.0': '元气微笑',
        'face.1': '酷炫墨镜',
        'face.2': '眯眼大笑',
        'face.3': '俏皮眨眼',
        'face.4': '呆萌大眼',
        'face.5': '学霸眼镜',
        'face.6': '惊讶张嘴',
        'face.7': '坚定斗志',
        'face.8': '爱心眼',
        'face.9': '哈欠犯困',
        'face.10': '怒气喷发',
        'face.11': '忍者面罩',
        'face.12': '星星眼',
        'face.13': '泪奔大哭',
        'face.14': '猫须喵喵',
        'face.15': 'WLR 吸血鬼',
        'face.16': '搞怪吐舌',
        'face.17': '暴富金币眼',
        'face.18': '晕乎圈圈眼',
        'face.19': '害羞红晕',
        'face.20': '绅士单片镜',
        'face.21': '赛博机械面',
        'face.22': '仓鼠鼓腮',

        'hair.0': '动感短发',
        'hair.1': '朋克飞机头',
        'hair.2': '蓬松爆炸头',
        'hair.3': '双丸子头',
        'hair.4': '齐刘海妹妹头',
        'hair.5': '反戴棒球帽',
        'hair.6': '高贵大背头',
        'hair.7': '呆毛小光头',
        'hair.8': '双麻花辫',
        'hair.9': '武士顶髻',
        'hair.10': '刺猬刺毛',
        'hair.11': '长波浪披肩',
        'hair.12': '狼尾短切',
        'hair.13': '单股长辫',
        'hair.14': '血红脏辫',
        'hair.15': '活力双马尾',
        'hair.16': '潮流鲻鱼头',
        'hair.17': '复古名媛卷',
        'hair.18': '街头渔夫帽',
        'hair.19': '浪漫贝雷帽',
        'hair.20': '赛博莫西干',
        'hair.21': '丝滑黑长直',
        'hair.22': '宇航太空盔',

        'acc.0': '无配饰',
        'acc.1': '猫耳发箍',
        'acc.2': '恶魔弯角',
        'acc.3': '天使光环',
        'acc.4': '头戴耳机',
        'acc.5': '侧边大蝴蝶结',
        'acc.6': '海盗眼罩',
        'acc.7': '迷你皇冠',
        'acc.8': '针织围脖',
        'acc.9': 'WLR 十字架链',
        'acc.10': '赛博VR目镜',
        'acc.11': '派对彩条帽',
        'acc.12': '头顶小黄鸭',
        'acc.13': '创可贴贴纸',
        'acc.14': '复古黑框方镜',
        'acc.15': '闪亮珍珠项圈',
        'acc.16': '头顶萌芽发夹',
        'acc.17': '暗夜小蝙蝠翼',
        'acc.18': '冠军金牌',

        // --- 大屏主持端 / Room Host ---
        'host.title': '主持游戏 - %s',
        'host.default_room_name': '互动测验房间',
        'host.join_hint': '请使用手机浏览器访问并输入 6 位房间号加入',
        'host.room_pin_label': 'ROOM PIN',
        'host.joined_count': '已加入：<strong id="host-player-count">%s</strong> 人',
        'host.total_questions_count': '共 <strong>%s</strong> 道试题',
        'host.players_wall_title': '已进入玩家',
        'host.waiting_players_tip': '等待学生连线中… 手机输入房间号后将实时在此处显示',
        'host.btn_start': '开始游戏',
        'host.btn_starting': '正在开启游戏…',
        'host.answered_progress': '已答：<strong id="answer-count">%s</strong> / <span id="total-players">%s</span> 人',
        'host.btn_end_q': '结束本题',
        'host.btn_end_explanation': '下一题',
        'host.btn_next_q': '下一题',
        'host.btn_show_ranking': '查看排行榜',
        'host.btn_ceremony': '颁奖典礼',
        'host.reveal_kicker': '答题揭晓',
        'host.reveal_title': '本题统计',
        'host.reveal_subtitle': '各选项作答人数与正确答案',
        'host.correct_answer': '正确答案',
        'host.word_cloud_title': '实时词云汇总',
        'host.word_cloud_empty': '暂无回答，等待大家提交...',
        'host.short_correct_count': '人答对',
        'host.short_meta': '共 %s 人作答 · %s 人未作答',
        'host.loading_stem': '加载题干中…',
        'host.explanation_done': '讲解结束',
        'host.explanation_done_sub': '本题无需作答，可进入下一题',
        'host.live_ranking': '实时积分榜',

        // 题型徽章
        'qtype.single': '【单选】',
        'qtype.multiple': '【多选】',
        'qtype.judgment': '【判断】',
        'qtype.short_answer': '【简答】',
        'qtype.word_cloud': '【词云】',
        'qtype.explanation': '【解释】',
        'qtype.label.single': '单选题',
        'qtype.label.multiple': '多选题',
        'qtype.label.judgment': '判断题',
        'qtype.label.short_answer': '简答题',
        'qtype.label.word_cloud': '词云题',
        'qtype.label.explanation': '解释',

        // --- 数据分析系统 / Analytics ---
        'analytics.title': '答题数据分析',
        'analytics.kpi_players': '参战学生',
        'analytics.kpi_accuracy': '全场综合正确率',
        'analytics.kpi_avg_score': '平均积分',
        'analytics.kpi_max_score': '最高得分',
        'analytics.kpi_questions': '试题总数',
        'analytics.unit_person': '人',
        'analytics.unit_question': '题',
        'analytics.unit_score': '分',
        'analytics.tab_by_question': '按题目分析 (正误名单)',
        'analytics.tab_by_player': '按学生分析 (错对题单)',
        'analytics.spotlight_hardest': '易错题：第 %s 题 (正确率 %s%)',
        'analytics.search_q_placeholder': '搜索题目或选项...',
        'analytics.search_p_placeholder': '搜索学生昵称...',
        'analytics.filter_all_types': '全部题型',
        'analytics.correct_list': '答对学生 (%s)',
        'analytics.wrong_list': '答错学生 (%s)',
        'analytics.unanswered_list': '未作答学生 (%s)',
        'analytics.none': '无',
        'analytics.correct_answer_label': '正确答案：',
        'analytics.response_time': '平均用时：%ss',
        'analytics.empty_search': '未找到匹配的分析记录',
        'analytics.score_col': '得分',
        'analytics.rank_col': '排名',
        'analytics.status_correct': '正确',
        'analytics.status_wrong': '错误',
        'analytics.status_unanswered': '未作答',

        // --- 题目编辑器 / Shoot Editor ---
        'editor.placeholder_title': 'Shoot 名称',
        'editor.toast_saved': '已快速保存',
        'editor.btn_add': '+ 添加',
        'editor.upload_img_tip': '点击上传题目图片（可选）',
        'editor.btn_remove_img': '移除图片',
        'editor.stem_placeholder': '输入题干…',
        'editor.opt_a': '选项 A',
        'editor.opt_b': '选项 B',
        'editor.opt_c': '选项 C',
        'editor.opt_d': '选项 D',
        'editor.mark_correct': '标为正确答案',
        'editor.short_correct_label': '参考答案（多个用 | 分隔）',
        'editor.wordcloud_tip': '词云题：学生提交文字后实时汇总，无标准答案。',
        'editor.props_title': '题目设置',
        'editor.field_type': '题型',
        'editor.field_time': '答题时限',
        'editor.btn_save_q': '保存本题',
        'editor.btn_delete_q': '删除本题',
        'editor.exit_modal_title': '离开编辑？',
        'editor.exit_modal_desc': '离开前请选择是否保存修改，以及是否将套题公开到题库。',
        'editor.save_changes_label': '保存当前修改',
        'editor.save_changes_desc': '保存题目、选项、配图和套题名称等编辑内容。',
        'editor.publish_label': '公开此套测验题库',
        'editor.publish_desc': '公开后，其他老师可在公共题库中浏览并一键选用本套题。',
        'editor.btn_confirm_exit': '确认离开',
        'editor.time_seconds': '%s 秒',
        'editor.type_hint_single': '单选：点击右侧 ✓ 标记唯一正确答案',
        'editor.type_hint_multiple': '多选：点击右侧 ✓ 勾选多个正确答案（至少 2 个）',
        'editor.type_hint_judgment': '判断：A 为「正确」，B 为「错误」，点击 ✓ 标记',
        'editor.type_hint_short': '简答：在参考答案框输入标准文本（多个用 | 分隔）',
        'editor.type_hint_wordcloud': '词云：学生输入词汇实时聚合展示，无对错评分',
        'editor.type_hint_explanation': '解释：只上传一张图片，上课铺满大屏；不限时，讲完后点下一题。学生不看、不作答',

        // --- 我的题库列表 / Question List ---
        'qlist.title': '我的题库',
        'qlist.table_title': '我的测验套题',
        'qlist.col_title': '套题名称',
        'qlist.col_count': '试题数量',
        'qlist.col_vis': '可见权限',
        'qlist.col_time': '创建时间',
        'qlist.col_actions': '快捷操作',
        'qlist.unit_q': '题',
        'qlist.status_public': '公开',
        'qlist.status_private': '私有',
        'qlist.btn_edit': '编辑',
        'qlist.delete_confirm': '确定要删除套题「%s」吗？此操作不可恢复。',
        'qlist.page_prev': '← 上一页',
        'qlist.page_next': '下一页 →',
        'qlist.page_indicator': '第 %s / %s 页',
        'qlist.empty_title': '暂无测验套题',
        'qlist.empty_desc': '你可以前往创建向导，使用手动、AI 或 Excel 快速创建你的第一套题库。',
        'qlist.btn_create_first': '+ 新建测验题库 →',

        'practice.score_now': '总分 %s',
        'practice.final_score': '总分 %s',
        'practice.your_rank': '第 %s 名',
        'practice.empty_board': '还没有其他人的练习记录',
        'practice.word_cloud_title': '本题词云',
    };

    const DICT_EN = {
        // --- 通用 / General ---
        'app.title': 'Shoot Studio',
        'lang.name': 'English',
        'lang.switch': '中文',
        'btn.back': 'Back',
        'btn.save': 'Save',
        'btn.exit': 'Exit',
        'btn.cancel': 'Cancel',
        'btn.confirm': 'Confirm',
        'btn.delete': 'Delete',
        'btn.edit': 'Edit',
        'btn.close': 'Close',
        'btn.home': 'Back to Home',
        'btn.dashboard': 'Back to Dashboard',
        'status.loading': 'Loading…',
        'status.saving': 'Saving…',
        'status.saved': 'Saved',
        'status.error': 'Action failed',
        'conn.connecting': 'Connecting, will send shortly...',
        'conn.connected': 'Connected',
        'conn.error': 'Connection error, retrying...',
        'conn.closed': 'Disconnected, reconnecting...',

        // --- 首页 / Landing ---
        'landing.headline_1': 'every question.',
        'landing.headline_2': 'every answer.',
        'landing.student_title': 'Join as Player',
        'landing.room_code': 'PIN / Practice code',
        'landing.room_code_placeholder': '6-digit PIN / Practice code',
        'landing.join_hint': '',
        'landing.nickname': 'Nickname',
        'landing.nickname_placeholder': 'Enter your nickname',
        'landing.btn_join': 'Enter Game',
        'landing.switch_to_teacher': 'Are you the host? <strong>Switch to Teacher Mode ↻</strong>',
        'landing.switch_to_student': '← <strong>Back to Player Join</strong>',
        'landing.teacher_title': 'Teacher Login',
        'landing.username': 'Username',
        'landing.username_placeholder': 'Enter teacher username',
        'landing.password': 'Password',
        'landing.password_placeholder': 'Password set during signup',
        'landing.btn_teacher_login': 'Log In to Studio',
        'landing.no_account': 'No account? Register with invite code →',

        // --- 老师控制台 / Teacher Dashboard ---
        'dash.title': 'Teacher Studio',
        'dash.current_user': 'Current user: %s',
        'dash.logout': 'Log Out',
        'dash.create_room_title': 'Host Live Game Room',
        'dash.create_room_desc': 'Pick a quiz set, generate a 6-digit game PIN on the big screen, and organize students to compete live on mobile devices.',
        'dash.btn_create_room': '+ Create New Room',
        'dash.btn_assign_practice': 'Assign practice',
        'assign.share_text': 'Open the quiz home page and enter practice code %s to start “%s”.',
        'assign.copied_code': 'Copied practice code %s',
        'assign.copied_share': 'Copied the student share message',
        'dash.quiz_bank_title': 'Create Shoot / My Quiz Bank',
        'dash.quiz_bank_desc': 'Build manually or use AI generation, freely configuring single, multiple, true/false, and media questions.',
        'dash.btn_new_shoot': '+ New Shoot',
        'dash.btn_manage_bank': 'Manage My Quizzes (%s)',
        'dash.settings': 'Account Settings',
        'dash.settings_hint': 'Manage avatar, gender, and login details',
        'dash.display_name': 'Display Name',
        'dash.username': 'Username',
        'dash.gender': 'Gender',
        'dash.gender.unspecified': 'Prefer not to say',
        'dash.gender.female': 'Female',
        'dash.gender.male': 'Male',
        'dash.gender.other': 'Other',
        'dash.current_password': 'Current Password',
        'dash.new_password': 'New Password',
        'dash.new_password_confirm': 'Confirm New Password',
        'dash.password_hint': 'Current password is required to change username or password. Leave new password blank to keep it.',
        'dash.btn_save_settings': 'Save Settings',
        'dash.settings_saved': 'Saved',
        'dash.avatar_random': 'Randomize',

        // --- 题库向导 / Wizard ---
        'wizard.title': 'Create Quiz Set',
        'wizard.step_1_indicator': '1. Name Quiz',
        'wizard.step_2_indicator': '2. Choose Method',
        'wizard.back_dashboard': 'Back to Studio',
        'wizard.back_step_1': 'Edit Quiz Name',
        'wizard.step_1_title': 'Step 1: Name Your Quiz Set',
        'wizard.step_1_desc': 'Each new quiz is saved as a <strong>reusable standalone set</strong> that you can host live anytime or edit later.',
        'wizard.quiz_name_label': 'Quiz Name',
        'wizard.quiz_name_placeholder': 'e.g., Grade 7 Geography Review / Cell Biology Quiz',
        'wizard.btn_goto_step_2': 'Next: Choose Creation Method',
        'wizard.step_2_title': 'Step 2: Choose Creation Method',
        'wizard.step_2_desc': 'Select how you want to build this quiz, then start editing or batch generating questions immediately.',
        'wizard.mode_manual_title': 'Manual Editor',
        'wizard.mode_manual_desc': 'Craft question stems and options step-by-step with single, multiple, true/false, short answer, and media support.',
        'wizard.mode_manual_btn': 'Start Manual Editing →',
        'wizard.mode_ai_title': 'AI Generation',
        'wizard.mode_ai_desc': 'Provide a topic, grade level, and question breakdown to auto-generate questions with large language models.',
        'wizard.mode_ai_btn': 'Generate with AI →',
        'wizard.mode_excel_title': 'Excel Batch Import',
        'wizard.mode_excel_desc': 'Download our standard template and upload formatted .xlsx spreadsheets for quick batch importing.',
        'wizard.mode_excel_btn': 'Upload Excel File →',
        'wizard.mode_public_title': 'From Public Library',
        'wizard.mode_public_desc': 'Browse curated quiz sets published by other educators and clone or modify them with one click.',
        'wizard.mode_public_btn': 'Browse Public Quizzes →',

        // --- 学生游戏端 / Play Screen ---
        'play.room_pin': 'PIN',
        'play.player': 'Player',
        'play.connected_count': 'Connected: <strong id="player-count">%s</strong> players',
        'play.random_avatar': 'Randomize',
        'play.face': 'Face',
        'play.hair': 'Hair',
        'play.waiting_host': 'Waiting for host to start',
        'play.question_num': 'Question %s of %s',
        'play.text_placeholder': 'Type your answer here...',
        'play.text_placeholder_wordcloud': 'Type a word or short phrase...',
        'play.word_cloud_title': 'What people are saying',
        'play.word_cloud_need_word': 'Please enter a word',
        'play.btn_submit': 'Submit Answer',
        'play.waiting_next': 'Waiting for next question...',
        'play.explanation_title': 'Teacher is explaining',
        'play.explanation_detail': 'Please look at the classroom screen. No answer needed.',
        'play.live_ranking': 'Leaderboard',
        'play.your_rank_score': 'Rank #%s · %s pts',
        'play.danmaku_send': 'Send',
        'play.danmaku_btn': 'Danmaku',
        'countdown.get_ready': 'Get Ready',
        'countdown.go': 'GO!',
        'countdown.go_hint': 'Go!',

        // 反馈卡片状态
        'fb.correct': 'Correct!',
        'fb.wrong': 'Incorrect',
        'fb.timeup': 'Time is up! Waiting for reveal...',
        'fb.submitted': 'Submitted! Waiting for reveal...',
        'fb.submitted_short': 'Submitted',
        'fb.question_ended': 'Question Ended',
        'fb.get_ready': 'Get Ready',

        // 最终结算与领奖台
        'awards.ceremony': 'Awards Ceremony',
        'awards.full_ranking': 'Full Leaderboard',
        'awards.btn_analytics': 'View Analytics',
        'awards.back_to_podium': '← Back to Honor Podium',
        'awards.champion': 'Champion',
        'awards.runner_up': '2nd Place',
        'awards.third_place': '3rd Place',
        'awards.rank_n': 'Rank #%s',
        'awards.final_score': 'Final Score: <strong>%s</strong> pts',
        'awards.pts_unit': 'pts',
        'awards.pts_gain': '+%s',

        // --- 头像表情、发型与配饰 / Avatar System ---
        'face.0': 'Cheerful Smile',
        'face.1': 'Cool Sunglasses',
        'face.2': 'Grinning Eyes',
        'face.3': 'Playful Wink',
        'face.4': 'Innocent Big Eyes',
        'face.5': 'Smart Glasses',
        'face.6': 'Surprised O-Mouth',
        'face.7': 'Determined Focus',
        'face.8': 'Heart Eyes',
        'face.9': 'Sleepy Yawn',
        'face.10': 'Angry Fire',
        'face.11': 'Ninja Mask',
        'face.12': 'Sparkling Stars',
        'face.13': 'Crying Waterfall',
        'face.14': 'Neko Cat Whiskers',
        'face.15': 'WLR Vampire',
        'face.16': 'Goofy Derp Wink',
        'face.17': 'Rich Money Eyes',
        'face.18': 'Dizzy Spirals',
        'face.19': 'Blushing Shy',
        'face.20': 'Gentleman Monocle',
        'face.21': 'Cyberpunk Android',
        'face.22': 'Nom-Nom Hamster',

        'hair.0': 'Dynamic Short',
        'hair.1': 'Punk Fauxhawk',
        'hair.2': 'Puffy Afro Curls',
        'hair.3': 'Double Buns',
        'hair.4': 'Cute Bob Bangs',
        'hair.5': 'Backwards Baseball Cap',
        'hair.6': 'Slicked Back Hair',
        'hair.7': 'Ahoge Sprout Bald',
        'hair.8': 'Twin Braids',
        'hair.9': 'Samurai Topknot',
        'hair.10': 'Spiky Hedgehog',
        'hair.11': 'Long Wavy Hair',
        'hair.12': 'Mullet Wolf Cut',
        'hair.13': 'Single Long Ponytail',
        'hair.14': 'WLR Crimson Dreadlocks',
        'hair.15': 'Dynamic Twintails',
        'hair.16': 'Modern Shag Mullet',
        'hair.17': 'Vintage Glamour Waves',
        'hair.18': 'Street Bucket Hat',
        'hair.19': 'Chic French Beret',
        'hair.20': 'Neon Cyber Mohawk',
        'hair.21': 'Flowing Long Straight',
        'hair.22': 'Astronaut Bubble Helmet',

        'acc.0': 'No Accessory',
        'acc.1': 'Cat Ears Headband',
        'acc.2': 'Devil Horns',
        'acc.3': 'Angel Halo',
        'acc.4': 'DJ Headphones',
        'acc.5': 'Side Bow',
        'acc.6': 'Pirate Eyepatch',
        'acc.7': 'Mini Crown',
        'acc.8': 'Knitted Scarf',
        'acc.9': 'WLR Punk Cross Chain',
        'acc.10': 'Cyber VR Visor',
        'acc.11': 'Party Cone Hat',
        'acc.12': 'Duckling On Head',
        'acc.13': 'Anime Face Bandages',
        'acc.14': 'Hipster Square Glasses',
        'acc.15': 'Pearl & Gem Choker',
        'acc.16': 'Sprout Seedling Clip',
        'acc.17': 'Mini Vampire Bat Wings',
        'acc.18': 'Champion Gold Medal',

        // --- 大屏主持端 / Room Host ---
        'host.title': 'Hosting - %s',
        'host.default_room_name': 'Live Quiz Arena',
        'host.join_hint': 'Join with your phone browser and enter the 6-digit Game PIN',
        'host.room_pin_label': 'GAME PIN',
        'host.joined_count': 'Joined: <strong id="host-player-count">%s</strong> players',
        'host.total_questions_count': 'Total <strong>%s</strong> questions',
        'host.players_wall_title': 'Connected Players',
        'host.waiting_players_tip': 'Waiting for players to join… Names will show here in real time after entering the PIN.',
        'host.btn_start': 'Start Game',
        'host.btn_starting': 'Starting game…',
        'host.answered_progress': 'Answered: <strong id="answer-count">%s</strong> / <span id="total-players">%s</span> players',
        'host.btn_end_q': 'End Question',
        'host.btn_end_explanation': 'Next Question',
        'host.btn_next_q': 'Next Question',
        'host.btn_show_ranking': 'Show Leaderboard',
        'host.btn_ceremony': 'Awards Ceremony',
        'host.reveal_kicker': 'Answer Reveal',
        'host.reveal_title': 'Question Results',
        'host.reveal_subtitle': 'Responses per option and correct answer',
        'host.correct_answer': 'Correct Answer',
        'host.word_cloud_title': 'Live Word Cloud',
        'host.word_cloud_empty': 'No answers yet, waiting for player submissions...',
        'host.short_correct_count': 'answered correctly',
        'host.short_meta': '%s answered · %s did not answer',
        'host.loading_stem': 'Loading question…',
        'host.explanation_done': 'Explanation finished',
        'host.explanation_done_sub': 'No answer required. Continue to the next question.',
        'host.live_ranking': 'Live Leaderboard',

        // 题型徽章
        'qtype.single': '[Single Choice]',
        'qtype.multiple': '[Multiple Choice]',
        'qtype.judgment': '[True/False]',
        'qtype.short_answer': '[Short Answer]',
        'qtype.word_cloud': '[Word Cloud]',
        'qtype.explanation': '[Explanation]',
        'qtype.label.single': 'Single Choice',
        'qtype.label.multiple': 'Multiple Choice',
        'qtype.label.judgment': 'True / False',
        'qtype.label.short_answer': 'Short Answer',
        'qtype.label.word_cloud': 'Word Cloud',
        'qtype.label.explanation': 'Explanation',

        // --- 数据分析系统 / Analytics ---
        'analytics.title': 'Game Match Analytics',
        'analytics.kpi_players': 'Total Players',
        'analytics.kpi_accuracy': 'Overall Accuracy',
        'analytics.kpi_avg_score': 'Average Score',
        'analytics.kpi_max_score': 'Top Score',
        'analytics.kpi_questions': 'Total Questions',
        'analytics.unit_person': 'players',
        'analytics.unit_question': 'q',
        'analytics.unit_score': 'pts',
        'analytics.tab_by_question': 'By Question (Correct / Wrong)',
        'analytics.tab_by_player': 'By Student (Performance)',
        'analytics.spotlight_hardest': 'Hardest Question: Q%s (Accuracy %s%)',
        'analytics.search_q_placeholder': 'Search questions or options...',
        'analytics.search_p_placeholder': 'Search student nickname...',
        'analytics.filter_all_types': 'All Question Types',
        'analytics.correct_list': 'Correct Students (%s)',
        'analytics.wrong_list': 'Incorrect Students (%s)',
        'analytics.unanswered_list': 'Unanswered Students (%s)',
        'analytics.none': 'None',
        'analytics.correct_answer_label': 'Correct Answer: ',
        'analytics.response_time': 'Avg Time: %ss',
        'analytics.empty_search': 'No matching analytics records found',
        'analytics.score_col': 'Score',
        'analytics.rank_col': 'Rank',
        'analytics.status_correct': 'Correct',
        'analytics.status_wrong': 'Wrong',
        'analytics.status_unanswered': 'Unanswered',

        // --- 题目编辑器 / Shoot Editor ---
        'editor.placeholder_title': 'Shoot Title',
        'editor.toast_saved': 'Saved',
        'editor.btn_add': '+ Add',
        'editor.upload_img_tip': 'Click to upload question image (optional)',
        'editor.btn_remove_img': 'Remove Image',
        'editor.stem_placeholder': 'Type your question stem here…',
        'editor.opt_a': 'Option A',
        'editor.opt_b': 'Option B',
        'editor.opt_c': 'Option C',
        'editor.opt_d': 'Option D',
        'editor.mark_correct': 'Mark as correct',
        'editor.short_correct_label': 'Accepted Answers (separate with |)',
        'editor.wordcloud_tip': 'Word Cloud: Aggregates student responses live without grading.',
        'editor.props_title': 'Question Settings',
        'editor.field_type': 'Question Type',
        'editor.field_time': 'Time Limit',
        'editor.btn_save_q': 'Save Question',
        'editor.btn_delete_q': 'Delete Question',
        'editor.exit_modal_title': 'Leave Editor?',
        'editor.exit_modal_desc': 'Please choose whether to save changes and whether to publish this quiz to the public library.',
        'editor.save_changes_label': 'Save current changes',
        'editor.save_changes_desc': 'Save edits to questions, options, media, and title.',
        'editor.publish_label': 'Make this quiz public',
        'editor.publish_desc': 'Once public, other teachers can browse and use this quiz set.',
        'editor.btn_confirm_exit': 'Confirm & Leave',
        'editor.time_seconds': '%s sec',
        'editor.type_hint_single': 'Single: Click ✓ on the right to mark the single correct answer',
        'editor.type_hint_multiple': 'Multiple: Click ✓ on multiple options (at least 2)',
        'editor.type_hint_judgment': 'True/False: Option A is True, B is False. Click ✓ to mark',
        'editor.type_hint_short': 'Short Answer: Enter accepted text (separate with |)',
        'editor.type_hint_wordcloud': 'Word Cloud: Aggregates student submissions live without scoring',
        'editor.type_hint_explanation': 'Explanation: Upload one image that fills the classroom screen. No timer — tap Next when you finish talking. Students do not see or answer it.',

        // --- 我的题库列表 / Question List ---
        'qlist.title': 'My Quiz Bank',
        'qlist.table_title': 'My Quiz Sets',
        'qlist.col_title': 'Quiz Name',
        'qlist.col_count': 'Questions',
        'qlist.col_vis': 'Visibility',
        'qlist.col_time': 'Created At',
        'qlist.col_actions': 'Actions',
        'qlist.unit_q': 'items',
        'qlist.status_public': 'Public',
        'qlist.status_private': 'Private',
        'qlist.btn_edit': 'Edit',
        'qlist.delete_confirm': 'Are you sure you want to delete quiz set "%s"? This cannot be undone.',
        'qlist.page_prev': '← Prev',
        'qlist.page_next': 'Next →',
        'qlist.page_indicator': 'Page %s of %s',
        'qlist.empty_title': 'No Quiz Sets Yet',
        'qlist.empty_desc': 'Head to the creation wizard to craft your first quiz using Manual, AI, or Excel import.',
        'qlist.btn_create_first': '+ Create First Quiz →',

        'practice.score_now': 'Score %s',
        'practice.final_score': 'Score %s',
        'practice.your_rank': 'Rank #%s',
        'practice.empty_board': 'No other practice runs yet',
        'practice.word_cloud_title': 'Word cloud',
    };

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    function setCookie(name, value, days = 365) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${encodeURIComponent(value)};expires=${d.toUTCString()};path=/;SameSite=Lax`;
    }

    function detectLocale() {
        const htmlLang = document.documentElement.getAttribute('lang');
        if (htmlLang) {
            const lower = htmlLang.toLowerCase();
            if (lower.startsWith('en')) return 'en';
            if (lower.startsWith('zh')) return 'zh-hans';
        }
        const cookieLang = getCookie('django_language');
        if (cookieLang) {
            const lower = cookieLang.toLowerCase();
            if (lower.startsWith('en')) return 'en';
            if (lower.startsWith('zh')) return 'zh-hans';
        }
        const storageLang = localStorage.getItem('shoot_lang');
        if (storageLang) {
            return storageLang === 'en' ? 'en' : 'zh-hans';
        }
        return 'zh-hans';
    }

    let currentLocale = detectLocale();

    const ShootI18n = {
        getLocale() {
            return currentLocale;
        },

        isEn() {
            return currentLocale === 'en';
        },

        isZh() {
            return currentLocale === 'zh-hans';
        },

        t(key, ...args) {
            const dict = currentLocale === 'en' ? DICT_EN : DICT_ZH;
            let str = dict[key];
            if (str === undefined) {
                str = DICT_ZH[key] !== undefined ? DICT_ZH[key] : key;
            }
            if (args.length === 0) {
                return str;
            }
            if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null && !Array.isArray(args[0])) {
                const params = args[0];
                return str.replace(/\{(\w+)\}/g, (m, k) => (params[k] !== undefined ? params[k] : m));
            }
            let i = 0;
            return str.replace(/%s/g, () => (args[i] !== undefined ? args[i++] : ''));
        },

        setLanguage(lang) {
            const target = (lang || '').toLowerCase().startsWith('en') ? 'en' : 'zh-hans';
            currentLocale = target;
            localStorage.setItem('shoot_lang', target);
            setCookie('django_language', target, 365);

            // Redirect through django set_language or refresh page
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/i18n/setlang/';
            form.style.display = 'none';

            const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const csrfToken = (csrfInput && csrfInput.value)
                || (csrfMeta && csrfMeta.getAttribute('content'))
                || getCookie('csrftoken');

            if (csrfToken) {
                const csrfField = document.createElement('input');
                csrfField.type = 'hidden';
                csrfField.name = 'csrfmiddlewaretoken';
                csrfField.value = csrfToken;
                form.appendChild(csrfField);
            }

            const langField = document.createElement('input');
            langField.type = 'hidden';
            langField.name = 'language';
            langField.value = target;
            form.appendChild(langField);

            const nextField = document.createElement('input');
            nextField.type = 'hidden';
            nextField.name = 'next';
            nextField.value = window.location.pathname + window.location.search + window.location.hash;
            form.appendChild(nextField);

            document.body.appendChild(form);
            form.submit();
        },

        toggleLanguage() {
            this.setLanguage(this.isEn() ? 'zh-hans' : 'en');
        },

        initLanguageSwitchers() {
            if (this._langDelegated) return;
            this._langDelegated = true;
            // Delegate on document so Turbo body swaps keep the language toggle clickable.
            document.addEventListener('click', (e) => {
                const btn = e.target.closest && e.target.closest('[data-action="toggle-lang"]');
                if (!btn) return;
                e.preventDefault();
                e.stopPropagation();
                this.toggleLanguage();
            });
        }
    };

    global.ShootI18n = ShootI18n;
    global.t = function (key, ...args) {
        return ShootI18n.t(key, ...args);
    };

    ShootI18n.initLanguageSwitchers();
    document.addEventListener('turbo:load', () => ShootI18n.initLanguageSwitchers());
    document.addEventListener('DOMContentLoaded', () => ShootI18n.initLanguageSwitchers());

})(typeof window !== 'undefined' ? window : this);
