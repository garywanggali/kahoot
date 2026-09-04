# Shoot 互动课堂测验平台 · 代码库完整指引文档

本文档面向全栈开发人员、维护者与协同合作者，详细梳理了本项目的系统架构、目录结构、数据模型、实时通信协议、核心业务逻辑、前端交互体系及运维部署流程。

---

## 一、项目架构总览

本项目是一个基于 **Django 6 + Channels (Daphne) + WebSocket + SQLite** 的 Shoot 风格互动课堂测验平台，采用混合架构设计：
- **后端**：Django + Django Channels 处理 HTTP 请求与高并发全双工 WebSocket 长连接。
- **内存层（Room Runtime）**：在 `room_cache.py` 中维护房间答题内存态，避免高频数据库写争用，定期/结题时批量写回数据库（Flush）。
- **前端**：采用 Vanilla JS + Hotwired Turbo + 原生 SVG + CSS Design Tokens，保持高响应、低延迟，无前端框架构建负担。
- **设计风格**：工业极简与硬件质感设计（Industrial Craft / MK-78），主色为象牙白、哑光黑、高能电光橙。

```
                    ┌───────────────────────────────┐
                    │  客户端 (学生手机 / 老师大屏)   │
                    └───────┬───────────────┬───────┘
                            │ HTTP (Turbo)  │ WebSocket
                            ▼               ▼
                    ┌───────────────────────────────┐
                    │    Daphne ASGI Web Server     │
                    └───────┬───────────────┬───────┘
                            │               │
            ┌───────────────▼──┐         ┌──▼────────────────┐
            │   Django Views   │         │  GameConsumer WS  │
            └───────┬──────────┘         └──┬────────────────┘
                    │                       │
                    │         ┌─────────────┴─────────────┐
                    │         │  RoomRuntime 内存缓存层   │
                    │         │  (线程锁 + 脏标记批量落库)  │
                    │         └─────────────┬─────────────┘
                    ▼                       ▼
            ┌─────────────────────────────────────────────┐
            │              SQLite 数据库                  │
            └─────────────────────────────────────────────┘
```

---

## 二、目录结构速查

```text
shoot/
├── game/                         # 核心游戏业务 App
│   ├── analytics.py              # 对战数据复盘与学情分析计算引擎
│   ├── consumers.py              # WebSocket Consumer (处理进房、答题、切题、弹幕、换装)
│   ├── models.py                 # 数据库模型 (Teacher, Room, Question, QuizSet, Player, Answer 等)
│   ├── room_cache.py             # 房间运行时内存缓存 (线程安全、计分加速、脏数据批量落库)
│   ├── views.py                  # HTTP 视图函数 (老师控制台、套题编辑、导入导出、房间管理)
│   ├── urls.py                   # 路由配置
│   ├── excel_import.py           # Excel 批量导入与模版导出 (含 openpyxl 下拉框校验)
│   ├── ai_shoot.py              # 阶跃星辰/StepFun AI 批量出题逻辑
│   ├── stepfun_client.py         # AI 接口 Client
│   ├── question_save.py          # 题目保存与表单验证
│   ├── quiz_set_utils.py         # 套题复制、克隆、与房间关联辅助函数
│   ├── teacher_auth.py           # 教师权限与 Session 认证
│   ├── tests.py                  # 单元测试 (计分规则、个性化头像、数据分析)
│   └── tests_excel_import.py     # Excel 导入及数据校验单元测试
├── shoot_project/               # Django 项目配置目录
│   ├── settings.py               # 项目配置 (INSTALLED_APPS, CHANNEL_LAYERS, 静态/媒体资源)
│   ├── asgi.py                   # ASGI 入口 (HTTP + WebSocket 路由分发)
│   ├── urls.py                   # 全局 URL 分发
│   └── wsgi.py                   # WSGI 入口
├── templates/                    # HTML 模板目录
│   ├── base.html                 # 基础母版 (引入 Turbo、全局 BGM、Avatar 系统、设计 Token)
│   ├── game/
│   │   ├── index.html            # 平台首页 (选择加入游戏或进入老师端)
│   │   ├── join.html             # 学生端输入房间号与昵称
│   │   ├── play.html             # 学生端主界面 (大厅换装、答题界面、荣誉领奖台)
│   │   ├── room_host.html        # 老师端大屏主持 (5阶段：等待大厅/答题中/排行榜/颁奖典礼/数据分析)
│   │   ├── room_analytics.html   # 独立的对战数据分析报告页面
│   │   ├── teacher_dashboard.html# 老师主控制台 (发房间/管题库/近期房间报告)
│   │   ├── shoot_editor.html    # 题库可视化编辑器 (支持定时自动保存)
│   │   ├── shoot_detail.html    # 题库详情
│   │   ├── shoot_import.html    # Excel 模版下载与上传解析界面
│   │   └── room_create.html      # 选择题库并发起房间
├── static/                       # 静态资源目录
│   ├── css/
│   │   ├── design_tokens.css     # 全局色彩、圆角、阴影与字体设计变量
│   │   └── style.css             # 核心组件样式 (大厅、答题板、3D领奖台、数据看板)
│   ├── js/
│   │   ├── avatar.js             # SVG 模块化头像生成器 (脸部表情、发型样式、配色算法)
│   │   ├── analytics.js          # 对战数据分析渲染组件 (按题目/按学生两维切换、正误对比)
│   │   ├── awards.js             # 3D 荣誉领奖台与金银铜金属勋章渲染
│   │   ├── wordcloud.js          # 词云互动题渲染
│   │   ├── bgm.js                # 全局跨页面常驻背景音乐控制
│   │   └── shoot_editor.js      # 可视化编辑器客户端逻辑
│   └── audio/                    # 背景音乐音频素材
├── deploy.sh                     # 本机一键同步与远程重启部署脚本
├── run.sh / stop.sh              # 服务器后台启动与停止控制脚本
├── server_update.sh              # 服务器本地 Git 拉取更新并重启脚本
├── requirements.txt              # Python 依赖包清单
└── README.md                     # 项目使用简介
```

