# Zelda Mini — Pyxel 版迷你薩爾達

仿照 `workshop-pacman` 架構，用 Python + [Pyxel](https://github.com/kitao/pyxel) 製作的俯視視角小型薩爾達遊戲。所有圖像皆用程式繪製，**不需要 sprite 圖檔**。

## 玩法

- 移動：方向鍵 / `WASD`
- 攻擊（揮劍）：`SPACE` / `J` / `X`
- 退出：`Q`
- 死亡或破關後：`ENTER` 重新開始

3 顆心血量，每個敵人撞到扣半顆心。劍揮中敵人造成 1 點傷害。

清光全部 9 個房間的敵人即獲勝。HUD 右側有小地圖：黃 = 當前房間、綠 = 已清空、灰 = 未清。

## 執行方式

使用 `uv`（推薦）：

```bash
cd workshop-zelda
uv sync
uv run python main.py
```

或用 pip：

```bash
cd workshop-zelda
pip install "pyxel>=2.9.2"
python main.py
```

## 程式架構

單一檔案 `main.py`，依職責分區：

| 區段 | 內容 |
| --- | --- |
| 基本參數 / 顏色 / 地圖字元 | 螢幕尺寸、調色盤索引、tile 代號 |
| `build_room`, `ROOMS_CONFIG`, `ENEMY_CONFIG` | 9 房間的牆/門/石頭與敵人配置 |
| `tile_collides`, `wall_only_collides`, `rects_overlap` | 共用碰撞偵測 |
| `Link` | 玩家：移動、揮劍、HP、無敵閃爍、擊退 |
| `Slime`, `Bat` | 兩種敵人：隨機遊走 vs. 追蹤 |
| `App` | Pyxel 主迴圈、狀態機（play / gameover / win）、跨房間切換 |

與 `workshop-pacman` 共用的觀念：

- **格子座標 + 進度模型**：Zelda 改用像素級移動（更貼近原作手感）。
- **狀態機**：`play → gameover/win → play`。
- **單一 update / draw**：所有邏輯走 `pyxel.run(self.update, self.draw)`。

## 延伸挑戰

- 加入血量道具：敵人死掉有機率掉一顆心。
- 加入「最終王」房間：(1,1) 中央房放 boss。
- 加入炸彈，可以炸開 `T_ROCK`。
- 把房間切換做成「滑動轉場」動畫（參考原版 NES Zelda）。
- 加入 `main.pyxres` sprite 圖檔，把方塊角色換成像素圖。
