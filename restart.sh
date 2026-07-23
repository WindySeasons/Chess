#!/bin/bash
# 中国象棋服务器重启脚本
set -e

echo ">>> 杀旧进程..."
fuser -k 80/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 2

echo ">>> 检查引擎..."
if [ ! -f /root/Chess/pikafish ]; then
    echo "!!! pikafish 引擎不存在，请先运行 bash setup.sh"
    exit 1
fi
if [ ! -f /root/Chess/pikafish.nnue ]; then
    echo "!!! pikafish.nnue 权重文件不存在"
    exit 1
fi
chmod +x /root/Chess/pikafish

echo ">>> 启动服务..."
cd /root/Chess
nohup python3 -u server.py > /var/log/chess.log 2>&1 &
sleep 3

echo ">>> 验证..."
if ss -tlnp | grep -q ':80'; then
    echo "✓ 服务运行正常 (端口 80)"
    echo "  日志: tail -f /var/log/chess.log"
else
    echo "✗ 启动失败！最近日志:"
    tail -10 /var/log/chess.log
    exit 1
fi
