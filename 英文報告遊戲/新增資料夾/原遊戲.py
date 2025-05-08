import random
import time # 保持戲劇效果 (Keep the dramatic effect)
import sys # 用於 exit()

# --- 遊戲設定 (Game Settings) ---
PATH_LENGTH = 15      # 道路長度 (Length of the path) - 更新 (Updated)
NUM_PLAYERS = 7       # 玩家數量 (Number of players)
INITIAL_TRAPS = 3     # 初始陷阱數量 (Initial number of traps)
MIN_NEW_TRAPS = 2     # 骰到6時最少新陷阱數 (Min new traps when rolling a 6)
MAX_NEW_TRAPS = 4     # 骰到6時最多新陷阱數 (Max new traps when rolling a 6)
START_POSITION = 0    # 起點位置 (Starting position) - 確認 (Confirmed)
END_POSITION = PATH_LENGTH - 1 # 終點位置 (Ending position) - 更新 (Updated)
INITIAL_LIVES = 3     # 初始生命值 (Initial lives) - 新增 (New)
FINISHERS_NEEDED = 3  # 需要多少玩家到達終點才結束遊戲 (How many players need to finish to end the game) - 新增 (New)
ENCOUNTER_BONUS_STEP = 1 # 遇到其他玩家時額外走的步數 (Bonus step when encountering another player) - 新增 (New)

# --- 輔助函數 (Helper Functions) ---

def display_board(players, traps, path_length, finished_players_ranked)
    顯示目前的遊戲盤面狀態 (Display the current game board state)
    board = ['_']  path_length
    # 標記陷阱 (Mark traps) - 用 'T'
    for trap_pos in traps
        if 0 = trap_pos  path_length
            board[trap_pos] = 'T'

    # 標記玩家 (Mark players) - 用玩家編號
    # 如果玩家和陷阱在同一格，顯示玩家優先 (If player and trap are on the same square, show player)
    player_positions = {} # 記錄每個位置有哪些玩家 (Record which players are at each position)
    for player_id, data in players.items()
        pos = data['position']
        if 0 = pos  path_length
            if pos not in player_positions
                player_positions[pos] = []
            player_positions[pos].append(str(player_id)) # 記錄玩家 ID 字串 (Record player ID string)

    for pos, ids in player_positions.items()
        if board[pos] == '_' or board[pos] == 'T' # 優先顯示玩家 (Prioritize showing player)
            if len(ids)  1
                board[pos] = '' # 多個玩家用 '' (Multiple players use '')
            else
                board[pos] = ids[0] # 單個玩家顯示 ID (Single player show ID)

    print(n + = (path_length  2 + 10)) # 加寬分隔線 (Wider separator)
    print( .join(board))
    print(f陷阱位置 (Trap positions) {sorted(list(traps))})
    print(玩家狀態 (Player Status))
    for player_id, data in players.items()
        status = 
        if data['finished']
            # 查找該玩家在完成列表中的排名 (Find player's rank in the finished list)
            rank = 未知 (Unknown)
            for i, finished_player_id in enumerate(finished_players_ranked)
                if finished_player_id == player_id
                    rank = f第 {i+1} 名 (Rank {i+1})
                    break
            status = f已完成 ({rank})
        elif data['lives'] = 0
             status = 生命耗盡 (Out of lives) # 雖然規則是回起點，但標示一下 (Although rule is reset, mark it)
        else
            status = f位置 {data['position']}, 生命 {data['lives']}, 遭遇 {data['encounters']}
            status += f (Pos {data['position']}, Lives {data['lives']}, Encounters {data['encounters']})
        print(f  玩家 {player_id} {status})

    print(= (path_length  2 + 10))


def generate_traps(num_traps, path_length, existing_players_pos)
    
    隨機生成指定數量的陷阱位置 (Randomly generate trap positions)
    陷阱不能在起點或終點 (Traps cannot be at the start or end position) - 更新 (Updated)
    
    # 可放置陷阱的位置：從 1 到 path_length - 2 (Positions available for traps from 1 to path_length - 2)
    possible_positions = list(range(START_POSITION + 1, END_POSITION))
    # 確保陷阱數量不超過可用位置數量 (Ensure number of traps doesn't exceed available positions)
    num_traps = min(num_traps, len(possible_positions))
    if num_traps = 0
        return set() # 沒有位置可以放陷阱了 (No positions left for traps)

    trap_positions = set(random.sample(possible_positions, num_traps))
    return trap_positions

