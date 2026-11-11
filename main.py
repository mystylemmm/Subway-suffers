import os
import json
import random
from datetime import date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line


GAME_NAME = "CYBER DASH LEGENDS V5"
SAVE_FILE = "cyber_dash_save.json"

CHARACTERS = [
    {"name": "Cyber Kid", "price": 0, "color": (.1, .9, 1, 1)},
    {"name": "Neon Ninja", "price": 150, "color": (.8, .2, 1, 1)},
    {"name": "Golden Bot", "price": 500, "color": (1, .75, .1, 1)},
    {"name": "Shadow", "price": 1000, "color": (.6, .6, .8, 1)},
    {"name": "Toxic", "price": 1800, "color": (.2, 1, .3, 1)},
    {"name": "Fireball", "price": 3000, "color": (1, .2, .05, 1)},
    {"name": "Valkyrie", "price": 5000, "color": (1, .85, .3, 1)},
    {"name": "Glitch", "price": 9000, "color": (.9, .1, .9, 1)},
    {"name": "Quantum", "price": 16000, "color": (.1, 1, .8, 1)},
    {"name": "Apex Legend", "price": 35000, "color": (1, 1, 1, 1)},
    {"name": "PHANTOM", "price": 80000, "color": (.5, .1, .8, 1)},
]

POWERUPS = {
    "shield": {"name": "ENERGY SHIELD", "price": 300, "duration": 8},
    "magnet": {"name": "COIN MAGNET", "price": 450, "duration": 10},
    "boost": {"name": "SCORE BOOST", "price": 600, "duration": 8},
    "laser": {"name": "MEGA LASER", "price": 800, "duration": 7},
    "slow": {"name": "TIME CONTROL", "price": 1000, "duration": 8},
}

POWER_KEYS = list(POWERUPS.keys())

WORLDS = [
    {"name": "NEON CITY", "sky": (.01, .02, .1, 1),
     "road": (.03, .04, .12, 1), "glow": (0, .9, 1, 1)},
    {"name": "LAVA ZONE", "sky": (.2, .02, .01, 1),
     "road": (.12, .03, .01, 1), "glow": (1, .25, .02, 1)},
    {"name": "FROZEN PLANET", "sky": (.01, .08, .2, 1),
     "road": (.02, .1, .18, 1), "glow": (.3, .9, 1, 1)},
    {"name": "CYBER VOID", "sky": (.08, .01, .15, 1),
     "road": (.04, .01, .1, 1), "glow": (1, .1, .8, 1)},
]

BOSS_MAX = 150
PLAYER_Y = .17
ROAD_LEFT = .12
ROAD_WIDTH = .76


def lane_x(lane):
    return ROAD_LEFT + ROAD_WIDTH * (lane + .5) / 3


def default_save():
    return {
        "coins": 500,
        "best_score": 0,
        "games": 0,
        "coins_earned": 0,
        "bosses": 0,
        "levels": 0,
        "unlocked": [0],
        "character": 0,
        "powerups": {k: 2 for k in POWERUPS},
        "daily_date": "",
        "streak": 0,
        "claimed": [],
        "sound": True,
    }


def load_save():
    path = os.path.join(App.get_running_app().user_data_dir,
                        SAVE_FILE)
    data = default_save()

    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                old = json.load(f)
            if isinstance(old, dict):
                data.update(old)
    except Exception:
        pass

    if not isinstance(data.get("unlocked"), list):
        data["unlocked"] = [0]

    data["unlocked"] = sorted(set(
        i for i in data["unlocked"]
        if isinstance(i, int) and 0 <= i < len(CHARACTERS)
    ) | {0})

    if not isinstance(data.get("powerups"), dict):
        data["powerups"] = {}

    for k in POWERUPS:
        try:
            data["powerups"][k] = max(0, int(data["powerups"].get(k, 0)))
        except Exception:
            data["powerups"][k] = 0

    if not isinstance(data.get("claimed"), list):
        data["claimed"] = []

    for k in ("coins", "best_score", "games", "coins_earned",
              "bosses", "levels", "streak"):
        try:
            data[k] = max(0, int(data.get(k, 0)))
        except Exception:
            data[k] = 0

    try:
        selected = int(data.get("character", 0))
    except Exception:
        selected = 0

    data["character"] = selected if selected in data["unlocked"] else 0
    return data


