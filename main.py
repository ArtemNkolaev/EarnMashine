import arcade
import random
from pyglet.graphics import Batch
import time

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

    def on_update(self, delta_time):
        for reel in self.reels:
            reel.update()
        if self.is_game_spinning:
            spinning_reels = [r for r in self.reels if r.is_spinning]
            if not spinning_reels:
                self.is_game_spinning = False
                self.check_win()

    def spin_all_reels(self):
        if self.balance < self.spin_cost:
            return
        self.balance -= self.spin_cost
        self.info_text = f"Balance: ${self.balance} | Bet: ${self.bet}"
        for reel in self.reels:
            reel.start_spin(random.uniform(1.5, 2.5))
        self.is_game_spinning = True

    def check_win(self):
        symbols = [SYMBOLS[r.current_symbol_idx]["emoji"] for r in self.reels]
        if symbols[0] == symbols[1] == symbols[2]:
            symbol_idx = self.reels[0].current_symbol_idx
            multiplier = SYMBOLS[symbol_idx]["multiplier"]
            win_amount = self.bet * multiplier
            self.balance += win_amount
            self.info_text = f"JACKPOT! {symbols[0]} x{multiplier} = +${win_amount} | Balance: ${self.balance}"
        else:
            self.info_text = f"Balance: ${self.balance} | Bet: ${self.bet}"

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.spin_button.check_click(x, y) and not self.is_game_spinning:
            self.spin_button.is_pressed = True
            self.spin_all_reels()

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.spin_button.is_pressed = False










def main():
    game = EarnMashine()
    arcade.play_sound(background_music, volume=0.9, loop=True)
    arcade.run()


if __name__ == "__main__":
    main()
