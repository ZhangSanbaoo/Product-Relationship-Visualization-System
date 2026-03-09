"""
LLM 引擎：支持本地 GGUF 模型（llama-cpp-python）和在线 API（OpenAI 兼容）。

状态机: unloaded → loading → loaded
聊天使用 get_llm_if_loaded()，不自动加载，用户手动控制。
"""
import json
import os
import re
from pathlib import Path
from typing import Generator

import streamlit as st

from core.settings import BASE_DIR

MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

MAX_HISTORY_ROUNDS_API = 10    # 在线 API: 保留最近 10 轮
MAX_HISTORY_ROUNDS_LOCAL = 3   # 本地 GGUF: 保留最近 3 轮（省上下文空间）

API_CONFIG_PATH = BASE_DIR / "api_config.json"

# ── 预设服务商 ────────────────────────────────────────────
# 格式: (显示名, base_url, 默认模型, 常用模型提示)
PRESET_PROVIDERS: list[tuple[str, str, str, str]] = [
    ("OpenAI",      "https://api.openai.com/v1",
     "gpt-4o-mini", "gpt-4o / gpt-4o-mini / o3-mini"),
    ("DeepSeek",    "https://api.deepseek.com/v1",
     "deepseek-chat", "deepseek-chat / deepseek-reasoner"),
    ("通义千问",     "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "qwen-plus",   "qwen-max / qwen-plus / qwen-turbo"),
    ("智谱 GLM",    "https://open.bigmodel.cn/api/paas/v4",
     "glm-4-flash", "glm-4 / glm-4-flash"),
    ("Moonshot",    "https://api.moonshot.cn/v1",
     "moonshot-v1-8k", "moonshot-v1-8k / moonshot-v1-32k"),
    ("SiliconFlow", "https://api.siliconflow.cn/v1",
     "",            "见平台模型列表"),
]

PRESET_NAMES = [name for name, _, _, _ in PRESET_PROVIDERS] + ["自定义"]


# ── API 配置持久化 ────────────────────────────────────────

def load_api_config() -> dict:
    """从本地 JSON 读取已保存的 API 配置。"""
    if API_CONFIG_PATH.exists():
        try:
            return json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_api_config(preset: str, base_url: str, api_key: str, model: str) -> None:
    """将 API 配置保存到本地 JSON。"""
    data = {
        "preset": preset,
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }
    API_CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 模型扫描 ──────────────────────────────────────────────

def list_local_models() -> list[str]:
    """扫描 models/ 目录下的 .gguf 文件。"""
    if not MODELS_DIR.exists():
        return []
    return sorted(
        f.name for f in MODELS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() == ".gguf"
    )


# ── 显存检测 & 推荐 ──────────────────────────────────────

def detect_vram_mb() -> int:
    """尝试检测 GPU 显存（MB），失败返回 0。"""
    # 方法1: pynvml
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        return int(info.total / 1024 / 1024)
    except Exception:
        pass
    # 方法2: torch
    try:
        import torch
        if torch.cuda.is_available():
            return int(torch.cuda.get_device_properties(0).total_mem / 1024 / 1024)
    except Exception:
        pass
    # 方法3: nvidia-smi 子进程
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return 0


def recommend_ctx(vram_mb: int) -> int:
    """根据显存推荐上下文长度。"""
    if vram_mb <= 0:
        return 2048
    if vram_mb < 4096:
        return 2048
    if vram_mb < 8192:
        return 4096
    if vram_mb < 16384:
        return 8192
    if vram_mb < 24576:
        return 16384
    return 32768


# ── 状态管理 ─────────────────────────────────────────────

def get_state() -> str:
    """返回当前状态: unloaded / loading / loaded"""
    return st.session_state.get("_llm_state", "unloaded")


def get_model_name() -> str | None:
    return st.session_state.get("_llm_model_name")


def is_ready() -> bool:
    return get_state() == "loaded"


# ── 加载 / 卸载 ──────────────────────────────────────────

def load_local_model(model_name: str, n_ctx: int = 4096, n_gpu_layers: int = -1) -> str:
    """加载本地 GGUF 模型，返回状态消息。"""
    try:
        from llama_cpp import Llama
    except ImportError:
        return "错误：未安装 llama-cpp-python。请运行: pip install llama-cpp-python"

    model_path = str(MODELS_DIR / model_name)
    if not os.path.isfile(model_path):
        return f"错误：文件不存在 {model_path}"

    st.session_state["_llm_state"] = "loading"

    try:
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )
        st.session_state["_llm_instance"] = model
        st.session_state["_llm_mode"] = "local"
        st.session_state["_llm_api_client"] = None
        st.session_state["_llm_model_name"] = model_name
        st.session_state["_llm_state"] = "loaded"
        return f"已加载: {model_name}"
    except Exception as e:
        st.session_state["_llm_state"] = "unloaded"
        return f"加载失败: {e}"


