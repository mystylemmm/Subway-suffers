import random
import io
import wave
import struct
import json
import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line

# Character definitions (All 4 characters fully accessible)
CHARACTERS = [
    {"id": 0, "name": "Cyber Blue", "cost": 0, "color": (0, 1, 0.8, 1), "visor": (0.1, 0.1, 0.2, 1)},
    {"id": 1, "name": "Neon Ninja", "cost": 15, "color": (0.8, 0.1, 1, 1), "visor": (1, 1, 0, 1)},
    {"id": 2, "name": "Gold Sprinter", "cost": 30, "color": (1, 0.8, 0, 1), "visor": (0, 0, 0, 1)},
    {"id": 3, "name": "Mecha Red", "cost": 50, "color": (1, 0.2, 0.1, 1), "visor": (1, 1, 1, 1)}
]

class RunnerGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.load_game_data()
        self.state = 'menu'
        
        self.score = 0
        self.session_coins = 0
        self.player_lane = 1  # 0: Left, 1: Center, 2: Right
        
        # Player movement physics states (Run, Jump, Slide)
        self.player_action = 'run'
        self.action_timer = 0.0
        
        # Power-up states
        self.magnet_active = False
        self.magnet_timer = 0.0
        self.jetpack_active = False
        self.jetpack_timer = 0.0
        
        self.obstacles = []
        self.coins = []
        self.powerups = []
        self.bg_offset = 0.0

        # Procedural Audio (Safely wrapped for Android compatibility)
        self.coin_sound = self.generate_tone_sound(frequency=950, duration=0.08)
        self.click_sound = self.generate_tone_sound(frequency=600, duration=0.05)
        self.bgm_sound = self.generate_bgm_loop()
        
        if self.bgm_sound:
            self.bgm_sound.loop = True
            self.bgm_sound.play()

        self.ui_elements = []
        self.touch_start_x = 0
        self.touch_start_y = 0
        
        self.bind(size=self._update_layout, pos=self._update_layout)
        Clock.schedule_interval(self.update_game, 1 / 60.0)
        Clock.schedule_interval(self.spawn_entities, 1.0)
        
        self.show_menu()

    def get_save_path(self):
        try:
            return os.path.join(App.get_running_app().user_data_dir, 'save_data.json')
        except:
            return 'save_data.json'

    def load_game_data(self):
        path = self.get_save_path()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.total_coins = data.get('total_coins', 0)
                    self.high_score = data.get('high_score', 0)
                    self.unlocked_chars = data.get('unlocked_chars', [0])
                    self.selected_char = data.get('selected_char', 0)
                    self.magnet_level = data.get('magnet_level', 1)
                    self.jetpack_level = data.get('jetpack_level', 1)
                    return
            except:
                pass
        self.total_coins = 0
        self.high_score = 0
        self.unlocked_chars = [0]
        self.selected_char = 0
        self.magnet_level = 1
        self.jetpack_level = 1

    def save_game_data(self):
        path = self.get_save_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump({
                    'total_coins': self.total_coins,
                    'high_score': self.high_score,
                    'unlocked_chars': self.unlocked_chars,
                    'selected_char': self.selected_char,
                    'magnet_level': self.magnet_level,
                    'jetpack_level': self.jetpack_level
                }, f)
        except:
            pass

    def generate_tone_sound(self, frequency=440, duration=0.15):
        """Safely generates sound effects in memory with fallback for Android."""
        try:
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                for i in range(num_samples):
                    value = int(32767 * 0.4 * __import__('math').sin(2 * __import__('math').pi * frequency * i / sample_rate))
                    wav_file.writeframes(struct.pack('<h', value))
            wav_io.seek(0)
            return SoundLoader.load(data=wav_io.read(), ext='wav')
        except:
            return None

    def generate_bgm_loop(self):
        """Safely generates procedural ambient background music with fallback for Android."""
        try:
            sample_rate = 22050
            duration = 2.0
            num_samples = int(sample_rate * duration)
            wav_io = io.BytesIO()
            freqs = [220, 261.63, 329.63, 392]
            with wave.open(wav_io, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                for i in range(num_samples):
                    t = i / sample_rate
                    val = sum(__import__('math').sin(2 * __import__('math').pi * f * t) * 0.1 for f in freqs)
                    value = int(32767 * 0.3 * val)
                    wav_file.writeframes(struct.pack('<h', value))
            wav_io.seek(0)
            return SoundLoader.load(data=wav_io.read(), ext='wav')
        except:
            return None

    def play_click(self):
        if self.click_sound:
            self.click_sound.play()

    def clear_ui(self):
        for widget in self.ui_elements:
            self.remove_widget(widget)
        self.ui_elements.clear()

    def _update_layout(self, *args):
        pass

    # --- SCREENS ---
    def show_menu(self):
        self.state = 'menu'
        self.clear_ui()
        self.canvas.before.clear()
        self.canvas.clear()
        
        with self.canvas.before:
            Color(0.08, 0.08, 0.12, 1)
            RoundedRectangle(pos=self.pos, size=self.size)

        title = Label(text="CYBER RUNNER", font_size='34sp', bold=True, color=(0, 1, 0.8, 1),
                      pos=(0, self.height * 0.72), size=(self.width, 60))
        high_score_lbl = Label(text=f"🏆 BEST SCORE: {self.high_score}", font_size='18sp', bold=True, color=(0, 1, 0.4, 1),
                               pos=(0, self.height * 0.61), size=(self.width, 40))
        coins_lbl = Label(text=f"🪙 Total Coins: {self.total_coins}", font_size='18sp', color=(1, 0.84, 0, 1),
                          pos=(0, self.height * 0.52), size=(self.width, 40))
        
        play_btn = Button(text="PLAY GAME", font_size='22sp', bold=True, 
                          background_color=(0, 0.8, 0.5, 1),
                          pos=(self.width / 2 - 120, self.height * 0.36), size=(240, 55))
        play_btn.bind(on_press=lambda x: [self.play_click(), self.start_game()])

        shop_btn = Button(text="SHOP & UPGRADES", font_size='18sp', bold=True, 
                          background_color=(0.8, 0.2, 0.8, 1),
                          pos=(self.width / 2 - 120, self.height * 0.23), size=(240, 55))
        shop_btn.bind(on_press=lambda x: [self.play_click(), self.show_shop()])

        self.add_widget(title)
        self.add_widget(high_score_lbl)
        self.add_widget(coins_lbl)
        self.add_widget(play_btn)
        self.add_widget(shop_btn)
        self.ui_elements.extend([title, high_score_lbl, coins_lbl, play_btn, shop_btn])

    def show_shop(self):
        self.state = 'shop'
        self.clear_ui()
        self.canvas.before.clear()
        self.canvas.clear()

        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            RoundedRectangle(pos=self.pos, size=self.size)

        title = Label(text="SHOP & POWER-UP UPGRADES", font_size='20sp', bold=True, color=(0.8, 0.2, 0.8, 1),
                      pos=(0, self.height * 0.86), size=(self.width, 40))
        coins_lbl = Label(text=f"Coins: {self.total_coins}", font_size='18sp', color=(1, 0.84, 0, 1),
                          pos=(0, self.height * 0.79), size=(self.width, 30))
        self.add_widget(title)
        self.add_widget(coins_lbl)
        self.ui_elements.extend([title, coins_lbl])

        y_pos = self.height * 0.67

        # Magnet Upgrade Row
        mag_cost = self.magnet_level * 20
        mag_status = f"LVL {self.magnet_level} (UPG: {mag_cost}🪙)" if self.magnet_level < 5 else "MAX LEVEL"
        mag_lbl = Label(text=f"🧲 Magnet ({self.magnet_level * 2 + 4}s)", font_size='14sp', bold=True, pos=(self.width * 0.05, y_pos), size=(160, 35))
        mag_btn = Button(text=mag_status, font_size='12sp', bold=True, background_color=(0.2, 0.5, 0.8, 1),
                         pos=(self.width * 0.50, y_pos), size=(190, 35))
        mag_btn.bind(on_press=lambda x: [self.play_click(), self.upgrade_powerup('magnet')])
        self.add_widget(mag_lbl)
        self.add_widget(mag_btn)
        self.ui_elements.extend([mag_lbl, mag_btn])

        y_pos -= 45

        # Jetpack Upgrade Row
        jet_cost = self.jetpack_level * 25
        jet_status = f"LVL {self.jetpack_level} (UPG: {jet_cost}🪙)" if self.jetpack_level < 5 else "MAX LEVEL"
        jet_lbl = Label(text=f"🚀 Jetpack ({self.jetpack_level * 2 + 3}s)", font_size='14sp', bold=True, pos=(self.width * 0.05, y_pos), size=(160, 35))
        jet_btn = Button(text=jet_status, font_size='12sp', bold=True, background_color=(0.8, 0.4, 0.1, 1),
                         pos=(self.width * 0.50, y_pos), size=(190, 35))
        jet_btn.bind(on_press=lambda x: [self.play_click(), self.upgrade_powerup('jetpack')])
        self.add_widget(jet_lbl)
        self.add_widget(jet_btn)
        self.ui_elements.extend([jet_lbl, jet_btn])

        y_pos -= 50
        char_header = Label(text="CHARACTER SKINS (All Unlocked)", font_size='16sp', bold=True, color=(0, 1, 0.8, 1), pos=(0, y_pos), size=(self.width, 30))
        self.add_widget(char_header)
        self.ui_elements.append(char_header)

        y_pos -= 45
        for char in CHARACTERS:
            is_unlocked = char['id'] in self.unlocked_chars
            is_selected = char['id'] == self.selected_char
            status_text = "EQUIPPED" if is_selected else ("EQUIP" if is_unlocked else f"BUY ({char['cost']}🪙)")
            bg_col = (0.2, 0.6, 0.2, 1) if is_selected else ((0.2, 0.4, 0.8, 1) if is_unlocked else (0.8, 0.5, 0.1, 1))

            char_lbl = Label(text=f"{char['name']}", font_size='14sp', bold=True, pos=(self.width * 0.05, y_pos), size=(160, 35))
            action_btn = Button(text=status_text, font_size='13sp', bold=True, background_color=bg_col,
                                pos=(self.width * 0.50, y_pos), size=(190, 35))
            action_btn.bind(on_press=lambda x, cid=char['id'], cost=char['cost']: [self.play_click(), self.handle_shop_action(cid, cost)])

            self.add_widget(char_lbl)
            self.add_widget(action_btn)
            self.ui_elements.extend([char_lbl, action_btn])
            y_pos -= 42

        back_btn = Button(text="BACK TO MENU", font_size='15sp', bold=True, background_color=(0.5, 0.5, 0.5, 1),
                          pos=(self.width / 2 - 110, 15), size=(220, 40))
        back_btn.bind(on_press=lambda x: [self.play_click(), self.show_menu()])
        self.add_widget(back_btn)
        self.ui_elements.append(back_btn)

    def upgrade_powerup(self, p_type):
        if p_type == 'magnet' and self.magnet_level < 5:
            cost = self.magnet_level * 20
            if self.total_coins >= cost:
                self.total_coins -= cost
                self.magnet_level += 1
                self.save_game_data()
        elif p_type == 'jetpack' and self.jetpack_level < 5:
            cost = self.jetpack_level * 25
            if self.total_coins >= cost:
                self.total_coins -= cost
                self.jetpack_level += 1
                self.save_game_data()
        self.show_shop()

    def handle_shop_action(self, char_id, cost):
        if char_id in self.unlocked_chars:
            self.selected_char = char_id
        elif self.total_coins >= cost:
            self.total_coins -= cost
            self.unlocked_chars.append(char_id)
            self.selected_char = char_id
            self.save_game_data()
        self.show_shop()

    def start_game(self):
        self.state = 'playing'
        self.clear_ui()
        self.score = 0
        self.session_coins = 0
        self.obstacles.clear()
        self.coins.clear()
        self.powerups.clear()
        self.player_lane = 1
        self.player_action = 'run'
        self.action_timer = 0.0
        self.magnet_active = False
        self.magnet_timer = 0.0
        self.jetpack_active = False
        self.jetpack_timer = 0.0

        self.score_label = Label(
            text="SCORE: 0   COINS: 0",
            font_size='20sp',
            bold=True,
            pos=(0, self.height - 60),
            size=(self.width, 40)
        )
        self.add_widget(self.score_label)
        self.ui_elements.append(self.score_label)

    # --- GAMEPLAY LOOP ---
    def spawn_entities(self, dt):
        if self.state != 'playing':
            return
            
        lane = random.choice([0, 1, 2])
        lane_width = self.width / 3
        center_x = (lane * lane_width) + (lane_width / 2)
        
        rand_val = random.random()
        if rand_val > 0.45:
            obs_type = 'ground' if random.random() > 0.4 else 'overhead'
            self.obstacles.append({
                'x': center_x - 38,
                'y': self.height + 50,
                'w': 76,
                'h': 70 if obs_type == 'ground' else 50,
                'type': obs_type,
                'lane': lane
            })
        elif rand_val > 0.20:
            self.coins.append({
                'x': center_x - 20, 'y': self.height + 50, 'r': 22, 'lane': lane
            })
        elif rand_val > 0.10:
            self.powerups.append({
                'x': center_x - 22, 'y': self.height + 50, 'r': 24, 'lane': lane, 'type': 'magnet'
            })
        else:
            self.powerups.append({
                'x': center_x - 22, 'y': self.height + 50, 'r': 24, 'lane': lane, 'type': 'jetpack'
            })

    def update_game(self, dt):
        if self.state != 'playing':
            return

        self.score += 1
        speed = 12 + (self.score // 150)
        self.bg_offset = (self.bg_offset + speed) % 50

        if self.player_action != 'run':
            self.action_timer -= dt
            if self.action_timer <= 0:
                self.player_action = 'run'

        lane_width = self.width / 3
        player_x = (self.player_lane * lane_width) + (lane_width / 2) - 30
        
        if self.jetpack_active:
            player_y = 280
            player_h = 95
        elif self.player_action == 'jump':
            player_y = 210
            player_h = 95
        elif self.player_action == 'slide':
            player_y = 100
            player_h = 45
        else:
            player_y = 100
            player_h = 95

        player_w = 60
        player_center_x = player_x + (player_w / 2)
        player_center_y = player_y + (player_h / 2)

        if self.magnet_active:
            self.magnet_timer -= dt
            if self.magnet_timer <= 0:
                self.magnet_active = False

        if self.jetpack_active:
            self.jetpack_timer -= dt
            if random.random() < 0.3:
                spawn_lane = random.choice([0, 1, 2])
                self.coins.append({
                    'x': (spawn_lane * lane_width) + (lane_width / 2) - 20,
                    'y': self.height + 50,
                    'r': 22,
                    'lane': spawn_lane
                })
            if self.jetpack_timer <= 0:
                self.jetpack_active = False

        for obs in self.obstacles[:]:
            obs['y'] -= speed
            if not self.jetpack_active:
                if obs['lane'] == self.player_lane:
                    if obs['type'] == 'ground' and self.player_action != 'jump':
                        if obs['y'] < player_y + player_h and obs['y'] + obs['h'] > player_y:
                            self.trigger_game_over()
                    elif obs['type'] == 'overhead' and self.player_action != 'slide':
                        if obs['y'] < player_y + player_h and obs['y'] + obs['h'] > player_y:
                            self.trigger_game_over()
            if obs['y'] < -100:
                self.obstacles.remove(obs)

        for p in self.powerups[:]:
            p['y'] -= speed
            if (p['lane'] == self.player_lane and 
                p['y'] < player_y + player_h and 
                p['y'] + (p['r'] * 2) > player_y):
                
                if p['type'] == 'magnet':
                    self.magnet_active = True
                    self.magnet_timer = 4.0 + (self.magnet_level * 2)
                elif p['type'] == 'jetpack':
                    self.jetpack_active = True
                    self.jetpack_timer = 3.0 + (self.jetpack_level * 2)
                
                if self.coin_sound:
                    self.coin_sound.play()
                self.powerups.remove(p)
            elif p['y'] < -100:
                self.powerups.remove(p)

        for coin in self.coins[:]:
            coin['y'] -= speed
            coin_center_x = coin['x'] + coin['r']
            coin_center_y = coin['y'] + coin['r']

            if self.magnet_active:
                dx = player_center_x - coin_center_x
                dy = player_center_y - coin_center_y
                dist = (dx**2 + dy**2)**0.5
                if dist < 350:
                    coin['x'] += dx * 0.15
                    coin['y'] += dy * 0.15

            dx_coll = player_center_x - (coin['x'] + coin['r'])
            dy_coll = player_center_y - (coin['y'] + coin['r'])
            dist_coll = (dx_coll**2 + dy_coll**2)**0.5

            if dist_coll < 45:
                self.session_coins += 1
                if self.coin_sound:
                    self.coin_sound.play()
                self.coins.remove(coin)
            elif coin['y'] < -100:
                self.coins.remove(coin)

        status_extra = ""
        if self.jetpack_active:
            status_extra += f" | 🚀 JET: {int(self.jetpack_timer)}s"
        if self.magnet_active:
            status_extra += f" | 🧲 MAG: {int(self.magnet_timer)}s"
            
        self.score_label.text = f"SCORE: {self.score}   COINS: {self.session_coins}{status_extra}"
        self.redraw_game()

    def redraw_game(self):
        self.canvas.before.clear()
        self.canvas.clear()
        
        lane_width = self.width / 3
        theme_tier = (self.score // 300) % 3
        bg_color = (0.08, 0.08, 0.12, 1) if theme_tier == 0 else ((0.12, 0.05, 0.15, 1) if theme_tier == 1 else (0.05, 0.12, 0.1, 1))

        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size)
            
            Color(0, 0.9, 1, 0.2)
            Line(points=[lane_width, 0, lane_width, self.height], width=2)
            Line(points=[lane_width * 2, 0, lane_width * 2, self.height], width=2)

        with self.canvas:
            player_x = (self.player_lane * lane_width) + (lane_width / 2) - 30
            player_y = 280 if self.jetpack_active else (210 if self.player_action == 'jump' else 100)
            player_h = 45 if self.player_action == 'slide' else 95
            
            if self.magnet_active:
                Color(0.7, 0, 1, 0.3)
                Ellipse(pos=(player_x - 20, player_y - 15), size=(100, 125))

            if self.jetpack_active:
                Color(1, 0.5, 0, 1)
                Ellipse(pos=(player_x + 15, player_y - 25), size=(30, 35))

            char_profile = CHARACTERS[self.selected_char]
            Color(*char_profile['color'])
            RoundedRectangle(pos=(player_x, player_y), size=(60, player_h), radius=[10])
            
            if self.player_action != 'slide':
                Color(*char_profile['visor'])
                RoundedRectangle(pos=(player_x + 10, player_y + (player_h - 40)), size=(40, 20), radius=[5])

            for obs in self.obstacles:
                if obs['type'] == 'ground':
                    Color(1, 0.1, 0.4, 1)
                    RoundedRectangle(pos=(obs['x'], obs['y']), size=(obs['w'], obs['h']), radius=[8])
                else:
                    Color(1, 0.8, 0.1, 1)
                    RoundedRectangle(pos=(obs['x'], obs['y'] + 60), size=(obs['w'], 25), radius=[5])

            for p in self.powerups:
                if p['type'] == 'magnet':
                    Color(0.8, 0, 1, 1)
                else:
                    Color(1, 0.5, 0, 1)
                Ellipse(pos=(p['x'], p['y']), size=(p['r'] * 2, p['r'] * 2))
                Color(1, 1, 1, 0.9)
                Ellipse(pos=(p['x'] + 8, p['y'] + 8), size=((p['r'] - 5) * 2, (p['r'] - 5) * 2))

            for coin in self.coins:
                Color(1, 0.84, 0, 1)
                Ellipse(pos=(coin['x'], coin['y']), size=(coin['r'] * 2, coin['r'] * 2))
                Color(1, 1, 1, 0.9)
                Ellipse(pos=(coin['x'] + 8, coin['y'] + 8), size=((coin['r'] - 4) * 2, (coin['r'] - 4) * 2))

    def on_touch_down(self, touch):
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        if self.state == 'game_over':
            self.play_click()
            self.show_menu()

    def on_touch_up(self, touch):
        if self.state != 'playing':
            return
        
        dx = touch.x - self.touch_start_x
        dy = touch.y - self.touch_start_y
        
        if abs(dx) > abs(dy) and abs(dx) > 30:
            if dx > 0 and self.player_lane < 2:
                self.player_lane += 1
            elif dx < 0 and self.player_lane > 0:
                self.player_lane -= 1
        elif abs(dy) > abs(dx) and abs(dy) > 30:
            if dy > 0:
                self.player_action = 'jump'
                self.action_timer = 0.6
            else:
                self.player_action = 'slide'
                self.action_timer = 0.5

    def trigger_game_over(self):
        self.state = 'game_over'
        
        is_new_high = False
        if self.score > self.high_score:
            self.high_score = self.score
            is_new_high = True

        self.total_coins += self.session_coins
        self.save_game_data()

        self.clear_ui()
        
        high_score_text = "\n🔥 NEW HIGH SCORE! 🔥" if is_new_high else f"\nBEST SCORE: {self.high_score}"
        
        over_lbl = Label(
            text=f"GAME OVER!\nSCORE: {self.score}{high_score_text}\nCOINS EARNED: +{self.session_coins}\n\n[ TAP ANYWHERE TO RETURN ]",
            font_size='22sp',
            bold=True,
            halign='center',
            color=(1, 1, 1, 1),
            pos=(0, self.height * 0.25),
            size=(self.width, self.height * 0.5)
        )
        self.add_widget(over_lbl)
        self.ui_elements.append(over_lbl)

class RunnerApp(App):
    def build(self):
        return RunnerGame()

if __name__ == '__main__':
    RunnerApp().run()
