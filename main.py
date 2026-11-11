import os
import json
import random
import math
import wave
import struct
from datetime import date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line

GAME_NAME = "CYBER DASH LEGENDS V6 - MERGED"
SAVE_FILE = "cyber_dash_legends_save.json"
SAVE_PATH = SAVE_FILE
PLAYER_Y = 0.17
BOSS_MAX = 150
ROAD_L, ROAD_W = .12, .76

SPEED_STAGES = [
    (0, 0.38, "EASY", 1.30),
    (200, 0.50, "MEDIUM", 1.10),
    (500, 0.65, "HARD", 0.95),
    (900, 0.82, "VERY HARD", 0.80),
    (1400, 1.00, "INSANE", 0.65),
    (2000, 1.20, "NIGHTMARE", 0.52),
    (3000, 1.45, "IMPOSSIBLE", 0.40),
]

def get_stage(score):
    stage = SPEED_STAGES[0]
    for s in SPEED_STAGES:
        if score >= s[0]:
            stage = s
    return stage

# === MERGED: MY EXPENSIVE PRICES + HIS FACE SYSTEM ===
CHARACTERS = [
    {"name": "Cyber Kid", "price": 0, "color": (.1, .9, 1, 1), "face": "normal"},
    {"name": "Neon Ninja", "price": 800, "color": (.8, .2, 1, 1), "face": "ninja"},
    {"name": "Golden Bot", "price": 2000, "color": (1, .75, .1, 1), "face": "bot"},
    {"name": "Shadow", "price": 4000, "color": (.65, .7, .85, 1), "face": "shadow"},
    {"name": "Toxic", "price": 7000, "color": (.2, 1, .35, 1), "face": "toxic"},
    {"name": "Fireball", "price": 11000, "color": (1, .25, .1, 1), "face": "fire"},
    {"name": "Valkyrie", "price": 17000, "color": (1, .9, .3, 1), "face": "crown"},
    {"name": "Glitch", "price": 25000, "color": (.9, .1, .9, 1), "face": "glitch"},
    {"name": "Quantum", "price": 38000, "color": (.1, 1, .9, 1), "face": "quantum"},
    {"name": "Apex Legend", "price": 55000, "color": (1, 1, 1, 1), "face": "apex"},
    {"name": "PHANTOM", "price": 80000, "color": (.5, 0, 1, 1), "face": "phantom"},
]

# === MERGED: MY 6 POWERS + HIS CLEAN NAMES ===
POWERUPS = {
    "shield": {"name": "Energy Shield", "price": 300, "duration": 8, "color": (.1, .8, 1, 1), "icon": "shield"},
    "magnet": {"name": "Coin Magnet", "price": 450, "duration": 10, "color": (1, .3, .3, 1), "icon": "magnet"},
    "boost": {"name": "Score Boost", "price": 600, "duration": 8, "color": (1, .85, .1, 1), "icon": "star"},
    "laser": {"name": "Lane Laser", "price": 750, "duration": 6, "color": (1, .1, .1, 1), "icon": "laser"},
    "slow": {"name": "Time Dilation", "price": 900, "duration": 7, "color": (.6, .3, 1, 1), "icon": "clock"},
    "double": {"name": "Double Coins", "price": 1000, "duration": 10, "color": (1, .75, .1, 1), "icon": "coins"},
}
POWER_KEYS = list(POWERUPS.keys())

WORLDS = [
    {"name": "NEON CITY", "sky": (.01, .02, .09, 1), "road": (.03, .04, .11, 1), "glow": (0, .9, 1, 1)},
    {"name": "LAVA ZONE", "sky": (.16, .025, .01, 1), "road": (.12, .035, .015, 1), "glow": (1, .25, .02, 1)},
    {"name": "FROZEN PLANET", "sky": (.015, .07, .16, 1), "road": (.025, .09, .16, 1), "glow": (.3, .9, 1, 1)},
    {"name": "VOID REALM", "sky": (.05, 0, .12, 1), "road": (.08, 0, .15, 1), "glow": (.7, 0, 1, 1)},
]

def lane_nx(lane):
    return ROAD_L + ROAD_W * (lane + .5) / 3

# === MERGED SAVE: HIS CLEAN SYSTEM + MY FIELDS ===
def default_save():
    return {"coins": 100, "total_coins": 100, "best_score": 0, "games_played": 0, "levels_completed": 0, "selected_character": 0, "unlocked": [0], "powerups": {k: 1 for k in POWERUPS}, "sound": True, "daily_date": "", "daily_streak": 0, "missions_claimed": [], "bosses_defeated": 0, "total_combos": 0, "best_combo": 0, "coin_pickups": 0, "jumps": 0, "dashes": 0}

def load_save():
    data = default_save()
    try:
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception:
        pass
    # HIS CLEAN UNLOCKED LOGIC
    if not isinstance(data.get("unlocked"), list):
        data["unlocked"] = [0]
    data["unlocked"] = sorted(set(i for i in data["unlocked"] if isinstance(i, int) and 0 <= i < len(CHARACTERS)) | {0})
    if not isinstance(data.get("powerups"), dict):
        data["powerups"] = {}
    for k in POWERUPS:
        try:
            data["powerups"][k] = max(0, int(data["powerups"].get(k, 0)))
        except Exception:
            data["powerups"][k] = 0
    if not isinstance(data.get("missions_claimed"), list):
        data["missions_claimed"] = []
    for k in ("coins","total_coins","best_score","games_played","levels_completed","daily_streak","bosses_defeated","total_combos","best_combo","coin_pickups","jumps","dashes"):
        try:
            data[k] = max(0, int(data.get(k, 0)))
        except Exception:
            data[k] = 0
    try:
        sel = int(data.get("selected_character", 0))
    except Exception:
        sel = 0
    data["selected_character"] = sel if sel in data["unlocked"] else 0
    data["sound"] = bool(data.get("sound", True))
    if not isinstance(data.get("daily_date"), str):
        data["daily_date"] = ""
    return data

def save_data(data):
    try:
        temp = SAVE_PATH + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(temp, SAVE_PATH)
    except Exception as e:
        print("Save error:", e)

def make_label(text, size=18, color=(1, 1, 1, 1), bold=False):
    return Label(text=text, font_size=dp(size), color=color, bold=bold, halign="center", valign="middle")

