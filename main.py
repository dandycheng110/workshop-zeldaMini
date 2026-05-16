import math
import random

import pyxel

# ====== 基本參數 ======
WIDTH = 256
HEIGHT = 240
TS = 16  # 每格 16x16 像素（Tile Size）
COLS = 16
ROWS = 13
HUD_H = HEIGHT - ROWS * TS  # 32px 上方狀態列
PLAY_Y = HUD_H

# ====== 顏色（Pyxel 0-15 固定調色盤）======
COL_BG = 3           # 草地綠
COL_WALL = 4         # 牆壁褐
COL_WALL_LIGHT = 15  # 牆壁亮邊
COL_WALL_DARK = 1    # 牆壁暗邊
COL_DOOR = 9         # 門 橘
COL_LINK_BODY = 11   # Link 綠衣
COL_LINK_DARK = 3
COL_SKIN = 14        # 膚色
COL_SWORD = 7        # 劍 白
COL_SWORD_EDGE = 6   # 劍邊
COL_SLIME = 11
COL_BAT = 2
COL_HEART = 8
COL_HEART_EMPTY = 5
COL_TEXT = 7
COL_HUD = 1

# ====== 地圖字元 ======
T_FLOOR = "."
T_WALL = "#"
T_ROCK = "O"   # 障礙石頭
T_DOOR_N = "n"
T_DOOR_S = "s"
T_DOOR_E = "e"
T_DOOR_W = "w"

DOOR_TILES = (T_DOOR_N, T_DOOR_S, T_DOOR_E, T_DOOR_W)


