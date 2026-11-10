import os
import json
import random
import io
import wave
import struct
import math
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line


CHARACTERS = [
    {"id": 0, "name": "Cyber Blue", "cost": 0,
     "color": (0, 1, 0.8, 1), "visor": (0.1, 0.1, 0.2, 1)},
    {"id": 1, "name": "Neon Ninja", "cost": 15,
     "color": (0.8, 0.1, 1, 1), "visor": (1, 1, 0, 1)},
    {"id": 2, "name": "Gold Sprinter", "cost": 30,
     "color": (1, 0.8, 0, 1), "visor": (0, 0, 0, 1)},
    {"id": 3, "name": "Mecha Red", "cost": 50,
     "color": (1, 0.2, 0.1, 1), "visor": (1, 1, 1, 1)}
]


class RunnerGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.load_game_data()
        self.state = "menu"

        self.score = 0
        self.session_coins = 0
        self.player_lane = 1
        self.player_action = "run"
        self.action_timer = 0.0

        self.lives = 3
        self.max_lives = 3

        self.magnet_active = False
        self.magnet_timer = 0.0
        self.jetpack_active = False
        self.jetpack_timer = 0.0
        self.shield_active = False
        self.shield_timer = 0.0
        self.speed_boost_active = False
        self.speed_boost_timer = 0.0

        self.obstacles = []
        self.coins = []
        self.powerups = []
        self.particles = []
        self.bg_offset = 0.0
        self.spawn_elapsed = 0.0
        self.touch_start_x = 0
        self.touch_start_y = 0

        self.ui_elements = []
        self.score_label = None
        self.music_enabled = True
        self.sound_enabled = True

        self.coin_sound = self.generate_tone_sound(950, 0.08)
        self.click_sound = self.generate_tone_sound(600, 0.05)
        self.hit_sound = self.generate_tone_sound(150, 0.18)
        self.bgm_sound = self.generate_bgm_loop()

        if self.bgm_sound:
            self.bgm_sound.loop = True
            self.bgm_sound.volume = 0.25
            self.bgm_sound.play()

        self.bind(size=self._update_layout, pos=self._update_layout)
        Clock.schedule_interval(self.update_game, 1 / 60.0)
        Clock.schedule_interval(self.spawn_entities, 0.85)

        self.show_menu()

    # ---------------- SAVE DATA ----------------

    def get_save_path(self):
        try:
            return os.path.join(
                App.get_running_app().user_data_dir, "save_data.json"
            )
        except Exception:
            return "save_data.json"

    def load_game_data(self):
        defaults = {
            "total_coins": 0,
            "high_score": 0,
            "unlocked_chars": [0],
            "selected_char": 0,
            "magnet_level": 1,
            "jetpack_level": 1,
            "games_played": 0,
            "last_daily_reward": ""
        }
        path = self.get_save_path()
        data = {}
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
        except (OSError, ValueError, TypeError):
            data = {}

        for key, value in defaults.items():
            setattr(self, key, data.get(key, value))

        # Protect against corrupted or edited save data.
        self.unlocked_chars = [
            int(cid) for cid in self.unlocked_chars
            if isinstance(cid, (int, float)) and 0 <= int(cid) < len(CHARACTERS)
        ]
        if 0 not in self.unlocked_chars:
            self.unlocked_chars.insert(0, 0)
        if self.selected_char not in self.unlocked_chars:
            self.selected_char = 0
        self.magnet_level = max(1, min(5, int(self.magnet_level)))
        self.jetpack_level = max(1, min(5, int(self.jetpack_level)))

    def save_game_data(self):
        path = self.get_save_path()
        data = {
            "total_coins": self.total_coins,
            "high_score": self.high_score,
            "unlocked_chars": self.unlocked_chars,
            "selected_char": self.selected_char,
            "magnet_level": self.magnet_level,
            "jetpack_level": self.jetpack_level,
            "games_played": self.games_played,
            "last_daily_reward": self.last_daily_reward
        }
        try:
            folder = os.path.dirname(path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            temp_path = path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file)
            os.replace(temp_path, path)
        except OSError:
            pass

    # ---------------- AUDIO ----------------

    def generate_tone_sound(self, frequency=440, duration=0.12):
        try:
            sample_rate = 22050
            count = int(sample_rate * duration)
            output = io.BytesIO()
            with wave.open(output, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                frames = bytearray()
                for i in range(count):
                    sample = int(
                        32767 * 0.25 *
                        math.sin(2 * math.pi * frequency * i / sample_rate)
                    )
                    frames.extend(struct.pack("<h", sample))
                wav_file.writeframes(bytes(frames))
            return SoundLoader.load(data=output.getvalue(), ext="wav")
        except Exception:
            return None

    def generate_bgm_loop(self):
        try:
            sample_rate = 22050
            duration = 2.0
            count = int(sample_rate * duration)
            freqs = [220, 261.63, 329.63, 392]
            output = io.BytesIO()
            with wave.open(output, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                frames = bytearray()
                for i in range(count):
                    t = i / sample_rate
                    value = sum(
                        math.sin(2 * math.pi * f * t) * 0.035
                        for f in freqs
                    )
                    frames.extend(struct.pack(
                        "<h", int(32767 * value)
                    ))
                wav_file.writeframes(bytes(frames))
            return SoundLoader.load(data=output.getvalue(), ext="wav")
        except Exception:
            return None

    def play_sound(self, sound):
        if self.sound_enabled and sound:
            try:
                sound.stop()
                sound.play()
            except Exception:
                pass

    def play_click(self):
        self.play_sound(self.click_sound)

    # ---------------- UI HELPERS ----------------

    def clear_ui(self):
        for item in self.ui_elements:
            if item.parent is self:
                self.remove_widget(item)
        self.ui_elements.clear()

    def add_ui(self, widget):
        self.add_widget(widget)
        self.ui_elements.append(widget)
        return widget

    def make_label(self, text, y, height=40, size=18, color=(1, 1, 1, 1),
                   bold=False):
        return Label(
            text=text, font_size=f"{size}sp", color=color, bold=bold,
            halign="center", valign="middle",
            pos=(0, y), size=(self.width, height)
        )

    def make_button(self, text, y, callback, color=(0.1, 0.5, 0.7, 1),
                    height=48, width=240, font_size=17):
        button = Button(
            text=text, font_size=f"{font_size}sp", bold=True,
            background_normal="", background_color=color,
            pos=(self.width / 2 - width / 2, y),
            size=(width, height)
        )
        button.bind(on_press=lambda _button: (self.play_click(), callback()))
        return self.add_ui(button)

    def _update_layout(self, *args):
        # Screens are rebuilt after orientation/size changes.
        if self.state == "menu":
            Clock.schedule_once(lambda _dt: self.show_menu(), 0)
        elif self.state == "shop":
            Clock.schedule_once(lambda _dt: self.show_shop(), 0)

    def draw_background(self, color=(0.07, 0.07, 0.11, 1)):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size)

    # ---------------- MENUS ----------------

    def show_menu(self):
        self.state = "menu"
        self.clear_ui()
        self.canvas.clear()
        self.draw_background()

        self.add_ui(self.make_label(
            "CYBER RUNNER", self.height * 0.76, 65, 34,
            (0, 1, 0.8, 1), True
        ))
        self.add_ui(self.make_label(
            f"BEST SCORE: {self.high_score}",
            self.height * 0.66, 40, 18, (0, 1, 0.4, 1), True
        ))
        self.add_ui(self.make_label(
            f"TOTAL COINS: {self.total_coins}",
            self.height * 0.59, 35, 18, (1, 0.84, 0, 1)
        ))
        self.make_button(
            "DAILY REWARD", self.height * 0.47,
            self.claim_daily_reward, (0.65, 0.35, 0.05, 1)
        )
        self.make_button(
            "PLAY GAME", self.height * 0.35,
            self.start_game, (0, 0.65, 0.4, 1), height=55, font_size=21
        )
        self.make_button(
            "SHOP & UPGRADES", self.height * 0.23,
            self.show_shop, (0.55, 0.15, 0.65, 1)
        )
        self.make_button(
            "SETTINGS", self.height * 0.11,
            self.show_settings, (0.25, 0.35, 0.55, 1)
        )

    def claim_daily_reward(self):
        today = date.today().isoformat()
        if self.last_daily_reward == today:
            self.show_message("Daily reward already collected today!")
            return
        self.total_coins += 25
        self.last_daily_reward = today
        self.save_game_data()
        self.show_menu()
        self.show_message("Daily reward: +25 coins!")

    def show_settings(self):
        self.state = "settings"
        self.clear_ui()
        self.canvas.clear()
        self.draw_background()

        self.add_ui(self.make_label(
            "SETTINGS", self.height * 0.75, 55, 30,
            (0, 1, 0.8, 1), True
        ))
        self.make_button(
            f"SOUND: {'ON' if self.sound_enabled else 'OFF'}",
            self.height * 0.55, self.toggle_sound
        )
        self.make_button(
            f"MUSIC: {'ON' if self.music_enabled else 'OFF'}",
            self.height * 0.42, self.toggle_music
        )
        self.make_button(
            "BACK", self.height * 0.20, self.show_menu,
            (0.2, 0.4, 0.6, 1)
        )

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.show_settings()

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.bgm_sound:
            if self.music_enabled:
                self.bgm_sound.play()
            else:
                self.bgm_sound.stop()
        self.show_settings()

    def show_message(self, message):
        label = Label(
            text=message, font_size="16sp", color=(1, 0.9, 0.2, 1),
            halign="center", valign="middle",
            pos=(0, self.height * 0.02), size=(self.width, 45)
        )
        self.add_ui(label)
        Clock.schedule_once(
            lambda _dt: self.remove_message(label), 2.2
        )

    def remove_message(self, label):
        if label.parent is self:
            self.remove_widget(label)
        if label in self.ui_elements:
            self.ui_elements.remove(label)

    # ---------------- SHOP ----------------

    def show_shop(self):
        self.state = "shop"
        self.clear_ui()
        self.canvas.clear()
        self.draw_background()

        self.add_ui(self.make_label(
            "CYBER SHOP", self.height * 0.84, 45, 29,
            (0, 1, 0.8, 1), True
        ))
        self.add_ui(self.make_label(
            f"COINS: {self.total_coins}",
            self.height * 0.77, 35, 18, (1, 0.84, 0, 1)
        ))

        row_y = self.height * 0.67
        for character in CHARACTERS:
            cid = character["id"]
            unlocked = cid in self.unlocked_chars
            selected = cid == self.selected_char
            if selected:
                text = f"{character['name']} - SELECTED"
                color = (0.1, 0.55, 0.3, 1)
            elif unlocked:
                text = f"{character['name']} - SELECT"
                color = (0.15, 0.4, 0.65, 1)
            else:
                text = f"{character['name']} - {character['cost']} COINS"
                color = (0.45, 0.2, 0.55, 1)

            self.make_button(
                text, row_y, lambda cid=cid: self.select_character(cid),
                color, height=40, width=min(self.width - 30, 340),
                font_size=14
            )
            row_y -= 48

        self.make_button(
            f"UPGRADE MAGNET (LV {self.magnet_level})",
            row_y - 5, self.upgrade_magnet,
            (0.5, 0.2, 0.65, 1), height=40, width=280, font_size=14
        )
        row_y -= 50
        self.make_button(
            f"UPGRADE JETPACK (LV {self.jetpack_level})",
            row_y, self.upgrade_jetpack,
            (0.5, 0.2, 0.65, 1), height=40, width=280, font_size=14
        )
        self.make_button(
            "BACK", 15, self.show_menu,
            (0.2, 0.4, 0.6, 1), height=42
        )

    def select_character(self, cid):
        character = CHARACTERS[cid]
        if cid not in self.unlocked_chars:
            if self.total_coins < character["cost"]:
                self.show_message("Not enough coins!")
                return
            self.total_coins -= character["cost"]
            self.unlocked_chars.append(cid)

        self.selected_char = cid
        self.save_game_data()
        self.show_shop()

    def upgrade_magnet(self):
        if self.magnet_level >= 5:
            self.show_message("Magnet is already max level!")
            return
        cost = self.magnet_level * 20
        if self.total_coins < cost:
            self.show_message(f"Need {cost} coins!")
            return
        self.total_coins -= cost
        self.magnet_level += 1
        self.save_game_data()
        self.show_shop()

    def upgrade_jetpack(self):
        if self.jetpack_level >= 5:
            self.show_message("Jetpack is already max level!")
            return
        cost = self.jetpack_level * 25
        if self.total_coins < cost:
            self.show_message(f"Need {cost} coins!")
            return
        self.total_coins -= cost
        self.jetpack_level += 1
        self.save_game_data()
        self.show_shop()

    # ---------------- GAME CONTROL ----------------

    def start_game(self):
        self.state = "playing"
        self.clear_ui()
        self.canvas.clear()

        self.score = 0
        self.session_coins = 0
        self.lives = self.max_lives
        self.player_lane = 1
        self.player_action = "run"
        self.action_timer = 0.0

        self.magnet_active = False
        self.magnet_timer = 0.0
        self.jetpack_active = False
        self.jetpack_timer = 0.0
        self.shield_active = False
        self.shield_timer = 0.0
        self.speed_boost_active = False
        self.speed_boost_timer = 0.0

        self.obstacles.clear()
        self.coins.clear()
        self.powerups.clear()
        self.particles.clear()
        self.spawn_elapsed = 0.0

        self.games_played += 1
        self.save_game_data()

        self.score_label = self.add_ui(self.make_label(
            self.get_hud_text(), self.height - 55, 45, 16,
            (1, 1, 1, 1), True
        ))
        self.make_button(
            "Ⅱ", self.height - 55, self.pause_game,
            (0.15, 0.25, 0.4, 0.9), height=42, width=55, font_size=22
        )
        self.redraw_game()

    def get_hud_text(self):
        active = []
        if self.magnet_active:
            active.append("MAGNET")
        if self.jetpack_active:
            active.append("JETPACK")
        if self.shield_active:
            active.append("SHIELD")
        if self.speed_boost_active:
            active.append("BOOST")
        power_text = " | ".join(active)
        return (
            f"SCORE: {self.score}    COINS: {self.session_coins}    "
            f"LIVES: {'♥ ' * self.lives}\n{power_text}"
        )

    def pause_game(self):
        if self.state != "playing":
            return
        self.state = "paused"
        self.clear_ui()
        self.add_ui(self.make_label(
            "PAUSED", self.height * 0.62, 60, 34,
            (0, 1, 0.8, 1), True
        ))
        self.make_button(
            "RESUME", self.height * 0.45, self.resume_game,
            (0, 0.6, 0.35, 1)
        )
        self.make_button(
            "RESTART", self.height * 0.32, self.start_game,
            (0.55, 0.3, 0.1, 1)
        )
        self.make_button(
            "MAIN MENU", self.height * 0.19, self.show_menu,
            (0.2, 0.4, 0.6, 1)
        )

    def resume_game(self):
        self.state = "playing"
        self.clear_ui()
        self.score_label = self.add_ui(self.make_label(
            self.get_hud_text(), self.height - 55, 45, 16,
            (1, 1, 1, 1), True
        ))
        self.make_button(
            "Ⅱ", self.height - 55, self.pause_game,
            (0.15, 0.25, 0.4, 0.9), height=42, width=55, font_size=22
        )

    # ---------------- SPAWNING ----------------

    def spawn_entities(self, dt):
        if self.state != "playing":
            return

        difficulty = min(0.35, self.score / 2500)
        interval = max(0.42, 0.85 - difficulty)
        self.spawn_elapsed += dt
        if self.spawn_elapsed < interval:
            return
        self.spawn_elapsed = 0.0

        lane_width = self.width / 3
        lane = random.randint(0, 2)
        x = lane * lane_width + lane_width / 2

        obstacle_type = random.choice(["ground", "overhead"])
        self.obstacles.append({
            "lane": lane,
            "x": x - 25,
            "y": self.height + 30,
            "w": 50,
            "h": 55,
            "type": obstacle_type
        })

        if random.random() < 0.72:
            coin_lane = random.randint(0, 2)
            coin_x = coin_lane * lane_width + lane_width / 2
            self.coins.append({
                "lane": coin_lane,
                "x": coin_x - 12,
                "y": self.height + random.randint(80, 180),
                "r": 12
            })

        if random.random() < 0.13:
            power_lane = random.randint(0, 2)
            power_x = power_lane * lane_width + lane_width / 2
            power_type = random.choice([
                "magnet", "jetpack", "shield", "speed"
            ])
            self.powerups.append({
                "lane": power_lane,
                "x": power_x - 15,
                "y": self.height + random.randint(100, 220),
                "r": 15,
                "type": power_type
            })

    # ---------------- GAME UPDATE ----------------

    def update_game(self, dt):
        if self.state != "playing":
            return

        dt = min(dt, 0.05)
        self.score += int(dt * 10)
        self.bg_offset += dt * 100

        base_speed = 280 + min(220, self.score * 0.08)
        speed = base_speed * (1.5 if self.speed_boost_active else 1)

        for name in [
            "magnet", "jetpack", "shield", "speed_boost"
        ]:
            timer_name = name + "_timer"
            active_name = name + "_active"
            if getattr(self, active_name):
                setattr(self, timer_name, getattr(self, timer_name) - dt)
                if getattr(self, timer_name) <= 0:
                    setattr(self, active_name, False)

        if self.action_timer > 0:
            self.action_timer -= dt
            if self.action_timer <= 0:
                self.player_action = "run"

        lane_width = self.width / 3
        player_cx = self.player_lane * lane_width + lane_width / 2
        player_y = 100
        player_h = 95 if self.player_action != "slide" else 45
        player_cy = player_y + player_h / 2

        for obs in self.obstacles[:]:
            obs["y"] -= speed * dt
            if obs["lane"] == self.player_lane:
                collision = (
                    obs["type"] == "ground"
                    and obs["y"] < player_y + player_h
                    and obs["y"] + obs["h"] > player_y
                    and self.player_action != "jump"
                    and not self.jetpack_active
                ) or (
                    obs["type"] == "overhead"
                    and self.player_action != "slide"
                    and not self.jetpack_active
                    and obs["y"] + 60 < player_y + player_h
                    and obs["y"] + 85 > player_y
                )

                if collision:
                    self.obstacles.remove(obs)
                    if self.shield_active:
                        self.shield_active = False
                        self.add_particles(player_cx, player_cy, (0, 0.8, 1, 1))
                    else:
                        self.lives -= 1
                        self.play_sound(self.hit_sound)
                        self.add_particles(player_cx, player_cy, (1, 0.1, 0.2, 1))
                        if self.lives <= 0:
                            self.trigger_game_over()
                            return
                    continue

            if obs["y"] < -120:
                self.obstacles.remove(obs)

        for power in self.powerups[:]:
            power["y"] -= speed * dt
            if (power["lane"] == self.player_lane
                    and power["y"] < player_y + player_h
                    and power["y"] + power["r"] * 2 > player_y):
                kind = power["type"]
                if kind == "magnet":
                    self.magnet_active = True
                    self.magnet_timer = 4 + self.magnet_level * 2
                elif kind == "jetpack":
                    self.jetpack_active = True
                    self.jetpack_timer = 3 + self.jetpack_level * 2
                elif kind == "shield":
                    self.shield_active = True
                    self.shield_timer = 8
                elif kind == "speed":
                    self.speed_boost_active = True
                    self.speed_boost_timer = 6
                self.play_sound(self.coin_sound)
                self.add_particles(
                    power["x"] + power["r"], power["y"] + power["r"],
                    (0.4, 0.9, 1, 1)
                )
                self.powerups.remove(power)
            elif power["y"] < -100:
                self.powerups.remove(power)

        for coin in self.coins[:]:
            coin["y"] -= speed * dt
            coin_cx = coin["x"] + coin["r"]
            coin_cy = coin["y"] + coin["r"]

            if self.magnet_active:
                dx, dy = player_cx - coin_cx, player_cy - coin_cy
                distance = math.hypot(dx, dy)
                if distance < 350:
                    coin["x"] += dx * min(0.15, dt * 9)
                    coin["y"] += dy * min(0.15, dt * 9)

            if math.hypot(
                player_cx - (coin["x"] + coin["r"]),
                player_cy - (coin["y"] + coin["r"])
            ) < 45:
                self.session_coins += 1
                self.play_sound(self.coin_sound)
                self.coins.remove(coin)
                self.add_particles(coin_cx, coin_cy, (1, 0.8, 0, 1))
            elif coin["y"] < -100:
                self.coins.remove(coin)

        self.update_particles(dt)
        if self.score_label:
            self.score_label.text = self.get_hud_text()
        self.redraw_game()

    # ---------------- PARTICLES / DRAWING ----------------

    def add_particles(self, x, y, color):
        for _ in range(9):
            self.particles.append({
                "x": x, "y": y,
                "dx": random.uniform(-100, 100),
                "dy": random.uniform(-100, 100),
                "life": random.uniform(0.25, 0.55),
                "color": color
            })

    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle["x"] += particle["dx"] * dt
            particle["y"] += particle["dy"] * dt
            particle["life"] -= dt
            if particle["life"] <= 0:
                self.particles.remove(particle)

    def redraw_game(self):
        self.canvas.before.clear()
        self.canvas.clear()

        lane_width = self.width / 3
        theme = (self.score // 300) % 3
        bg = (
            (0.07, 0.07, 0.12, 1) if theme == 0 else
            (0.12, 0.05, 0.15, 1) if theme == 1 else
            (0.04, 0.12, 0.10, 1)
        )

        with self.canvas.before:
            Color(*bg)
            RoundedRectangle(pos=self.pos, size=self.size)
            Color(0, 0.9, 1, 0.22)
            Line(points=[lane_width, 0, lane_width, self.height], width=2)
            Line(points=[lane_width * 2, 0, lane_width * 2, self.height], width=2)

        with self.canvas:
            px = self.player_lane * lane_width + lane_width / 2 - 30
            py = 280 if self.jetpack_active else (
                210 if self.player_action == "jump" else 100
            )
            ph = 45 if self.player_action == "slide" else 95

            if self.magnet_active:
                Color(0.7, 0, 1, 0.25)
                Ellipse(pos=(px - 20, py - 15), size=(100, 125))
            if self.shield_active:
                Color(0, 0.8, 1, 0.3)
                Line(circle=(px + 30, py + ph / 2, 58), width=2)
            if self.jetpack_active:
                Color(1, 0.45, 0, 1)
                Ellipse(pos=(px + 15, py - 25), size=(30, 35))

            char = CHARACTERS[self.selected_char]
            Color(*char["color"])
            RoundedRectangle(pos=(px, py), size=(60, ph), radius=[10])
            if self.player_action != "slide":
                Color(*char["visor"])
                RoundedRectangle(
                    pos=(px + 10, py + ph - 40), size=(40, 20), radius=[5]
                )

            for obs in self.obstacles:
                if obs["type"] == "ground":
                    Color(1, 0.1, 0.4, 1)
                    RoundedRectangle(
                        pos=(obs["x"], obs["y"]),
                        size=(obs["w"], obs["h"]), radius=[8]
                    )
                else:
                    Color(1, 0.8, 0.1, 1)
                    RoundedRectangle(
                        pos=(obs["x"], obs["y"] + 60),
                        size=(obs["w"], 25), radius=[5]
                    )

            power_colors = {
                "magnet": (0.8, 0, 1, 1),
                "jetpack": (1, 0.5, 0, 1),
                "shield": (0, 0.8, 1, 1),
                "speed": (1, 1, 0, 1)
            }
            for power in self.powerups:
                Color(*power_colors.get(power["type"], (1, 1, 1, 1)))
                Ellipse(
                    pos=(power["x"], power["y"]),
                    size=(power["r"] * 2, power["r"] * 2)
                )

            for coin in self.coins:
                Color(1, 0.84, 0, 1)
                Ellipse(
                    pos=(coin["x"], coin["y"]),
                    size=(coin["r"] * 2, coin["r"] * 2)
                )
                Color(1, 1, 1, 0.8)
                Ellipse(
                    pos=(coin["x"] + 8, coin["y"] + 8),
                    size=((coin["r"] - 4) * 2, (coin["r"] - 4) * 2)
                )

            for particle in self.particles:
                Color(*particle["color"])
                Ellipse(
                    pos=(particle["x"], particle["y"]),
                    size=(6, 6)
                )

    # ---------------- INPUT / GAME OVER ----------------

    def on_touch_down(self, touch):
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y

        if self.state == "game_over":
            self.play_click()
            self.show_menu()
            return True

        # Let Kivy buttons receive touches on menu/shop/pause screens.
        if self.state != "playing":
            return super().on_touch_down(touch)

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.state != "playing":
            return super().on_touch_up(touch)

        dx = touch.x - self.touch_start_x
        dy = touch.y - self.touch_start_y

        # Ignore swipes that begin on the pause button.
        if self.touch_start_x > self.width - 85:
            return super().on_touch_up(touch)

        if abs(dx) > abs(dy) and abs(dx) > 30:
            if dx > 0:
                self.player_lane = min(2, self.player_lane + 1)
            else:
                self.player_lane = max(0, self.player_lane - 1)
        elif abs(dy) > abs(dx) and abs(dy) > 30:
            if dy > 0:
                self.player_action = "jump"
                self.action_timer = 0.6
            else:
                self.player_action = "slide"
                self.action_timer = 0.5

        return True

    def trigger_game_over(self):
        if self.state != "playing":
            return

        self.state = "game_over"
        new_record = self.score > self.high_score
        if new_record:
            self.high_score = self.score

        self.total_coins += self.session_coins
        self.save_game_data()
        self.clear_ui()
        self.canvas.clear()

        self.add_ui(self.make_label(
            "GAME OVER", self.height * 0.67, 55, 32,
            (1, 0.2, 0.3, 1), True
        ))
        self.add_ui(self.make_label(
            f"SCORE: {self.score}", self.height * 0.56,
            40, 21, (1, 1, 1, 1), True
        ))
        record_text = "NEW HIGH SCORE!" if new_record else (
            f"BEST SCORE: {self.high_score}"
        )
        self.add_ui(self.make_label(
            record_text, self.height * 0.47, 40, 18,
            (1, 0.85, 0, 1), True
        ))
        self.add_ui(self.make_label(
            f"COINS EARNED: +{self.session_coins}",
            self.height * 0.39, 40, 18
        ))
        self.make_button(
            "MAIN MENU", self.height * 0.22,
            self.show_menu, (0.15, 0.5, 0.4, 1)
        )


class RunnerApp(App):
    def build(self):
        self.title = "Cyber Runner"
        return RunnerGame()

    def on_pause(self):
        # Keep the app alive when Android temporarily backgrounds it.
        return True

    def on_resume(self):
        return None


if __name__ == "__main__":
    RunnerApp().run()
