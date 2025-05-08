from flask import Flask, jsonify, render_template, request
import random
import time # 為了模擬一些延遲，讓前端有時間反應，實際部署時可移除

app = Flask(__name__)

# --- 遊戲核心設定 (從 "原遊戲.py" 移植和整合) ---
PATH_LENGTH = 15
NUM_PLAYERS = 7  # TODO (可改進): 考慮讓玩家數量可以在遊戲開始前設定
INITIAL_LIVES = 3
INITIAL_TRAPS = 3
MIN_NEW_TRAPS = 2
MAX_NEW_TRAPS = 4
START_POSITION = 0
END_POSITION = PATH_LENGTH - 1
FINISHERS_NEEDED = 3 # 需要多少玩家到達終點才結束遊戲
ENCOUNTER_BONUS_STEP = 1 # 遇到其他玩家時額外走的步數

# --- 全域遊戲狀態 ---
game_data = {}

def add_game_message(message_cn, message_en=""):
    """新增遊戲訊息到紀錄中，並限制長度"""
    full_message = f"{message_cn}"
    if message_en:
        full_message += f" ({message_en})"
    game_data["message_log"].append(full_message)
    MAX_LOG_MESSAGES = 20 # TODO (可改進): 訊息長度可配置
    if len(game_data["message_log"]) > MAX_LOG_MESSAGES:
        game_data["message_log"] = game_data["message_log"][-MAX_LOG_MESSAGES:]
    print(f"[GAME LOG] {full_message}") # 後端日誌，方便追蹤

