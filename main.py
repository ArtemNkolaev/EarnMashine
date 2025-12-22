import arcade


class EarnMashine(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "EarnMashine")
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()


def main():
    game = EarnMashine()
    arcade.run()


if __name__ == "__main__":
    main()
