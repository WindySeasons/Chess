"""皮卡鱼（Pikafish）UCI 引擎封装 + FEN 坐标转换"""
import subprocess
import os
import platform


# ---- FEN 棋子映射 ----
RED_FEN = {
    '帥': 'K', '仕': 'A', '相': 'B', '車': 'R', '馬': 'N', '砲': 'C', '兵': 'P',
}
BLACK_FEN = {
    '將': 'k', '士': 'a', '象': 'b', '車': 'r', '馬': 'n', '炮': 'c', '卒': 'p',
}


def pieces_to_fen(pieces, current_turn):
    """将 pieces 数组转为中国象棋 FEN 字符串"""
    board = [['' for _ in range(9)] for _ in range(10)]
    for p in pieces:
        ch = RED_FEN.get(p['text']) if p['isRed'] else BLACK_FEN.get(p['text'])
        if ch:
            board[p['row']][p['col']] = ch

    fen_rows = []
    for row in range(10):
        empty = 0
        line = ''
        for col in range(9):
            ch = board[row][col]
            if ch:
                if empty:
                    line += str(empty)
                    empty = 0
                line += ch
            else:
                empty += 1
        if empty:
            line += str(empty)
        fen_rows.append(line)

    turn = 'b' if current_turn else 'w'  # Pikafish: w=黑方走, b=红方走
    return '/'.join(fen_rows) + ' ' + turn


def uci_to_coords(uci):
    """UCI 走法 → (from_row, from_col, to_row, to_col)"""
    fr = int(uci[1])
    fc = ord(uci[0]) - ord('a')
    tr = int(uci[3])
    tc = ord(uci[2]) - ord('a')
    return fr, fc, tr, tc


def get_engine_path():
    """获取当前平台对应的引擎路径"""
    sys = platform.system()
    name = 'pikafish.exe' if sys == 'Windows' else 'pikafish'
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    return local if os.path.exists(local) else name


class ChessEngine:
    """皮卡鱼 UCI 引擎 — 每次查询全新握手，无残留状态"""

    def __init__(self, movetime=500, binary=None):
        self.movetime = movetime
        self._binary = binary or get_engine_path()

    def get_best_move(self, fen):
        """给定 FEN，返回 UCI 走法字符串。每次调用都全新启动引擎进程，彻底隔离状态。"""
        proc = subprocess.Popen(
            [self._binary],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            # 完整 UCI 握手 + 走子查询，与命令行测试完全一致
            proc.stdin.write('uci\n')
            proc.stdin.write('isready\n')
            proc.stdin.write('ucinewgame\n')
            proc.stdin.write('isready\n')
            proc.stdin.write('position fen ' + fen + '\n')
            proc.stdin.write('go movetime ' + str(self.movetime) + '\n')
            proc.stdin.flush()

            # 逐行读取直到 bestmove
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('bestmove'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] != '0000':
                        return parts[1]
                    return None
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                proc.kill()

        return None

    def close(self):
        pass  # 不再持有持久进程，无需清理
