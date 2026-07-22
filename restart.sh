#!/bin/bash
fuser -k 80/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null
sleep 1
cd /root/Chess
nohup python3 server.py > /var/log/chess.log 2>&1 &
echo "Server restarted on port 80"
