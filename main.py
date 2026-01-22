import arcade
import random
from pyglet.graphics import Batch
import time
import threading


background_music = arcade.load_sound("music/music.mp3")


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN_TITLE = "EarnMashine"
SYMBOLS = [
    {"emoji": "🍒", "name": "Cherry", "multiplier": 2, "weight": 30},
    {"emoji": "🍋", "name": "Lemon", "multiplier": 3, "weight": 25},
    {"emoji": "🔔", "name": "Bell", "multiplier": 5, "weight": 20},
    {"emoji": "🥝", "name": "Kiwi", "multiplier": 10, "weight": 15},
    {"emoji": "🍌", "name": "Banana", "multiplier": 20, "weight": 10},
]


class EarnMashine(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.ARMY_GREEN)

        self.balance = 1000
        self.bet = 10
        self.spin_cost = 10

        reel_width = 180
        reel_height = 300
        reel_spacing = 20
        total_width = reel_width * 3 + reel_spacing * 2
        start_x = (SCREEN_WIDTH - total_width) / 2 + reel_width / 2
        self.reels = [
            Reel(start_x, 350, reel_width, reel_height),
            Reel(start_x + reel_width + reel_spacing, 350, reel_width, reel_height),
            Reel(start_x + (reel_width + reel_spacing) * 2, 350, reel_width, reel_height)
        ]

        self.spin_button = Button(
            x=SCREEN_WIDTH // 2, y=100,
            width=150, height=50,
            text=f"SPIN ({self.spin_cost}$)",
            color=arcade.color.GREEN
        )

        self.is_game_spinning = False
        self.info_text = f"Balance: ${self.balance} | Bet: ${self.bet}"

        self.level = 1
        self.xp = 0
        self.xp_to_next = 100

        self.autospin = False
        self.autospin_delay = 1.2
        self.last_autospin_time = 0


        self.total_spins = 0
        self.total_wins = 0
        self.total_win_amount = 0
        self.lose_streak = 0

        self.last_results = []
        self.win_flash = 0

    def on_draw(self):
        self.clear()
        for reel in self.reels:
            reel.draw()
        self.spin_button.draw()

        arcade.draw_text(
            self.info_text,
            SCREEN_WIDTH // 2, 180,
            arcade.color.WHITE, 20,
            align="center", anchor_x="center"
        )
        arcade.draw_text(
            f"LEVEL: {self.level}  XP: {self.xp}/{self.xp_to_next}",
            20, SCREEN_HEIGHT - 40,
            arcade.color.GOLD, 16
        )
        arcade.draw_text(
            f"SPINS: {self.total_spins}  WINS: {self.total_wins}",
            20, SCREEN_HEIGHT - 65,
            arcade.color.GOLD, 14
        )

        if self.win_flash > 0:
            arcade.draw_lrbt_rectangle_filled(
                left=0,
                right=SCREEN_WIDTH,
                bottom=0,
                top=SCREEN_HEIGHT,
                color=(255, 215, 0, 60)
            )


    def on_update(self, delta_time):
        for reel in self.reels:
            reel.update()

        if self.is_game_spinning:
            if not any(r.is_spinning for r in self.reels):
                self.is_game_spinning = False
                self.check_win()


        if self.autospin and not self.is_game_spinning:
            if time.time() - self.last_autospin_time >= self.autospin_delay:
                self.spin_all_reels()
                self.last_autospin_time = time.time()


        if self.win_flash > 0:
            self.win_flash -= delta_time

    def spin_all_reels(self):
        if self.balance < self.spin_cost:
            return

        self.balance -= self.spin_cost
        self.total_spins += 1
        self.add_xp(10)

        self.info_text = f"Balance: ${self.balance} | Bet: ${self.bet}"

        for reel in self.reels:
            reel.start_spin(random.uniform(1.5, 2.5))

        self.is_game_spinning = True

    def check_win(self):
        symbols = [SYMBOLS[r.current_symbol_idx]["emoji"] for r in self.reels]

        self.last_results.append(symbols)
        if len(self.last_results) > 5:
            self.last_results.pop(0)


        if symbols[0] == symbols[1] == symbols[2]:
            symbol_idx = self.reels[0].current_symbol_idx
            multiplier = SYMBOLS[symbol_idx]["multiplier"]
            win_amount = self.bet * multiplier

            self.balance += win_amount
            self.total_wins += 1
            self.total_win_amount += win_amount
            self.lose_streak = 0

            self.add_xp(25)

            self.win_flash = 0.4

            self.info_text = (
                f"JACKPOT! {symbols[0]} x{multiplier} "
                f"+${win_amount} | Balance: ${self.balance}"
            )

        else:
            self.lose_streak += 1
            self.add_xp(5)

            if self.lose_streak >= 5:
                bonus = 20
                self.balance += bonus
                self.lose_streak = 0
                self.info_text = f"BONUS +${bonus} for try again!"
            else:
                self.info_text = f"Balance: ${self.balance} | Bet: ${self.bet}"

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.spin_button.check_click(x, y) and not self.is_game_spinning:
            self.spin_button.is_pressed = True
            self.spin_all_reels()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.spin_button.is_pressed = False

    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            self.info_text = f"LEVEL UP! Level {self.level}"

