from flask import Flask, jsonify, render_template, request, make_response
import random
import time # 為了模擬一些延遲，讓前端有時間反應，實際部署時可移除
import uuid

app = Flask(__name__)

# --- 遊戲核心設定 (從 "原遊戲.py" 移植和整合) ---
PATH_LENGTH = 21
NUM_PLAYERS = 7  # TODO (可改進): 考慮讓玩家數量可以在遊戲開始前設定
INITIAL_LIVES = 3
INITIAL_TRAPS = 3
MIN_NEW_TRAPS = 2
MAX_NEW_TRAPS = 4
START_POSITION = 0
END_POSITION = PATH_LENGTH - 1
FINISHERS_NEEDED = 3 # 需要多少玩家到達終點才結束遊戲
ENCOUNTER_BONUS_STEP = 1 # 遇到其他玩家時額外走的步數
MAX_MESSAGES = 9

# --- 全域遊戲狀態 ---
game_data = {}
player_cookies = {}  # 儲存玩家ID和cookie的對應關係
reset_requests = set()  # 儲存同意重置的玩家ID

def add_game_message(message_cn, message_en=""):
    """新增遊戲訊息到紀錄中，並限制長度"""
    full_message = f"{message_cn}"
    if message_en:
        full_message += f" ({message_en})"
    game_data["message_log"].append(full_message)
    if len(game_data["message_log"]) > MAX_MESSAGES:
        game_data["message_log"] = game_data["message_log"][-MAX_MESSAGES:]
    print(f"[GAME LOG] {full_message}") # 後端日誌，方便追蹤

def initialize_player_data():
    """初始化玩家資料"""
    players = {}
    for i in range(1, len(player_cookies) + 1):
        players[i] = {
            'id': i,
            'name': f'玩家 {i}',  # 預設名稱
            'position': START_POSITION,
            'lives': INITIAL_LIVES,
            'finished': False,
            'finish_turn': None,
            'encounters': 0,
            'is_ready': False  # 玩家準備狀態
        }
    return players

def generate_new_traps(num_traps_to_generate, path_len, start_pos, end_pos):
    """生成陷阱，避開起點和終點"""
    # INFO: 陷阱不能在起點或終點
    possible_positions = list(range(start_pos + 1, end_pos)) # 從 START_POSITION + 1 到 END_POSITION - 1
    
    # INFO: 確保陷阱數量不超過可用位置數量
    actual_num_traps = min(num_traps_to_generate, len(possible_positions))
    if actual_num_traps <= 0:
        return set()
    return set(random.sample(possible_positions, actual_num_traps))

def handle_player_trap_fall_web(player_id, trap_position):
    """處理玩家掉入陷阱 (Web版，主要更新 game_data 和 message_log)"""
    player = game_data["players"][player_id]
    
    message_prefix_cn = f"😱 啊哈！玩家 {player_id} 在位置 {trap_position} 踩到陷阱！"
    message_prefix_en = f"😱 Aha! Player {player_id} stepped on a trap at position {trap_position}!"

    if player['lives'] > 0:
        player['lives'] -= 1
        add_game_message(f"{message_prefix_cn} 失去 1 條命。", f"{message_prefix_en} Lost 1 life.")
        if player['lives'] == 0:
            add_game_message(f"玩家 {player_id} 的生命已耗盡！但仍可繼續移動... 只是運氣不太好。",
                             f"Player {player_id} has run out of lives! They can still move... just with bad luck.")
        else:
            add_game_message(f"玩家 {player_id} 剩下 {player['lives']} 條命。",
                             f"Player {player_id} has {player['lives']} lives left.")
    else:
        add_game_message(f"😅 {message_prefix_cn} 但已經沒有命可以扣了。",
                         f"😅 {message_prefix_en} But no lives left to lose.")

    player['position'] = START_POSITION
    add_game_message(f"玩家 {player_id} 回到起點 {START_POSITION}。",
                     f"Player {player_id} returns to start {START_POSITION}.")
    # time.sleep(1) # 由前端控制顯示節奏，後端盡快回應

def check_players_on_new_traps_web():
    """檢查是否有玩家正好在新生成的陷阱上 (Web版)"""
    trapped_players_info = []
    for p_id, p_data in game_data["players"].items():
        if not p_data['finished'] and p_data['position'] in game_data["traps"]:
            # INFO: 規則中生命為0是否也該檢查？原遊戲設計是生命>0才扣，但都回起點。
            # 目前邏輯是只要在陷阱上就處理（即使生命為0也送回起點，但不扣命）
            trapped_players_info.append((p_id, p_data['position']))

    if trapped_players_info:
        add_game_message("💥 新陷阱生成時有人中獎了！", "💥 Someone hit the jackpot when new traps were generated!")
        for p_id, position in trapped_players_info:
            handle_player_trap_fall_web(p_id, position)
    else:
        add_game_message("😌 新陷阱生成，暫時安全。", "😌 New traps generated, safe for now.")