def make_button(text, callback, color=(.05, .55, .85, 1), height=dp(52)):
    btn = Button(text=text, size_hint_y=None, height=height, font_size=dp(16), bold=True, background_normal="", background_down="", background_color=color, color=(1, 1, 1, 1))
    btn.bind(on_release=lambda *_: callback())
    return btn

# === CHARACTER FACES - MERGED, CANVAS ONLY, NO LEAK ===
class CharacterPreview(Widget):
    def __init__(self, char, **kwargs):
        super().__init__(**kwargs)
        self.char = char
        self.color = char["color"]
        self.size_hint = (None, None)
        self.size = (dp(60), dp(60))
        self.bind(pos=self.draw, size=self.draw)
        self.draw()
    def draw(self, *_):
        self.canvas.clear()
        if self.width <= 0:
            return
        cx, cy = self.center_x, self.center_y
        col = self.color
        face = self.char.get("face", "normal")
        with self.canvas:
            Color(*col[:3], .25)
            Ellipse(pos=(cx - dp(29), cy - dp(29)), size=(dp(58), dp(58)))
            Color(*col)
            RoundedRectangle(pos=(cx - dp(18), cy - dp(22)), size=(dp(36), dp(46)), radius=[dp(10)])
            # Visor base
            Color(.025, .035, .09, 1)
            RoundedRectangle(pos=(cx - dp(16), cy - dp(2)), size=(dp(32), dp(16)), radius=[dp(5)])
            if face == "ninja":
                Color(1, 1, 1, 1)
                Ellipse(pos=(cx - dp(10), cy + dp(3)), size=(dp(6), dp(6)))
                Ellipse(pos=(cx + dp(4), cy + dp(3)), size=(dp(6), dp(6)))
            elif face == "bot":
                Color(.1, .1, .1, 1)
                Rectangle(pos=(cx - dp(12), cy), size=(dp(10), dp(10)))
                Rectangle(pos=(cx + dp(2), cy), size=(dp(10), dp(10)))
                Color(1, 1, .2, 1)
                Ellipse(pos=(cx - dp(9), cy + dp(3)), size=(dp(4), dp(4)))
                Ellipse(pos=(cx + dp(5), cy + dp(3)), size=(dp(4), dp(4)))
            elif face in ("shadow", "phantom"):
                Color(1, .1, 1, 1)
                Ellipse(pos=(cx - dp(10), cy + dp(3)), size=(dp(7), dp(7)))
                Ellipse(pos=(cx + dp(3), cy + dp(3)), size=(dp(7), dp(7)))
            elif face == "fire":
                Color(1, .9, .1, 1)
                Ellipse(pos=(cx - dp(10), cy + dp(3)), size=(dp(7), dp(7)))
                Ellipse(pos=(cx + dp(3), cy + dp(3)), size=(dp(7), dp(7)))
            elif face in ("crown", "quantum", "apex"):
                Color(1, .85, .1, 1)
                Line(points=[cx - dp(12), cy + dp(18), cx - dp(6), cy + dp(24), cx, cy + dp(18), cx + dp(6), cy + dp(24), cx + dp(12), cy + dp(18)], width=dp(2.5))
                Color(.02, .04, .1, 1)
                Ellipse(pos=(cx - dp(10), cy + dp(3)), size=(dp(6), dp(6)))
                Ellipse(pos=(cx + dp(4), cy + dp(3)), size=(dp(6), dp(6)))
            elif face == "toxic":
                Color(.3, 1, .1, 1)
                Ellipse(pos=(cx - dp(10), cy + dp(3)), size=(dp(7), dp(7)))
                Ellipse(pos=(cx + dp(3), cy + dp(3)), size=(dp(7), dp(7)))
            elif face == "glitch":
                Color(1, .1, .8, 1)
                Rectangle(pos=(cx - dp(14), cy), size=(dp(10), dp(8)))
                Color(.1, 1, 1, 1)
                Rectangle(pos=(cx + dp(4), cy + dp(3)), size=(dp(10), dp(5)))
            else:
                Color(.1, .9, 1, 1)
                Ellipse(pos=(cx - dp(10), cy + dp(3)), size=(dp(7), dp(7)))
                Ellipse(pos=(cx + dp(3), cy + dp(3)), size=(dp(7), dp(7)))

class PowerPreview(Widget):
    def __init__(self, power_key, **kwargs):
        super().__init__(**kwargs)
        self.key = power_key
        self.p = POWERUPS[power_key]
        self.size_hint = (None, None)
        self.size = (dp(60), dp(60))
        self.bind(pos=self.draw, size=self.draw)
        self.draw()
    def draw(self, *_):
        self.canvas.clear()
        if self.width <= 0:
            return
        cx, cy = self.center_x, self.center_y
        col = self.p["color"]
        with self.canvas:
            Color(*col[:3], .25)
            Ellipse(pos=(cx - dp(29), cy - dp(29)), size=(dp(58), dp(58)))
            Color(*col)
            icon = self.p["icon"]
            if icon == "shield":
                Line(points=[cx, cy + dp(20), cx + dp(16), cy + dp(12), cx + dp(16), cy - dp(8), cx, cy - dp(20), cx - dp(16), cy - dp(8), cx - dp(16), cy + dp(12), cx, cy + dp(20)], width=dp(3), close=True)
                Color(1, 1, 1, 1)
                Ellipse(pos=(cx - dp(4), cy - dp(4)), size=(dp(8), dp(8)))
            elif icon == "magnet":
                Line(points=[cx - dp(14), cy + dp(15), cx - dp(14), cy - dp(5), cx, cy - dp(18), cx + dp(14), cy - dp(5), cx + dp(14), cy + dp(15)], width=dp(7))
                Color(1, 1, 1, 1)
                Rectangle(pos=(cx - dp(18), cy + dp(10)), size=(dp(8), dp(8)))
                Rectangle(pos=(cx + dp(10), cy + dp(10)), size=(dp(8), dp(8)))
            elif icon == "star":
                Line(points=[cx, cy + dp(20), cx + dp(6), cy + dp(6), cx + dp(20), cy + dp(5), cx + dp(9), cy - dp(6), cx + dp(12), cy - dp(20), cx, cy - dp(11), cx - dp(12), cy - dp(20), cx - dp(9), cy - dp(6), cx - dp(20), cy + dp(5), cx - dp(6), cy + dp(6), cx, cy + dp(20)], width=dp(2.5), close=True)
            elif icon == "laser":
                Line(points=[cx - dp(18), cy, cx + dp(18), cy], width=dp(6))
                Color(1, 1, 1, 1)
                Ellipse(pos=(cx - dp(5), cy - dp(5)), size=(dp(10), dp(10)))
                Line(points=[cx, cy - dp(20), cx, cy + dp(20)], width=dp(2))
            elif icon == "clock":
                Line(circle=(cx, cy, dp(18)), width=dp(3))
                Line(points=[cx, cy, cx, cy + dp(12)], width=dp(3))
                Line(points=[cx, cy, cx + dp(10), cy], width=dp(3))
            elif icon == "coins":
                Ellipse(pos=(cx - dp(18), cy - dp(12)), size=(dp(24), dp(24)))
                Color(1, .9, .3, 1)
                Ellipse(pos=(cx - dp(6), cy - dp(12)), size=(dp(24), dp(24)))
                Color(.6, .4, 0, 1)
                Ellipse(pos=(cx - dp(1), cy - dp(6)), size=(dp(14), dp(12)))

