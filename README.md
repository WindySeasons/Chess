# 中国象棋 联机对战

基于 Flask + SocketIO 的中国象棋在线对战平台，支持房间系统、走法规则验证、聊天等功能。

## 项目结构

```
Chess/
├── server.py              # Flask 后端（走法验证 + 房间管理 + WebSocket）
├── requirements.txt        # Python 依赖
├── restart.sh              # 服务器重启脚本
├── deploy.sh               # 服务器一键部署脚本（git pull + 重启）
├── .gitignore
├── public/
│   └── index.html          # 前端页面（棋盘绘制 + SocketIO 客户端）
└── frontend/
    └── chinese-chess.html  # 早期本地单机版（可忽略）
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask + Flask-SocketIO + eventlet |
| 前端 | 原生 HTML/CSS/JS + Canvas 绘图 + SocketIO 客户端 |
| 通信 | WebSocket（实时双向通信） |
| 部署 | 服务器 `nohup` 后台运行 |

## 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务（默认 80 端口）
python server.py

# 3. 打开浏览器
# 本地测试：http://localhost:80
# 两个窗口分别创建/加入房间即可对战
```

## 部署到服务器

### 首次部署

```bash
# 1. 克隆仓库
cd /root
git clone https://github.com/WindySeasons/Chess.git
cd Chess

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
bash restart.sh
```

### 日常更新

服务器上一键更新：

```bash
bash /root/Chess/deploy.sh
```

或者手动分步：

```bash
cd /root/Chess
git pull                    # 拉取最新代码
bash restart.sh             # 重启服务
```

## 服务器脚本说明

| 脚本 | 用途 |
|------|------|
| `deploy.sh` | git pull + 重启（日常更新用） |
| `restart.sh` | 仅重启服务（改配置后用） |

最佳实践：**拉取代码和重启分开**。这样你可以：
- 只 pull 不重启（看代码变化）
- 只重启不 pull（调整了服务器配置）
- 用 deploy.sh 一键完成日常更新

## 核心功能

### 房间系统
- 创建房间 → 自动生成 6 位数字房间码
- 加入房间 → 输入房间码 / 点击分享链接
- 满 2 人自动开始，创建者执红先手

### 走法规则（服务端全量校验）
- 車：四方向直线，遇子停
- 馬：日字形 + 蹩脚检查
- 砲/炮：直线走子 + 翻山吃子
- 相/象：田字形 + 不过河 + 塞眼
- 仕/士：九宫内斜走一步
- 帥/將：九宫内直走一步 + 飞将规则
- 兵/卒：未过河向前，过河可左右前

### 游戏功能
- 将军 / 将死 / 困毙 判定
- 悔棋（双方均可发起，撤销上一步）
- 认输
- 再来一局
- 走棋日志（显示每一步的棋子、坐标）
- 音效（走子 / 吃子不同音效）
- 文字聊天
- 分享链接（`http://IP/?room=XXXXXX`）
- 黑方棋盘自动翻转

## WebSocket 事件一览

### 客户端 → 服务端

| 事件 | 参数 | 说明 |
|------|------|------|
| `create_room` | - | 创建房间 |
| `join_room` | `{room_code}` | 加入房间 |
| `move` | `{from_row, from_col, to_row, to_col}` | 走子 |
| `request_undo` | - | 请求悔棋 |
| `resign` | - | 认输 |
| `play_again` | - | 再来一局 |
| `chat` | `{message}` | 发送聊天 |

### 服务端 → 客户端

| 事件 | 内容 | 说明 |
|------|------|------|
| `room_created` | `{room_code, side}` | 房间创建成功 |
| `room_joined` | `{room_code, side}` | 加入房间成功 |
| `game_start` | `{pieces, your_side, current_turn}` | 游戏开始 |
| `move_made` | `{from, to, piece_text, captured, current_turn}` | 走子广播 |
| `undo_done` | `{pieces, current_turn, msg}` | 悔棋完成 |
| `game_over` | `{winner, reason}` | 游戏结束 |
| `game_reset` | `{pieces, your_side, current_turn}` | 游戏重置 |
| `in_check` | `{side}` | 将军提醒 |
| `chat_message` | `{sender, message}` | 聊天消息 |
| `opponent_disconnected` | - | 对手断线 |
| `error` | `{message}` | 错误提示 |

## 本地开发备忘

### 修改代码后

```bash
# 本地测试
git add . && git commit -m "说明" && git push

# 部署到服务器
ssh ecs "cd /root/Chess && bash deploy.sh"
```

### 服务管理命令

```bash
# 查看服务状态
ssh ecs "ss -tlnp | grep 80"

# 查看日志
ssh ecs "tail -f /var/log/chess.log"

# 手动重启
ssh ecs "bash /root/Chess/restart.sh"
```