def determine_next_player():
    """決定下一個輪到的玩家，如果一輪結束則增加回合數"""
    if game_data["game_over"]:
        return

    active_players_ids = [pid for pid, pdata in game_data["players"].items() if not pdata['finished']]
    if not active_players_ids:
        add_game_message("所有玩家都已完成！遊戲結束。", "All players have finished! Game Over.")
        game_data["game_over"] = True
        return

    try:
        # 找到目前玩家在活躍玩家列表中的索引
        current_player_index = active_players_ids.index(game_data["current_player_id"])
        next_player_list_index = (current_player_index + 1) % len(active_players_ids)
        
        # 如果是列表中的第一個玩家，表示新的一輪開始 (或者只有一個活躍玩家時)
        if next_player_list_index == 0:
            game_data["turn_count"] += 1
            add_game_message(f"--- 第 {game_data['turn_count']} 回合開始 ---", f"--- Turn {game_data['turn_count']} begins ---")

    except ValueError: # 如果 current_player_id 不在 active_players_ids 中 (例如剛完成)
        # 預設從活躍玩家列表的第一個開始，並開始新回合
        next_player_list_index = 0
        game_data["turn_count"] += 1 # 因為是輪到下一個人，算作新回合的開始，或回合繼續
        add_game_message(f"--- 第 {game_data['turn_count']} 回合 ---", f"--- Turn {game_data['turn_count']} ---")


    game_data["current_player_id"] = active_players_ids[next_player_list_index]
    add_game_message(f"輪到玩家 {game_data['current_player_id']} 行動。", f"Player {game_data['current_player_id']}'s turn.")
    # TODO (可改進): 如果選擇的玩家生命值為0，是否要跳過或有特殊提示？
    # 原遊戲邏輯是生命為0仍可被選擇並移動（但踩陷阱不扣命）。此處遵循。

def reset_game_state():
    """重置遊戲狀態"""
    global game_data # 宣告我們要修改的是全域變數
    game_data["players"] = initialize_player_data()
    game_data["traps"] = generate_new_traps(INITIAL_TRAPS, PATH_LENGTH, START_POSITION, END_POSITION)
    game_data["finished_players_ranked"] = []
    game_data["turn_count"] = 1 # 遊戲開始算第一回合
    game_data["current_player_id"] = 1 # 預設從玩家1開始
    game_data["message_log"] = [f"遊戲已重置！等待玩家準備..."]
    game_data["message_log"].append(f"初始陷阱位置: {sorted(list(game_data['traps'])) if game_data['traps'] else '無'}")
    game_data["game_over"] = False
    game_data["game_started"] = False # 遊戲開始狀態
    game_data["last_dice_roll"] = None
    # INFO: 這些額外資訊方便前端渲染
    game_data["path_length"] = PATH_LENGTH
    game_data["end_position"] = END_POSITION
    game_data["finishers_needed"] = FINISHERS_NEEDED
    game_data["num_players"] = NUM_PLAYERS

    print("--- Game state has been reset ---")
    print(f"Initial traps: {game_data['traps']}")
    print("---------------------------------")
    
import copy # 如果需要深拷貝，但這裡淺拷貝修改應該足夠

# ... (你其他的 import 和 Flask app 初始化) ...

def prepare_data_for_json(original_data):
    """將原始資料中不可序列化的部分轉換為可序列化格式 (例如 set -> list)"""
    if not original_data:
        return {}
    # 建立一個淺拷貝，這樣我們不會修改到原始的 game_data 中的 set (保留 set 的效能優勢)
    data_to_send = original_data.copy()
    if "traps" in data_to_send and isinstance(data_to_send["traps"], set):
        data_to_send["traps"] = list(data_to_send["traps"])
    # 如果還有其他 set 或不可序列化的類型，可以在這裡一併處理
    # 例如:
    # if "some_other_set_field" in data_to_send and isinstance(data_to_send["some_other_set_field"], set):
    #     data_to_send["some_other_set_field"] = list(data_to_send["some_other_set_field"])
    return data_to_send

def get_player_id_from_cookie():
    """從cookie中獲取玩家ID"""
    cookie = request.cookies.get('player_id')
    if cookie and cookie in player_cookies:
        return player_cookies[cookie]
    return None