---

## 三、核心数据模型 (`game/models.py`)

1. **`Teacher` (老师账号)**
   - 包含 `username`、`password_hash`、`display_name`、`is_active`。
   - 具备安全哈希比对方法：`set_password()`、`check_password()`。
2. **`QuizSet` (套题 / 题库)**
   - 老师创建的题目合集，支持私有与公开共享 (`is_public`)。
   - 通过 `QuizSetItem` 关联 `Question` 并记录题目顺序 `order`。
3. **`Question` (试题库)**
   - 支持五大题型：
     - `single` (单选题)：A/B/C/D 四个选项。
     - `multiple` (多选题)：A/B/C/D 四个选项，全部选对才得分。
     - `judgment` (判断题)：A（正确）、B（错误）。
     - `short_answer` (简答题)：以 `|` 分隔同义词（如 `H2O|水`），支持模糊大小写归一化匹配。
     - `word_cloud` (词云题)：学生输入观点生成实时词频分布图。
   - 属性与方法：`time_limit`（倒计时秒数）、`image`（配图）、`is_answer_correct(selected)`。
4. **`Room` (互动房间)**
   - `code`：6 位唯一房间号（如 `889922`）。
   - `status`：`waiting`（大厅等待）→ `playing`（答题中）→ `leaderboard`（单题排行榜）→ `ended`（游戏完结）。
   - `current_question_index`：当前题目索引。
5. **`Player` (参赛学生)**
   - `nickname`、`session_id`、`score`（总积分）。
   - `avatar`：存储 JSON 字符串（如 `{"face": 2, "hair": 4}`），提供 `get_avatar_dict()`。
6. **`Answer` (作答记录)**
   - 关联 `player`、`room`、`question`，记录 `selected_option`、`is_correct`、`points`、`response_time_ms`。

---

## 四、高性能房间运行时缓存 (`game/room_cache.py`)

为解决多学生同时提交答案时的数据库写锁冲突：
- 采用 **`RoomRuntime`** 内存对象跟踪房间当前状态：
  - `lock`：`threading.Lock` 保护并发安全。
  - `players`：`dict[session_id, CachedPlayer]`。
  - `answers`：`dict[(session_id, question_id), CachedAnswer]`。
  - `pending_players` / `pending_answers`：待落库写缓冲队列。
  - `avatar_dirty` / `score_dirty`：脏标记。
- **批量落库（Flush）**：
  - 每达到一定数量或在切题、结题时调用 `flush_runtime()`。
  - 使用 `bulk_create` 与 `bulk_update` 一次性将增量落盘，兼顾极速吞吐与数据持久化。

---

## 五、WebSocket 实时协议与事件流 (`game/consumers.py`)

客户端通过 `ws://<host>/ws/game/<room_code>/` 建立连接。

### 1. 客户端发往服务端动作 (`action`)
| Action | 参数 | 说明 |
| :--- | :--- | :--- |
| `join` | `nickname`, `session_id`, `avatar` | 学生进入等待大厅 |
| `update_avatar` | `avatar` (`{face, hair}`) | 学生在大厅中个性化换装 |
| `start_game` | - | 老师端大屏点击「开始游戏」 |
| `submit_answer` | `question_id`, `selected` | 学生提交作答 |
| `show_leaderboard` | - | 老师端结算当前题目并展示排行榜 |
| `next_question` | - | 老师端切入下一题或触发结束 |
| `send_danmaku` | `text`, `nickname` | 师生实时发送弹幕 |

