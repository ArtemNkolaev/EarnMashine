import arcade
import random
import time
import sys
import sqlite3
from PyQt6 import QtWidgets
from pyglet.graphics import Batch



DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 1000,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            total_spins INTEGER DEFAULT 0,
            total_wins INTEGER DEFAULT 0,
            total_win_amount INTEGER DEFAULT 0,
            lose_streak INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


class LoginWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EarnMashine Login")
        self.setGeometry(500, 300, 350, 250)

        self.user_authenticated = False
        self.user_id = None

        self.initial_balance = 1000
        self.initial_bet = 10

        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)


        self.balance_input = QtWidgets.QLineEdit()
        self.balance_input.setPlaceholderText("Initial Balance (e.g. 2000)")
        layout.addWidget(self.balance_input)

        self.bet_input = QtWidgets.QLineEdit()
        self.bet_input.setPlaceholderText("Initial Bet (e.g. 10)")
        layout.addWidget(self.bet_input)

        self.apply_button = QtWidgets.QPushButton("Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(self.apply_button)


        self.info_label = QtWidgets.QLabel("")
        layout.addWidget(self.info_label)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self.login_user)
        layout.addWidget(self.login_button)

        self.register_button = QtWidgets.QPushButton("Register")
        self.register_button.clicked.connect(self.register_user)
        layout.addWidget(self.register_button)

        self.setLayout(layout)


    def apply_settings(self):
        try:
            balance = int(self.balance_input.text())
            bet = int(self.bet_input.text())
            if balance <= 0 or bet <= 0:
                self.info_label.setText("Balance and bet must be > 0")
                return
            self.initial_balance = balance
            self.initial_bet = bet
            self.info_label.setText(f"Applied: Balance=${balance}, Bet=${bet}")
        except ValueError:
            self.info_label.setText("Enter valid integers for balance and bet")

    def login_user(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (self.username_input.text(), self.password_input.text())
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            self.user_authenticated = True
            self.user_id = result[0]
            self.close()
        else:
            self.info_label.setText("Invalid username or password")

    def register_user(self):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (self.username_input.text(), self.password_input.text())
            )

            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO progress (user_id, balance) VALUES (?, ?)",
                (user_id, self.initial_balance)
            )

            conn.commit()
            conn.close()

            self.info_label.setText("Registration successful!")

        except sqlite3.IntegrityError:
            self.info_label.setText("Username already exists")

def run_login():
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    app.exec()
    return window.user_authenticated, window.user_id, window.initial_balance, window.initial_bet


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN_TITLE = "EarnMashine"

background_music = arcade.load_sound("music/music.mp3")

SYMBOLS = [
    {"emoji": "🍒", "multiplier": 2, "weight": 30},
    {"emoji": "🍋", "multiplier": 3, "weight": 25},
    {"emoji": "🔔", "multiplier": 5, "weight": 20},
    {"emoji": "🥝", "multiplier": 10, "weight": 15},
    {"emoji": "🍌", "multiplier": 20, "weight": 10},
]


class ThemeManager:

    def __init__(self):
        self.current_theme = "light"
        self.themes = {}
        self.load_themes()

    def load_themes(self):
        self.themes["light"] = {
            "background": arcade.color.ARMY_GREEN,
            "reel_bg": arcade.color.DARK_GRAY,
            "reel_border": arcade.color.GOLD,
            "button": arcade.color.GREEN,
            "text": arcade.color.WHITE
        }

        self.themes["dark"] = {
            "background": arcade.color.BLACK,
            "reel_bg": arcade.color.DARK_SLATE_GRAY,
            "reel_border": arcade.color.GOLD,
            "button": arcade.color.DARK_GREEN,
            "text": arcade.color.WHITE
        }

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"

    def get(self, key):
        return self.themes[self.current_theme][key]