# --- Flask 路由 (API Endpoints) ---
@app.route('/')
def home():
    """提供主遊戲頁面 (HTML) - 前端渲染的入口"""
    # INFO: 你需要在 templates 資料夾下建立一個 index.html 檔案
    return render_template('index.html') # 前端需要自行實作

@app.route('/join_game', methods=['POST'])
def join_game():
    """新玩家加入遊戲"""
    cookie = request.cookies.get('player_id')
    
    # 如果已經有cookie且是已註冊的玩家
    if cookie and cookie in player_cookies:
        return jsonify({"player_id": player_cookies[cookie]})
    
    # 生成新的cookie
    new_cookie = str(uuid.uuid4())
    player_id = len(player_cookies) + 1
    player_cookies[new_cookie] = player_id
    
    # 如果遊戲還沒開始，新增新玩家資料
    if not game_data.get("game_started", False):
        if "players" not in game_data:
            game_data["players"] = {}
        game_data["players"][player_id] = {
            'id': player_id,
            'name': f'玩家 {player_id}',
            'position': START_POSITION,
            'lives': INITIAL_LIVES,
            'finished': False,
            'finish_turn': None,
            'encounters': 0,
            'is_ready': False
        }
        add_game_message(f"新玩家 {player_id} 加入了遊戲！")
    
    response = make_response(jsonify({"player_id": player_id}))
    response.set_cookie('player_id', new_cookie, max_age=86400)  # cookie有效期24小時
    return response

@app.route('/get_state', methods=['GET'])
def get_state():
    """提供目前的遊戲完整狀態給前端"""
    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({"error": "請先加入遊戲"}), 401
    
    data = prepare_data_for_json(game_data)
    data["current_player_id"] = player_id
    return jsonify(data)

@app.route('/get_current_player', methods=['GET'])
def get_current_player():
    if not game_data.get("game_started", False):
        return jsonify({'current_player_id': None})
    
    current_player_id = game_data.get("current_player_id")
    if current_player_id and current_player_id in game_data["players"]:
        current_player = game_data["players"][current_player_id]
        return jsonify({
            'current_player_id': current_player_id,
            'player_name': current_player['name']
        })
    return jsonify({'current_player_id': None})

@app.route('/roll_dice', methods=['POST'])
def roll_dice():
    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({'error': '未找到玩家ID'}), 400

    # 簡化擲骰子條件：只有當前回合的玩家可以擲骰子
    if game_data["current_player_id"] != player_id:
        return jsonify({'error': '不是你的回合'}), 400

    if game_data["game_over"]:
        return jsonify({'error': '遊戲已結束'}), 400

    if not game_data.get("game_started", False):
        return jsonify({'error': '遊戲尚未開始'}), 400

    player = game_data["players"][player_id]
    if player['finished']:
        return jsonify({'error': '你已經完成遊戲'}), 400

    # 1. 擲骰子
    dice_result = random.randint(1, 6)
    old_position = player['position']
    add_game_message(f"{player['name']} 擲出 {dice_result} 點")

    # 2. 計算初始新位置
    new_position = min(old_position + dice_result, game_data["path_length"] - 1)
    
    # 3. 重複檢查是否遇到其他玩家，直到沒有遇到人為止
    while True:
        encountered_players = []
        for other_id, other_player in game_data["players"].items():
            if other_id != player_id and other_player['position'] == new_position and not other_player['finished']:
                encountered_players.append(other_player)
        
        if not encountered_players:
            break  # 如果沒有遇到人，跳出循環
            
        # 遇到其他玩家，額外移動一格
        new_position = min(new_position + ENCOUNTER_BONUS_STEP, game_data["path_length"] - 1)
        player_names = [p['name'] for p in encountered_players]
        add_game_message(f"{player['name']} 遇到 {', '.join(player_names)}，額外移動一格！")
        
        # 如果已經到達終點，就不需要再檢查了
        if new_position >= game_data["path_length"] - 1:
            break

    # 4. 更新位置並顯示移動訊息
    player['position'] = new_position
    add_game_message(f"{player['name']} 移動到位置 {new_position}")

    # 5. 檢查是否踩到陷阱
    if new_position in game_data["traps"]:
        player['lives'] -= 1
        add_game_message(f"{player['name']} 踩到陷阱，失去一條生命！")
        # 踩到陷阱後回到起點
        player['position'] = START_POSITION
        add_game_message(f"{player['name']} 回到起點！")
        if player['lives'] <= 0:
            player['finished'] = True
            add_game_message(f"{player['name']} 失去所有生命，遊戲結束！")

    # 6. 檢查是否到達終點
    if player['position'] >= game_data["path_length"] - 1:
        player['finished'] = True
        add_game_message(f"{player['name']} 到達終點！")

    # 7. 檢查遊戲是否結束
    active_players = [p for p in game_data["players"].values() if not p['finished']]
    if len(active_players) <= 1:
        game_data["game_over"] = True
        if len(active_players) == 1:
            winner = active_players[0]
            add_game_message(f"遊戲結束！{winner['name']} 獲勝！")
        else:
            add_game_message("遊戲結束！沒有玩家獲勝！")

    # 8. 切換到下一個玩家
    if not game_data["game_over"]:
        player_ids = list(game_data["players"].keys())
        current_index = player_ids.index(player_id)
        next_index = (current_index + 1) % len(player_ids)
        while game_data["players"][player_ids[next_index]]['finished']:
            next_index = (next_index + 1) % len(player_ids)
        game_data["current_player_id"] = player_ids[next_index]
        next_player = game_data["players"][player_ids[next_index]]
        add_game_message(f"輪到 {next_player['name']} 行動")

    return jsonify(prepare_data_for_json(game_data))