def initialize_player_data():
    """初始化玩家資料"""
    players = {}
    for i in range(1, NUM_PLAYERS + 1):
        players[i] = {
            'id': i, # 加入玩家ID本身，方便前端使用
            'position': START_POSITION,
            'lives': INITIAL_LIVES,
            'finished': False,
            'finish_turn': None,
            'encounters': 0 # 新增遭遇次數
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
    game_data["message_log"] = [f"遊戲已重置！第 {game_data['turn_count']} 回合開始！新局開始！ (Game Reset! Turn {game_data['turn_count']} begins! New game starts!)"]
    game_data["message_log"].append(f"初始陷阱位置: {sorted(list(game_data['traps'])) if game_data['traps'] else '無'}")
    game_data["message_log"].append(f"輪到玩家 {game_data['current_player_id']} 行動。")
    game_data["game_over"] = False
    game_data["last_dice_roll"] = None
    # INFO: 這些額外資訊方便前端渲染
    game_data["path_length"] = PATH_LENGTH
    game_data["end_position"] = END_POSITION
    game_data["finishers_needed"] = FINISHERS_NEEDED
    game_data["num_players"] = NUM_PLAYERS

    print("--- Game state has been reset ---")
    print(f"Initial traps: {game_data['traps']}")
    print(f"Turn: {game_data['turn_count']}, Current Player: {game_data['current_player_id']}")
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

# --- Flask 路由 (API Endpoints) ---
@app.route('/')
def home():
    """提供主遊戲頁面 (HTML) - 前端渲染的入口"""
    # INFO: 你需要在 templates 資料夾下建立一個 index.html 檔案
    return render_template('index.html') # 前端需要自行實作

@app.route('/get_state', methods=['GET'])
def get_state():
    """提供目前的遊戲完整狀態給前端"""
    # TODO (可改進): 可以考慮只傳送自上次請求以來發生變化的部分，以減少傳輸量，但這會增加複雜性。
    return jsonify(prepare_data_for_json(game_data))

@app.route('/roll_dice', methods=['POST'])
def roll_dice_action():
    global game_data

    if game_data["game_over"]:
        add_game_message("遊戲已經結束了。 (The game is already over.)")
        return jsonify(prepare_data_for_json(game_data))

    request_data = request.json
    if not request_data or 'player_id' not in request_data:
        add_game_message("錯誤：請求中未指定玩家 ID。 (Error: Player ID not specified in request.)")
        return jsonify(prepare_data_for_json({"error": "Player ID missing"})), 400

    try:
        player_id_to_move = int(request_data['player_id'])
    except ValueError:
        add_game_message("錯誤：玩家 ID 格式不正確。 (Error: Invalid Player ID format.)")
        return jsonify(prepare_data_for_json({"error": "Invalid Player ID format"})), 400

    if player_id_to_move not in game_data["players"]:
        add_game_message(f"錯誤：無效的玩家 ID {player_id_to_move}。 (Error: Invalid Player ID {player_id_to_move}.)")
        return jsonify(prepare_data_for_json({"error": f"Invalid Player ID {player_id_to_move}"})), 400

    if game_data["players"][player_id_to_move]['finished']:
        add_game_message(f"玩家 {player_id_to_move} 已經完成遊戲，不能再移動。 (Player {player_id_to_move} has finished and cannot move.)")
        return jsonify(prepare_data_for_json(game_data))

    # 更新當前玩家 ID
    game_data["current_player_id"] = player_id_to_move
    add_game_message(f"輪到玩家 {player_id_to_move} 行動。 (Player {player_id_to_move}'s turn.)")

    # 擲骰子
    dice_roll = random.randint(1, 6)
    game_data["last_dice_roll"] = dice_roll
    add_game_message(f"玩家 {player_id_to_move} 擲出 {dice_roll} 點。 (Player {player_id_to_move} rolled {dice_roll}.)")

    # 如果骰到六點，更新陷阱位置
    if dice_roll == 6:
        num_new_traps = random.randint(MIN_NEW_TRAPS, MAX_NEW_TRAPS)
        new_traps = generate_new_traps(num_new_traps, PATH_LENGTH, START_POSITION, END_POSITION)
        game_data["traps"] = new_traps
        add_game_message(f"骰到六點！生成 {num_new_traps} 個新陷阱。 (Rolled a six! Generated {num_new_traps} new traps.)")
        add_game_message(f"新陷阱位置: {sorted(list(new_traps)) if new_traps else '無'} (New trap positions: {sorted(list(new_traps)) if new_traps else 'none'})")
        check_players_on_new_traps_web()  # 檢查是否有玩家在新陷阱上

    # 移動玩家
    current_position = game_data["players"][player_id_to_move]["position"]
    new_position = min(current_position + dice_roll, game_data["path_length"] - 1)
    game_data["players"][player_id_to_move]["position"] = new_position

    # 檢查是否踩到陷阱
    if new_position in game_data["traps"]:
        game_data["players"][player_id_to_move]["lives"] -= 1
        add_game_message(f"玩家 {player_id_to_move} 踩到陷阱！失去一條生命。 (Player {player_id_to_move} hit a trap! Lost one life.)")
        if game_data["players"][player_id_to_move]["lives"] <= 0:
            add_game_message(f"玩家 {player_id_to_move} 生命值歸零！ (Player {player_id_to_move} has no lives left!)")
        
        # 立即將玩家位置更新為起點
        game_data["players"][player_id_to_move]["position"] = START_POSITION
        add_game_message(f"玩家 {player_id_to_move} 回到起點位置 {START_POSITION}。 (Player {player_id_to_move} returns to start position {START_POSITION}.)")

    # 檢查是否到達終點
    if new_position == game_data["path_length"] - 1:
        game_data["players"][player_id_to_move]["finished"] = True
        game_data["players"][player_id_to_move]["finish_turn"] = game_data["turn_count"]
        game_data["finished_players_ranked"].append(player_id_to_move)
        add_game_message(f"玩家 {player_id_to_move} 到達終點！ (Player {player_id_to_move} reached the finish!)")

        # 檢查是否達到結束條件
        if len(game_data["finished_players_ranked"]) >= game_data["finishers_needed"]:
            game_data["game_over"] = True
            add_game_message("遊戲結束！達到所需完成人數。 (Game Over! Required number of finishers reached.)")

    # 更新回合數
    game_data["turn_count"] += 1
    add_game_message(f"--- 第 {game_data['turn_count']} 回合開始 ---", f"--- Turn {game_data['turn_count']} begins ---")

    return jsonify(prepare_data_for_json(game_data))

@app.route('/reset', methods=['POST'])
def reset_action():
    """重置遊戲"""
    reset_game_state()
    return jsonify(prepare_data_for_json(game_data))

# --- 主程式入口 ---
if __name__ == '__main__':
    reset_game_state() # 伺服器啟動時初始化/重置一次遊戲
    # INFO: debug=True 只在開發時使用。部署時應關閉。
    # INFO: host='0.0.0.0' 可以讓區域網路內的其他裝置訪問你的開發伺服器。
    app.run(debug=True, host='0.0.0.0', port=5000)