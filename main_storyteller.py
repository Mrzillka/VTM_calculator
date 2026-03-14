import logging
import sys
from pathlib import Path

# Allow imports from the project root (game/, lang.py, config.py, etc.)
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_app_data_dir
from ui.storyteller.root import Root

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