def build_room(doors: str, rocks=()) -> list[str]:
    """產生一個房間：四周是牆，依 doors 字串開門（'N','S','E','W'），rocks 是障礙石頭格子座標。"""
    grid = [[T_FLOOR] * COLS for _ in range(ROWS)]
    for c in range(COLS):
        grid[0][c] = T_WALL
        grid[ROWS - 1][c] = T_WALL
    for r in range(ROWS):
        grid[r][0] = T_WALL
        grid[r][COLS - 1] = T_WALL
    # 門開在牆的中央，每個門占 2 格寬
    if "N" in doors:
        grid[0][COLS // 2 - 1] = T_DOOR_N
        grid[0][COLS // 2] = T_DOOR_N
    if "S" in doors:
        grid[ROWS - 1][COLS // 2 - 1] = T_DOOR_S
        grid[ROWS - 1][COLS // 2] = T_DOOR_S
    if "E" in doors:
        grid[ROWS // 2 - 1][COLS - 1] = T_DOOR_E
        grid[ROWS // 2][COLS - 1] = T_DOOR_E
    if "W" in doors:
        grid[ROWS // 2 - 1][0] = T_DOOR_W
        grid[ROWS // 2][0] = T_DOOR_W
    for rx, ry in rocks:
        if 0 < rx < COLS - 1 and 0 < ry < ROWS - 1:
            grid[ry][rx] = T_ROCK
    return ["".join(r) for r in grid]


# ====== 3x3 地下城地圖 ======
# 每個房間設定：(門組合, 石頭位置)
ROOMS_CONFIG = {
    (0, 0): ("SE", [(3, 3), (4, 3), (10, 8), (11, 8)]),
    (1, 0): ("WSE", [(5, 5), (6, 5), (7, 5)]),
    (2, 0): ("SW", [(2, 2), (2, 3), (2, 4)]),
    (0, 1): ("NES", [(4, 6), (5, 6), (6, 6)]),
    (1, 1): ("NWES", [(7, 3), (8, 3), (7, 9), (8, 9)]),
    (2, 1): ("NWS", [(10, 5), (11, 5), (12, 5)]),
    (0, 2): ("NE", [(3, 8), (4, 8)]),
    (1, 2): ("NWE", []),
    (2, 2): ("NW", [(6, 4), (7, 4), (8, 4)]),
}

ROOMS = {pos: build_room(*cfg) for pos, cfg in ROOMS_CONFIG.items()}

# 每個房間的敵人配置 (種類, tx, ty)
ENEMY_CONFIG = {
    (0, 0): [("slime", 5, 5), ("slime", 8, 7)],
    (1, 0): [("bat", 7, 4), ("slime", 10, 7)],
    (2, 0): [("slime", 5, 5), ("slime", 7, 7), ("bat", 9, 3)],
    (0, 1): [("bat", 7, 5)],
    (1, 1): [("slime", 4, 4), ("slime", 11, 4), ("bat", 4, 8), ("bat", 11, 8)],
    (2, 1): [("slime", 7, 6)],
    (0, 2): [("slime", 6, 6), ("slime", 9, 6)],
    (1, 2): [("bat", 5, 5), ("bat", 10, 5), ("bat", 7, 8)],
    (2, 2): [("slime", 4, 5), ("slime", 10, 7)],
}


def rects_overlap(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)


def tile_collides(room, px, py, w=12, h=12, off_x=2, off_y=2):
    """檢查 hitbox 是否與牆或石頭重疊。px/py 為角色左上角螢幕座標（可為 float）。"""
    bx1 = int(px + off_x)
    by1 = int(py + off_y)
    bx2 = int(px + off_x + w - 1)
    by2 = int(py + off_y + h - 1)
    tx1 = max(0, bx1 // TS)
    tx2 = min(COLS - 1, bx2 // TS)
    ty1 = max(0, (by1 - PLAY_Y) // TS)
    ty2 = min(ROWS - 1, (by2 - PLAY_Y) // TS)
    for ty in range(ty1, ty2 + 1):
        for tx in range(tx1, tx2 + 1):
            t = room[ty][tx]
            if t == T_WALL or t == T_ROCK:
                return True
    return False


def wall_only_collides(room, px, py, w=12, h=12, off_x=2, off_y=2):
    """蝙蝠用：只看牆，不擋石頭。"""
    bx1 = int(px + off_x)
    by1 = int(py + off_y)
    bx2 = int(px + off_x + w - 1)
    by2 = int(py + off_y + h - 1)
    tx1 = max(0, bx1 // TS)
    tx2 = min(COLS - 1, bx2 // TS)
    ty1 = max(0, (by1 - PLAY_Y) // TS)
    ty2 = min(ROWS - 1, (by2 - PLAY_Y) // TS)
    for ty in range(ty1, ty2 + 1):
        for tx in range(tx1, tx2 + 1):
            if room[ty][tx] == T_WALL:
                return True
    return False


# ====== Link ======
DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT = 0, 1, 2, 3


class Link:
    def __init__(self):
        self.x = WIDTH // 2 - 8
        self.y = PLAY_Y + ROWS * TS // 2 - 8
        self.dir = DIR_DOWN
        self.max_hp = 6  # 3 顆心，每顆 2 半心
        self.hp = 6
        self.attack_timer = 0
        self.invuln = 0
        self.knock_dx = 0
        self.knock_dy = 0
        self.knock_timer = 0
        self.anim = 0

    @property
    def cx(self):
        return self.x + 8

    @property
    def cy(self):
        return self.y + 8

    def update(self, room, app):
        if self.invuln > 0:
            self.invuln -= 1
        if self.attack_timer > 0:
            self.attack_timer -= 1

        # 擊退中：朝擊退方向移動，期間無法操作
        if self.knock_timer > 0:
            self._move(room, self.knock_dx, self.knock_dy, app)
            self.knock_timer -= 1
            return

        dx = dy = 0
        # 攻擊中不能移動
        if self.attack_timer == 0:
            if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
                dx = -2
                self.dir = DIR_LEFT
            elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
                dx = 2
                self.dir = DIR_RIGHT
            elif pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
                dy = -2
                self.dir = DIR_UP
            elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
                dy = 2
                self.dir = DIR_DOWN

            if (
                pyxel.btnp(pyxel.KEY_SPACE)
                or pyxel.btnp(pyxel.KEY_J)
                or pyxel.btnp(pyxel.KEY_X)
            ):
                self.attack_timer = 12

        if dx or dy:
            self.anim = (self.anim + 1) % 16
            self._move(room, dx, dy, app)

    def _move(self, room, dx, dy, app):
        # 分別嘗試 X、Y 軸：避免卡牆
        nx = self.x + dx
        if not tile_collides(room, nx, self.y):
            self.x = nx
        ny = self.y + dy
        if not tile_collides(room, self.x, ny):
            self.y = ny

        # 跨房間：踩到地圖邊界外時切換到鄰房
        if self.x < 0:
            app.transit(-1, 0, new_x=WIDTH - 16 - 2, new_y=self.y)
        elif self.x > WIDTH - 16:
            app.transit(1, 0, new_x=2, new_y=self.y)
        elif self.y < PLAY_Y:
            app.transit(0, -1, new_x=self.x, new_y=PLAY_Y + ROWS * TS - 16 - 2)
        elif self.y > PLAY_Y + ROWS * TS - 16:
            app.transit(0, 1, new_x=self.x, new_y=PLAY_Y + 2)

    def sword_rect(self):
        """劍只在攻擊中段顯示，避免太強。"""
        if self.attack_timer == 0:
            return None
        if self.attack_timer > 9 or self.attack_timer < 3:
            return None
        if self.dir == DIR_UP:
            return (self.x + 4, self.y - 12, 8, 12)
        if self.dir == DIR_DOWN:
            return (self.x + 4, self.y + 16, 8, 12)
        if self.dir == DIR_LEFT:
            return (self.x - 12, self.y + 4, 12, 8)
        # DIR_RIGHT
        return (self.x + 16, self.y + 4, 12, 8)

    def take_damage(self, src_x, src_y):
        if self.invuln > 0:
            return False
        self.hp -= 1
        if self.hp < 0:
            self.hp = 0
        self.invuln = 45
        # 擊退方向：遠離傷害源（取較大軸）
        kdx = 1 if self.cx > src_x else -1
        kdy = 1 if self.cy > src_y else -1
        if abs(self.cx - src_x) > abs(self.cy - src_y):
            self.knock_dx, self.knock_dy = kdx * 3, 0
        else:
            self.knock_dx, self.knock_dy = 0, kdy * 3
        self.knock_timer = 6
        return True

    def draw(self):
        # 受傷閃爍
        if self.invuln > 0 and (self.invuln // 3) % 2 == 0:
            return
        x, y = int(self.x), int(self.y)
        # 帽子
        pyxel.rect(x + 3, y + 1, 10, 2, COL_LINK_BODY)
        pyxel.rect(x + 4, y + 0, 8, 1, COL_LINK_BODY)
        # 臉
        pyxel.rect(x + 4, y + 3, 8, 4, COL_SKIN)
        # 身體（綠衣）
        pyxel.rect(x + 3, y + 7, 10, 7, COL_LINK_BODY)
        pyxel.rect(x + 4, y + 9, 8, 2, COL_LINK_DARK)  # 腰帶陰影
        # 腳
        pyxel.rect(x + 3, y + 14, 4, 2, COL_LINK_BODY)
        pyxel.rect(x + 9, y + 14, 4, 2, COL_LINK_BODY)
        # 方向暗示（眼睛或帽簷）
        if self.dir == DIR_DOWN:
            pyxel.pset(x + 6, y + 5, 0)
            pyxel.pset(x + 9, y + 5, 0)
        elif self.dir == DIR_UP:
            # 看背面，臉被帽子蓋住
            pyxel.rect(x + 4, y + 3, 8, 3, COL_LINK_BODY)
            pyxel.rect(x + 4, y + 6, 8, 1, COL_SKIN)
        elif self.dir == DIR_LEFT:
            pyxel.pset(x + 5, y + 5, 0)
        elif self.dir == DIR_RIGHT:
            pyxel.pset(x + 10, y + 5, 0)

        # 劍
        sr = self.sword_rect()
        if sr:
            sx, sy, sw, sh = sr
            pyxel.rect(sx, sy, sw, sh, COL_SWORD)
            pyxel.rectb(sx, sy, sw, sh, COL_SWORD_EDGE)
            # 劍柄
            if self.dir in (DIR_UP, DIR_DOWN):
                hilt_y = sy + sh if self.dir == DIR_UP else sy - 2
                pyxel.rect(sx - 1, hilt_y, sw + 2, 2, COL_DOOR)
            else:
                hilt_x = sx + sw if self.dir == DIR_LEFT else sx - 2
                pyxel.rect(hilt_x, sy - 1, 2, sh + 2, COL_DOOR)


# ====== 敵人 ======
class Slime:
    """隨機遊走、撞牆轉向。"""

    def __init__(self, tx, ty):
        self.x = float(tx * TS)
        self.y = float(PLAY_Y + ty * TS)
        self.dx, self.dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.timer = random.randint(30, 80)
        self.hp = 1
        self.dead = False
        self.anim = 0
        self.speed = 0.7

    @property
    def cx(self):
        return self.x + 8

    @property
    def cy(self):
        return self.y + 8

    def update(self, room, link):
        self.anim += 1
        self.timer -= 1
        if self.timer <= 0:
            self.dx, self.dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            self.timer = random.randint(40, 100)

        nx = self.x + self.dx * self.speed
        ny = self.y + self.dy * self.speed
        moved = False
        if not tile_collides(room, nx, self.y):
            self.x = nx
            moved = True
        else:
            self.dx = -self.dx
        if not tile_collides(room, self.x, ny):
            self.y = ny
            moved = True
        else:
            self.dy = -self.dy
        # 限制在房間內（避免從門縫滑出）
        self.x = max(TS - 4, min(WIDTH - TS - 4, self.x))
        self.y = max(PLAY_Y + TS - 4, min(PLAY_Y + ROWS * TS - TS - 4, self.y))
        if not moved:
            self.timer = 0  # 重新挑方向

    def hitbox(self):
        return (self.x + 2, self.y + 4, 12, 10)

    def draw(self):
        x, y = int(self.x), int(self.y)
        bob = (self.anim // 8) % 2
        # 史萊姆水滴狀身體
        pyxel.rect(x + 2, y + 7 + bob, 12, 7 - bob, COL_SLIME)
        pyxel.rect(x + 3, y + 5 + bob, 10, 2, COL_SLIME)
        pyxel.rect(x + 5, y + 3 + bob, 6, 2, COL_SLIME)
        pyxel.rect(x + 2, y + 13, 12, 1, COL_LINK_DARK)
        # 眼睛
        pyxel.pset(x + 6, y + 8 + bob, 0)
        pyxel.pset(x + 10, y + 8 + bob, 0)
        pyxel.pset(x + 6, y + 9 + bob, 7)
        pyxel.pset(x + 10, y + 9 + bob, 7)


class Bat:
    """朝玩家飛行；可穿越石頭，但不能穿牆。"""

    def __init__(self, tx, ty):
        self.x = float(tx * TS)
        self.y = float(PLAY_Y + ty * TS)
        self.hp = 1
        self.dead = False
        self.anim = 0
        self.speed = 1.0
        # 加一點亂飛偏移避免完全直線
        self.wobble = random.uniform(0, 6.28)

    @property
    def cx(self):
        return self.x + 8

    @property
    def cy(self):
        return self.y + 8

    def update(self, room, link):
        self.anim += 1
        ddx = link.cx - self.cx
        ddy = link.cy - self.cy
        dist = max(1.0, (ddx * ddx + ddy * ddy) ** 0.5)
        # 加一個與玩家方向垂直的左右擺動
        side = math.sin((self.anim + self.wobble * 10) / 8) * 0.4
        perp_x = -ddy / dist
        perp_y = ddx / dist
        vx = self.speed * ddx / dist + perp_x * side
        vy = self.speed * ddy / dist + perp_y * side

        nx = self.x + vx
        if not wall_only_collides(room, nx, self.y):
            self.x = nx
        ny = self.y + vy
        if not wall_only_collides(room, self.x, ny):
            self.y = ny
        # 限制在房間內
        self.x = max(TS - 4, min(WIDTH - TS - 4, self.x))
        self.y = max(PLAY_Y + TS - 4, min(PLAY_Y + ROWS * TS - TS - 4, self.y))

    def hitbox(self):
        return (self.x + 2, self.y + 4, 12, 8)

    def draw(self):
        x, y = int(self.x), int(self.y)
        flap = (self.anim // 4) % 2
        # 身體
        pyxel.rect(x + 6, y + 6, 4, 6, COL_BAT)
        # 翅膀
        if flap:
            pyxel.tri(x + 2, y + 6, x + 6, y + 6, x + 4, y + 10, COL_BAT)
            pyxel.tri(x + 14, y + 6, x + 10, y + 6, x + 12, y + 10, COL_BAT)
        else:
            pyxel.tri(x + 1, y + 8, x + 6, y + 6, x + 5, y + 11, COL_BAT)
            pyxel.tri(x + 15, y + 8, x + 10, y + 6, x + 11, y + 11, COL_BAT)
        # 紅眼
        pyxel.pset(x + 7, y + 8, 8)
        pyxel.pset(x + 9, y + 8, 8)


# ====== 主程式 ======
class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Zelda Mini", fps=30)
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.state = "play"
        self.link = Link()
        self.room_pos = (0, 0)
        self.cleared: set[tuple[int, int]] = set()
        self.spawn_enemies()

    def spawn_enemies(self):
        if self.room_pos in self.cleared:
            self.enemies = []
            return
        self.enemies = []
        for kind, tx, ty in ENEMY_CONFIG.get(self.room_pos, []):
            if kind == "slime":
                self.enemies.append(Slime(tx, ty))
            elif kind == "bat":
                self.enemies.append(Bat(tx, ty))

    def current_room(self):
        return ROOMS[self.room_pos]

    def transit(self, ddx, ddy, new_x, new_y):
        new_pos = (self.room_pos[0] + ddx, self.room_pos[1] + ddy)
        if new_pos not in ROOMS:
            # 不存在的方向：把 Link 拉回房內
            self.link.x = max(2, min(WIDTH - 18, self.link.x - ddx * 6))
            self.link.y = max(
                PLAY_Y + 2,
                min(PLAY_Y + ROWS * TS - 18, self.link.y - ddy * 6),
            )
            return
        self.room_pos = new_pos
        self.link.x = new_x
        self.link.y = new_y
        self.link.knock_timer = 0
        self.spawn_enemies()

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        if self.state == "gameover" or self.state == "win":
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
                self.reset()
            return

        room = self.current_room()
        self.link.update(room, self)
        room = self.current_room()  # 可能換了房間

        for e in self.enemies:
            if not e.dead:
                e.update(room, self.link)

        # 劍打到敵人
        sr = self.link.sword_rect()
        if sr:
            for e in self.enemies:
                if not e.dead and rects_overlap(sr, e.hitbox()):
                    e.hp -= 1
                    if e.hp <= 0:
                        e.dead = True

        # 敵人撞到 Link
        link_rect = (self.link.x + 2, self.link.y + 4, 12, 11)
        for e in self.enemies:
            if not e.dead and rects_overlap(link_rect, e.hitbox()):
                if self.link.take_damage(e.cx, e.cy):
                    if self.link.hp <= 0:
                        self.state = "gameover"
                    break

        self.enemies = [e for e in self.enemies if not e.dead]

        if not self.enemies and self.room_pos not in self.cleared:
            self.cleared.add(self.room_pos)
            if len(self.cleared) >= len(ROOMS):
                self.state = "win"

    # === 繪圖 ===
    def draw(self):
        pyxel.cls(COL_BG)
        self.draw_hud()
        self.draw_room()
        for e in self.enemies:
            if not e.dead:
                e.draw()
        self.link.draw()

        if self.state == "gameover":
            self._draw_banner("GAME OVER", 8)
        elif self.state == "win":
            self._draw_banner("YOU WIN!", 10)

    def draw_hud(self):
        pyxel.rect(0, 0, WIDTH, HUD_H, COL_HUD)
        pyxel.rect(0, HUD_H - 1, WIDTH, 1, 0)
        pyxel.text(4, 4, "ZELDA - MINI DUNGEON", COL_TEXT)
        pyxel.text(4, 14, f"ROOM {self.room_pos[0]},{self.room_pos[1]}", COL_TEXT)
        pyxel.text(4, 22, "ARROWS/WASD MOVE  SPACE ATTACK  Q QUIT", 6)

        # 心 (max_hp // 2 顆)
        for i in range(self.link.max_hp // 2):
            hx = WIDTH - 80 + i * 11
            hy = 4
            full = self.link.hp - i * 2
            if full >= 2:
                self._draw_heart(hx, hy, COL_HEART, full=True)
            elif full == 1:
                self._draw_heart(hx, hy, COL_HEART_EMPTY, full=True)
                self._draw_heart_half(hx, hy, COL_HEART)
            else:
                self._draw_heart(hx, hy, COL_HEART_EMPTY, full=True)

        # 小地圖
        map_x = WIDTH - 28
        map_y = 16
        for (rx, ry) in ROOMS:
            mx = map_x + rx * 8
            my = map_y + ry * 5
            if (rx, ry) == self.room_pos:
                col = 10  # 黃 = 當前
            elif (rx, ry) in self.cleared:
                col = 11  # 綠 = 清空
            else:
                col = 5  # 灰 = 未清
            pyxel.rect(mx, my, 7, 4, col)
            pyxel.rectb(mx, my, 7, 4, 0)

    def _draw_heart(self, x, y, col, full=True):
        # 9x8 像素愛心
        pyxel.rect(x + 1, y + 1, 7, 5, col)
        pyxel.pset(x, y + 2, col)
        pyxel.pset(x, y + 3, col)
        pyxel.pset(x + 8, y + 2, col)
        pyxel.pset(x + 8, y + 3, col)
        pyxel.tri(x + 1, y + 6, x + 7, y + 6, x + 4, y + 8, col)
        # 中間切口
        pyxel.pset(x + 4, y + 1, COL_HUD)
        pyxel.pset(x + 4, y + 2, COL_HUD)

    def _draw_heart_half(self, x, y, col):
        # 畫左半邊紅
        pyxel.rect(x + 1, y + 1, 3, 5, col)
        pyxel.pset(x, y + 2, col)
        pyxel.pset(x, y + 3, col)
        pyxel.tri(x + 1, y + 6, x + 4, y + 6, x + 4, y + 8, col)

    def draw_room(self):
        room = self.current_room()
        for ty in range(ROWS):
            for tx in range(COLS):
                t = room[ty][tx]
                px = tx * TS
                py = PLAY_Y + ty * TS
                if t == T_WALL:
                    pyxel.rect(px, py, TS, TS, COL_WALL)
                    pyxel.rect(px, py, TS, 2, COL_WALL_LIGHT)
                    pyxel.rect(px, py + TS - 2, TS, 2, COL_WALL_DARK)
                    pyxel.line(px, py, px, py + TS - 1, COL_WALL_DARK)
                elif t == T_ROCK:
                    pyxel.rect(px + 2, py + 2, TS - 4, TS - 4, COL_WALL)
                    pyxel.rect(px + 2, py + 2, 2, 2, COL_WALL_LIGHT)
                    pyxel.rect(px + TS - 4, py + TS - 4, 2, 2, COL_WALL_DARK)
                elif t in DOOR_TILES:
                    # 草地保留
                    # 門框
                    if t in (T_DOOR_N, T_DOOR_S):
                        # 上下門：左右畫牆框
                        pyxel.rect(px, py, TS, 3, COL_WALL)
                        pyxel.rect(px, py + TS - 3, TS, 3, COL_WALL)
                    else:
                        pyxel.rect(px, py, 3, TS, COL_WALL)
                        pyxel.rect(px + TS - 3, py, 3, TS, COL_WALL)
                    # 門上的小裝飾
                    cx = px + TS // 2
                    cy = py + TS // 2
                    pyxel.circb(cx, cy, 2, COL_DOOR)

    def _draw_banner(self, text, col):
        w = len(text) * 4 + 24
        bx = WIDTH // 2 - w // 2
        by = HEIGHT // 2 - 14
        pyxel.rect(bx, by, w, 28, 0)
        pyxel.rectb(bx, by, w, 28, col)
        pyxel.text(bx + 12, by + 6, text, col)
        pyxel.text(bx + 6, by + 16, "PRESS ENTER", 7)


App()