class EarnMashine(arcade.Window):

    def __init__(self, user_id, initial_balance=1000, initial_bet=10):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.user_id = user_id
        self.theme_manager = ThemeManager()

        self.initial_balance = initial_balance
        self.initial_bet = initial_bet

        self.load_progress()

        self.reels = [
            Reel(350, 350),
            Reel(450, 350),
            Reel(550, 350)
        ]

        self.spin_button = Button(450, 100, 160, 50, "SPIN")
        self.theme_button = Button(820, 560, 120, 35, "THEME")


        self.bet_plus_button = Button(650, 100, 50, 40, "+")
        self.bet_minus_button = Button(250, 100, 50, 40, "-")

        self.is_game_spinning = False

        self.apply_theme()


    def apply_theme(self):
        arcade.set_background_color(self.theme_manager.get("background"))

        for reel in self.reels:
            reel.bg_color = self.theme_manager.get("reel_bg")
            reel.border_color = self.theme_manager.get("reel_border")

        self.spin_button.color = self.theme_manager.get("button")
        self.bet_plus_button.color = self.theme_manager.get("button")
        self.bet_minus_button.color = self.theme_manager.get("button")


    def load_progress(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT balance, level, xp,
                   total_spins, total_wins,
                   total_win_amount, lose_streak
            FROM progress WHERE user_id=?
        """, (self.user_id,))

        result = cursor.fetchone()
        if result:
            (
                self.balance,
                self.level,
                self.xp,
                self.total_spins,
                self.total_wins,
                self.total_win_amount,
                self.lose_streak
            ) = result
        else:
            self.balance = self.initial_balance
            self.level = 1
            self.xp = 0
            self.total_spins = 0
            self.total_wins = 0
            self.total_win_amount = 0
            self.lose_streak = 0

        conn.close()

        self.bet = self.initial_bet
        self.xp_to_next = 100

    def save_progress(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE progress SET
            balance=?, level=?, xp=?,
            total_spins=?, total_wins=?,
            total_win_amount=?, lose_streak=?
            WHERE user_id=?
        """, (
            self.balance,
            self.level,
            self.xp,
            self.total_spins,
            self.total_wins,
            self.total_win_amount,
            self.lose_streak,
            self.user_id
        ))

        conn.commit()
        conn.close()



    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.level_up()

    def level_up(self):
        self.xp -= self.xp_to_next
        self.level += 1
        self.xp_to_next = int(self.xp_to_next * 1.5)
        self.balance += 50


    def increase_bet(self):
        self.bet += 5

    def decrease_bet(self):
        if self.bet > 5:
            self.bet -= 5


    def on_draw(self):
        self.clear()

        for reel in self.reels:
            reel.draw()

        self.spin_button.draw()
        self.theme_button.draw()
        self.bet_plus_button.draw()
        self.bet_minus_button.draw()

        arcade.draw_text(
            f"Balance: ${self.balance}",
            20, SCREEN_HEIGHT - 40,
            self.theme_manager.get("text"), 18
        )
        arcade.draw_text(
            f"LEVEL: {self.level}  XP: {self.xp}/{self.xp_to_next}",
            20, SCREEN_HEIGHT - 65,
            self.theme_manager.get("text"), 14
        )
        arcade.draw_text(
            f"SPINS: {self.total_spins}  WINS: {self.total_wins}",
            20, SCREEN_HEIGHT - 90,
            self.theme_manager.get("text"), 14
        )
        arcade.draw_text(
            f"BET: ${self.bet}",
            SCREEN_WIDTH // 2,
            160,
            self.theme_manager.get("text"),
            18,
            anchor_x="center"
        )

    def on_update(self, delta_time):
        for reel in self.reels:
            reel.update()

        if self.is_game_spinning and not any(r.is_spinning for r in self.reels):
            self.is_game_spinning = False
            self.check_win()
            self.save_progress()



    def spin_all_reels(self):
        if self.balance < self.bet:
            return

        self.balance -= self.bet
        self.total_spins += 1
        self.add_xp(10)

        for reel in self.reels:
            reel.start_spin()

        self.is_game_spinning = True

    def check_win(self):
        ids = [r.current_symbol_idx for r in self.reels]

        if ids[0] == ids[1] == ids[2]:
            win = self.bet * SYMBOLS[ids[0]]["multiplier"]
            self.balance += win
            self.total_wins += 1
            self.total_win_amount += win
            self.lose_streak = 0
            self.add_xp(25)
        else:
            self.lose_streak += 1
            self.add_xp(5)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.spin_button.check_click(x, y) and not self.is_game_spinning:
            self.spin_all_reels()

        if self.theme_button.check_click(x, y):
            self.theme_manager.toggle_theme()
            self.apply_theme()

        if self.bet_plus_button.check_click(x, y):
            self.increase_bet()

        if self.bet_minus_button.check_click(x, y):
            self.decrease_bet()



class Reel:

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.current_symbol_idx = 0
        self.is_spinning = False
        self.bg_color = arcade.color.DARK_GRAY
        self.border_color = arcade.color.GOLD

    def start_spin(self):
        self.is_spinning = True
        self.stop_time = time.time() + random.uniform(1.5, 2.5)

    def update(self):
        if self.is_spinning:
            self.current_symbol_idx = random.randint(0, len(SYMBOLS) - 1)
            if time.time() >= self.stop_time:
                self.is_spinning = False

    def draw(self):
        arcade.draw_lbwh_rectangle_filled(
            self.x - 45, self.y - 70, 90, 140, self.bg_color
        )
        arcade.draw_lbwh_rectangle_outline(
            self.x - 45, self.y - 70, 90, 140, self.border_color, 3
        )
        arcade.draw_text(
            SYMBOLS[self.current_symbol_idx]["emoji"],
            self.x, self.y,
            arcade.color.WHITE, 48,
            anchor_x="center", anchor_y="center"
        )



class Button:

    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = arcade.color.GRAY

    def draw(self):
        arcade.draw_lbwh_rectangle_filled(
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.width,
            self.height,
            self.color
        )
        arcade.draw_text(
            self.text,
            self.x, self.y,
            arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center"
        )

    def check_click(self, x, y):
        return (
            self.x - self.width / 2 <= x <= self.x + self.width / 2 and
            self.y - self.height / 2 <= y <= self.y + self.height / 2
        )



def main():
    init_db()
    ok, user_id, init_balance, init_bet = run_login()
    if ok:
        arcade.play_sound(background_music, loop=True, volume=0.8)
        EarnMashine(user_id, init_balance, init_bet)
        arcade.run()

if __name__ == "__main__":
    main()