def handle_trap_fall(player_id, players, traps, position)
    處理玩家掉入陷阱的情況 (Handle player falling into a trap)
    if players[player_id]['lives']  0 # 只有還有命才會扣 (Only deduct life if they have lives left)
        players[player_id]['lives'] -= 1
        print(f😱 啊哈！玩家 {player_id} 在位置 {position} 踩到陷阱！失去 1 條命。)
        print(f(😱 Aha! Player {player_id} stepped on a trap at position {position}! Lost 1 life.))
        if players[player_id]['lives'] == 0
            print(f玩家 {player_id} 的生命已耗盡！但仍可繼續移動... 只是運氣不太好。)
            print(f(Player {player_id} has run out of lives! They can still move... just with bad luck.))
        else
            print(f玩家 {player_id} 剩下 {players[player_id]['lives']} 條命。)
            print(f(Player {player_id} has {players[player_id]['lives']} lives left.))
    else
         print(f😅 玩家 {player_id} 在位置 {position} 踩到陷阱！但已經沒有命可以扣了。)
         print(f(😅 Player {player_id} stepped on a trap at position {position}! But no lives left to lose.))

    players[player_id]['position'] = START_POSITION
    print(f玩家 {player_id} 回到起點 {START_POSITION}。 (Player {player_id} returns to start {START_POSITION}.))
    time.sleep(1)


def check_player_on_new_trap(players, traps)
    檢查是否有玩家正好在新生成的陷阱上 (Check if any player is on a newly generated trap)
    trapped_players_info = [] # 記錄掉入陷阱的玩家和位置 (Record trapped players and positions)
    for player_id, data in players.items()
        # 只有未完成且生命  0 的玩家會受新陷阱影響 (Only unfinished players with lives  0 are affected by new traps)
        # 思考：生命為0的是否也該檢查？規則沒說，目前設計是不檢查 (Question Should players with 0 lives also be checked Rule didn't say, current design doesn't check)
        if not data['finished'] and data['position'] in traps and data['lives']  0
            trapped_players_info.append((player_id, data['position']))

    if trapped_players_info
        print(💥 新陷阱生成時有人中獎了！ (💥 Someone hit the jackpot when new traps were generated!))
        for player_id, position in trapped_players_info
             handle_trap_fall(player_id, players, traps, position) # 使用通用處理函數 (Use common handler)
    else
        print(😌 新陷阱生成，暫時安全。 (😌 New traps generated, safe for now.))


# --- 遊戲主邏輯 (Main Game Logic) ---