class Reel:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.batch = Batch()

        self.reel_text = arcade.Text(
            "SPINNING...",
            self.x - self.width // 3,
            self.height - 80,
            arcade.color.YELLOW,
            16,
            align="center",
            batch=self.batch
        )

        self.current_symbol_idx = 0
        self.is_spinning = False
        self.spin_speed = 0.01
        self.last_spin_time = 0
        self.final_symbol_idx = 0
        self.bg_color = arcade.color.DARK_GRAY
        self.border_color = arcade.color.GOLD

    def start_spin(self, duration=1.5):
        self.is_spinning = True
        self.spin_start_time = time.time()
        self.spin_duration = duration
        self.last_symbol_change = time.time()
        weights = [s["weight"] for s in SYMBOLS]
        self.final_symbol_idx = random.choices(range(len(SYMBOLS)), weights=weights)[0]

    def update(self):
        if not self.is_spinning:
            return

        current_time = time.time()
        elapsed = current_time - self.spin_start_time

        if elapsed >= self.spin_duration:
            self.is_spinning = False
            self.current_symbol_idx = self.final_symbol_idx
            self.spin_speed = 0.1
            return

        if current_time - self.last_spin_time > self.spin_speed:
            self.current_symbol_idx = (self.current_symbol_idx + 1) % len(SYMBOLS)
            self.last_spin_time = current_time

            if elapsed > self.spin_duration * 0.7:
                self.spin_speed = min(self.spin_speed * 1.1, 0.3)

    def draw(self):
        arcade.draw_lbwh_rectangle_filled(
            self.x - self.width // 2, self.y - self.height // 3, self.width, self.height, self.bg_color
        )
        arcade.draw_lbwh_rectangle_outline(
            self.x - self.width // 2, self.y - self.height // 3, self.width, self.height, self.border_color, 3
        )
        symbol = SYMBOLS[self.current_symbol_idx]["emoji"]
        arcade.draw_text(
            symbol,
            self.x,
            self.y,
            arcade.color.WHITE,
            70,
            align="center",
            anchor_x="center",
            anchor_y="center"
        )
        if self.is_spinning:
            self.batch.draw()

class Button:
    def __init__(self, x, y, width, height, text,
                 color=arcade.color.GREEN,
                 text_color=arcade.color.WHITE):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.text_color = text_color
        self.is_pressed = False
        self.rect = (self.x - self.width, self.y - self.height, self.width * 2, self.height * 2)
        self.batch = Batch()
        self.but_text = arcade.Text(
            self.text, self.x - 31, self.y,
            self.text_color, 20,
            align="center", batch=self.batch
        )

    def draw(self):
        current_color = arcade.color.RED if self.is_pressed else self.color
        arcade.draw_lbwh_rectangle_filled(*self.rect, current_color)
        self.batch.draw()

    def check_click(self, x, y):
        return (self.x - self.width <= x <= self.x + self.width and
                self.y - self.height <= y <= self.y + self.height)

def main():
    game = EarnMashine()
    arcade.play_sound(background_music, volume=0.9, loop=True)
    arcade.run()

if __name__ == "__main__":
    main()