def save_data(data):
    app = App.get_running_app()
    path = os.path.join(app.user_data_dir, SAVE_FILE)
    temp = path + ".tmp"

    try:
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp, path)
    except Exception as e:
        print("Save error:", e)


def label(text, size=18, color=(1, 1, 1, 1)):
    return Label(
        text=text,
        font_size=dp(size),
        color=color,
        bold=True,
        halign="center",
        valign="middle"
    )


def button(text, callback, color=(.05, .4, .8, 1)):
    b = Button(
        text=text,
        size_hint_y=None,
        height=dp(52),
        font_size=dp(15),
        bold=True,
        background_normal="",
        background_down="",
        background_color=color
    )
    b.bind(on_release=lambda *_: callback())
    return b


class GameField(Widget):

    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()

        if self.width <= 0 or self.height <= 0:
            return

        g = self.game
        w = self.width
        h = self.height
        ox = self.x
        oy = self.y
        world = WORLDS[g.world]

        with self.canvas:
            Color(*world["sky"])
            Rectangle(pos=self.pos, size=self.size)

            Color(*world["road"])
            Rectangle(
                pos=(ox + w * ROAD_LEFT, oy),
                size=(w * ROAD_WIDTH, h)
            )

            Color(*world["glow"])
            Line(points=[
                ox + w * ROAD_LEFT, oy,
                ox + w * ROAD_LEFT, oy + h
            ], width=dp(2))

            Line(points=[
                ox + w * (ROAD_LEFT + ROAD_WIDTH), oy,
                ox + w * (ROAD_LEFT + ROAD_WIDTH), oy + h
            ], width=dp(2))

            Color(.2, .6, .9, .6)

            for i in (1, 2):
                x = ox + w * (ROAD_LEFT + ROAD_WIDTH * i / 3)
                Line(
                    points=[x, oy, x, oy + h],
                    dash_length=dp(12),
                    width=dp(1)
                )

            for i in range(15):
                y = oy + ((i * .1 - g.road_offset) % 1) * h
                Color(*world["glow"][:3], .2)
                Line(points=[
                    ox + w * ROAD_LEFT, y,
                    ox + w * (ROAD_LEFT + ROAD_WIDTH), y
                ])

            for item in g.items:
                cx = ox + w * lane_x(item["lane"])
                cy = oy + item["y"] * h

                if item["type"] == "coin":
                    Color(1, .85, .05, 1)
                    Ellipse(
                        pos=(cx - dp(12), cy - dp(12)),
                        size=(dp(24), dp(24))
                    )

                elif item["type"] == "power":
                    Color(.1, 1, .7, 1)
                    RoundedRectangle(
                        pos=(cx - dp(14), cy - dp(14)),
                        size=(dp(28), dp(28)),
                        radius=[dp(6)]
                    )

                elif item["type"] == "obstacle":
                    Color(1, .1, .15, 1)
                    RoundedRectangle(
                        pos=(cx - dp(20), cy - dp(20)),
                        size=(dp(40), dp(40)),
                        radius=[dp(7)]
                    )

                elif item["type"] == "boss_shot":
                    Color(1, .1, .9, 1)
                    Ellipse(
                        pos=(cx - dp(14), cy - dp(14)),
                        size=(dp(28), dp(28))
                    )

            if g.boss:
                bx = ox + w * .5
                by = oy + h * .82

                Color(.8, .02, .12, 1)
                RoundedRectangle(
                    pos=(bx - dp(55), by - dp(25)),
                    size=(dp(110), dp(50)),
                    radius=[dp(12)]
                )

                Color(1, .9, .1, 1)
                Ellipse(
                    pos=(bx - dp(25), by - dp(5)),
                    size=(dp(13), dp(13))
                )
                Ellipse(
                    pos=(bx + dp(12), by - dp(5)),
                    size=(dp(13), dp(13))
                )

                Color(.1, .1, .1, 1)
                Rectangle(
                    pos=(ox + w * .2, oy + h * .92),
                    size=(w * .6, dp(10))
                )

                Color(1, .05, .1, 1)
                Rectangle(
                    pos=(ox + w * .2, oy + h * .92),
                    size=(w * .6 * max(0, g.boss_hp / BOSS_MAX),
                          dp(10))
                )

            px = ox + w * lane_x(g.lane)
            py = oy + h * PLAYER_Y

            char = CHARACTERS[g.data["character"]]

            Color(*char["color"][:3], .25)
            Ellipse(
                pos=(px - dp(30), py - dp(30)),
                size=(dp(60), dp(60))
            )

            Color(*char["color"])
            RoundedRectangle(
                pos=(px - dp(18), py - dp(22)),
                size=(dp(36), dp(46)),
                radius=[dp(10)]
            )

            Color(.02, .03, .1, 1)
            Ellipse(
                pos=(px - dp(10), py + dp(5)),
                size=(dp(6), dp(6))
            )
            Ellipse(
                pos=(px + dp(4), py + dp(5)),
                size=(dp(6), dp(6))
            )

            if g.power_timer["shield"] > 0:
                Color(.1, .8, 1, .8)
                Line(circle=(px, py, dp(35)), width=dp(3))

            if g.power_timer["magnet"] > 0:
                Color(.1, 1, .5, .6)
                Line(circle=(px, py, dp(43)), width=dp(2))

            if g.power_timer["laser"] > 0:
                Color(1, .1, .1, .8)
                Line(points=[px, py, px, oy + h], width=dp(4))


