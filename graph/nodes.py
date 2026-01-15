import base64
import io
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st
from streamlit_agraph import Node

from core.settings import BASE_DIR, IMG_W, GRAPH_THUMB


def img_path_or_none(image_path: str | None) -> Optional[Path]:
    """把数据库相对路径转为实际路径（不存在则返回 None）。"""
    if not image_path:
        return None
    p = BASE_DIR / image_path
    return p if p.exists() else None


@st.cache_data(show_spinner=False)
def image_to_data_uri_and_luma(path_str: str, thumb: int = GRAPH_THUMB) -> Tuple[str, float]:
    """
    生成 data URI（用于 circularImage），并计算平均亮度 luma。

    注意：
    - luma 目前不用于动态字体色，但保留输出便于后续扩展
    """
    p = Path(path_str)
    raw = p.read_bytes()

    luma = 255.0
    try:
        from PIL import Image

        im = Image.open(io.BytesIO(raw)).convert("RGBA")
        im.thumbnail((thumb, thumb))

        rgb = im.convert("RGB")
        w, h = rgb.size
        n = w * h
        if n > 0:
            total = 0.0
            for r, g, b in rgb.getdata():
                total += 0.2126 * r + 0.7152 * g + 0.0722 * b
            luma = total / n

        buf = io.BytesIO()
        im.save(buf, format="PNG")
        data = buf.getvalue()
    except Exception:
        data = raw
        luma = 255.0

    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}", float(luma)


def _short(s: str, n: int = 10) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[:n] + "…"


def node_for_product(
    node_id: str,
    name: str,
    image_path: str | None,
    *,
    level: Optional[int] = None,
    x: Optional[int] = None,
    y: Optional[float] = None,
    fixed: bool = False,
    hover_extra: Optional[str] = None,
) -> Node:
    """
    构造 agraph Node。

    支持影子节点（用于全局关系图避免合并）：
    - A01@@UP@@L3@@weak
    """
    raw_id = node_id
    base_code = raw_id.split("@@")[0]

    # 影子节点信息（L1/weak）如果你后续要用可以保留，但不要显示在 label 上
    # extra = ""
    # if "@@" in raw_id:
    #     parts = raw_id.split("@@")
    #     if len(parts) >= 4:
    #         extra = f"{parts[2]} | {parts[3]}"

    # label：只显示 code + name
    label = f"{base_code}\n{_short(name, 10)}"


    title = f"{base_code} | {name}"
    if hover_extra:
        title += f"\n{hover_extra}"

    imgp = img_path_or_none(image_path)

    kwargs = dict(
        id=raw_id,
        label=label,
        title=title,
        font={"color": "#FFFFFF"},
    )

    if imgp:
        uri, _ = image_to_data_uri_and_luma(str(imgp))
        kwargs.update(image=uri, shape="circularImage", size=32)
    else:
        kwargs.update(shape="box", size=28)
        kwargs["label"] = label + "\n(无图)"

    if x is not None:
        kwargs["x"] = int(x)
    if y is not None:
        kwargs["y"] = float(y)
    if fixed:
        kwargs["fixed"] = {"x": True, "y": True}

    n = Node(**kwargs)

    if level is not None:
        try:
            n.level = int(level)
        except Exception:
            n = Node(**{**n.__dict__, "level": int(level)})

    return n


def show_image_with_zoom(path: Path, thumb_w: int = IMG_W) -> None:
    """卡片图展示：缩略图 + 放大查看。"""
    raw = path.read_bytes()

    try:
        from PIL import Image

        im = Image.open(path).convert("RGBA")
        w, h = im.size
        if w > thumb_w:
            new_h = int(h * (thumb_w / w))
            im = im.resize((thumb_w, new_h), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        st.image(buf.getvalue(), width=thumb_w)
    except Exception:
        st.image(raw, width=thumb_w)

    if hasattr(st, "popover"):
        with st.popover("🔍 放大查看"):
            st.image(raw, width="stretch")
    else:
        with st.expander("🔍 放大查看"):
            st.image(raw, width="stretch")


def save_product_image_overwrite(code: str, name: str, uploaded_file, img_dir: Path) -> str:
    """
    保存产品图片：同型号覆盖，并清理同 base 的旧后缀残留。

    Returns:
        相对路径（写入 DB），如 img/A01_产品名.png
    """

    def safe_filename(s: str) -> str:
        s = (s or "").strip()
        for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "\n", "\r", "\t"]:
            s = s.replace(ch, "_")
        s = " ".join(s.split())
        return s

    code = safe_filename(code)
    name = safe_filename(name)

    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        ext = ".png"

    base = f"{code}_{name}"
    filename = f"{base}{ext}"

    for old in img_dir.glob(f"{base}.*"):
        try:
            old.unlink()
        except Exception:
            pass

    dst = img_dir / filename
    with dst.open("wb") as f:
        f.write(uploaded_file.getbuffer())

    return f"img/{filename}"