def play_game()
    開始遊戲 (Start the game)
    # 初始化玩家狀態 (Initialize player state) - 使用字典嵌套字典 (Use nested dictionary)
    players = {
        i {
            'position' START_POSITION,
            'lives' INITIAL_LIVES,
            'finished' False,
            'finish_turn' None, # 記錄完成時的回合數 (Record turn number upon finishing)
            'encounters' 0 # 記錄遭遇其他玩家的次數 (Record encounters with other players)
        }
        for i in range(1, NUM_PLAYERS + 1)
    }

    # 初始化陷阱 (Initialize traps)
    print(f正在初始設置 {INITIAL_TRAPS} 個陷阱... (Setting up {INITIAL_TRAPS} initial traps...))
    # 提供當前所有玩家的位置給陷阱生成器 (Provide all current player positions to trap generator)
    current_positions = [data['position'] for data in players.values()]
    traps = generate_traps(INITIAL_TRAPS, PATH_LENGTH, current_positions)
    print(f初始陷阱位置 (Initial trap positions) {traps})
    time.sleep(1)

    game_over = False
    finished_players_ranked = [] # 按完成順序記錄玩家 ID (Record player IDs in order of finishing)
    turn_count = 0 # 回合計數器 (Turn counter)

    while not game_over
        turn_count += 1
        print(fn--- 第 {turn_count} 回合 --- (--- Turn {turn_count} ---))
        display_board(players, traps, PATH_LENGTH, finished_players_ranked)

        # --- 檢查是否已有足夠玩家完成 (Check if enough players have finished) ---
        if len(finished_players_ranked) = FINISHERS_NEEDED
            print(fn已有 {len(finished_players_ranked)} 位玩家到達終點！遊戲結束！)
            print(f(Already {len(finished_players_ranked)} players reached the end! Game Over!))
            game_over = True
            continue # 跳過本輪剩餘部分，直接去顯示排名 (Skip rest of the turn, go to display ranking)

        # --- 選擇玩家 (Select Player) ---
        while True
            try
                active_players = [pid for pid, data in players.items() if not data['finished']]
                if not active_players # 理論上不該發生，因為上面有結束條件 (Shouldn't happen due to end condition above)
                     print(所有玩家都已完成或無法移動！遊戲提前結束。(All players finished or unable to move! Game ends early.))
                     game_over = True
                     break # 跳出選擇迴圈 (Break selection loop)

                prompt = f請選擇下一位移動的玩家 ({', '.join(map(str, active_players))})，或輸入 'quit' 結束遊戲：
                prompt += fn(Select next player ({', '.join(map(str, active_players))}) or type 'quit' to exit) 
                choice = input(prompt)

                if choice.lower() == 'quit'
                     print(好吧，下次再玩！ (Okay, play next time!))
                     game_over = True
                     # 使用 sys.exit() 可以更明確地終止程式 (Using sys.exit() terminates more explicitly)
                     # 但在這裡我們只想結束遊戲迴圈，所以設置 game_over 並 break
                     # But here we just want to end the game loop, so set game_over and break
                     break # 跳出選擇迴圈 (Break selection loop)

                player_to_move = int(choice)
                if player_to_move in players and not players[player_to_move]['finished']
                    # 檢查玩家生命值 (Check player lives) - 即使生命為0也可以被選中移動 (Can be selected even with 0 lives)
                    # if players[player_to_move]['lives'] = 0
                    #     print(f玩家 {player_to_move} 生命已耗盡，無法移動。請選擇其他玩家。)
                    #     print(f(Player {player_to_move} has no lives left and cannot move. Please choose another player.))
                    #     continue # 重新選擇 (Choose again)
                    # 上面這段註解掉了，因為規則是掉陷阱回起點，沒說不能動 (Commented out above because rule is reset to start, not immobile)
                    break # 選擇有效，跳出迴圈 (Valid choice, break the loop)
                elif player_to_move in players and players[player_to_move]['finished']
                     print(f玩家 {player_to_move} 已經到達終點了，請選擇其他未完成的玩家。)
                     print(f(Player {player_to_move} has already finished. Please choose another unfinished player.))
                else
                    print(f無效的玩家編號，請從 {active_players} 中選擇。)
                    print(f(Invalid player number. Please choose from {active_players}.))
            except ValueError
                print(請輸入數字來選擇玩家，或輸入 'quit'。 (Please enter a number to select a player, or 'quit'.))

        if game_over # 如果在選擇階段輸入 quit (If quit during selection phase)
            break # 跳出主遊戲迴圈 (Break main game loop)

        print(fn輪到玩家 {player_to_move} 移動... (Player {player_to_move}'s turn...))
        time.sleep(0.5)

        # --- 擲骰子 (Roll the Dice) ---
        dice_roll = random.randint(1, 6)
        print(f玩家 {player_to_move} 骰出了 (rolled a) {dice_roll}！)
        time.sleep(1)

        # --- 特殊處理：骰到 6 (Special Handling Rolled a 6) ---
        if dice_roll == 6
            print(骰到 6！清除所有舊陷阱！準備迎接新的「驚喜」！)
            print((Rolled a 6! Clearing all old traps! Get ready for new 'surprises'!))
            traps.clear()
            time.sleep(1)

            num_new_traps = random.randint(MIN_NEW_TRAPS, MAX_NEW_TRAPS)
            print(f正在隨機生成 {num_new_traps} 個新陷阱... (Randomly generating {num_new_traps} new traps...))
            current_positions = [data['position'] for data in players.values() if not data['finished']] # 只考慮未完成玩家的位置 (Only consider unfinished players' positions)
            traps = generate_traps(num_new_traps, PATH_LENGTH, current_positions)
            print(f新陷阱位置 (New trap positions) {traps})
            time.sleep(1)

            # 檢查是否有人「中獎」 (Check if anyone won the lottery)
            check_player_on_new_trap(players, traps) # 會處理生命值和重置 (Handles lives and reset)
            time.sleep(1)

            print(f玩家 {player_to_move} 因為忙著重置陷阱，本輪原地休息。 (Player {player_to_move} rests this turn, busy resetting traps.))

        # --- 一般移動 (Normal Movement) ---
        else
            player_data = players[player_to_move]
            current_position = player_data['position']
            target_position = current_position + dice_roll
            original_target = target_position # 記錄原始目標，用於顯示 (Record original target for display)

            print(f玩家 {player_to_move} 嘗試從 {current_position} 移動 {dice_roll} 步到 {target_position}...)
            print(f(Player {player_to_move} attempts to move {dice_roll} steps from {current_position} to {target_position}...))
            time.sleep(0.5)

            # --- 檢查是否遇到其他玩家 (Check for Encounter) ---
            bonus_step_taken = False
            # 檢查目標位置是否有其他 未完成 的玩家 (Check if target position has other unfinished players)
            encountered_players = [
                pid for pid, data in players.items()
                if pid != player_to_move and not data['finished'] and data['position'] == target_position
            ]

            if encountered_players and target_position  END_POSITION # 只有在終點前才觸發獎勵 (Only trigger bonus before the end)
                print(f🤝 玩家 {player_to_move} 在位置 {target_position} 遇到了玩家 {encountered_players}！)
                print(f(🤝 Player {player_to_move} encountered player(s) {encountered_players} at position {target_position}!))
                player_data['encounters'] += 1 # 增加遭遇計數 (Increment encounter count)
                print(f獲得額外 {ENCOUNTER_BONUS_STEP} 步獎勵！ (Gets a bonus of {ENCOUNTER_BONUS_STEP} step(s)!))
                target_position += ENCOUNTER_BONUS_STEP
                bonus_step_taken = True
                print(f新的目標位置是 (New target position is) {target_position})
                time.sleep(1)

            # --- 處理最終位置 (Process Final Position) ---
            final_position = target_position # 可能是原始目標或獎勵後的位置 (Could be original target or post-bonus position)

            # 1. 檢查是否到達終點 (Check for Finish)
            if final_position = END_POSITION
                final_position = END_POSITION # 停在終點 (Stop at the end)
                player_data['position'] = final_position
                if not player_data['finished'] # 只有第一次到達才算 (Only count the first time reaching)
                    player_data['finished'] = True
                    player_data['finish_turn'] = turn_count
                    finished_players_ranked.append(player_to_move)
                    rank = len(finished_players_ranked)
                    print(fn🏁 玩家 {player_to_move} 到達終點！成為第 {rank} 位完成者！ 🏁)
                    print(f(🏁 Player {player_to_move} reached the end! Became the {rank} finisher! 🏁))
                    time.sleep(1)
                    # 不在這裡結束遊戲，等待迴圈開頭的檢查 (Don't end game here, wait for check at loop start)
            else
                # 2. 檢查是否踩到陷阱 (Check for Trap)
                if final_position in traps
                    # 根據獎勵步調整顯示訊息 (Adjust message based on bonus step)
                    if bonus_step_taken
                         print(f玩家 {player_to_move} 從 {current_position} 移動 {dice_roll} 步，遇到玩家後又走了 {ENCOUNTER_BONUS_STEP} 步...)
                         print(f(Player {player_to_move} moved {dice_roll} steps from {current_position}, encountered player(s), then moved {ENCOUNTER_BONUS_STEP} more step(s)...))
                    handle_trap_fall(player_to_move, players, traps, final_position)
                else
                    # 3. 安全移動 (Safe Move)
                    player_data['position'] = final_position
                    # 根據獎勵步調整顯示訊息 (Adjust message based on bonus step)
                    if bonus_step_taken
                         print(f玩家 {player_to_move} 從 {current_position} 移動 {dice_roll} 步，遇到玩家後獎勵 {ENCOUNTER_BONUS_STEP} 步，安全到達 {final_position}。)
                         print(f(Player {player_to_move} moved {dice_roll} steps from {current_position}, got {ENCOUNTER_BONUS_STEP} bonus step(s) after encounter, safely arrived at {final_position}.))
                    else
                        print(f玩家 {player_to_move} 安全移動到 (safely moved to) {final_position}.)
                    time.sleep(0.5)

        print(-  20) # 分隔線 (Separator)
        time.sleep(1) # 給點時間看結果 (Allow time to see results)

    # --- 遊戲結束，顯示排名 (Game Over, Display Ranking) ---
    print(n==================== 遊戲結束 ====================)
    print((==================== GAME OVER ====================))

    if not finished_players_ranked
        print(n沒有玩家到達終點。 (No players reached the finish line.))
    else
        print(n🏆最終排名 (Final Ranking))
        for i, player_id in enumerate(finished_players_ranked)
            if i  3 # 只顯示前三名 (Only show top 3)
                player_data = players[player_id]
                print(f  第 {i+1} 名 玩家 {player_id} (在第 {player_data['finish_turn']} 回合完成，剩餘生命 {player_data['lives']}，遭遇 {player_data['encounters']} 次))
                print(f  (Rank {i+1} Player {player_id} (Finished on turn {player_data['finish_turn']}, {player_data['lives']} lives left, {player_data['encounters']} encounters)))
            else
                break # 最多顯示前三 (Show top 3 at most)

        if len(finished_players_ranked)  FINISHERS_NEEDED and len(finished_players_ranked)  0
             print(fn雖然遊戲因玩家退出而結束，但還是有 {len(finished_players_ranked)} 位玩家完成了！)
             print(f(Although the game ended due to player quit, {len(finished_players_ranked)} player(s) still finished!))


# --- 啟動遊戲 (Start the Game) ---
if __name__ == __main__
    play_game()