"""
右侧 AI 对话面板：基于数据库内容的 RAG 问答。

状态机: unloaded → loading → loaded
加载/卸载由用户手动控制，不自动吃显存。
"""
import streamlit as st

from core.llm_engine import (
    list_local_models, detect_vram_mb, recommend_ctx,
    load_local_model, load_api_client, unload,
    get_state, get_model_name, is_ready,
    chat_stream, build_messages,
    PRESET_PROVIDERS, PRESET_NAMES,
    load_api_config, save_api_config,
)
from core.rag_context import build_system_prompt_full, build_system_prompt_compact


def _status_indicator() -> str:
    """状态指示: 灰=未加载  黄=加载中  绿=就绪"""
    s = get_state()
    if s == "loaded":
        return "🟢"
    if s == "loading":
        return "🟡"
    return "⚪"


def render_chat_panel() -> None:
    state = get_state()
    model_name = get_model_name()

    st.caption(f"{_status_indicator()} {model_name or '未加载'}")

    # ── 模型设置 ──
    with st.expander(":material/tune: 模型设置", expanded=(state != "loaded")):

        if state == "loaded":
            # 已加载 → 显示信息 + 卸载按钮
            st.success(f"已加载: {model_name}")
            if st.button("卸载模型", key="btn_unload", icon=":material/eject:",
                         use_container_width=True, type="secondary"):
                unload()
                st.rerun()

        else:
            # 未加载 → 选择模式和配置
            mode = st.radio("模式", ["本地 GGUF", "在线 API"],
                            horizontal=True, key="llm_mode_radio",
                            disabled=(state == "loading"))

            if mode == "本地 GGUF":
                models = list_local_models()
                if not models:
                    st.warning(
                        "models/ 文件夹内无 .gguf 文件。\n\n"
                        "请将模型放入项目根目录的 `models/` 文件夹。"
                    )
                else:
                    model_pick = st.selectbox("选择模型", models, key="gguf_model_pick",
                                              disabled=(state == "loading"))

                    # 检测显存（缓存在 session 中，可通过删除 key 刷新）
                    if "_vram_mb" not in st.session_state or st.session_state["_vram_mb"] == 0:
                        st.session_state["_vram_mb"] = detect_vram_mb()
                    vram = st.session_state["_vram_mb"]
                    rec_ctx = recommend_ctx(vram)

                    if vram > 0:
                        st.caption(f"检测到显存: {vram} MB · 推荐上下文: {rec_ctx}")
                    else:
                        st.caption(f"未检测到 GPU · 默认上下文: {rec_ctx}")

                    # 上下文长度滑块
                    n_ctx = st.slider(
                        "上下文长度", min_value=512, max_value=131072, step=256,
                        value=rec_ctx, key="_ctx_slider",
                        disabled=(state == "loading"),
                    )

                    n_gpu = st.number_input("GPU 层数 (-1=全部)", value=-1,
                                             min_value=-1, step=1, key="gguf_gpu",
                                             disabled=(state == "loading"))

                    if state == "loading":
                        st.info("加载中，请稍候...")
                    else:
                        if st.button("加载模型", key="btn_load_local",
                                     icon=":material/download:",
                                     use_container_width=True):
                            with st.spinner("正在加载模型..."):
                                msg = load_local_model(model_pick, int(n_ctx), int(n_gpu))
                            if get_state() == "loaded":
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

            else:  # 在线 API
                # 加载已保存的配置
                saved = load_api_config()
                saved_preset = saved.get("preset", "自定义")
                saved_base_url = saved.get("base_url", "")
                saved_api_key = saved.get("api_key", "")
                saved_model = saved.get("model", "")

                # 服务商下拉框
                default_idx = (PRESET_NAMES.index(saved_preset)
                               if saved_preset in PRESET_NAMES else
                               len(PRESET_NAMES) - 1)
                preset_pick = st.selectbox(
                    "服务商", PRESET_NAMES,
                    index=default_idx, key="api_preset_pick",
                    disabled=(state == "loading"),
                )

                is_custom = (preset_pick == "自定义")

                if not is_custom:
                    idx = PRESET_NAMES.index(preset_pick)
                    _, preset_url, default_model, model_hint = PRESET_PROVIDERS[idx]
                    base_url = st.text_input(
                        "API Base URL", value=preset_url, key="api_url",
                        disabled=(state == "loading"),
                    )
                    model_input = st.text_input(
                        "模型名", value=saved_model if saved_preset == preset_pick else default_model,
                        key="api_model", disabled=(state == "loading"),
                        help=f"可用: {model_hint}",
                    )
                else:
                    base_url = st.text_input(
                        "API Base URL", value=saved_base_url, key="api_url",
                        placeholder="https://api.openai.com/v1",
                        disabled=(state == "loading"),
                    )
                    model_input = st.text_input(
                        "模型名", value=saved_model, key="api_model",
                        placeholder="模型名称",
                        disabled=(state == "loading"),
                    )

                api_key = st.text_input(
                    "API Key", value=saved_api_key, key="api_key",
                    type="password", disabled=(state == "loading"),
                )

                if state == "loading":
                    st.info("连接中，请稍候...")
                else:
                    if st.button("连接 API", key="btn_load_api",
                                 icon=":material/cloud:",
                                 use_container_width=True):
                        if not base_url.strip() or not model_input.strip():
                            st.error("请填写 URL 和模型名")
                        else:
                            save_api_config(
                                preset_pick, base_url.strip(),
                                api_key.strip(), model_input.strip(),
                            )
                            with st.spinner("正在连接..."):
                                msg = load_api_client(
                                    base_url.strip(), api_key.strip(), model_input.strip()
                                )
                            if get_state() == "loaded":
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    # ── 未就绪时提示并返回 ──
    if not is_ready():
        st.caption("请先加载模型或连接 API 后开始对话")
        return

    # ── 初始化聊天记录 ──
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # ── 间距 ──
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # ── 消息区域（可滚动） ──
    chat_box = st.container(height=450)
    with chat_box:
        if not st.session_state.chat_messages:
            st.caption("基于数据库内容提问，例如：「有哪些产品线？」")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # ── 间距 ──
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # ── 输入 ──
    prompt = st.chat_input("输入问题...", key="chat_input")

    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        # 根据模式选择 prompt 策略：本地模型用精简+按需补充，在线 API 用全量
        llm_mode = st.session_state.get("_llm_mode")
        history = st.session_state.chat_messages[:-1]
        if llm_mode == "local":
            system_prompt = build_system_prompt_compact(prompt, history)
        else:
            system_prompt = build_system_prompt_full()

        messages = build_messages(
            system_prompt,
            history,
            prompt,
        )

        with chat_box:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                response = st.write_stream(chat_stream(messages))

        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

    # ── 间距 + 清空 ──
    if st.session_state.get("chat_messages"):
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
        if st.button("清空对话", key="btn_clear_chat",
                     icon=":material/delete_sweep:",
                     use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
