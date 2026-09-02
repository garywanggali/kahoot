# Kahoot

基于 Django + SQLite 的 Kahoot 风格互动课堂测验平台。

## 功能

- **学生端**：输入房间号 + 昵称加入，实时答题，每题结束后查看积分排行
- **老师端**：题库管理（选择题）、创建房间、主持游戏流程
- **实时通信**：WebSocket (Django Channels)
- **计分规则**：答对后根据答题速度获得 0–1000 分（越快越高）

## 快速开始

```bash
# 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 导入示例题目（可选）
python manage.py load_sample_questions

# 启动服务
python manage.py runserver
```

浏览器访问 <http://127.0.0.1:8000>

## 使用流程

### 老师

1. 首页 → **老师入口** → 密码默认 `teacher123`
2. **题库管理** → 添加选择题（4 个选项 + 正确答案 + 时限）
3. **创建房间** → 选择题目 → 获得 6 位房间号
4. **主持游戏** → 显示房间号让学生加入 → 开始游戏 → 每题结束后点「显示排行」→ 下一题

### 学生

1. 首页 → **加入游戏**
2. 输入房间号和昵称
3. 等待老师开始，选择彩色选项答题
4. 每题结束后查看排行榜

## 技术栈

- Django 6 + Channels + Daphne
- SQLite
- WebSocket 实时同步

## 部署到老师服务器 (110.40.153.38)

端口使用 **5002**（与课堂其他项目 5000–5010 段一致）。

### 方式一：本机一键部署（需已配置 SSH）

```bash
export DEPLOY_SERVER=你的英文名@110.40.153.38
./deploy.sh
```

### 方式二：在服务器上手动部署

```bash
# 1. SSH 登录
ssh 你的英文名@110.40.153.38

# 2. 上传代码后进入目录（或用 git clone）
cd kahoot

# 3. 启动（后台运行）
chmod +x run.sh stop.sh
./run.sh 5002
```

### 访问地址

- 首页：`http://110.40.153.38:5002/`
- 老师入口：`http://110.40.153.38:5002/teacher/login/`（密码默认 `teacher123`）

### 停止 / 重启

```bash
./stop.sh
./run.sh 5002
```

### 日志

```bash
tail -f logs/server.log
```

### 服务器上用 Git 更新（推荐）

若目录是 rsync 上传的，还没有 `.git`，先初始化一次（**保留 venv 和数据库**）：

```bash
cd ~/kahoot
chmod +x server_init_git.sh server_update.sh
./server_init_git.sh
```

之后每次更新：

```bash
cd ~/kahoot
./server_update.sh 5002
```

或全新克隆：

```bash
cd ~
git clone https://github.com/garywanggali/kahoot.git kahoot-new
cd kahoot-new
./run.sh 5002
```