def load_api_client(base_url: str, api_key: str, model: str) -> str:
    """连接 OpenAI 兼容 API，返回状态消息。"""
    try:
        from openai import OpenAI
    except ImportError:
        return "错误：未安装 openai。请运行: pip install openai"

    st.session_state["_llm_state"] = "loading"

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        st.session_state["_llm_api_client"] = {"client": client, "model": model}
        st.session_state["_llm_mode"] = "api"
        st.session_state["_llm_instance"] = None
        st.session_state["_llm_model_name"] = model
        st.session_state["_llm_state"] = "loaded"
        return f"已连接: {model}"
    except Exception as e:
        st.session_state["_llm_state"] = "unloaded"
        return f"连接失败: {e}"


def unload() -> None:
    """卸载模型 / 断开 API，释放资源。"""
    inst = st.session_state.get("_llm_instance")
    if inst is not None:
        # llama-cpp-python Llama 没有显式 close，删引用让 GC 回收
        del inst
    st.session_state["_llm_instance"] = None
    st.session_state["_llm_api_client"] = None
    st.session_state["_llm_mode"] = None
    st.session_state["_llm_model_name"] = None
    st.session_state["_llm_state"] = "unloaded"


# ── 消息构建 ─────────────────────────────────────────────

def build_messages(system_prompt: str, history: list[dict], user_msg: str) -> list[dict]:
    """
    组装完整消息列表: system + 最近 N 轮历史 + 当前用户消息。
    前端维护完整历史，后端根据模式截断。
    """
    mode = st.session_state.get("_llm_mode")
    max_rounds = MAX_HISTORY_ROUNDS_LOCAL if mode == "local" else MAX_HISTORY_ROUNDS_API

    msgs = [{"role": "system", "content": system_prompt}]
    msgs.extend(history[-(max_rounds * 2):])
    msgs.append({"role": "user", "content": user_msg})
    return msgs


# ── think 标签过滤 ────────────────────────────────────────

def _filter_think_tags(raw_stream) -> Generator[str, None, None]:
    """
    流式过滤 <think>...</think> 标签（Qwen3 / DeepSeek-R1 等推理模型）。
    使用状态机，边接收边过滤。
    """
    in_think = False
    buf = ""

    for token in raw_stream:
        if not token:
            continue
        buf += token

        while buf:
            if in_think:
                m = re.search(r"</think>", buf, re.I)
                if m:
                    buf = buf[m.end():]
                    in_think = False
                else:
                    # 防内存泄漏，只保留尾部
                    if len(buf) > 20:
                        buf = buf[-20:]
                    break
            else:
                m = re.search(r"<think>", buf, re.I)
                if m:
                    if m.start():
                        yield buf[:m.start()]
                    buf = buf[m.end():]
                    in_think = True
                else:
                    lt = buf.rfind("<")
                    if 0 <= lt > len(buf) - 10:
                        yield buf[:lt]
                        buf = buf[lt:]
                        break
                    else:
                        yield buf
                        buf = ""
                        break

    if buf and not in_think:
        yield buf


# ── 流式生成 ─────────────────────────────────────────────

def _raw_stream_local(messages: list[dict]) -> Generator[str, None, None]:
    model = st.session_state.get("_llm_instance")
    if not model:
        yield "错误：模型未加载"
        return
    response = model.create_chat_completion(
        messages=messages, stream=True,
        temperature=0.5, max_tokens=1024,
    )
    for chunk in response:
        delta = chunk["choices"][0].get("delta", {})
        content = delta.get("content", "")
        if content:
            yield content


def _raw_stream_api(messages: list[dict]) -> Generator[str, None, None]:
    api_info = st.session_state.get("_llm_api_client")
    if not api_info:
        yield "错误：API 未连接"
        return
    stream = api_info["client"].chat.completions.create(
        model=api_info["model"],
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content


def chat_stream(messages: list[dict]) -> Generator[str, None, None]:
    """流式生成回复，自动过滤 think 标签。"""
    mode = st.session_state.get("_llm_mode")

    try:
        if mode == "local":
            yield from _filter_think_tags(_raw_stream_local(messages))
        elif mode == "api":
            yield from _filter_think_tags(_raw_stream_api(messages))
        else:
            yield "请先加载模型或连接 API"
    except Exception as e:
        yield f"\n\n[错误] {e}"
