#!/bin/bash
# ==========================================
# 中国象棋 一键部署脚本
# git pull 最新代码 + 下载/更新引擎 + 重启服务
# 用法: bash deploy.sh
# ==========================================

cd /root/Chess

echo ">>> 拉取最新代码..."
git pull origin main

echo ">>> 检查/下载皮卡鱼引擎..."
if [ ! -f pikafish ]; then
    bash setup.sh
else
    echo "✓ 引擎已存在，跳过下载"
fi

echo ">>> 重启服务..."
fuser -k 80/tcp 2>/dev/null
sleep 1
nohup python3 -u server.py > /var/log/chess.log 2>&1 &

sleep 2
echo ">>> 检查服务状态..."
if ss -tlnp | grep -q ':80'; then
    echo "✓ 服务运行正常 (端口 80)"
    curl -s -o /dev/null -w "HTTP 状态码: %{http_code}\n" http://localhost:80
else
    echo "✗ 服务启动失败，查看日志: tail /var/log/chess.log"
fi
