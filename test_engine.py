from engine import ChessEngine, pieces_to_fen

# 模拟红方炮 (7,7)→(0,7) 吃黑马后的棋子状态
pieces = [
    {'text': '車', 'isRed': False, 'row': 0, 'col': 0},
    {'text': '馬', 'isRed': False, 'row': 0, 'col': 1},
    {'text': '象', 'isRed': False, 'row': 0, 'col': 2},
    {'text': '士', 'isRed': False, 'row': 0, 'col': 3},
    {'text': '將', 'isRed': False, 'row': 0, 'col': 4},
    {'text': '士', 'isRed': False, 'row': 0, 'col': 5},
    {'text': '象', 'isRed': False, 'row': 0, 'col': 6},
    {'text': '砲', 'isRed': True, 'row': 0, 'col': 7},
    {'text': '車', 'isRed': False, 'row': 0, 'col': 8},
    {'text': '炮', 'isRed': False, 'row': 2, 'col': 1},
    {'text': '炮', 'isRed': False, 'row': 2, 'col': 7},
    {'text': '卒', 'isRed': False, 'row': 3, 'col': 0},
    {'text': '卒', 'isRed': False, 'row': 3, 'col': 2},
    {'text': '卒', 'isRed': False, 'row': 3, 'col': 4},
    {'text': '卒', 'isRed': False, 'row': 3, 'col': 6},
    {'text': '卒', 'isRed': False, 'row': 3, 'col': 8},
    {'text': '兵', 'isRed': True, 'row': 6, 'col': 0},
    {'text': '兵', 'isRed': True, 'row': 6, 'col': 2},
    {'text': '兵', 'isRed': True, 'row': 6, 'col': 4},
    {'text': '兵', 'isRed': True, 'row': 6, 'col': 6},
    {'text': '兵', 'isRed': True, 'row': 6, 'col': 8},
    {'text': '砲', 'isRed': True, 'row': 7, 'col': 1},
    {'text': '車', 'isRed': True, 'row': 9, 'col': 0},
    {'text': '馬', 'isRed': True, 'row': 9, 'col': 1},
    {'text': '相', 'isRed': True, 'row': 9, 'col': 2},
    {'text': '仕', 'isRed': True, 'row': 9, 'col': 3},
    {'text': '帥', 'isRed': True, 'row': 9, 'col': 4},
    {'text': '仕', 'isRed': True, 'row': 9, 'col': 5},
    {'text': '相', 'isRed': True, 'row': 9, 'col': 6},
    {'text': '馬', 'isRed': True, 'row': 9, 'col': 7},
    {'text': '車', 'isRed': True, 'row': 9, 'col': 8},
]

eng = ChessEngine()
print('Binary:', eng._binary)
fen = pieces_to_fen(pieces, False)
print('FEN:', fen)
print('Best move:', eng.get_best_move(fen))
