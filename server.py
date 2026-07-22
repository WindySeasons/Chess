import eventlet
eventlet.monkey_patch()

import random
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['SECRET_KEY'] = 'chess-online-secret'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

# ---------- 棋盘常量 ----------
COLS = 9
ROWS = 10


def create_initial_pieces():
    return [
        # 黑方（上方，row 0~4）
        {'text': '車', 'isRed': False, 'row': 0, 'col': 0},
        {'text': '馬', 'isRed': False, 'row': 0, 'col': 1},
        {'text': '象', 'isRed': False, 'row': 0, 'col': 2},
        {'text': '士', 'isRed': False, 'row': 0, 'col': 3},
        {'text': '將', 'isRed': False, 'row': 0, 'col': 4},
        {'text': '士', 'isRed': False, 'row': 0, 'col': 5},
        {'text': '象', 'isRed': False, 'row': 0, 'col': 6},
        {'text': '馬', 'isRed': False, 'row': 0, 'col': 7},
        {'text': '車', 'isRed': False, 'row': 0, 'col': 8},
        {'text': '炮', 'isRed': False, 'row': 2, 'col': 1},
        {'text': '炮', 'isRed': False, 'row': 2, 'col': 7},
        {'text': '卒', 'isRed': False, 'row': 3, 'col': 0},
        {'text': '卒', 'isRed': False, 'row': 3, 'col': 2},
        {'text': '卒', 'isRed': False, 'row': 3, 'col': 4},
        {'text': '卒', 'isRed': False, 'row': 3, 'col': 6},
        {'text': '卒', 'isRed': False, 'row': 3, 'col': 8},
        # 红方（下方，row 5~9）
        {'text': '兵', 'isRed': True, 'row': 6, 'col': 0},
        {'text': '兵', 'isRed': True, 'row': 6, 'col': 2},
        {'text': '兵', 'isRed': True, 'row': 6, 'col': 4},
        {'text': '兵', 'isRed': True, 'row': 6, 'col': 6},
        {'text': '兵', 'isRed': True, 'row': 6, 'col': 8},
        {'text': '砲', 'isRed': True, 'row': 7, 'col': 1},
        {'text': '砲', 'isRed': True, 'row': 7, 'col': 7},
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


# ---------- 房间管理 ----------
rooms = {}  # room_code -> {...}
sid_to_room = {}  # sid -> room_code


def generate_room_code():
    while True:
        code = ''.join(random.choices('0123456789', k=6))
        if code not in rooms:
            return code


def copy_pieces(pieces):
    return [dict(p) for p in pieces]


# ==================== 走法规则（Python 版）====================

def in_board(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def piece_at(r, c, pieces):
    for i, p in enumerate(pieces):
        if p['row'] == r and p['col'] == c:
            return i
    return -1


def get_rook_moves(r, c, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        while in_board(nr, nc):
            idx = piece_at(nr, nc, pieces)
            if idx == -1:
                moves.append({'row': nr, 'col': nc})
            else:
                if pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
                    moves.append({'row': nr, 'col': nc})
                break
            nr += dr
            nc += dc
    return moves


def get_knight_moves(r, c, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    jumps = [
        (-2, -1, -1, 0), (-2, 1, -1, 0),
        (2, -1, 1, 0), (2, 1, 1, 0),
        (-1, -2, 0, -1), (-1, 2, 0, 1),
        (1, -2, 0, -1), (1, 2, 0, 1),
    ]
    for dr, dc, lr, lc in jumps:
        nr, nc = r + dr, c + dc
        leg_r, leg_c = r + lr, c + lc
        if not in_board(nr, nc):
            continue
        if piece_at(leg_r, leg_c, pieces) != -1:
            continue
        idx = piece_at(nr, nc, pieces)
        if idx == -1 or pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
            moves.append({'row': nr, 'col': nc})
    return moves


def get_cannon_moves(r, c, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        # 走子：直线到第一个阻挡
        while in_board(nr, nc) and piece_at(nr, nc, pieces) == -1:
            moves.append({'row': nr, 'col': nc})
            nr += dr
            nc += dc
        # 吃子：跳过炮架
        if in_board(nr, nc):
            nr += dr
            nc += dc
            while in_board(nr, nc):
                idx = piece_at(nr, nc, pieces)
                if idx != -1:
                    if pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
                        moves.append({'row': nr, 'col': nc})
                    break
                nr += dr
                nc += dc
    return moves


def get_elephant_moves(r, c, is_red, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    dests = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
    eyes = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for (dr, dc), (er, ec) in zip(dests, eyes):
        nr, nc = r + dr, c + dc
        eye_r, eye_c = r + er, c + ec
        if not in_board(nr, nc):
            continue
        if is_red and nr < 5:
            continue
        if not is_red and nr > 4:
            continue
        if piece_at(eye_r, eye_c, pieces) != -1:
            continue
        idx = piece_at(nr, nc, pieces)
        if idx == -1 or pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
            moves.append({'row': nr, 'col': nc})
    return moves


def get_advisor_moves(r, c, is_red, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if not in_board(nr, nc):
            continue
        if nc < 3 or nc > 5:
            continue
        if is_red and (nr < 7 or nr > 9):
            continue
        if not is_red and (nr < 0 or nr > 2):
            continue
        idx = piece_at(nr, nc, pieces)
        if idx == -1 or pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
            moves.append({'row': nr, 'col': nc})
    return moves


def get_general_moves(r, c, is_red, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if not in_board(nr, nc):
            continue
        if nc < 3 or nc > 5:
            continue
        if is_red and (nr < 7 or nr > 9):
            continue
        if not is_red and (nr < 0 or nr > 2):
            continue
        idx = piece_at(nr, nc, pieces)
        if idx == -1 or pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
            moves.append({'row': nr, 'col': nc})
    return moves


def get_pawn_moves(r, c, is_red, pieces):
    moves = []
    my_idx = piece_at(r, c, pieces)
    forward = -1 if is_red else 1
    crossed = r <= 4 if is_red else r >= 5

    nr = r + forward
    if in_board(nr, c):
        idx = piece_at(nr, c, pieces)
        if idx == -1 or pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
            moves.append({'row': nr, 'col': c})

    if crossed:
        for dc in (-1, 1):
            nc = c + dc
            if in_board(r, nc):
                idx = piece_at(r, nc, pieces)
                if idx == -1 or pieces[idx]['isRed'] != pieces[my_idx]['isRed']:
                    moves.append({'row': r, 'col': nc})
    return moves


def get_raw_moves(piece_index, pieces):
    p = pieces[piece_index]
    t = p['text']
    if t == '車':
        return get_rook_moves(p['row'], p['col'], pieces)
    elif t == '馬':
        return get_knight_moves(p['row'], p['col'], pieces)
    elif t in ('砲', '炮'):
        return get_cannon_moves(p['row'], p['col'], pieces)
    elif t in ('相', '象'):
        return get_elephant_moves(p['row'], p['col'], p['isRed'], pieces)
    elif t in ('仕', '士'):
        return get_advisor_moves(p['row'], p['col'], p['isRed'], pieces)
    elif t in ('帥', '將'):
        return get_general_moves(p['row'], p['col'], p['isRed'], pieces)
    elif t in ('兵', '卒'):
        return get_pawn_moves(p['row'], p['col'], p['isRed'], pieces)
    return []


def is_in_check(side_is_red, pieces):
    """检查某方是否被将军（含飞将规则）"""
    king_idx = -1
    for i, p in enumerate(pieces):
        if p['isRed'] == side_is_red and p['text'] in ('帥', '將'):
            king_idx = i
            break
    if king_idx == -1:
        return False

    king = pieces[king_idx]

    # 对方棋子能否攻击到将/帅
    for i, p in enumerate(pieces):
        if p['isRed'] == side_is_red:
            continue
        for m in get_raw_moves(i, pieces):
            if m['row'] == king['row'] and m['col'] == king['col']:
                return True

    # 飞将检查
    enemy_king_idx = -1
    for i, p in enumerate(pieces):
        if p['isRed'] != side_is_red and p['text'] in ('帥', '將'):
            enemy_king_idx = i
            break

    if enemy_king_idx != -1 and pieces[enemy_king_idx]['col'] == king['col']:
        blocked = False
        min_row = min(king['row'], pieces[enemy_king_idx]['row'])
        max_row = max(king['row'], pieces[enemy_king_idx]['row'])
        for i, p in enumerate(pieces):
            if i in (king_idx, enemy_king_idx):
                continue
            if p['col'] == king['col'] and min_row < p['row'] < max_row:
                blocked = True
                break
        if not blocked:
            return True

    return False


def is_move_legal(piece_index, to_row, to_col, pieces):
    """模拟走一步，检查是否导致己方被将军"""
    # 使用副本避免修改原始数据
    sim = [dict(p) for p in pieces]
    p = sim[piece_index]
    orig_row, orig_col = p['row'], p['col']
    captured_idx = piece_at(to_row, to_col, sim)

    if captured_idx != -1:
        sim.pop(captured_idx)
        if captured_idx < piece_index:
            piece_index -= 1

    sim[piece_index]['row'] = to_row
    sim[piece_index]['col'] = to_col
    return not is_in_check(sim[piece_index]['isRed'], sim)


def get_legal_moves(piece_index, pieces):
    raw = get_raw_moves(piece_index, pieces)
    return [m for m in raw if is_move_legal(piece_index, m['row'], m['col'], pieces)]


def has_legal_move(side_is_red, pieces):
    for i, p in enumerate(pieces):
        if p['isRed'] != side_is_red:
            continue
        if get_legal_moves(i, pieces):
            return True
    return False


def is_checkmate(side_is_red, pieces):
    return is_in_check(side_is_red, pieces) and not has_legal_move(side_is_red, pieces)


def is_stalemate(side_is_red, pieces):
    return not is_in_check(side_is_red, pieces) and not has_legal_move(side_is_red, pieces)


# ==================== 房间辅助函数 ====================

def get_room_of_sid(sid):
    code = sid_to_room.get(sid)
    return rooms.get(code)


def opponent_sid(room, my_sid):
    if room['creator'] == my_sid:
        return room.get('joiner')
    return room['creator']


def my_side(room, my_sid):
    return 'red' if room['creator'] == my_sid else 'black'


# ==================== WebSocket 事件 ====================

@socketio.on('connect')
def on_connect():
    print(f'[connect] {request.sid}')


@socketio.on('disconnect')
def on_disconnect():
    print(f'[disconnect] {request.sid}')
    code = sid_to_room.pop(request.sid, None)
    if not code or code not in rooms:
        return
    room = rooms[code]
    opp = opponent_sid(room, request.sid)
    if opp:
        socketio.emit('opponent_disconnected', to=opp)
    del rooms[code]


@socketio.on('create_room')
def on_create_room():
    code = generate_room_code()
    rooms[code] = {
        'creator': request.sid,
        'joiner': None,
        'pieces': create_initial_pieces(),
        'current_turn': True,  # True=红方
        'game_started': False,
        'game_over': None,     # None / 'red' / 'black'
        'chat': [],
        'move_history': [],
    }
    sid_to_room[request.sid] = code
    join_room(code)
    emit('room_created', {'room_code': code, 'side': 'red'})
    print(f'[room] {code} created by {request.sid}')


@socketio.on('join_room')
def on_join_room(data):
    code = data.get('room_code', '').strip()
    if not code or code not in rooms:
        emit('error', {'message': '房间不存在'})
        return

    room = rooms[code]
    if room['joiner'] is not None:
        emit('error', {'message': '房间已满'})
        return
    if room['creator'] == request.sid:
        emit('error', {'message': '不能加入自己创建的房间'})
        return

    room['joiner'] = request.sid
    sid_to_room[request.sid] = code
    join_room(code)
    emit('room_joined', {'room_code': code, 'side': 'black'})

    # 通知创建者
    socketio.emit('opponent_joined', to=room['creator'])

    # 两人到齐，开始游戏
    room['game_started'] = True
    pieces_data = [dict(p) for p in room['pieces']]
    for sid, side in [(room['creator'], 'red'), (room['joiner'], 'black')]:
        socketio.emit('game_start', {
            'pieces': pieces_data,
            'your_side': side,
            'current_turn': 'red',
        }, to=sid)

    print(f'[room] {code} started')


@socketio.on('move')
def on_move(data):
    room = get_room_of_sid(request.sid)
    code = sid_to_room.get(request.sid)
    if not room or not room['game_started']:
        emit('error', {'message': '游戏未开始'})
        return

    side = my_side(room, request.sid)
    expected_turn = 'red' if room['current_turn'] else 'black'
    if side != expected_turn:
        emit('error', {'message': '还没轮到你走棋'})
        return

    fr, fc = data.get('from_row'), data.get('from_col')
    tr, tc = data.get('to_row'), data.get('to_col')
    if fr is None or fc is None or tr is None or tc is None:
        emit('error', {'message': '无效的走法数据'})
        return

    # 查找来源位置的棋子
    src_idx = piece_at(fr, fc, room['pieces'])
    if src_idx == -1:
        emit('error', {'message': '该位置没有棋子'})
        return

    piece = room['pieces'][src_idx]
    expected_is_red = (side == 'red')
    if piece['isRed'] != expected_is_red:
        emit('error', {'message': '不能移动对方的棋子'})
        return

    # 合法性检查
    legal = get_legal_moves(src_idx, room['pieces'])
    is_legal = any(m['row'] == tr and m['col'] == tc for m in legal)
    if not is_legal:
        emit('error', {'message': '不合法的走法'})
        return

    # 执行走子
    captured = False
    captured_piece = None
    target_idx = piece_at(tr, tc, room['pieces'])
    if target_idx != -1:
        captured_piece = dict(room['pieces'][target_idx])
        room['pieces'].pop(target_idx)
        if target_idx < src_idx:
            src_idx -= 1
        captured = True

    piece_text = room['pieces'][src_idx]['text']
    piece_is_red = room['pieces'][src_idx]['isRed']

    room['pieces'][src_idx]['row'] = tr
    room['pieces'][src_idx]['col'] = tc
    room['current_turn'] = not room['current_turn']

    # 记录走棋历史
    room['move_history'].append({
        'from_row': fr, 'from_col': fc,
        'to_row': tr, 'to_col': tc,
        'captured_piece': captured_piece,
        'piece_text': piece_text,
    })

    # 广播走子
    turn_str = 'red' if room['current_turn'] else 'black'
    side_label = '红方' if piece_is_red else '黑方'
    socketio.emit('move_made', {
        'from': {'row': fr, 'col': fc},
        'to': {'row': tr, 'col': tc},
        'piece_text': piece_text,
        'side_label': side_label,
        'captured': captured,
        'current_turn': turn_str,
    }, to=code)

    # 检查将军/将死/困毙
    side_in_check = room['current_turn']
    if is_in_check(side_in_check, room['pieces']):
        socketio.emit('in_check', {'side': 'red' if side_in_check else 'black'}, to=code)

    if is_checkmate(side_in_check, room['pieces']):
        winner = 'black' if side_in_check else 'red'
        room['game_over'] = winner
        socketio.emit('game_over', {'winner': winner, 'reason': 'checkmate'}, to=code)
    elif is_stalemate(side_in_check, room['pieces']):
        winner = 'black' if side_in_check else 'red'
        room['game_over'] = winner
        socketio.emit('game_over', {'winner': winner, 'reason': 'stalemate'}, to=code)


@socketio.on('request_undo')
def on_request_undo():
    room = get_room_of_sid(request.sid)
    code = sid_to_room.get(request.sid)
    if not room or not room['game_started']:
        return
    if room['game_over']:
        emit('error', {'message': '游戏已结束'})
        return
    if not room['move_history']:
        emit('error', {'message': '没有可以悔棋的步骤'})
        return

    # 弹出最后一步
    last = room['move_history'].pop()

    # 把棋子移回原位
    piece_found = False
    for p in room['pieces']:
        if p['row'] == last['to_row'] and p['col'] == last['to_col']:
            p['row'] = last['from_row']
            p['col'] = last['from_col']
            piece_found = True
            break

    if not piece_found:
        emit('error', {'message': '悔棋失败'})
        return

    # 恢复被吃的棋子
    if last['captured_piece']:
        room['pieces'].append(last['captured_piece'])

    # 切换走棋方
    room['current_turn'] = not room['current_turn']
    turn_str = 'red' if room['current_turn'] else 'black'

    pieces_data = [dict(p) for p in room['pieces']]
    socketio.emit('undo_done', {
        'pieces': pieces_data,
        'current_turn': turn_str,
        'msg': '已悔棋',
    }, to=code)


@socketio.on('resign')
def on_resign():
    room = get_room_of_sid(request.sid)
    code = sid_to_room.get(request.sid)
    if not room or not room['game_started'] or room['game_over']:
        return

    side = my_side(room, request.sid)
    winner = 'black' if side == 'red' else 'red'
    room['game_over'] = winner
    socketio.emit('game_over', {'winner': winner, 'reason': 'resign'}, to=code)


@socketio.on('play_again')
def on_play_again():
    room = get_room_of_sid(request.sid)
    code = sid_to_room.get(request.sid)
    if not room or not room['game_over']:
        return

    # 重置游戏
    room['pieces'] = create_initial_pieces()
    room['current_turn'] = True
    room['game_over'] = None
    room['move_history'] = []
    room['game_started'] = True

    pieces_data = [dict(p) for p in room['pieces']]
    for sid, side in [(room['creator'], 'red'), (room['joiner'], 'black')]:
        socketio.emit('game_reset', {
            'pieces': pieces_data,
            'your_side': side,
            'current_turn': 'red',
        }, to=sid)


@socketio.on('chat')
def on_chat(data):
    room = get_room_of_sid(request.sid)
    code = sid_to_room.get(request.sid)
    if not room:
        return

    msg = data.get('message', '').strip()
    if not msg:
        return

    side = my_side(room, request.sid)
    side_label = '红方' if side == 'red' else '黑方'
    chat_entry = {'sender': side_label, 'message': msg}
    room['chat'].append(chat_entry)
    if len(room['chat']) > 50:
        room['chat'] = room['chat'][-50:]

    socketio.emit('chat_message', chat_entry, to=code)


# ==================== 静态文件 ====================

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


if __name__ == '__main__':
    print('中国象棋联机服务器启动于 http://localhost:3000')
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)
