// 等待 HTML 文件完全載入後執行
document.addEventListener('DOMContentLoaded', function() {
    const gameBoard = document.getElementById('game-board');
    const turnCountDisplay = document.getElementById('turn-count');
    const currentPlayerDisplay = document.getElementById('current-player-display');
    const playerSelectorDropdown = document.getElementById('player-selector-dropdown');
    const diceResultDisplay = document.getElementById('dice-result-display');
    const rollDiceButton = document.getElementById('roll-dice-button');
    const resetGameButton = document.getElementById('reset-game-button');
    const playerStatusArea = document.getElementById('player-status-area');
    const messageList = document.getElementById('message-list');
    const rankingList = document.getElementById('ranking-list');

    const PATH_LENGTH_FROM_JS = 15; // 與後端設定一致

    // 函數：獲取並更新遊戲狀態
    async function fetchAndUpdateState() {
        try {
            const response = await fetch('/get_state'); // 向後端請求狀態
            if (!response.ok) throw new Error('Failed to fetch game state');
            const state = await response.json();

            console.log('Received game state:', state); // 添加除錯訊息

            updateBoard(state.players, state.traps);
            updateGameInfo(state.turn_count, state.current_player_id, state.last_dice_roll);
            updatePlayerStatus(state.players);
            updateMessageLog(state.message_log);
            updateRanking(state.finished_players_ranked, state.players);
            updatePlayerSelector(state.players, state.game_over); // 確保這行被執行

            if (state.game_over) {
                rollDiceButton.disabled = true;
                currentPlayerDisplay.textContent = "遊戲結束！";
            } else {
                rollDiceButton.disabled = false;
            }

        } catch (error) {
            console.error("Error fetching state:", error);
            messageList.innerHTML = `<li>載入遊戲狀態失敗: ${error.message}</li>`;
        }
    }

    // 函數：更新遊戲棋盤顯示
    function updateBoard(players, traps) {
        gameBoard.innerHTML = ''; // 清空舊棋盤
        // 設定棋盤格子欄數，讓它能正確排列
        gameBoard.style.gridTemplateColumns = `repeat(${PATH_LENGTH_FROM_JS}, 40px)`;


        for (let i = 0; i < PATH_LENGTH_FROM_JS; i++) {
            const square = document.createElement('div');
            square.classList.add('board-square');
            square.textContent = i; // 顯示格子編號

            // 顯示陷阱
            if (traps.includes(i)) { // 假設 traps 是一個包含位置的陣列或集合
                const trapDiv = document.createElement('div');
                trapDiv.classList.add('trap-indicator');
                trapDiv.textContent = 'T';
                square.appendChild(trapDiv);
            }

            // 顯示玩家棋子 (這裡需要更細緻的處理，例如多個玩家在同一格)
            Object.entries(players).forEach(([playerId, playerData]) => {
                if (playerData.position === i) {
                    const piece = document.createElement('div');
                    piece.classList.add('player-piece', `player-${playerId}`);
                    piece.textContent = playerId;
                    // 為了避免棋子重疊，你可能需要調整 CSS 或用更複雜的定位
                    // 簡單處理：稍微錯開
                    const numPlayersOnSquare = Object.values(players).filter(p => p.position === i).length;
                    const playerIndexOnSquare = Object.keys(players).filter(pid => players[pid].position === i).indexOf(playerId);
                    piece.style.left = `${5 + playerIndexOnSquare * 5}px`; // 簡易錯位
                    piece.style.top = `${5 + playerIndexOnSquare * 2}px`;
                    square.appendChild(piece);
                }
            });
            gameBoard.appendChild(square);
        }
    }

    // 函數：更新一般遊戲資訊
    function updateGameInfo(turn, currentPlayerId, diceResult) {
        turnCountDisplay.textContent = turn;
        currentPlayerDisplay.textContent = currentPlayerId !== null ? `玩家 ${currentPlayerId}` : '-';
        diceResultDisplay.textContent = diceResult !== null ? diceResult : '-';
    }

    // 函數：更新玩家狀態區域
    function updatePlayerStatus(players) {
        playerStatusArea.innerHTML = '<h2>玩家狀態</h2>'; // 清空舊內容並加回標題
        Object.entries(players).forEach(([playerId, data]) => {
            const p = document.createElement('p');
            let status = `玩家 ${playerId}: 位置 ${data.position}, 生命 ${data.lives}`;
            if (data.finished) {
                status += ` (已於第 ${data.finish_turn} 回合完成)`;
            }
            p.textContent = status;
            playerStatusArea.appendChild(p);
        });
    }

    // 函數：更新遊戲訊息紀錄
    function updateMessageLog(messages) {
        messageList.innerHTML = ''; // 清空舊訊息
        messages.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = msg;
            messageList.appendChild(li);
        });
        messageList.scrollTop = messageList.scrollHeight; // 自動滾動到底部
    }

    // 函數：更新排行榜
    function updateRanking(rankedIds, playersData) {
        rankingList.innerHTML = ''; // 清空舊排名
        rankedIds.forEach((playerId, index) => {
            const li = document.createElement('li');
            const player = playersData[playerId];
            li.textContent = `第 ${index + 1} 名: 玩家 ${playerId} (回合 ${player.finish_turn}, 生命 ${player.lives})`;
            rankingList.appendChild(li);
        });
    }
    //函數：下拉選單更新玩家選擇器
    function updatePlayerSelector(playersData, gameIsOver) {
        console.log('Updating player selector with:', playersData); // 添加除錯訊息
        playerSelectorDropdown.innerHTML = ''; // 清空舊選項

        if (gameIsOver) {
            playerSelectorDropdown.disabled = true;
            rollDiceButton.disabled = true; // 遊戲結束時禁用擲骰按鈕
            return;
        }

        // 添加一個預設選項
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '請選擇玩家';
        playerSelectorDropdown.appendChild(defaultOption);

        let hasActivePlayers = false;
        Object.entries(playersData).forEach(([playerId, playerData]) => {
            console.log('Processing player:', playerId, playerData); // 添加除錯訊息
            // 只顯示未完成且生命值大於 0 的玩家
            if (!playerData.finished && playerData.lives > 0) {
                const option = document.createElement('option');
                option.value = playerId;
                option.textContent = `玩家 ${playerId} (生命: ${playerData.lives})`;
                playerSelectorDropdown.appendChild(option);
                hasActivePlayers = true;
            }
        });

        console.log('Has active players:', hasActivePlayers); // 添加除錯訊息
        playerSelectorDropdown.disabled = !hasActivePlayers; // 如果沒有活躍玩家，也禁用選擇器
        rollDiceButton.disabled = !hasActivePlayers; // 同時禁用擲骰按鈕
    }

    // 統一更新 UI 的函數
    function updateUI(state) {
        updateBoard(state.players, state.traps);
        updateGameInfo(state.turn_count, state.current_player_id, state.last_dice_roll);
        updatePlayerStatus(state.players);
        updateMessageLog(state.message_log);
        updateRanking(state.finished_players_ranked, state.players);
        updatePlayerSelector(state.players, state.game_over); // 更新玩家選擇器

        if (state.game_over) {
            rollDiceButton.disabled = true;
            currentPlayerDisplay.textContent = "遊戲結束！";
            setTimeout(()=> alert("遊戲結束！請查看排行榜。"), 100);
        } else {
            rollDiceButton.disabled = false;
        }
    }

    // 事件監聽：點擊擲骰子按鈕
    rollDiceButton.addEventListener('click', async function() {
        const selectedPlayerId = playerSelectorDropdown.value; // 從下拉選單獲取選中的玩家 ID

        if (!selectedPlayerId) { // 以防萬一沒有選中任何玩家
            alert("請選擇一位玩家！(Please select a player!)");
            return;
        }

        diceResultDisplay.textContent = "擲骰中...";
        try {
            const response = await fetch('/roll_dice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ player_id: parseInt(selectedPlayerId) })
            });

            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({ message: '擲骰失敗，且無法解析錯誤回應。' }));
                 throw new Error(errorData.message || '擲骰動作失敗 (Roll dice action failed)');
            }
            const state = await response.json();
            updateUI(state);
        } catch (error) {
            console.error("Error rolling dice:", error);
            const li = document.createElement('li');
            li.textContent = error.message;
            li.style.color = 'red';
            messageList.appendChild(li);
            messageList.scrollTop = messageList.scrollHeight;
        }
    });

    // 添加玩家選擇器的變更事件監聽器
    playerSelectorDropdown.addEventListener('change', function() {
        const selectedPlayerId = this.value;
        if (selectedPlayerId) {
            currentPlayerDisplay.textContent = `玩家 ${selectedPlayerId}`;
        } else {
            currentPlayerDisplay.textContent = '-';
        }
    });

    // 事件監聽：點擊重新開始按鈕
    resetGameButton.addEventListener('click', async function() {
        if (confirm("確定要重新開始遊戲嗎？")) {
            try {
                const response = await fetch('/reset', { method: 'POST' });
                if (!response.ok) throw new Error('Reset game action failed');
                const state = await response.json();
                updateUI(state);
            } catch (error) {
                console.error("Error resetting game:", error);
                messageList.innerHTML = `<li>重置遊戲失敗: ${error.message}</li>`;
            }
        }
    });

    // 頁面初次載入時，獲取一次遊戲狀態
    fetchAndUpdateState();
});