class GameField(Widget):
    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.bind(pos=self.redraw, size=self.redraw)
    def lane_x(self, lane):
        return self.x + self.width * lane_nx(lane)
    def redraw(self, *_):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return
        g = self.game
        w, h = self.width, self.height
        ox, oy = self.x, self.y
        world = WORLDS[g.world_index]
        with self.canvas:
            Color(*world["sky"])
            Rectangle(pos=self.pos, size=self.size)
            Color(*world["road"])
            Rectangle(pos=(ox + w * ROAD_L, oy), size=(w * ROAD_W, h))
            Color(*world["glow"])
            for edge in (ROAD_L, ROAD_L + ROAD_W):
                Line(points=[ox + w * edge, oy, ox + w * edge, oy + h], width=dp(2))
            Color(.2, .55, .8, .55)
            for i in (1, 2):
                x = ox + w * (ROAD_L + ROAD_W * i / 3)
                Line(points=[x, oy, x, oy + h], dash_length=dp(14), dash_offset=dp(10), width=dp(1))
            Color(*world["glow"][:3], .22)
            for i in range(14):
                yy = oy + ((i * .1 - g.road_offset) % 1) * h
                Line(points=[ox + w * (ROAD_L + .02), yy, ox + w * (ROAD_L + ROAD_W - .02), yy], width=dp(1))
            for p in g.particles:
                Color(p["color"][0], p["color"][1], p["color"][2], max(0, p["alpha"]))
                s = dp(p["size"])
                Ellipse(pos=(ox + p["x"] * w - s, oy + p["y"] * h - s), size=(s * 2, s * 2))
            for item in g.items:
                cx = self.lane_x(item["lane"])
                cy = oy + item["y"] * h
                t = item["type"]
                if t == "coin":
                    Color(1, .82, .05, 1)
                    Ellipse(pos=(cx - dp(12), cy - dp(12)), size=(dp(24), dp(24)))
                    Color(1, 1, .8, 1)
                    Ellipse(pos=(cx - dp(5), cy - dp(5)), size=(dp(10), dp(10)))
                elif t == "power":
                    Color(.1, 1, .75, 1)
                    RoundedRectangle(pos=(cx - dp(14), cy - dp(14)), size=(dp(28), dp(28)), radius=[dp(6)])
                    Color(1, 1, 1, 1)
                    Line(rectangle=(cx - dp(14), cy - dp(14), dp(28), dp(28)), width=dp(1.5))
                elif t == "obstacle":
                    Color(1, .12, .18, 1)
                    RoundedRectangle(pos=(cx - dp(20), cy - dp(20)), size=(dp(40), dp(40)), radius=[dp(7)])
                    Color(1, .65, .1, 1)
                    Line(rectangle=(cx - dp(20), cy - dp(20), dp(40), dp(40)), width=dp(2))
                elif t == "boss_projectile":
                    Color(1, .1, .9, 1)
                    Ellipse(pos=(cx - dp(15), cy - dp(15)), size=(dp(30), dp(30)))
                    Color(1, .8, 1, 1)
                    Ellipse(pos=(cx - dp(6), cy - dp(6)), size=(dp(12), dp(12)))
            if g.boss_active:
                bx, by = ox + w * .5, oy + h * .82
                Color(.8, .04, .12, 1)
                RoundedRectangle(pos=(bx - dp(55), by - dp(28)), size=(dp(110), dp(56)), radius=[dp(12)])
                Color(1, .9, .1, 1)
                Ellipse(pos=(bx - dp(26), by - dp(7)), size=(dp(13), dp(13)))
                Ellipse(pos=(bx + dp(13), by - dp(7)), size=(dp(13), dp(13)))
                Color(.2, .02, .02, 1)
                Rectangle(pos=(ox + w * .2, oy + h * .91), size=(w * .6, dp(12)))
                Color(1, .08, .12, 1)
                Rectangle(pos=(ox + w * .2, oy + h * .91), size=(w * .6 * max(0, g.boss_health / BOSS_MAX), dp(12)))
            px, py = self.lane_x(g.player_lane), oy + (PLAYER_Y + g.jump_y) * h
            char = CHARACTERS[g.data["selected_character"]]
            if g.dash_timer > 0:
                Color(1, .9, .1, .5)
                Ellipse(pos=(px - dp(35), py - dp(35)), size=(dp(70), dp(70)))
            Color(*char["color"][:3], .25)
            Ellipse(pos=(px - dp(29), py - dp(29)), size=(dp(58), dp(58)))
            Color(*char["color"])
            RoundedRectangle(pos=(px - dp(18), py - dp(22)), size=(dp(36), dp(46)), radius=[dp(10)])
            Color(.02, .04, .1, 1)
            Ellipse(pos=(px - dp(10), py + dp(4)), size=(dp(6), dp(6)))
            Ellipse(pos=(px + dp(4), py + dp(4)), size=(dp(6), dp(6)))
            if g.power_timer["shield"] > 0:
                Color(.1, .8, 1, .7)
                Line(circle=(px, py, dp(33)), width=dp(3))
            if g.power_timer["magnet"] > 0:
                Color(.2, 1, .7, .5)
                Line(circle=(px, py, dp(43)), width=dp(2))
            if g.power_timer["laser"] > 0:
                Color(1, .1, .1, .8)
                Line(points=[px, py, px, oy + h], width=dp(4))
            if g.power_timer.get("double", 0) > 0:
                Color(1, .85, .1, .8)
                Line(circle=(px, py, dp(38)), width=dp(2))

