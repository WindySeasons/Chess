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


def coords_to_uci(fr, fc, tr, tc):
    """(from_row, from_col, to_row, to_col) → UCI 走法"""
    return chr(ord('a') + fc) + str(fr) + chr(ord('a') + tc) + str(tr)


def get_engine_path():
    """获取当前平台对应的引擎路径"""
    sys = platform.system()
    if sys == 'Windows':
        name = 'pikafish.exe'
    else:
        name = 'pikafish'
    # 先在项目目录找，再回退到 PATH
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    if os.path.exists(local):
        return local
    return name


class ChessEngine:
    """皮卡鱼 UCI 引擎"""

    def __init__(self, movetime=500, binary=None):
        self.movetime = movetime
        path = binary or get_engine_path()
        self._proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        # 完整 UCI 握手 + 新局初始化
        self._cmd('uci')
        self._read_until('uciok')
        self._cmd('ucinewgame')
        self._cmd('isready')
        self._read_until('readyok')

    def _cmd(self, line):
        self._proc.stdin.write(line + '\n')
        self._proc.stdin.flush()

    def _read_until(self, prefix):
        for line in self._proc.stdout:
            line = line.strip()
            if line.startswith(prefix):
                return line

    def get_best_move(self, fen):
        """给定 FEN，返回 UCI 走法字符串，无合法走法返回 None"""
        self._cmd('position fen ' + fen)
        self._cmd('go movetime ' + str(self.movetime))
        resp = self._read_until('bestmove')
        if not resp:
            return None
        parts = resp.split()
        if len(parts) < 2:
            return None
        move = parts[1]
        if move == '0000':
            return None
        return move

    def close(self):
        try:
            self._cmd('quit')
            self._proc.terminate()
            self._proc.wait(timeout=3)
        except Exception:
            self._proc.kill()
