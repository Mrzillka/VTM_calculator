import logging

from config import ensure_app_data_dir
from ui.player.root import Root

logging.basicConfig(
    format="%(asctime)s  %(name)-5s  %(levelname)-5s  %(message)s",
    level=logging.INFO,
)


def main() -> None:
    ensure_app_data_dir()
    app = Root()
    app.mainloop()


if __name__ == "__main__":
    main()