class GameScreen(FloatLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.data = app.data
        self.running = False
        self.paused = False
        self.player_lane = 1
        self.score = 0.0
        self.run_coins = 0
        self.speed = .38
        self.current_stage = "EASY"
        self.spawn_timer = .7
        self.road_offset = 0
        self.level = 1
        self.combo = 0
        self.best_run_combo = 0
        self.combo_timer = 0
        self.world_index = 0
        self.boss_active = False
        self.boss_health = BOSS_MAX
        self.boss_timer = 0
        self.boss_pattern = 0
        self.items = []
        self.particles = []
        self.power_timer = {k: 0 for k in POWERUPS}
        self.sel_power = 0
        self.save_timer = 0
        self.last_touch = None
        self._event = None
        self._banner_event = None
        self.jump_y = 0
        self.jump_vel = 0
        self.is_jumping = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.field = GameField(self, size_hint=(1, 1))
        self.add_widget(self.field)
        self.hud = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(54), pos_hint={"top": 1}, padding=dp(5), spacing=dp(3))
        self.score_label = make_label("SCORE: 0", 11, (.2, .95, 1, 1), True)
        self.coin_label = make_label("COINS: 0", 11, (1, .85, .1, 1), True)
        self.level_label = make_label("LVL: 1", 11, (.8, .3, 1, 1), True)
        self.stage_label = make_label("EASY", 11, (.3, 1, .5, 1), True)
        pause_btn = make_button("||", self.pause_game, (.8, .12, .2, 1), dp(48))
        pause_btn.size_hint_x = None
        pause_btn.width = dp(48)
        for wdg in (self.score_label, self.coin_label, self.level_label, self.stage_label, pause_btn):
            self.hud.add_widget(wdg)
        self.add_widget(self.hud)
        self.status = make_label("", 12, (.6, 1, .9, 1), True)
        self.status.size_hint = (1, None)
        self.status.height = dp(24)
        self.status.pos_hint = {"center_x": .5, "top": .93}
        self.add_widget(self.status)
        self.banner = make_label("", 22, (1, 1, 1, 1), True)
        self.banner.size_hint = (1, None)
        self.banner.height = dp(55)
        self.banner.pos_hint = {"center_x": .5, "center_y": .65}
        self.add_widget(self.banner)
        controls = BoxLayout(size_hint=(.98, None), height=dp(58), pos_hint={"center_x": .5, "y": .015}, spacing=dp(5))
        self.use_btn = make_button("USE", self.use_powerup, (.05, .55, .3, .95))
        self.use_btn.size_hint_y = 1
        self.dash_btn = make_button("DASH", self.do_dash, (1, .6, 0, .95))
        self.dash_btn.size_hint_y = 1
        jump_btn = make_button("JUMP", self.do_jump, (.6, .1, .9, .95))
        jump_btn.size_hint_y = 1
        cycle_btn = make_button("NEXT", self.cycle_power, (.3, .3, .55, .95))
        cycle_btn.size_hint_x = .55
        controls.add_widget(make_button("<", self.move_left, (.05, .3, .7, .9)))
        controls.add_widget(jump_btn)
        controls.add_widget(self.dash_btn)
        controls.add_widget(self.use_btn)
        controls.add_widget(cycle_btn)
        controls.add_widget(make_button(">", self.move_right, (.05, .3, .7, .9)))
        self.add_widget(controls)
        self.start_game()
    def start_game(self):
        if self._event is not None:
            self._event.cancel()
        self.running = True
        self.paused = False
        self.player_lane = 1
        self.score = 0.0
        self.run_coins = 0
        self.speed = .38
        self.current_stage = "EASY"
        self.spawn_timer = 1.3
        self.level = 1
        self.combo = 0
        self.best_run_combo = 0
        self.combo_timer = 0
        self.world_index = 0
        self.boss_active = False
        self.boss_health = BOSS_MAX
        self.items = []
        self.particles = []
        self.power_timer = {k: 0 for k in POWERUPS}
        self.banner.text = ""
        self.jump_y = 0; self.jump_vel = 0; self.is_jumping = False
        self.dash_timer = 0; self.dash_cooldown = 0
        self.update_hud()
        self.app.play_sound("bgm")
        self.show_banner("EASY MODE - GO!", 1.5)
        self._event = Clock.schedule_interval(self.update, 1 / 60)
    def stop_loop(self):
        self.running = False
        if self._event is not None:
            self._event.cancel()
            self._event = None
        if self._banner_event is not None:
            self._banner_event.cancel()
            self._banner_event = None
    def show_banner(self, text, seconds=1.8):
        if self._banner_event is not None:
            self._banner_event.cancel()
        self.banner.text = text
        self._banner_event = Clock.schedule_once(lambda *_: setattr(self.banner, "text", ""), seconds)
    def update_hud(self):
        self.score_label.text = f"SCORE: {int(self.score)}"
        self.coin_label.text = f"COINS: {self.run_coins}"
        self.level_label.text = f"LVL: {self.level}"
        self.stage_label.text = self.current_stage
        key = POWER_KEYS[self.sel_power]
        owned = self.data["powerups"].get(key, 0)
        self.use_btn.text = f"USE {POWERUPS[key]['name'].split()[-1].upper()} x{owned}"
        if self.dash_cooldown > 0:
            self.dash_btn.text = f"DASH {self.dash_cooldown:.0f}s"
        else:
            self.dash_btn.text = "DASH!"
        active = [f"{POWERUPS[k]['name']} {self.power_timer[k]:.0f}s" for k in POWER_KEYS if self.power_timer[k] > 0]
        combo = f"COMBO x{self.combo}  " if self.combo >= 3 else ""
        jump_txt = "AIR! " if self.is_jumping else ""
        dash_txt = "DASHING! " if self.dash_timer > 0 else ""
        self.status.text = jump_txt + dash_txt + combo + "  |  ".join(active)
    def move_left(self):
        if self.running and not self.paused:
            self.player_lane = max(0, self.player_lane - 1)
            self.add_particles(self.player_lane, PLAYER_Y + self.jump_y, (.1, .9, 1), 7)
    def move_right(self):
        if self.running and not self.paused:
            self.player_lane = min(2, self.player_lane + 1)
            self.add_particles(self.player_lane, PLAYER_Y + self.jump_y, (.1, .9, 1), 7)
    def do_jump(self):
        if not self.running or self.paused or self.is_jumping:
            return
        self.is_jumping = True
        self.jump_vel = 1.1
        self.data["jumps"] = self.data.get("jumps", 0) + 1
        self.app.play_sound("powerup")
    def do_dash(self):
        if not self.running or self.paused or self.dash_cooldown > 0:
            return
        self.dash_timer = 0.8
        self.dash_cooldown = 3.0
        self.data["dashes"] = self.data.get("dashes", 0) + 1
        self.app.play_sound("hit")
        self.show_banner("DASH!", 0.6)
    def cycle_power(self):
        self.sel_power = (self.sel_power + 1) % len(POWER_KEYS)
        self.update_hud()
    def use_powerup(self):
        if not self.running or self.paused:
            return
        key = POWER_KEYS[self.sel_power]
        if self.data["powerups"].get(key, 0) <= 0:
            self.show_banner(f"NO {POWERUPS[key]['name'].upper()} LEFT!", 1.2)
            return
        self.data["powerups"][key] -= 1
        self.power_timer[key] = POWERUPS[key]["duration"]
        self.app.play_sound("powerup")
        self.show_banner(POWERUPS[key]["name"] + " ACTIVATED!", 1.3)
        save_data(self.data)
        self.update_hud()
    def on_touch_down(self, touch):
        if self.running and not self.paused and self.y + dp(90) < touch.y < self.top - dp(60):
            self.last_touch = touch.pos
        else:
            self.last_touch = None
        return super().on_touch_down(touch)
    def on_touch_up(self, touch):
        if self.running and not self.paused and self.last_touch:
            dx = touch.x - self.last_touch[0]
            dy = touch.y - self.last_touch[1]
            if abs(dy) > dp(40) and dy > 0 and abs(dy) > abs(dx):
                self.do_jump()
            elif abs(dx) > dp(30) and abs(dx) > abs(dy):
                self.move_left() if dx < 0 else self.move_right()
            elif abs(dx) < dp(20) and abs(dy) < dp(20):
                self.move_left() if touch.x < self.center_x else self.move_right()
        self.last_touch = None
        return super().on_touch_up(touch)
    def add_particles(self, lane, y, color, count=6):
        for _ in range(count):
            self.particles.append({"x": lane_nx(lane) + random.uniform(-.04, .04), "y": y + random.uniform(-.03, .03), "vx": random.uniform(-.2, .2), "vy": random.uniform(.1, .4), "color": color, "alpha": 1, "size": random.uniform(3, 7)})
    def _add(self, kind, lane, y=1.05):
        self.items.append({"type": kind, "lane": lane, "y": y, "collected": False})
    def spawn_wave(self):
        if self.boss_active:
            return
        lane = random.randint(0, 2)
        roll = random.random()
        if self.current_stage in ("INSANE", "NIGHTMARE", "IMPOSSIBLE"):
            if roll < .25:
                self._add("coin", lane)
            elif roll < .35:
                self._add("power", lane)
            else:
                lanes = [0, 1, 2]
                random.shuffle(lanes)
                blocked = 2 if random.random() < .6 else 1
                for l in lanes[:blocked]:
                    self._add("obstacle", l)
                if random.random() < .4:
                    self._add("coin", lanes[-1])
            return
        if roll < .38:
            for i in range(random.randint(1, 3)):
                self._add("coin", lane, 1.05 + i * .09)
        elif roll < .48:
            self._add("power", lane)
        else:
            lanes = [0, 1, 2]
            random.shuffle(lanes)
            blocked = 2 if (self.level >= 3 and random.random() < .35) else 1
            for l in lanes[:blocked]:
                self._add("obstacle", l)
            if random.random() < .55:
                self._add("coin", lanes[-1])
    def update(self, dt):
        if not self.running or self.paused:
            return
        dt = min(dt, .05)
        ts = .5 if self.power_timer["slow"] > 0 else 1
        mult = 2 if self.power_timer["boost"] > 0 else 1
        if self.is_jumping:
            self.jump_y += self.jump_vel * dt * 1.2
            self.jump_vel -= 3.5 * dt
            if self.jump_y <= 0:
                self.jump_y = 0; self.is_jumping = False; self.jump_vel = 0
        if self.dash_timer > 0:
            self.dash_timer -= dt
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt
        self.road_offset = (self.road_offset + self.speed * dt * ts * .6) % 1
        self.score += dt * 12 * mult
        self.combo_timer -= dt
        if self.combo_timer <= 0:
            self.combo = 0
        new_level = 1 + int(self.score) // 400
        if new_level != self.level:
            self.level = new_level
            new_world = min(len(WORLDS) - 1, (self.level - 1) // 3)
            if new_world != self.world_index:
                self.world_index = new_world
                self.show_banner("NEW WORLD: " + WORLDS[new_world]["name"], 2)
            else:
                self.show_banner(f"LEVEL {self.level}!", 1.5)
            if self.level % 5 == 0:
                self.trigger_boss()
        min_score, new_speed, new_stage, base_spawn = get_stage(self.score)
        if new_stage != self.current_stage:
            self.current_stage = new_stage
            self.speed = new_speed
            self.show_banner(f"{new_stage} MODE! SPEED UP!", 2.2)
            self.app.play_sound("win")
        else:
            self.speed = new_speed
        for k in self.power_timer:
            self.power_timer[k] = max(0, self.power_timer[k] - dt)
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["alpha"] -= dt * 2.5
        self.particles = [p for p in self.particles if p["alpha"] > 0]
        self.spawn_timer -= dt * ts
        if self.spawn_timer <= 0 and not self.boss_active:
            self.spawn_wave()
            _, _, _, base_spawn = get_stage(self.score)
            self.spawn_timer = base_spawn
        if self.boss_active:
            self.boss_timer -= dt
            if self.boss_timer <= 0:
                self.boss_timer = 1.0
                self.boss_pattern = (self.boss_pattern + 1) % 2
                if self.boss_pattern == 0:
                    for l in [0,1,2]:
                        self._add("boss_projectile", l, .9)
                else:
                    l = random.randint(0,2)
                    self._add("boss_projectile", l, .9)
                    self._add("boss_projectile", l, 1.05)
            if self.power_timer["laser"] > 0:
                self.damage_boss(dt * 30)
        for item in list(self.items):
            item["y"] -= self.speed * dt * ts
            if self.power_timer["magnet"] > 0 and item["type"] == "coin" and abs(item["y"] - PLAYER_Y) < .25:
                if item["lane"] < self.player_lane:
                    item["lane"] += 1
                elif item["lane"] > self.player_lane:
                    item["lane"] -= 1
            if item["type"] == "boss_projectile" and not item["collected"] and not item.get("dodged") and item["y"] < PLAYER_Y - .1:
                item["dodged"] = True
                self.add_particles(item["lane"], PLAYER_Y, (1, .1, .9), 8)
                self.damage_boss(10)
                if not self.running:
                    return
            is_air = self.jump_y > 0.06
            hit = not item["collected"] and item["lane"] == self.player_lane and abs(item["y"] - PLAYER_Y) < .08
            if not hit:
                continue
            item["collected"] = True
            if item["type"] == "coin":
                self.combo += 1
                self.best_run_combo = max(self.best_run_combo, self.combo)
                self.combo_timer = 2.5
                reward = min(5, 1 + self.combo // 10)
                if self.power_timer.get("double", 0) > 0:
                    reward *= 2
                self.run_coins += reward
                self.data["coins"] += reward
                self.data["total_coins"] += reward
                self.data["total_combos"] += 1
                self.data["coin_pickups"] = self.data.get("coin_pickups", 0) + 1
                self.app.play_sound("coin")
                self.add_particles(self.player_lane, PLAYER_Y, (1, .8, .1), 10)
            elif item["type"] == "power":
                key = random.choice(POWER_KEYS)
                self.power_timer[key] = POWERUPS[key]["duration"]
                self.app.play_sound("powerup")
                self.show_banner(POWERUPS[key]["name"] + "!", 1.3)
            else:
                if is_air and item["type"] == "obstacle":
                    self.score += 15
                    self.show_banner("NICE JUMP! +15", 0.8)
                    continue
                if self.dash_timer > 0:
                    self.score += 20
                    self.show_banner("DASH THROUGH! +20", 0.8)
                    continue
                if self.power_timer["shield"] > 0:
                    self.power_timer["shield"] = 0
                    self.app.play_sound("hit")
                    self.add_particles(self.player_lane, PLAYER_Y, (.1, .8, 1), 14)
                elif item["type"] == "obstacle" and self.power_timer["laser"] > 0:
                    self.score += 10
                    self.add_particles(self.player_lane, PLAYER_Y, (1, .3, .2), 14)
                else:
                    self.app.play_sound("crash")
                    self.end_game()
                    return
        self.items = [i for i in self.items if i["y"] > -.15 and not i["collected"]]
        self.save_timer += dt
        if self.save_timer > 5:
            self.save_timer = 0
            save_data(self.data)
        self.update_hud()
        self.field.redraw()
    def trigger_boss(self):
        if self.boss_active:
            return
        self.boss_active = True
        self.boss_health = BOSS_MAX
        self.boss_timer = 1.5
        self.boss_pattern = 0
        self.items = [i for i in self.items if i["type"] == "coin"]
        self.show_banner("BOSS TIME!", 2.5)
    def damage_boss(self, amount):
        if not self.boss_active:
            return
        self.boss_health -= amount
        if self.boss_health <= 0:
            self.defeat_boss()
    def defeat_boss(self):
        self.boss_active = False
        self.items = [i for i in self.items if i["type"] == "coin"]
        self.spawn_timer = 1.2
        reward = 50 + 10 * (self.level // 5)
        if self.power_timer.get("double", 0) > 0:
            reward *= 2
        self.data["levels_completed"] += 1
        self.data["bosses_defeated"] += 1
        self.run_coins += reward
        self.data["coins"] += reward
        self.data["total_coins"] += reward
        self.score += 100
        self.app.play_sound("win")
        self.show_banner(f"BOSS DEFEATED! +{reward} COINS", 2.2)
        save_data(self.data)
    def pause_game(self):
        if not self.running:
            return
        self.paused = True
        self.app.stop_music()
        save_data(self.data)
        self.app.show_pause(self)
    def resume_game(self):
        self.paused = False
        self.app.play_music()
    def end_game(self):
        if not self.running:
            return
        self.stop_loop()
        final = int(self.score)
        new_best = final > self.data["best_score"]
        self.data["games_played"] += 1
        if new_best:
            self.data["best_score"] = final
        self.data["best_combo"] = max(self.data.get("best_combo", 0), self.best_run_combo)
        save_data(self.data)
        self.app.show_game_over(final, self.run_coins, new_best)

class CyberDashLegendsApp(App):
    def build(self):
        global SAVE_PATH
        self.title = GAME_NAME
        SAVE_PATH = os.path.join(self.user_data_dir, SAVE_FILE)
        self.data = load_save()
        Window.clearcolor = (.01, .015, .06, 1)
        Window.bind(on_key_down=self.on_keyboard)
        self.root_box = FloatLayout()
        self.game = None
        self.sounds = {}
        self.init_sounds()
        self.show_menu()
        return self.root_box
    def on_pause(self):
        save_data(self.data)
        if self.game and self.game.running and not self.game.paused:
            self.game.pause_game()
        return True
    def on_resume(self):
        pass
    def on_stop(self):
        save_data(self.data)
    def init_sounds(self):
        self.sounds = {}
        try:
            folder = os.path.join(self.user_data_dir, "sounds")
            os.makedirs(folder, exist_ok=True)
            self.make_wav(os.path.join(folder, "coin.wav"), 950, 0.15, "coin")
            self.make_wav(os.path.join(folder, "powerup.wav"), 600, 0.25, "beep")
            self.make_wav(os.path.join(folder, "hit.wav"), 300, 0.15, "beep")
            self.make_wav(os.path.join(folder, "crash.wav"), 100, 0.4, "crash")
            self.make_wav(os.path.join(folder, "win.wav"), 500, 0.5, "win")
            self.make_bgm_wav(os.path.join(folder, "bgm.wav"))
            files = {"coin": os.path.join(folder, "coin.wav"), "powerup": os.path.join(folder, "powerup.wav"), "hit": os.path.join(folder, "hit.wav"), "crash": os.path.join(folder, "crash.wav"), "win": os.path.join(folder, "win.wav"), "bgm": os.path.join(folder, "bgm.wav")}
            for key, path in files.items():
                try:
                    s = SoundLoader.load(path)
                    if s:
                        if key == "bgm":
                            s.loop = True
                        self.sounds[key] = s
                except Exception:
                    pass
        except Exception:
            pass
    def make_wav(self, path, freq, duration, kind):
        try:
            rate = 22050
            n = int(rate * duration)
            with wave.open(path, "w") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                for i in range(n):
                    t = i / rate
                    if kind == "coin":
                        val = math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * freq * 2 * t)
                    elif kind == "crash":
                        val = (1 - t / duration) * math.sin(2 * math.pi * 80 * t)
                    elif kind == "win":
                        val = math.sin(2 * math.pi * (freq + i * 2) * t)
                    else:
                        val = math.sin(2 * math.pi * freq * t)
                    v = int(32767 * 0.3 * val)
                    w.writeframes(struct.pack("<h", v))
        except Exception:
            pass
    def make_bgm_wav(self, path):
        try:
            rate = 22050
            duration = 4.0
            n = int(rate * duration)
            freqs = [220, 261, 329, 392]
            with wave.open(path, "w") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                for i in range(n):
                    t = i / rate
                    val = 0
                    for f in freqs:
                        val = val + math.sin(2 * math.pi * f * t) * 0.1
                    v = int(32767 * 0.3 * val)
                    w.writeframes(struct.pack("<h", v))
        except Exception:
            pass
    def play_sound(self, key):
        if key == "bgm":
            self.play_music()
            return
        if not self.data.get("sound", True):
            return
        s = self.sounds.get(key)
        if s:
            try:
                s.play()
            except Exception:
                pass
    def play_music(self):
        if not self.data.get("sound", True):
            return
        music = self.sounds.get("bgm")
        if music:
            try:
                if music.state != "play":
                    music.play()
            except Exception:
                try:
                    music.play()
                except Exception:
                    pass
    def stop_music(self):
        music = self.sounds.get("bgm")
        if music:
            try:
                music.stop()
            except Exception:
                pass
    def stop_all_sound(self):
        for s in self.sounds.values():
            try:
                s.stop()
            except Exception:
                pass
    def clear_screen(self):
        self.root_box.clear_widgets()
    def make_page(self, title):
        self.clear_screen()
        page = BoxLayout(orientation="vertical", padding=[dp(16), dp(16), dp(16), dp(30)], spacing=dp(12), size_hint=(.94, .94), pos_hint={"center_x": .5, "center_y": .5})
        heading = make_label(title, 24, (.1, .9, 1, 1), True)
        heading.size_hint_y = None
        heading.height = dp(55)
        page.add_widget(heading)
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)
        page.add_widget(scroll)
        self.root_box.add_widget(page)
        return content
    def kill_game(self):
        if self.game is not None:
            self.game.stop_loop()
            self.game = None
        self.stop_all_sound()
    def show_menu(self):
        self.kill_game()
        content = self.make_page(GAME_NAME)
        lbl = make_label(f"COINS: {self.data['coins']}   |   BEST: {self.data['best_score']}", 17, (1, .85, .2, 1), True)
        lbl.size_hint_y = None
        lbl.height = dp(40)
        content.add_widget(lbl)
        content.add_widget(make_button("PLAY GAME", self.start_game, (0, .65, .95, 1), dp(60)))
        content.add_widget(make_button("CHARACTER SHOP", self.show_shop))
        content.add_widget(make_button("POWER-UP SHOP", self.show_powerup_shop))
        content.add_widget(make_button("MISSIONS & ACHIEVEMENTS", self.show_missions))
        content.add_widget(make_button("DAILY REWARD", self.daily_reward))
        content.add_widget(make_button("STATISTICS", self.show_stats))
        content.add_widget(make_button("SOUND: ON" if self.data["sound"] else "SOUND: OFF", self.toggle_sound, (.35, .3, .65, 1)))
        content.add_widget(make_button("EXIT GAME", self.stop, (.7, .15, .2, 1)))
    def toggle_sound(self):
        self.data["sound"] = not self.data["sound"]
        save_data(self.data)
        if not self.data["sound"]:
            self.stop_all_sound()
        self.show_menu()
    def start_game(self):
        self.kill_game()
        self.clear_screen()
        self.game = GameScreen(self, size_hint=(1, 1))
        self.root_box.add_widget(self.game)
    def show_pause(self, game):
        content = self.make_page("GAME PAUSED")
        content.add_widget(make_button("RESUME", self.resume_game, (0, .65, .3, 1), dp(60)))
        content.add_widget(make_button("RESTART RUN", self.start_game, (.8, .5, .1, 1)))
        content.add_widget(make_button("MAIN MENU", self.show_menu, (.1, .45, .85, 1)))
    def resume_game(self):
        if self.game:
            self.clear_screen()
            self.root_box.add_widget(self.game)
            self.game.resume_game()
    def show_game_over(self, score, coins, new_best=False):
        self.stop_all_sound()
        content = self.make_page("GAME OVER")
        content.add_widget(make_label("SCORE: " + str(score), 28, (.1, .9, 1, 1), True))
        if new_best:
            content.add_widget(make_label("NEW PERSONAL BEST!", 20, (.4, 1, .5, 1), True))
        content.add_widget(make_label("COINS EARNED: " + str(coins), 20, (1, .85, .1, 1), True))
        content.add_widget(make_label("BEST SCORE: " + str(self.data["best_score"]), 18, (.7, .5, 1, 1), True))
        content.add_widget(make_button("PLAY AGAIN", self.start_game, (0, .65, .95, 1), dp(60)))
        content.add_widget(make_button("MAIN MENU", self.show_menu))
    def show_shop(self):
        content = self.make_page("CHARACTER SHOP")
        coins_lbl = make_label(f"COINS: {self.data['coins']}", 18, (1, .85, .1, 1), True)
        coins_lbl.size_hint_y = None
        coins_lbl.height = dp(40)
        content.add_widget(coins_lbl)
        for idx, char in enumerate(CHARACTERS):
            unlocked = idx in self.data["unlocked"]
            selected = idx == self.data["selected_character"]
            status = "ACTIVE" if selected else ("EQUIP" if unlocked else f"BUY: {char['price']}")
            row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(70), padding=dp(5))
            row.add_widget(CharacterPreview(char))
            btn = Button(text=f"{char['name']}\n{status}", size_hint=(1, 1), font_size=dp(15), bold=True, background_normal="", background_down="", background_color=char["color"], color=(1, 1, 1, 1))
            btn.bind(on_release=lambda *_ , i=idx: self.select_character(i))
            row.add_widget(btn)
            content.add_widget(row)
        content.add_widget(make_button("BACK", self.show_menu))
    def select_character(self, idx):
        char = CHARACTERS[idx]
        if idx not in self.data["unlocked"]:
            if self.data["coins"] < char["price"]:
                self.show_message("NOT ENOUGH COINS!", self.show_shop)
                return
            self.data["coins"] -= char["price"]
            self.data["unlocked"].append(idx)
            self.data["unlocked"] = sorted(set(self.data["unlocked"]))
        self.data["selected_character"] = idx
        save_data(self.data)
        self.show_shop()
    def show_powerup_shop(self):
        content = self.make_page("POWER-UP SHOP")
        coins_lbl = make_label(f"COINS: {self.data['coins']}", 18, (1, .85, .1, 1), True)
        coins_lbl.size_hint_y = None
        coins_lbl.height = dp(40)
        content.add_widget(coins_lbl)
        for key, p in POWERUPS.items():
            count = self.data["powerups"].get(key, 0)
            row = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(70), padding=dp(5))
            row.add_widget(PowerPreview(key))
            btn = Button(text=f"{p['name']}\nBUY: {p['price']}  [OWNED: {count}]", size_hint=(1, 1), font_size=dp(14), bold=True, background_normal="", background_down="", background_color=p["color"], color=(1, 1, 1, 1))
            btn.bind(on_release=lambda *_ , k=key: self.buy_powerup(k))
            row.add_widget(btn)
            content.add_widget(row)
        content.add_widget(make_button("BACK", self.show_menu))
    def buy_powerup(self, key):
        p = POWERUPS[key]
        if self.data["coins"] < p["price"]:
            self.show_message("NOT ENOUGH COINS!", self.show_powerup_shop)
            return
        self.data["coins"] -= p["price"]
        self.data["powerups"][key] += 1
        save_data(self.data)
        self.show_powerup_shop()
    def daily_reward(self):
        today = date.today().isoformat()
        if self.data["daily_date"] == today:
            self.show_message("ALREADY CLAIMED TODAY'S REWARD!", self.show_menu)
            return
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if self.data["daily_date"] == yesterday:
            self.data["daily_streak"] += 1
        else:
            self.data["daily_streak"] = 1
        reward = min(150 + (self.data["daily_streak"] - 1) * 25, 500)
        self.data["daily_date"] = today
        self.data["coins"] += reward
        self.data["total_coins"] += reward
        save_data(self.data)
        self.show_message(f"DAILY REWARD!\n+{reward} COINS!\nSTREAK: {self.data['daily_streak']} DAYS", self.show_menu)
    def show_missions(self):
        content = self.make_page("MISSIONS & ACHIEVEMENTS")
        d = self.data
        missions = [
            ("coins_100", "RICH RUNNER", "Earn 100 total coins", 100, d["total_coins"], 100),
            ("games_5", "DEDICATED", "Play 5 games", 5, d["games_played"], 150),
            ("score_500", "HIGH SCORER", "Reach 500 points", 500, d["best_score"], 200),
            ("boss_1", "BOSS HUNTER", "Defeat one boss", 1, d["bosses_defeated"], 250),
            ("combo_15", "COMBO KING", "Reach a 15 coin combo", 15, d.get("best_combo", 0), 200),
            ("score_2000", "LEGEND", "Reach 2000 points", 2000, d["best_score"], 400),
            ("boss_5", "BOSS SLAYER", "Defeat 5 bosses", 5, d["bosses_defeated"], 600),
            ("jump_20", "AIR MASTER", "Jump 20 times", 20, d.get("jumps", 0), 300),
            ("dash_10", "DASH KING", "Dash 10 times", 10, d.get("dashes", 0), 300),
            ("score_5000", "IMPOSSIBLE LEGEND", "Reach 5000 points", 5000, d["best_score"], 1000),
        ]
        for mid, name, desc, target, progress, reward in missions:
            claimed = mid in d["missions_claimed"]
            ready = progress >= target
            status = "CLAIMED" if claimed else ("READY TO CLAIM!" if ready else f"{min(progress, target)}/{target}")
            lbl = make_label(f"{name}\n{desc}\n{status} | REWARD: {reward}", 15, (.8, .9, 1, 1), True)
            lbl.size_hint_y = None
            lbl.height = dp(80)
            content.add_widget(lbl)
            if ready and not claimed:
                content.add_widget(make_button(f"CLAIM {reward} COINS", lambda m=mid, r=reward: self.claim_mission(m, r), (.05, .65, .25, 1)))
        content.add_widget(make_button("BACK", self.show_menu))
    def claim_mission(self, mission_id, reward):
        if mission_id in self.data["missions_claimed"]:
            return
        self.data["missions_claimed"].append(mission_id)
        self.data["coins"] += reward
        self.data["total_coins"] += reward
        save_data(self.data)
        self.show_missions()
    def show_stats(self):
        content = self.make_page("STATISTICS V6")
        d = self.data
        lbl = make_label(f"BEST SCORE: {d['best_score']}\nTOTAL COINS: {d['total_coins']}\nGAMES PLAYED: {d['games_played']}\nBOSSES DEFEATED: {d['bosses_defeated']}\nLEVELS CLEARED: {d['levels_completed']}\nCOIN PICKUPS: {d.get('coin_pickups', 0)}\nBEST COMBO: {d.get('best_combo', 0)}\nJUMPS: {d.get('jumps', 0)}\nDASHES: {d.get('dashes', 0)}", 19, (.8, .9, 1, 1))
        lbl.size_hint_y = None
        lbl.height = dp(280)
        content.add_widget(lbl)
        content.add_widget(make_button("BACK", self.show_menu))
    def show_message(self, message, callback):
        content = self.make_page("CYBER DASH V6")
        lbl = make_label(message, 20, (1, .85, .2, 1), True)
        lbl.size_hint_y = None
        lbl.height = dp(120)
        content.add_widget(lbl)
        content.add_widget(make_button("CONTINUE", callback))
    def on_keyboard(self, window, key, *args):
        playing = self.game is not None and self.game.running
        if key == 27:
            if playing:
                if not self.game.paused:
                    self.game.pause_game()
                else:
                    self.resume_game()
                return True
            self.show_menu()
            return True
        if playing and not self.game.paused:
            if key in (276, 97):
                self.game.move_left()
                return True
            if key in (275, 100):
                self.game.move_right()
                return True
            if key == 32:
                self.game.use_powerup()
                return True
            if key in (9, 101):
                self.game.cycle_power()
                return True
            if key in (273, 119):
                self.game.do_jump()
                return True
            if key in (274, 115):
                self.game.do_dash()
                return True
        return False

if __name__ == "__main__":
    CyberDashLegendsApp().run()
