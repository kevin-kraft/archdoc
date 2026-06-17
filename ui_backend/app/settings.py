from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings:
    project_name: str = "utilis"
    generated_static_dir: Path
    user_stories_dir: Path
    overlay_path: Path
    db_path: Path

    def __init__(self) -> None:
        self.generated_static_dir = Path(
            os.getenv(
                "ARCHDOC_STATIC_DIR",
                ROOT_DIR / "site" / "static" / "archdoc",
            )
        ).resolve()
        self.user_stories_dir = Path(
            os.getenv(
                "ARCHDOC_USER_STORIES_DIR",
                ROOT_DIR / "docs" / "architecture" / "user-stories",
            )
        ).resolve()
        self.overlay_path = Path(
            os.getenv(
                "ARCHDOC_OVERLAY_PATH",
                ROOT_DIR / "docs" / "architecture" / "overlays" / "review-overlay.json",
            )
        ).resolve()
        self.db_path = Path(
            os.getenv(
                "ARCHDOC_DB_PATH",
                ROOT_DIR / "docs" / "architecture" / "archdoc-review.sqlite3",
            )
        ).resolve()


settings = Settings()