class GameScreen(FloatLayout):

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self.app = app
        self.data = app.data

        self.running = True
        self.paused = False
        self.lane = 1
        self.score = 0
        self.run_coins = 0
        self.speed = .4
        self.level = 1
        self.world = 0
        self.road_offset = 0

        self.items = []
        self.boss = False
        self.boss_hp = BOSS_MAX
        self.boss_timer = 0

        self.combo = 0
        self.combo_timer = 0
        self.best_combo = 0

        self.spawn_timer = .7
        self.power_timer = {k: 0 for k in POWERUPS}
        self.selected_power = 0

        self.last_touch = None

        self.field = GameField(self)
        self.add_widget(self.field)

        self.hud = BoxLayout(
            size_hint=(1, None),
            height=dp(52),
            pos_hint={"top": 1},
            spacing=dp(3),
            padding=dp(3)
        )

        self.score_label = label("SCORE: 0", 12, (.1, .9, 1, 1))
        self.coin_label = label("COINS: 0", 12, (1, .85, .1, 1))
        self.level_label = label("LEVEL: 1", 12, (.8, .3, 1, 1))

        pause = button("PAUSE", self.pause_game, (.7, .1, .2, 1))
        pause.size_hint_x = .8

        self.hud.add_widget(self.score_label)
        self.hud.add_widget(self.coin_label)
        self.hud.add_widget(self.level_label)
        self.hud.add_widget(pause)

        self.add_widget(self.hud)

        self.status = label("", 12, (.4, 1, .8, 1))
        self.status.size_hint = (1, None)
        self.status.height = dp(28)
        self.status.pos_hint = {"top": .92}
        self.add_widget(self.status)

        self.banner = label("", 22, (1, 1, 1, 1))
        self.banner.size_hint = (1, None)
        self.banner.height = dp(55)
        self.banner.pos_hint = {"center_y": .65}
        self.add_widget(self.banner)

        controls = BoxLayout(
            size_hint=(.98, None),
            height=dp(60),
            pos_hint={"center_x": .5, "y": .015},
            spacing=dp(5)
        )

        controls.add_widget(button("LEFT", self.left, (.05, .3, .7, 1)))

        self.use_button = button("USE POWER", self.use_power,
                                 (.05, .6, .3, 1))
        controls.add_widget(self.use_button)

        controls.add_widget(button("NEXT", self.next_power,
                                   (.35, .25, .6, 1)))

        controls.add_widget(button("RIGHT", self.right,
                                   (.05, .3, .7, 1)))

        self.add_widget(controls)

        self.event = Clock.schedule_interval(self.update, 1 / 60)

    def show_banner(self, message):
        self.banner.text = message
        Clock.schedule_once(
            lambda *_: setattr(self.banner, "text", ""), 2
        )

    def left(self):
        if self.running and not self.paused:
            self.lane = max(0, self.lane - 1)
            self.field.draw()

    def right(self):
        if self.running and not self.paused:
            self.lane = min(2, self.lane + 1)
            self.field.draw()

    def next_power(self):
        self.selected_power = (self.selected_power + 1) % len(POWER_KEYS)
        self.update_hud()

    def use_power(self):
        if not self.running or self.paused:
            return

        key = POWER_KEYS[self.selected_power]

        if self.data["powerups"].get(key, 0) <= 0:
            self.show_banner("NO POWER-UP AVAILABLE!")
            return

        self.data["powerups"][key] -= 1
        self.power_timer[key] = POWERUPS[key]["duration"]

        save_data(self.data)
        self.show_banner(POWERUPS[key]["name"] + " ACTIVATED!")

        self.update_hud()

    def on_touch_down(self, touch):
        self.last_touch = touch.pos
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.running and not self.paused and self.last_touch:
            dx = touch.x - self.last_touch[0]
            dy = touch.y - self.last_touch[1]

            if abs(dx) > dp(30) and abs(dx) > abs(dy):
                if dx < 0:
                    self.left()
                else:
                    self.right()

        self.last_touch = None
        return super().on_touch_up(touch)

    def spawn(self):
        if self.boss:
            return

        lane = random.randint(0, 2)
        roll = random.random()

        if roll < .4:
            for i in range(random.randint(1, 3)):
                self.items.append({
                    "type": "coin",
                    "lane": lane,
                    "y": 1.05 + i * .1
                })

        elif roll < .5:
            self.items.append({
                "type": "power",
                "lane": lane,
                "y": 1.05
            })

        else:
            lanes = [0, 1, 2]
            random.shuffle(lanes)

            blocked = 2 if self.level >= 5 and random.random() < .25 else 1

            for l in lanes[:blocked]:
                self.items.append({
                    "type": "obstacle",
                    "lane": l,
                    "y": 1.05
                })

            if random.random() < .6:
                self.items.append({
                    "type": "coin",
                    "lane": lanes[-1],
                    "y": 1.05
                })

    def update_hud(self):
        self.score_label.text = "SCORE: " + str(int(self.score))
        self.coin_label.text = "COINS: " + str(self.run_coins)
        self.level_label.text = "LEVEL: " + str(self.level)

        key = POWER_KEYS[self.selected_power]
        count = self.data["powerups"].get(key, 0)
        self.use_button.text = "USE " + key.upper() + " x" + str(count)

        active = [
            k.upper() + " " + str(int(self.power_timer[k]))
            for k in POWER_KEYS if self.power_timer[k] > 0
        ]

        self.status.text = " | ".join(active)

    def update(self, dt):
        if not self.running or self.paused:
            return

        dt = min(dt, .05)

        slow = self.power_timer["slow"] > 0
        boost = self.power_timer["boost"] > 0

        time_scale = .5 if slow else 1
        score_scale = 2 if boost else 1

        self.score += dt * 12 * score_scale
        self.road_offset = (
            self.road_offset + self.speed * dt * time_scale
        ) % 1

        self.combo_timer -= dt
        if self.combo_timer <= 0:
            self.combo = 0

        new_level = 1 + int(self.score // 400)

        if new_level != self.level:
            self.level = new_level

            new_world = min(3, (self.level - 1) // 3)

            if new_world != self.world:
                self.world = new_world
                self.show_banner("WELCOME TO " + WORLDS[self.world]["name"])
            else:
                self.show_banner("LEVEL " + str(self.level))

            if self.level % 5 == 0:
                self.start_boss()

        self.speed = min(.95, .4 + self.score / 6000)

        for key in self.power_timer:
            self.power_timer[key] = max(
                0, self.power_timer[key] - dt
            )

        self.spawn_timer -= dt * time_scale

        if self.spawn_timer <= 0 and not self.boss:
            self.spawn()
            self.spawn_timer = max(.5, 1.3 - self.speed * .5)

        if self.boss:
            self.boss_timer -= dt

            if self.boss_timer <= 0:
                self.boss_timer = 1.1
                self.items.append({
                    "type": "boss_shot",
                    "lane": random.randint(0, 2),
                    "y": .9
                })

            if self.power_timer["laser"] > 0:
                self.damage_boss(dt * 35)

        for item in list(self.items):
            item["y"] -= self.speed * dt * time_scale

            if (
                self.power_timer["magnet"] > 0
                and item["type"] == "coin"
                and abs(item["y"] - PLAYER_Y) < .25
            ):
                item["lane"] = self.lane

            if (
                item["type"] == "boss_shot"
                and item["y"] < PLAYER_Y - .1
                and not item.get("dodged")
            ):
                item["dodged"] = True
                self.damage_boss(15)

            hit = (
                item["lane"] == self.lane
                and abs(item["y"] - PLAYER_Y) < .08
                and not item.get("collected")
            )

            if not hit:
                continue

            item["collected"] = True

            if item["type"] == "coin":
                self.combo += 1
                self.best_combo = max(self.best_combo, self.combo)
                self.combo_timer = 2.5

                reward = min(5, 1 + self.combo // 10)

                self.run_coins += reward
                self.data["coins"] += reward
                self.data["coins_earned"] += reward

            elif item["type"] == "power":
                key = random.choice(POWER_KEYS)
                self.power_timer[key] = POWERUPS[key]["duration"]
                self.show_banner(key.upper() + " POWER!")

            else:
                if self.power_timer["shield"] > 0:
                    self.power_timer["shield"] = 0

                elif (
                    item["type"] == "obstacle"
                    and self.power_timer["laser"] > 0
                ):
                    self.score += 10

                else:
                    self.end_game()
                    return

        self.items = [
            i for i in self.items
            if i["y"] > -.15 and not i.get("collected")
        ]

        self.update_hud()
        self.field.draw()

    def start_boss(self):
        if self.boss:
            return

        self.boss = True
        self.boss_hp = BOSS_MAX
        self.boss_timer = 1.5
        self.items = [
            i for i in self.items if i["type"] == "coin"
        ]

        self.show_banner("BOSS BATTLE! DODGE THE ATTACKS!")

    def damage_boss(self, amount):
        if not self.boss:
            return

        self.boss_hp -= amount

        if self.boss_hp <= 0:
            self.defeat_boss()

    def defeat_boss(self):
        self.boss = False
        self.data["bosses"] += 1
        self.data["levels"] += 1

        reward = 100 + self.level * 10

        self.data["coins"] += reward
        self.data["coins_earned"] += reward
        self.run_coins += reward

        self.score += 100

        save_data(self.data)
        self.show_banner("BOSS DEFEATED! +" + str(reward) + " COINS!")

    def pause_game(self):
        if not self.running:
            return

        self.paused = True
        save_data(self.data)
        self.app.show_pause()

    def resume_game(self):
        self.paused = False

    def stop(self):
        self.running = False

        if self.event:
            self.event.cancel()
            self.event = None

    def end_game(self):
        if not self.running:
            return

        self.stop()

        final_score = int(self.score)

        self.data["games"] += 1
        self.data["best_score"] = max(
            self.data["best_score"], final_score
        )

        save_data(self.data)

        self.app.show_game_over(final_score, self.run_coins)


class CyberDashApp(App):

    def build(self):
        self.title = GAME_NAME
        Window.clearcolor = (.01, .015, .06, 1)

        self.data = load_save()
        self.root_box = FloatLayout()
        self.game = None

        self.show_menu()
        return self.root_box

    def clear(self):
        self.root_box.clear_widgets()

    def page(self, title):
        self.clear()

        page = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10),
            size_hint=(.94, .94),
            pos_hint={"center_x": .5, "center_y": .5}
        )

        heading = label(title, 23, (.1, .9, 1, 1))
        heading.size_hint_y = None
        heading.height = dp(55)
        page.add_widget(heading)

        scroll = ScrollView(do_scroll_x=False)

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(9),
            size_hint_y=None
        )

        content.bind(minimum_height=content.setter("height"))

        scroll.add_widget(content)
        page.add_widget(scroll)
        self.root_box.add_widget(page)

        return content

    def stop_game(self):
        if self.game:
            self.game.stop()
            self.game = None

    def show_menu(self):
        self.stop_game()

        c = self.page(GAME_NAME)

        c.add_widget(label(
            "COINS: " + str(self.data["coins"]),
            18, (1, .85, .1, 1)
        ))

        c.add_widget(button("PLAY GAME", self.start_game,
                            (.05, .6, .95, 1)))

        c.add_widget(button("CHARACTER SHOP", self.shop))
        c.add_widget(button("POWER-UP SHOP", self.power_shop))
        c.add_widget(button("MISSIONS", self.missions))
        c.add_widget(button("DAILY REWARD", self.daily_reward))
        c.add_widget(button("STATISTICS", self.statistics))

        c.add_widget(button(
            "SOUND: ON" if self.data["sound"] else "SOUND: OFF",
            self.toggle_sound
        ))

        c.add_widget(button("EXIT", self.stop, (.7, .1, .2, 1)))

    def start_game(self):
        self.stop_game()
        self.clear()

        self.game = GameScreen(self)
        self.root_box.add_widget(self.game)

    def show_pause(self):
        c = self.page("GAME PAUSED")

        c.add_widget(button("RESUME", self.resume,
                            (.05, .65, .25, 1)))

        c.add_widget(button("RESTART", self.start_game))
        c.add_widget(button("MAIN MENU", self.show_menu))

    def resume(self):
        if self.game:
            self.clear()
            self.root_box.add_widget(self.game)
            self.game.resume_game()

    def show_game_over(self, score, coins):
        c = self.page("GAME OVER")

        c.add_widget(label("SCORE: " + str(score), 26,
                           (.1, .9, 1, 1)))

        c.add_widget(label("COINS EARNED: " + str(coins), 20,
                           (1, .85, .1, 1)))

        c.add_widget(label(
            "BEST SCORE: " + str(self.data["best_score"]),
            18
        ))

        c.add_widget(button("PLAY AGAIN", self.start_game))
        c.add_widget(button("MAIN MENU", self.show_menu))

    def shop(self):
        c = self.page("CHARACTER SHOP")

        c.add_widget(label(
            "YOUR COINS: " + str(self.data["coins"]),
            18, (1, .85, .1, 1)
        ))

        for i, char in enumerate(CHARACTERS):
            if i in self.data["unlocked"]:
                status = "SELECTED" if i == self.data["character"] else "EQUIP"
            else:
                status = "BUY " + str(char["price"])

            c.add_widget(button(
                char["name"] + "  |  " + status,
                lambda x=i: self.select_character(x),
                char["color"]
            ))

        c.add_widget(button("BACK", self.show_menu))

    def select_character(self, index):
        char = CHARACTERS[index]

        if index not in self.data["unlocked"]:
            if self.data["coins"] < char["price"]:
                self.message("NOT ENOUGH COINS!", self.shop)
                return

            self.data["coins"] -= char["price"]
            self.data["unlocked"].append(index)

        self.data["character"] = index

        save_data(self.data)
        self.shop()

    def power_shop(self):
        c = self.page("POWER-UP SHOP")

        c.add_widget(label(
            "YOUR COINS: " + str(self.data["coins"]),
            18, (1, .85, .1, 1)
        ))

        for key, p in POWERUPS.items():
            count = self.data["powerups"].get(key, 0)

            c.add_widget(button(
                p["name"] + " | " + str(p["price"]) +
                " COINS | OWNED: " + str(count),
                lambda k=key: self.buy_power(k)
            ))

        c.add_widget(button("BACK", self.show_menu))

    def buy_power(self, key):
        price = POWERUPS[key]["price"]

        if self.data["coins"] < price:
            self.message("NOT ENOUGH COINS!", self.power_shop)
            return

        self.data["coins"] -= price
        self.data["powerups"][key] += 1

        save_data(self.data)
        self.power_shop()

    def daily_reward(self):
        today = date.today()
        today_text = today.isoformat()

        if self.data["daily_date"] == today_text:
            self.message("YOU ALREADY CLAIMED TODAY'S REWARD!",
                         self.show_menu)
            return

        yesterday = (today - timedelta(days=1)).isoformat()

        if self.data["daily_date"] == yesterday:
            self.data["streak"] += 1
        else:
            self.data["streak"] = 1

        reward = min(150 + (self.data["streak"] - 1) * 25, 500)

        self.data["daily_date"] = today_text
        self.data["coins"] += reward
        self.data["coins_earned"] += reward

        save_data(self.data)

        self.message(
            "DAILY REWARD!\n+" + str(reward) +
            " COINS!\nSTREAK: " + str(self.data["streak"]),
            self.show_menu
        )

    def missions(self):
        c = self.page("MISSIONS")

        d = self.data

        tasks = [
            ("coins100", "EARN 100 COINS", d["coins_earned"], 100, 100),
            ("games5", "PLAY 5 GAMES", d["games"], 5, 200),
            ("score500", "REACH 500 SCORE", d["best_score"], 500, 250),
            ("boss1", "DEFEAT 1 BOSS", d["bosses"], 1, 300),
            ("boss5", "DEFEAT 5 BOSSES", d["bosses"], 5, 700),
            ("score2000", "REACH 2000 SCORE", d["best_score"], 2000, 500),
        ]

        for mid, name, progress, target, reward in tasks:
            claimed = mid in d["claimed"]
            ready = progress >= target

            if claimed:
                status = "CLAIMED"
            elif ready:
                status = "READY TO CLAIM"
            else:
                status = str(min(progress, target)) + "/" + str(target)

            c.add_widget(label(
                name + "\n" + status +
                " | REWARD: " + str(reward),
                15, (.8, .9, 1, 1)
            ))

            if ready and not claimed:
                c.add_widget(button(
                    "CLAIM " + str(reward) + " COINS",
                    lambda m=mid, r=reward: self.claim_mission(m, r),
                    (.05, .65, .25, 1)
                ))

        c.add_widget(button("BACK", self.show_menu))

    def claim_mission(self, mid, reward):
        if mid in self.data["claimed"]:
            return

        self.data["claimed"].append(mid)
        self.data["coins"] += reward
        self.data["coins_earned"] += reward

        save_data(self.data)
        self.missions()

    def statistics(self):
        d = self.data
        c = self.page("STATISTICS")

        stats = (
            "BEST SCORE: " + str(d["best_score"]) + "\n\n"
            "WALLET: " + str(d["coins"]) + "\n\n"
            "TOTAL COINS EARNED: " + str(d["coins_earned"]) + "\n\n"
            "GAMES PLAYED: " + str(d["games"]) + "\n\n"
            "BOSSES DEFEATED: " + str(d["bosses"]) + "\n\n"
            "LEVELS COMPLETED: " + str(d["levels"]) + "\n\n"
            "DAILY STREAK: " + str(d["streak"])
        )

        c.add_widget(label(stats, 18, (.8, .9, 1, 1)))
        c.add_widget(button("BACK", self.show_menu))

    def toggle_sound(self):
        self.data["sound"] = not self.data["sound"]
        save_data(self.data)
        self.show_menu()

    def message(self, msg, callback):
        c = self.page("CYBER DASH")

        c.add_widget(label(msg, 20, (1, .85, .1, 1)))
        c.add_widget(button("CONTINUE", callback))

    def on_pause(self):
        if self.game and self.game.running:
            self.game.paused = True
            save_data(self.data)

        return True

    def on_stop(self):
        if self.game:
            self.game.stop()

        save_data(self.data)


if __name__ == "__main__":
    CyberDashApp().run()
