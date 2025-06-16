// 等待 DOM 完全載入
document.addEventListener('DOMContentLoaded', () => {
    // 獲取 DOM 元素
    const playerInfoModal = document.getElementById('player-info-modal');
    const playerIdElement = document.getElementById('player-id');
    const playerNameInput = document.getElementById('player-name-input');
    const joinGameBtn = document.getElementById('join-game-btn');
    const playerInfo = document.getElementById('player-info');
    const playerList = document.getElementById('player-list');
    const gamePath = document.getElementById('game-path');
    const messageLog = document.getElementById('message-log');
    const rollDiceBtn = document.getElementById('roll-dice-btn');
    const resetGameBtn = document.getElementById('reset-game-btn');
    const resetRequestSection = document.getElementById('reset-request-section');
    const agreeResetBtn = document.getElementById('agree-reset-btn');
    const disagreeResetBtn = document.getElementById('disagree-reset-btn');

    // 遊戲狀態變數
    let playerId = null;
    let joinStep = 0;
    let resetAgreed = false;
    let resetDisagreed = false;
    let lastCurrentPlayerId = null;
    let lastGameState = null;

    // 加入遊戲按鈕點擊事件
    joinGameBtn.addEventListener('click', async () => {
        try {
            switch (joinStep) {
                case 0: // 加入遊戲
                    const joinResponse = await fetch('/join_game', {
                        method: 'POST'
                    });
                    const joinData = await joinResponse.json();
                    console.log('加入遊戲回應:', joinData);
                    if (joinData.player_id) {
                        playerId = joinData.player_id;
                        playerIdElement.textContent = `玩家 ID: ${playerId}`;
                        playerNameInput.disabled = false;
                        joinGameBtn.textContent = '確認名稱';
                        joinStep = 1;
                        updateGameState();
                    }
                    break;

                case 1: // 確認名稱
                    if (playerNameInput.value.trim()) {
                        const nameResponse = await fetch('/set_player_name', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                player_id: playerId,
                                name: playerNameInput.value.trim()
                            })
                        });
                        const nameData = await nameResponse.json();
                        console.log('設定名稱回應:', nameData);
                        if (nameData.players && nameData.players[playerId]) {
                            playerNameInput.disabled = true;
                            joinGameBtn.textContent = '準備';
                            joinStep = 2;
                            updateGameStateUI(nameData);
                        }
                    }
                    break;

                case 2: // 準備
                    const readyResponse = await fetch('/set_ready', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            player_id: playerId
                        })
                    });
                    const readyData = await readyResponse.json();
                    console.log('準備回應:', readyData);
                    if (readyData.players && readyData.players[playerId]) {
                        joinGameBtn.textContent = '取消準備';
                        joinStep = 3;
                        updateGameStateUI(readyData);
                    }
                    break;

                case 3: // 取消準備
                    const cancelResponse = await fetch('/set_ready', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            player_id: playerId
                        })
                    });
                    const cancelData = await cancelResponse.json();
                    console.log('取消準備回應:', cancelData);
                    if (cancelData.players && cancelData.players[playerId]) {
                        joinGameBtn.textContent = '準備';
                        joinStep = 2;
                        updateGameStateUI(cancelData);
                    }
                    break;
            }
        } catch (error) {
            console.error('操作失敗:', error);
        }
    });

    // 擲骰子按鈕點擊事件
    rollDiceBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/roll_dice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_id: playerId
                })
            });
            const data = await response.json();
            if (data.success) {
                updateGameState();
            }
        } catch (error) {
            console.error('擲骰子失敗:', error);
        }
    });

    // 重置遊戲按鈕點擊事件
    resetGameBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/request_reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_id: playerId
                })
            });
            const data = await response.json();
            if (data.success) {
                resetAgreed = false;
                resetDisagreed = false;
                updateGameState();
            }
        } catch (error) {
            console.error('請求重置遊戲失敗:', error);
        }
    });

    // 同意重置按鈕點擊事件
    agreeResetBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/agree_reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_id: playerId,
                    agree: true
                })
            });
            const data = await response.json();
            if (data.success) {
                resetAgreed = true;
                resetRequestSection.style.display = 'none';
                updateGameState();
            }
            } catch (error) {
            console.error('同意重置失敗:', error);
        }
    });

    // 不同意重置按鈕點擊事件
    disagreeResetBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/agree_reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    player_id: playerId,
                    agree: false
                })
            });
            const data = await response.json();
            if (data.success) {
                resetDisagreed = true;
                resetRequestSection.style.display = 'none';
                updateGameState();
            }
        } catch (error) {
            console.error('不同意重置失敗:', error);
        }
    });

    // 更新遊戲狀態
    async function updateGameState() {
        if (!playerId) {
            return; // 如果玩家還沒加入遊戲，不更新狀態
        }
        try {
            const response = await fetch('/get_state');
            const gameData = await response.json();
            console.log('收到遊戲狀態:', gameData); // 添加日誌
            if (gameData) { // 移除 success 檢查，因為後端可能沒有這個字段
                updateGameStateUI(gameData);
            }
        } catch (error) {
            console.error('更新遊戲狀態失敗:', error);
        }
    }

    // 播放陷阱音效
    function playTrapSound() {
        try {
            const audio = new Audio('/static/xm3522.wav');
            audio.volume = 0.5; // 設置音量為 50%
            const playPromise = audio.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('陷阱音效開始播放');
                }).catch(error => {
                    console.error('播放陷阱音效失敗:', error);
                });
            }
        } catch (error) {
            console.error('創建陷阱音效失敗:', error);
        }
    }

    // 更新遊戲狀態 UI
    function updateGameStateUI(gameData) {
        console.log('更新 UI，遊戲數據:', gameData); // 添加日誌

        // 更新玩家列表
        playerList.innerHTML = '';
        if (gameData.players) {
            Object.entries(gameData.players).forEach(([pid, player]) => {
                const li = document.createElement('li');
                li.textContent = `${player.name || `玩家 ${pid}`}${player.is_ready ? ' (已準備)' : ''}${pid === gameData.current_player_id ? ' (當前回合)' : ''}`;
                playerList.appendChild(li);
            });
        }

        // 更新遊戲路徑
        gamePath.innerHTML = '';
        if (gameData.path_length) {
            for (let i = 0; i < gameData.path_length; i++) {
                const cell = document.createElement('div');
                cell.className = 'path-cell';
                if (gameData.traps && gameData.traps.includes(i)) {
                    cell.classList.add('trap');
                }
                if (gameData.players) {
                    Object.entries(gameData.players).forEach(([pid, player]) => {
                        if (player.position === i) {
                            const piece = document.createElement('div');
                            piece.className = 'player-piece';
                            piece.textContent = pid;
                            cell.appendChild(piece);
                        }
                    });
                }
                if (i === gameData.current_position) {
                    cell.classList.add('current-position');
                }
                if (i === gameData.current_position && playerId === gameData.current_player_id) {
                    playTrapSound();
                }
                gamePath.appendChild(cell);
            }
        }

        // 更新訊息日誌
        messageLog.innerHTML = '';
        if (gameData.message_log) {
            gameData.message_log.slice(-10).forEach(msg => {
                const li = document.createElement('li');
                li.textContent = msg;
                messageLog.appendChild(li);
            });
        }

        // 更新按鈕狀態
        const isCurrentPlayer = gameData.current_player_id === playerId;
        const isGameStarted = gameData.game_started;
        const isGameOver = gameData.game_over;
        const isPlayerFinished = gameData.players && gameData.players[playerId]?.finished;

        if (isGameOver) {
            rollDiceBtn.disabled = true;
            rollDiceBtn.title = '遊戲已結束';
        } else if (isPlayerFinished) {
            rollDiceBtn.disabled = true;
            rollDiceBtn.title = '您已完成遊戲';
        } else if (!isGameStarted) {
            rollDiceBtn.disabled = true;
            rollDiceBtn.title = '等待遊戲開始';
        } else if (!isCurrentPlayer) {
            rollDiceBtn.disabled = true;
            rollDiceBtn.title = '等待其他玩家回合';
        } else {
            rollDiceBtn.disabled = false;
            rollDiceBtn.title = '擲骰子';
        }

        // 更新重置請求區域
        if (gameData.reset_requested && !resetAgreed && !resetDisagreed) {
            resetRequestSection.style.display = 'block';
        } else {
            resetRequestSection.style.display = 'none';
        }

        // 更新玩家資訊區域
        if (gameData.players && gameData.players[playerId]) {
            const player = gameData.players[playerId];
            playerInfo.innerHTML = `
                <p>玩家 ID: ${playerId}</p>
                <p>名稱: ${player.name || '未設定'}</p>
                <p>位置: ${player.position}</p>
                <p>生命值: ${player.lives}</p>
                <p>狀態: ${player.finished ? '已完成' : (player.is_ready ? '已準備' : '未準備')}</p>
            `;
        }

        // 更新彈窗顯示狀態
        if (isGameStarted) {
            document.body.classList.add('game-started');
            playerInfoModal.classList.add('hidden');
        } else {
            document.body.classList.remove('game-started');
            playerInfoModal.classList.remove('hidden');
        }
    }

    // 播放回合音效
    function playTurnSound() {
        try {
            const audio = new Audio('/static/y1249.wav');
            audio.volume = 0.5; // 設置音量為 50%
            const playPromise = audio.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('音效開始播放');
                }).catch(error => {
                    console.error('播放音效失敗:', error);
                });
            }
        } catch (error) {
            console.error('創建音效失敗:', error);
        }
    }

    // 檢查當前玩家
    async function checkCurrentPlayer() {
        if (!playerId) {
            return; // 如果玩家還沒加入遊戲，不檢查當前玩家
        }
        try {
            const response = await fetch('/get_current_player');
            const data = await response.json();
            console.log('當前玩家檢查:', data); // 添加日誌
            if (data.current_player_id !== lastCurrentPlayerId) {
                lastCurrentPlayerId = data.current_player_id;
                if (data.current_player_id === playerId) {
                    console.log('輪到當前玩家，播放音效');
                    playTurnSound();
                }
                updateGameState();
            }
        } catch (error) {
            console.error('檢查當前玩家失敗:', error);
        }
    }

    // 開始遊戲循環
    function startGameLoop() {
        // 每秒檢查一次當前玩家
        setInterval(checkCurrentPlayer, 1000);
        // 每秒更新一次遊戲狀態
        setInterval(updateGameState, 1000);
    }

    // 初始化
    startGameLoop();
});