# 中国象棋联机对战 —— 完整部署指南

> 这份文档会手把手教你如何把一个中国象棋在线对战项目，从本地开发一直部署到云服务器上，让你的朋友们可以通过浏览器随时随地切磋棋艺。

---

## 目录

1. [项目概览](#1-项目概览)
2. [准备工作](#2-准备工作)
3. [本地开发环境搭建](#3-本地开发环境搭建)
4. [项目结构说明](#4-项目结构说明)
5. [将代码上传到 GitHub](#5-将代码上传到-github)
6. [服务器端部署](#6-服务器端部署)
7. [服务器日常运维](#7-服务器日常运维)
8. [架构说明](#8-架构说明)
9. [常见问题排查](#9-常见问题排查)

---

## 1. 项目概览

在本教程中，我们将部署一个完整的中国象棋在线对战平台，它具备以下能力：

- **双人对战**：创建房间、分享链接，满两人自动开局
- **人机对战**：内置皮卡鱼 AI 引擎，棋力强劲
- **完整规则**：服务端校验所有走法（車馬砲相仕帥兵卒），含将军/将死/困毙判定
- **实时通信**：基于 WebSocket，走棋、聊天、悔棋、认输零延迟
- **棋盘翻转**：执黑方自动翻转视角，符合对弈习惯

整个项目的核心流程如下：

```
你的电脑（开发）          GitHub（代码仓库）         云服务器（运行）
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  server.py  │ ─push→  │ 你的用户名   │ ─pull→  │  server.py  │
│  engine.py  │         │   /Chess    │         │  (Flask)    │
│  public/    │         └─────────────┘         │  pikafish   │
│  restart.sh │                                 │  (AI引擎)   │
└─────────────┘                                 └─────────────┘
```

---

## 2. 准备工作

| 物品 | 说明 |
|------|------|
| 一台电脑 | Windows / macOS / Linux 均可，用于写代码 |
| GitHub 账号 | 免费注册：https://github.com |
| 一台云服务器 | 阿里云 ECS、腾讯云等，装好 Linux（本文以 Ubuntu/CentOS 为例） |
| 基本命令行技能 | 会 `cd`、`ls`、`git` 等基本命令即可 |

> **小贴士**：如果你还没有服务器，阿里云和腾讯云经常有学生优惠或者新用户活动，一台 1 核 2G 的轻量服务器就足够跑这个项目了，一个月几十块钱。

---

## 3. 本地开发环境搭建

### 3.1 安装 Python

项目后端使用 Python 3，推荐 3.8 以上版本。在命令行里检查是否已安装：

```bash
python3 --version
```

如果没有安装，去 https://www.python.org/downloads/ 下载安装即可。**安装时记得勾选 "Add Python to PATH"**。

### 3.2 安装 Git

Git 是代码版本管理工具，我们用它来把代码上传到 GitHub。

```bash
# Windows：去 https://git-scm.com/download/win 下载安装
# macOS：
brew install git
# Ubuntu/Debian：
sudo apt install git
```

安装完成后设置身份（Git 需要知道是谁在提交代码）：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

> `--global` 表示全局配置，这台电脑上所有 Git 仓库都会使用这个身份。如果只想在当前项目使用，去掉 `--global` 即可。

### 3.3 安装项目依赖

```bash
cd Chess
pip install -r requirements.txt
```

`requirements.txt` 列出了项目需要的第三方库。`pip install -r` 会把列表里的包一次性安装好。核心依赖：

- **Flask**：轻量级 Web 框架，负责处理 HTTP 请求和提供前端页面
- **Flask-SocketIO**：WebSocket 扩展，实现客户端与服务端实时双向通信
- **eventlet**：异步 IO 库，让 Flask-SocketIO 支持多人在线

### 3.4 下载 AI 引擎（可选）

如果需要"人机对战"功能，需要下载皮卡鱼 AI 引擎：

```bash
python download_pikafish.py
```

> 这个脚本会从 GitHub 下载皮卡鱼的 7z 压缩包并自动解压。如果只需要双人对战，可以跳过这步。

### 3.5 本地启动测试

```bash
python server.py
```

看到 `中国象棋联机服务器启动于 http://localhost:3000` 后，打开浏览器访问 `http://localhost:3000`。因为 Flask 开启了 debug 模式，改代码后刷新页面即可看到效果。

---

## 4. 项目结构说明

```
Chess/
├── server.py              # Flask 后端：走法验证 + 房间管理 + WebSocket 事件
├── engine.py              # 皮卡鱼 AI 封装 + FEN 格式互转
├── requirements.txt        # Python 依赖列表
├── restart.sh              # 服务器重启脚本
├── deploy.sh               # 一键部署脚本（pull + 下载引擎 + 重启）
├── setup.sh                # 引擎下载脚本
├── .gitignore              # Git 忽略规则
├── public/
│   └── index.html           # 前端页面：棋盘绘制 + SocketIO 客户端
└── frontend/
    └── chinese-chess.html   # 早期本地单机版（已废弃）
```

**各个文件的分工：**

| 文件 | 负责什么 |
|------|----------|
| `server.py` | 控制整个后端逻辑：接收前端请求、验证走法、管理房间、调度 AI |
| `engine.py` | 把皮卡鱼复杂的 UCI 协议封装成简单的 Python 函数调用 |
| `public/index.html` | 所有你能看到的 UI：棋盘、棋子、按钮、聊天框、走棋日志 |
| `restart.sh` | 在服务器上杀掉旧进程，启动新进程 |
| `.gitignore` | 告诉 Git 哪些文件不要管（比如临时文件、AI 引擎二进制文件） |

---

## 5. 将代码上传到 GitHub

### 5.1 为什么需要 GitHub？

GitHub 相当于一个"代码网盘"，把代码存在上面有三个好处：

1. **备份**：电脑坏了代码也不会丢
2. **版本管理**：改坏了可以回退到之前的版本
3. **协作中转**：服务器从 GitHub 拉取最新代码，不需要手动上传文件

### 5.2 初始化 Git 仓库

如果你的项目还不是 Git 仓库，首先初始化：

```bash
cd /path/to/Chess
git init
```

> `git init` 在当前目录创建一个隐藏的 `.git` 文件夹，用来记录所有版本信息。

### 5.3 创建 `.gitignore` 文件

有些文件不需要上传到 GitHub，比如 Python 缓存、AI 引擎二进制（太大且跨平台不通用）：

```
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.env
.venv/
venv/
*.log
.DS_Store
Thumbs.db

# 皮卡鱼引擎（二进制文件，通过 setup.sh 在服务器上下载）
pikafish
pikafish.exe
pikafish-*/
pikafish*.7z
pikafish*.tar.gz
pikafish*.zip
pikafish_extracted/
pikafish_linux
pikafish.nnue
```

> 每一行是一个匹配规则。`*` 是通配符，`/` 结尾表示只匹配目录。

### 5.4 第一次提交

```bash
# 把项目所有文件加入暂存区
git add .
# 提交到本地仓库，写一段说明
git commit -m "中国象棋联机对战 - 初始版本"
```

> `git add .` 里的 `.` 代表当前目录下所有文件。`git commit` 把暂存区的改动记录成一笔历史。`-m` 后面跟提交说明，方便以后查看。

### 5.5 关联 GitHub 远程仓库

首先在 GitHub 网页上创建一个新仓库（**不要勾选**"Initialize with README"）。创建后会看到类似这样的地址：

```
https://github.com/你的用户名/Chess.git
```

然后把本地仓库和远程仓库关联：

```bash
git remote add origin https://github.com/你的用户名/Chess.git
```

> `git remote add` 的意思是"添加一个远程地址"。`origin` 是这个远程地址的别名，约定俗成叫 origin。

### 5.6 推送到 GitHub

```bash
# GitHub 默认主分支叫 main，本地如果是 master 需要改名
git branch -M main
# 推送到 GitHub
git push -u origin main
```

> `-u` 会记住 origin/main 和本地 main 的对应关系，以后只需要 `git push` 即可。

### 5.7 日常提交流程

以后每次修改代码后，只需三步：

```bash
git add .
git commit -m "描述你做了什么改动"
git push
```

> **提交信息规范**：写清楚改了什么，比如 `"修复 AI 引擎 stdin 未关闭导致走法错误"`，而不是 `"改 bug"`。好的提交信息就像时间胶囊，三个月后再看也能快速理解改动的目的。

---

## 6. 服务器端部署

### 6.1 连接到你的服务器

```bash
ssh root@你的服务器IP
```

> `ssh` 是"安全外壳协议"（Secure Shell），用于远程登录服务器。`root` 是管理员用户名，`@` 后面是服务器 IP。输入密码后你就进入了服务器的命令行环境。

> **小技巧**：觉得每次输 IP 太麻烦？在本地 `~/.ssh/config` 里配一个别名：
>
> ```
> Host ecs
>     HostName 你的服务器IP
>     User root
> ```
>
> 之后只需要 `ssh ecs` 就能连接。

### 6.2 安装必要软件

```bash
# 安装 Git
sudo apt install git -y        # Ubuntu / Debian
sudo yum install git -y        # CentOS / RHEL

# 安装 Python 及 pip
sudo apt install python3 python3-pip -y
```

### 6.3 克隆项目

```bash
cd /root
git clone https://github.com/你的用户名/Chess.git
cd Chess
```

> `git clone` 把 GitHub 上的代码完整拷贝一份到服务器。

### 6.4 安装依赖

```bash
pip3 install -r requirements.txt
```

### 6.5 下载 AI 引擎（可选）

```bash
bash setup.sh
```

> 这个脚本会检测你的服务器是 Linux 还是其他系统，自动从 GitHub 下载对应版本的皮卡鱼引擎并解压。如果只需要双人对战，跳过。

### 6.6 首次启动

```bash
bash restart.sh
```

> `restart.sh` 做了三件事：① 杀掉旧的 Python 进程（释放端口）；② 等待 1 秒确认端口空闲；③ 用 `nohup` 在后台启动 Flask。

`nohup` 的意思是"no hang up"，即使用户退出 SSH 连接，进程也不会被杀掉。`> /var/log/chess.log 2>&1` 把标准输出和错误都重定向到日志文件，方便排查问题。

### 6.7 验证部署

```bash
# 检查端口是否在监听
ss -tlnp | grep :80
# 应该能看到类似 "LISTEN 0 128 0.0.0.0:80" 的输出
```

> `ss -tlnp` 列出所有正在监听的 TCP 端口。`-t` 只看 TCP，`-l` 只看监听状态，`-n` 显示数字端口号而不是服务名，`-p` 显示进程名。

打开浏览器访问 `http://你的服务器IP`，看到棋盘界面就是成功了！

> **注意**：如果访问不了，检查一下云服务器的**安全组**（防火墙）是否开放了 80 端口。阿里云/腾讯云默认只开放 22 端口（SSH），需要在控制台手动添加 80 端口的放行规则。

---

## 7. 服务器日常运维

### 7.1 日常更新的标准流程

```bash
# 在本地改完代码后
git add .
git commit -m "修改说明"
git push

# 然后 SSH 到服务器
ssh ecs
cd /root/Chess
bash deploy.sh
```

> `deploy.sh` 集成了三个动作：`git pull`（拉取最新代码）→ 检查/下载引擎 → 重启服务。一键完成所有部署。

### 7.2 只重启服务（不改代码）

```bash
ssh ecs "bash /root/Chess/restart.sh"
```

### 7.3 查看服务状态

```bash
# 检查服务是否在运行
ssh ecs "ss -tlnp | grep :80"

# 查看实时日志
ssh ecs "tail -f /var/log/chess.log"

# 查看最近 30 行日志
ssh ecs "tail -30 /var/log/chess.log"
```

> `tail -f` 会持续追踪日志文件，有新的输出立刻显示（按 `Ctrl+C` 退出）。`tail -30` 只显示最后 30 行。

### 7.4 手动停止服务

```bash
ssh ecs "fuser -k 80/tcp"
```

> `fuser` 找出占用特定端口或文件的进程。`-k` 意思是"kill"，杀掉这些进程。`80/tcp` 指定 TCP 协议的 80 端口。

### 7.5 服务器端 Git 使用技巧

由于 GitHub 在国内访问可能不稳定，当你无法 `git pull` 时，也可以直接通过 `scp` 上传文件：

```bash
# 从本地上传单个文件到服务器
scp server.py ecs:/root/Chess/

# 上传整个 public 目录
scp -r public/ ecs:/root/Chess/
```

> `scp` 是"安全拷贝"（Secure Copy），基于 SSH 传输文件。`-r` 表示递归拷贝整个目录。

---

## 8. 架构说明

### 8.1 通信流程

```
浏览器 A                    服务器                    浏览器 B
   │                         │                         │
   │── 点击棋子 ──────────→  │                         │
   │                   走法验证？                        │
   │                    通过 ↓                          │
   │                    更新棋盘                        │
   │←── 广播 move_made ──→│←── 广播 move_made ──→    │
   │                         │                         │
```

每一步走棋的流程：
1. 玩家 A 点击棋子 → 前端通过 WebSocket 发送 `move` 事件
2. 服务器接收后，用走法规则引擎验证该步是否合法
3. 合法则更新服务器的棋盘状态，切换到对方回合
4. 通过 WebSocket 向房间内所有玩家（包括 A 和 B）广播 `move_made` 事件
5. 各客户端收到后，更新自己的棋盘显示

### 8.2 WebSocket 事件表

**客户端 → 服务端：**

| 事件 | 参数 | 说明 |
|------|------|------|
| `create_room` | `{ai: true/false}` | 创建房间（可选 AI 模式） |
| `join_room` | `{room_code: "123456"}` | 通过 6 位房间码加入 |
| `move` | `{from_row, from_col, to_row, to_col}` | 走一步棋 |
| `request_undo` | - | 请求悔棋 |
| `resign` | - | 认输 |
| `play_again` | - | 游戏结束后重新开始 |
| `chat` | `{message: "hello"}` | 发送消息 |

**服务端 → 客户端：**

| 事件 | 内容 | 说明 |
|------|------|------|
| `room_created` | `{room_code, side}` | 房间创建成功 |
| `game_start` | `{pieces, your_side, current_turn}` | 游戏开始 |
| `move_made` | `{from, to, piece_text, captured, current_turn}` | 走子广播 |
| `undo_done` | `{pieces, current_turn}` | 悔棋完成 |
| `game_over` | `{winner, reason}` | 游戏结束 |
| `game_reset` | `{pieces, your_side, current_turn}` | 再来一局 |
| `in_check` | `{side}` | 将军提示 |
| `chat_message` | `{sender, message}` | 聊天广播 |
| `error` | `{message}` | 错误提示 |

### 8.3 AI 引擎工作流程

```
用户走棋 → 服务器更新棋盘
                ↓
        轮到 AI（黑方）走棋
                ↓
    engine.py: pieces_to_fen()  将棋盘转为 FEN 字符串
                ↓
    engine.py: get_best_move()  启动皮卡鱼子进程，发送 UCI 命令
                ↓
          皮卡鱼搜索并返回走法
                ↓
    server.py: get_legal_moves()  用规则引擎验证走法合法性
                ↓ 通过
          执行走法，广播给所有客户端
                ↓ 不通过
          用规则引擎兜底，随机选一个法律走法
```

> **为什么需要"兜底"机制？** 皮卡鱼在某些局面下存在 FEN 解析 bug，可能返回不存在的棋子坐标。我们的规则引擎 `get_legal_moves()` 作为最后一道安全屏障，确保棋盘状态永远不会出错。

---

## 9. 常见问题排查

### 问题 1：访问网站提示"无法访问"

**可能原因**：服务器安全组没有开放 80 端口。

**解决**：登录云服务商控制台 → 安全组 → 添加规则：允许 TCP 80 端口入站。

### 问题 2：`pip install` 报错

```bash
# 先升级 pip 本身
python3 -m pip install --upgrade pip
# 如果网络慢，用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3：AI 模式不工作

```bash
# 检查引擎文件是否存在
ls -la /root/Chess/pikafish
# 检查 NNUE 权重文件是否存在
ls -la /root/Chess/pikafish.nnue
# 检查引擎是否可执行
chmod +x /root/Chess/pikafish
```

如果缺少引擎文件，运行 `bash setup.sh` 重新下载。

### 问题 4：服务器日志在哪儿？

所有日志输出到 `/var/log/chess.log`。实时查看：

```bash
ssh ecs "tail -f /var/log/chess.log"
```

> 日志中 `[AI]` 开头的行记录了 AI 引擎的搜索过程和返回结果，是排查人机对战问题的重要线索。

### 问题 5：改完代码没生效

确认服务器已重启：

```bash
ssh ecs "bash /root/Chess/restart.sh"
```

如果还不行，清除浏览器缓存（`Ctrl+Shift+R` 强制刷新）。

---

> 恭喜你！如果能看到这里，你已经掌握了从零开始部署一个完整象棋对战平台的全部知识。祝你下棋愉快，代码无 Bug！

