from pathlib import Path
from core.runtime_paths import get_project_root, ensure_writable_assets

# -----------------------
# Paths
# -----------------------
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = get_project_root()
DB_PATH, IMG_DIR = ensure_writable_assets(PROJECT_ROOT)
IMG_DIR.mkdir(exist_ok=True)

# -----------------------
# UI constants
# -----------------------
IMG_W = 130
GRAPH_THUMB = 96

# -----------------------
# Graph layout constants
# -----------------------
X_GAP = 260
Y_GAP = 150
