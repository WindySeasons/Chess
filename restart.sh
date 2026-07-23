#!/bin/bash
fuser -k 80/tcp 2>/dev/null
fuser -k 3000/tcp 2>/dev/null
sleep 1
cd /root/Chess
nohup python3 -u server.py > /var/log/chess.log 2>&1 &
sleep 2
if ss -tlnp | grep -q ':80'; then
    echo "Server restarted on port 80"
else
    echo "FAILED - check /var/log/chess.log"
    tail -5 /var/log/chess.log
fi