@app.route('/set_player_name', methods=['POST'])
def set_player_name():
    """設定玩家名稱"""
    if game_data["game_over"]:
        return jsonify({"error": "遊戲已結束"}), 400

    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({"error": "請先加入遊戲"}), 401

    # 檢查玩家是否已準備
    if game_data["players"][player_id]['is_ready']:
        return jsonify({"error": "已準備的玩家不能修改名稱"}), 400

    request_data = request.json
    if not request_data or 'name' not in request_data:
        return jsonify({"error": "缺少必要參數"}), 400

    new_name = request_data['name'].strip()
    if not new_name:
        return jsonify({"error": "名稱不能為空"}), 400

    game_data["players"][player_id]['name'] = new_name
    add_game_message(f"玩家 {player_id} 將名稱改為：{new_name}")
    return jsonify(prepare_data_for_json(game_data))

@app.route('/set_ready', methods=['POST'])
def set_ready():
    """設定玩家準備狀態"""
    if game_data["game_over"]:
        return jsonify({"error": "遊戲已結束"}), 400

    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({"error": "請先加入遊戲"}), 401

    player = game_data["players"][player_id]
    player['is_ready'] = not player['is_ready']  # 切換準備狀態
    
    if player['is_ready']:
        add_game_message(f"{player['name']} 已準備好開始遊戲！")
    else:
        add_game_message(f"{player['name']} 取消準備。")

    # 檢查是否所有玩家都已準備
    all_ready = all(p['is_ready'] for p in game_data["players"].values())
    if all_ready and len(game_data["players"]) >= 2:  # 至少需要2個玩家
        add_game_message("所有玩家都已準備好，遊戲開始！")
        game_data["game_started"] = True
        game_data["current_player_id"] = 1

    return jsonify(prepare_data_for_json(game_data))

@app.route('/request_reset', methods=['POST'])
def request_reset():
    """請求重置遊戲"""
    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({"error": "請先加入遊戲"}), 401

    # 清除之前的重置請求
    reset_requests.clear()
    # 將請求者加入同意列表
    reset_requests.add(player_id)
    add_game_message(f"{game_data['players'][player_id]['name']} 請求重置遊戲")

    return jsonify({"reset_requested": True, **prepare_data_for_json(game_data)})

@app.route('/agree_reset', methods=['POST'])
def agree_reset():
    """玩家同意重置遊戲"""
    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({"error": "請先加入遊戲"}), 401

    reset_requests.add(player_id)
    add_game_message(f"{game_data['players'][player_id]['name']} 同意重置遊戲")

    # 檢查是否所有玩家都同意重置
    if len(reset_requests) == len(game_data["players"]):
        reset_game_state()
        reset_requests.clear()
        return jsonify({"reset_complete": True, **prepare_data_for_json(game_data)})
    
    return jsonify({"reset_complete": False, **prepare_data_for_json(game_data)})

@app.route('/disagree_reset', methods=['POST'])
def disagree_reset():
    """玩家不同意重置遊戲"""
    player_id = get_player_id_from_cookie()
    if not player_id:
        return jsonify({"error": "請先加入遊戲"}), 401

    add_game_message(f"{game_data['players'][player_id]['name']} 不同意重置遊戲")
    reset_requests.clear()
    return jsonify(prepare_data_for_json(game_data))

# --- 主程式入口 ---
if __name__ == '__main__':
    reset_game_state() # 伺服器啟動時初始化/重置一次遊戲
    # INFO: debug=True 只在開發時使用。部署時應關閉。
    # INFO: host='0.0.0.0' 可以讓區域網路內的其他裝置訪問你的開發伺服器。
    app.run(debug=True, host='0.0.0.0', port=5000)