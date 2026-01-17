import os
import sys
import shutil
import tempfile
import time
import webbrowser
import threading
import socket
from pathlib import Path


def wait_and_open(host: str, port: int, timeout: float = 15.0):
    """等 Streamlit 真正监听端口后再打开浏览器，避免机器慢导致打不开。"""
    url = f"http://{host}:{port}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                webbrowser.open(url)
                return
        except OSError:
            time.sleep(0.2)
    # 超时不报错，用户可以从 CMD 日志看到 URL 手动打开


def find_app(root: Path) -> Path:
    for p in [root / "app.py", root / "_internal" / "app.py"]:
        if p.exists():
            return p
    hits = list(root.rglob("app.py"))
    if hits:
        return hits[0]
    raise FileNotFoundError(f"app.py not found under {root}")


def ensure_user_assets(root: Path):
    """把 _internal 里的初始资源复制到 exe 同目录（仅第一次）"""
    internal = root / "_internal"

    # sqlite
    src_db = internal / "data.sqlite3"
    dst_db = root / "data.sqlite3"
    if (not dst_db.exists()) and src_db.exists():
        shutil.copy2(src_db, dst_db)

    # img
    src_img = internal / "img"
    dst_img = root / "img"
    if (not dst_img.exists()) and src_img.exists():
        shutil.copytree(src_img, dst_img)


def main():
    root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent

    ensure_user_assets(root)

    # 隔离 streamlit 配置 + 关闭 developmentMode
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    tmp_cfg = Path(tempfile.gettempdir()) / "prvs_streamlit"
    tmp_cfg.mkdir(parents=True, exist_ok=True)
    os.environ["STREAMLIT_CONFIG_DIR"] = str(tmp_cfg)

    # 工作目录固定到 exe 同目录（配合你的 PROJECT_ROOT 逻辑）
    os.chdir(root)

    # 让 Python 一定能找到打包后的本地模块
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "_internal"))

    app_path = find_app(root)

    host = "127.0.0.1"
    port = 8501

    # ✅ 关键：启动前开一个线程等待端口起来再打开浏览器
    threading.Thread(target=wait_and_open, args=(host, port), daemon=True).start()

    from streamlit.web.cli import main as stcli
    sys.argv = [
        "streamlit", "run", str(app_path),
        f"--server.port={port}",
        f"--server.address={host}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    stcli()


if __name__ == "__main__":
    main()
