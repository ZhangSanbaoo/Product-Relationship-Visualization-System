from __future__ import annotations
import sys
from pathlib import Path

APP_NAME = "PRVS"

def get_project_root() -> Path:
    """
    onedir 打包后：资源就在 exe 同目录（dist/PRVS/）
    开发态：项目根目录（core/ 的上一级）
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]

def ensure_writable_assets(project_root: Path) -> tuple[Path, Path]:
    """
    onedir：直接使用 exe 同目录（或项目根）下的 data.sqlite3 和 img/
    不再迁移到 AppData。
    """
    db_path = project_root / "data.sqlite3"
    img_dir = project_root / "img"
    img_dir.mkdir(parents=True, exist_ok=True)
    return db_path, img_dir
