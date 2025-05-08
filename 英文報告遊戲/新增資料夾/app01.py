from flask import Flask, jsonify, render_template, request
import random # 確保 random 被導入

app = Flask(__name__)

# --- 遊戲核心設定 (從你之前的程式碼移植) ---
PATH_LENGTH = 15
NUM_PLAYERS = 7 # 你可能希望這個之後可以動態設定
INITIAL_LIVES = 3
INITIAL_TRAPS = 3
MIN_NEW_TRAPS = 2
MAX_NEW_TRAPS = 4
START_POSITION = 0
END_POSITION = PATH_LENGTH - 1
FINISHERS_NEEDED = 3

# --- 全域遊戲狀態 (簡化範例，實務上可能用類別管理) ---
# 你需要將之前 players, traps, finished_players_ranked 等變數整合到這裡
game_data = {
    "players": {}, # 例如: {1: {"position": 0, "lives": 3, "finished": False, "finish_turn": None}, ...}
    "traps": set(),
    "finished_players_ranked": [],
    "turn_count": 0,
    "current_player_id": 1, # 目前輪到的玩家
    "message_log": [],     # 遊戲訊息紀錄
    "game_over": False,
    "last_dice_roll": None
}

def add_game_message(message):
    """新增遊戲訊息到紀錄中，並限制長度"""
    game_data["message_log"].append(message)
    MAX_LOG_MESSAGES = 15
    if len(game_data["message_log"]) > MAX_LOG_MESSAGES:
        game_data["message_log"] = game_data["message_log"][-MAX_LOG_MESSAGES:]

def initialize_player_data():
    """初始化玩家資料 (移植你之前的邏輯)"""
    players = {}
    for i in range(1, NUM_PLAYERS + 1):
        players[i] = {
            'position': START_POSITION,
            'lives': INITIAL_LIVES,
            'finished': False,
            'finish_turn': None
        }
    return players

def generate_new_traps(num, path_len, start_pos, end_pos):
    """生成陷阱 (移植你之前的邏輯，確保避開起點和終點)"""
    possible_positions = list(range(start_pos + 1, end_pos))
    num_traps = min(num, len(possible_positions))
    if num_traps <= 0:
        return set()
    return set(random.sample(possible_positions, num_traps))

def reset_game_state():
    """重置遊戲狀態"""
    global game_data
    game_data["players"] = initialize_player_data()
    game_data["traps"] = generate_new_traps(INITIAL_TRAPS, PATH_LENGTH, START_POSITION, END_POSITION)
    game_data["finished_players_ranked"] = []
    game_data["turn_count"] = 0
    game_data["current_player_id"] = 1 # 預設從玩家1開始
    game_data["message_log"] = ["遊戲已重置！新局開始！ (Game Reset! New game starts!)"]
    game_data["game_over"] = False
    game_data["last_dice_roll"] = None
    print("Game state has been reset.") # 後端日誌

# --- Flask 路由 (API Endpoints) ---
@app.route('/')
def home():
    """提供主遊戲頁面 (HTML)"""
    return render_template('index.html')

@app.route('/get_state', methods=['GET'])
def get_state():
    """提供目前的遊戲完整狀態給前端"""
    return jsonify(game_data)

@app.route('/roll_dice', methods=['POST'])
def roll_dice_action():
    """處理擲骰子和玩家移動的邏輯"""
    global game_data
    if game_data["game_over"]:
        add_game_message("遊戲已經結束了。 (The game is already over.)")
        return jsonify(game_data)

    player_id_to_move = game_data["current_player_id"] # 或從 request 取得
    # 這裡你需要從 `game_data` 中取得 `player_id_to_move` 的資料
    # 並執行擲骰子、移動、檢查陷阱、檢查生命值、檢查是否完成等邏輯
    # 這些邏輯需要從你之前的 `play_game` 函數中抽離和調整

    # 範例: (你需要大幅擴充這部分)
    dice_value = random.randint(1, 6)
    game_data["last_dice_roll"] = dice_value
    add_game_message(f"玩家 {player_id_to_move} 擲出了 {dice_value}！ (Player {player_id_to_move} rolled a {dice_value}!)")

    player = game_data["players"][player_id_to_move]

    if dice_value == 6:
        add_game_message("骰到6！清除舊陷阱，生成新陷阱！ (Rolled a 6! Clearing old traps, generating new ones!)")
        game_data["traps"] = generate_new_traps(random.randint(MIN_NEW_TRAPS, MAX_NEW_TRAPS), PATH_LENGTH, START_POSITION, END_POSITION)
        add_game_message(f"新陷阱位置: {sorted(list(game_data['traps']))}")
        # 檢查新陷阱是否影響到玩家 (你需要實作這部分)
        for pid, p_data in game_data["players"].items():
            if not p_data['finished'] and p_data['position'] in game_data["traps"]:
                if p_data['lives'] > 0:
                    p_data['lives'] -=1
                    add_game_message(f"玩家 {pid} 不幸踩在新生成的陷阱上！剩餘生命: {p_data['lives']}")
                p_data['position'] = START_POSITION # 送回起點
        add_game_message(f"玩家 {player_id_to_move} 本輪因處理陷阱而休息。")
    else:
        new_position = player['position'] + dice_value
        if new_position >= END_POSITION:
            player['position'] = END_POSITION
            if not player['finished']:
                player['finished'] = True
                player['finish_turn'] = game_data["turn_count"]
                game_data["finished_players_ranked"].append(player_id_to_move)
                add_game_message(f"玩家 {player_id_to_move} 到達終點！")
                if len(game_data["finished_players_ranked"]) >= FINISHERS_NEEDED:
                    game_data["game_over"] = True
                    add_game_message("遊戲結束！已有足夠玩家到達終點。")
        elif new_position in game_data["traps"]:
            add_game_message(f"玩家 {player_id_to_move} 踩到陷阱！")
            if player['lives'] > 0:
                player['lives'] -= 1
            player['position'] = START_POSITION
            if player['lives'] == 0:
                add_game_message(f"玩家 {player_id_to_move} 生命耗盡，但仍可繼續...只是運氣不好。")
        else:
            player['position'] = new_position
            add_game_message(f"玩家 {player_id_to_move} 移動到位置 {player['position']}。")

    # 決定下一個玩家 (你需要實作更完善的輪轉邏輯)
    if not game_data["game_over"]:
        active_players = [pid for pid, pdata in game_data["players"].items() if not pdata['finished']]
        if active_players:
            current_game_player_index = active_players.index(game_data["current_player_id"]) if game_data["current_player_id"] in active_players else -1
            next_player_index = (current_game_player_index + 1) % len(active_players)
            game_data["current_player_id"] = active_players[next_player_index]
            if next_player_index == 0: # 完成一輪
                game_data["turn_count"] += 1
        else: # 沒有可行動的玩家了
            game_data["game_over"] = True
            add_game_message("所有可行動玩家均已完成！遊戲結束。")


    return jsonify(game_data) # 回傳更新後的遊戲狀態

@app.route('/reset', methods=['POST'])
def reset_action():
    """重置遊戲"""
    reset_game_state()
    return jsonify(game_data)

# --- 主程式入口 ---
if __name__ == '__main__':
    reset_game_state() # 伺服器啟動時初始化/重置一次遊戲
    app.run(debug=True) # debug=True 只在開發時使用