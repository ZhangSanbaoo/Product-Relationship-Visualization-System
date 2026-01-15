from pathlib import Path

# -----------------------
# Paths
# -----------------------
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data.sqlite3"
IMG_DIR = BASE_DIR / "img"
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

# 主线同格节点“菱形分布”偏移比例（相对于 gap）
DIAMOND_DX_RATIO = 0.18
DIAMOND_DY_RATIO = 0.35