### 2. 服务端广播事件 (`event`)
| Event | 负载数据 (`data`) | 触发场景 |
| :--- | :--- | :--- |
| `player_joined` | `player_count`, `leaderboard` | 新学生加入房间 |
| `avatar_updated` | `session_id`, `avatar`, `leaderboard` | 学生大厅换装实时同步到大屏 |
| `game_started` | `state` | 游戏开始，进入第一题 |
| `question_started`| `state` (含题目内容、选项、倒计时) | 新题目开始答题 |
| `question_ended` | `state` (公布本题正解、柱状分布/词云) | 答题倒计时结束或老师提前结算 |
| `game_ended` | `state` (最终积分总榜) | 最后一题结束，进入颁奖典礼 |
| `danmaku` | `text`, `nickname`, `color` | 飘屏弹幕广播 |

---

## 六、特色系统实现说明

### 1. 模块化 SVG 头像系统 (`static/js/avatar.js`)
- 纯矢量 SVG 实时动态拼接：
  - **8 种表情面孔** (`FACES`)：微笑、酷炫墨镜、专注思考、星光闪烁、吐舌鬼脸、开心眨眼、惊讶张嘴、胜利坚毅。
  - **8 种发型样式** (`HAIRS`)：动感短发、潮流中分、蓬松卷发、阳光刺猬、侧分刘海、干练平头、个性长发、复古波浪。
  - **色彩调色盘**：基于昵称与序号哈希自动配对和谐的主体色与发色。
- 在学生等待大厅支持 ◀/▶ 翻页微调或 🎲 随机一键换装；在领奖台与数据分析页无损高保真缩放。

### 2. 老师大屏 5 阶段演进 (`templates/game/room_host.html`)
大屏界面严格按照现场课堂节奏推进：
1. **等待大厅 (`#host-waiting`)**：大字号 6 位房间号、连线雷达扫描波、学生个性头像胶囊列表。
2. **答题现场 (`#host-playing`)**：巨幅题干、配图展示、高能倒计时进度条、已答人数进度。
3. **单题排行榜 (`#host-leaderboard`)**：公布本题正确答案、选项分布柱状图/词云、即时积分榜前五。
4. **颁奖典礼 (`#host-ended`)**：3D 立体拟真领奖台（冠/亚/季军荣誉站台、金属质感立体勋章、专属金冠、飘带粒子）。
5. **对战数据分析 (`#host-analytics`)**：从领奖台一键无缝切入，对整场比赛进行数据复盘。

### 3. 学情复盘与数据分析引擎 (`game/analytics.py` & `static/js/analytics.js`)
- **双维度视角切换**：
  - **按题目分析 (By Question)**：查看每道题谁做对（所选选项、得分、用时）、谁做错/未答，并标注全场最易错的攻坚题。
  - **按学生分析 (By Player)**：查看每位学生的完整错对清单，对照学生所选与标准答案。
- **独立报告**：生成独立 URL 页面 (`/teacher/rooms/<id>/analytics/`)，在老师控制台的历史房间随时调取复盘。

### 4. Excel 模版题库批量导入 (`game/excel_import.py`)
- 利用 `openpyxl` 的 `DataValidation` 特性，在导出的 Excel 模版第 A 列（A2:A200）植入单选、多选、判断、简答的中文下拉选择列表，有效杜绝老师手动输入错别字。

### 5. 全局背景音乐跨页不间断 (`static/js/bgm.js` & Hotwired Turbo)
- 页面底部的全局 `<audio id="global-bgm">` 声明了 `data-turbo-permanent` 属性。
- 结合 `sessionStorage` 记录播放进度，在全站普通路由跳转时音乐丝滑过渡、不重置。

---

## 七、本地开发与测试

### 1. 运行测试套件
本项目包含健全的单元测试，涵盖计分算法、头像解析、缓存更新、Excel 校验与数据分析：
```bash
# 运行全部测试
python manage.py test

# 运行特定测试模块
python manage.py test game.tests.AnalyticsFeatureTests
python manage.py test game.tests_excel_import
```

### 2. 本地启动服务
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动开发服务器
python manage.py runserver 8000
```
访问本地：`http://127.0.0.1:8000/`

---

## 八、服务器部署与运维

- **生产服务器**：`110.40.153.38`
- **运行端口**：`5002`
- **默认教师账号**：`teacher` / 密码：`teacher123`

### 1. 本机一键部署 (推荐)
在本地修改代码并测试无误后：
```bash
# 执行一键同步与远程服务平滑重启
./deploy.sh
```

### 2. 服务器端常用命令
```bash
# 登入服务器
ssh gary@110.40.153.38

# 进入项目目录
cd ~/kahoot

# 停止服务
./stop.sh

# 启动服务 (指定 5002 端口)
./run.sh 5002

# 查看实时日志
tail -f logs/server.log
```
