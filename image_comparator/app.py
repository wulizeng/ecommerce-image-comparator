import time
import streamlit as st
import pandas as pd
from comparator import compare, CompareResult
from reporter import generate_excel_bytes

st.set_page_config(page_title="电商链接图片相似度比对", layout="wide", page_icon="🔍")

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
    font-size: 14px;
}
.stApp { background: #f8fafc; }
.block-container { padding: 0 !important; max-width: 100% !important; }
footer, #MainMenu, header { visibility: hidden; }

/* ── 主内容区 ── */
.main { max-width: 900px; margin: 0 auto; padding: 0 24px 60px; }

/* ── 顶栏 ── */
.topbar { max-width: 900px; margin: 0 auto; padding: 10px 24px 0; }

/* ── 卡片 ── */
.card {
    background: #ffffff;
    border: 1px solid rgba(99,102,241,0.1);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(99,102,241,0.06);
    transition: border-color .2s, box-shadow .2s;
}
.card:hover { border-color: rgba(99,102,241,0.25); box-shadow: 0 4px 16px rgba(99,102,241,0.1); }
.card-label {
    font-size: 10px; font-weight: 700; color: rgba(99,102,241,0.6);
    letter-spacing: .1em; text-transform: uppercase; margin-bottom: 14px;
}

/* ── 胶囊 Tab ── */
[data-testid="stTabs"] [role="tablist"] {
    background: #f1f5f9 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: none !important;
    margin-bottom: 0 !important;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 7px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #64748b !important;
    padding: 6px 24px !important;
    border: none !important;
    background: transparent !important;
    transition: all .15s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {
    color: #6366f1 !important;
    background: rgba(99,102,241,0.06) !important;
}
[data-testid="stTabs"] { margin-top: -72px !important; }
[data-testid="stTabPanel"] { padding-top: 16px !important; background: transparent !important; }

/* ── 输入框 ── */
.stTextInput input {
    background: #f8fafc !important;
    border: 1.5px solid rgba(99,102,241,0.2) !important;
    border-radius: 8px !important;
    color: #1a1b2e !important;
    font-size: 14px !important;
    padding: 0 14px !important;
    height: 40px !important;
    box-sizing: border-box !important;
    transition: all .18s !important;
}
.stTextInput input:focus {
    border-color: #6366f1 !important;
    background: #fff !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}
.stTextInput input::placeholder { color: rgba(0,0,0,0.25) !important; }
.stTextInput label { display: none !important; }
.stTextInput { margin-bottom: 0 !important; padding-bottom: 0 !important; overflow: visible !important; }
[data-testid="stTextInput"] > div { margin-bottom: 0 !important; overflow: visible !important; }

/* ── 按钮 ── */
.stButton button {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    height: 40px !important;
    padding: 0 18px !important;
    transition: all .18s !important;
    letter-spacing: .02em !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3) !important;
}
.stButton button[kind="primary"]:hover {
    box-shadow: 0 4px 18px rgba(99,102,241,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton button:not([kind="primary"]) {
    background: #ffffff !important;
    color: rgba(0,0,0,0.55) !important;
    border: 1.5px solid rgba(0,0,0,0.12) !important;
}
.stButton button:not([kind="primary"]):hover {
    border-color: rgba(99,102,241,0.35) !important;
    color: #6366f1 !important;
    background: rgba(99,102,241,0.04) !important;
}

/* ── 进度条 ── */
.stProgress > div { background: rgba(0,0,0,0.06) !important; border-radius: 99px !important; height: 4px !important; }
.stProgress > div > div { background: linear-gradient(90deg,#6366f1,#a78bfa) !important; border-radius: 99px !important; }

/* ── 文件上传 ── */
[data-testid="stFileUploader"] section {
    background: rgba(99,102,241,0.02) !important;
    border: 1.5px dashed rgba(99,102,241,0.3) !important;
    border-radius: 10px !important;
    padding: 24px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #6366f1 !important;
    background: rgba(99,102,241,0.05) !important;
}

/* ── 下载按钮 ── */
[data-testid="stDownloadButton"] button {
    background: #ffffff !important;
    color: #6366f1 !important;
    border: 1.5px solid rgba(99,102,241,0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    color: #fff !important;
    border-color: transparent !important;
}

/* ── 批量结果表格全宽 ── */
[data-testid="stDataFrame"] {
    width: 80vw !important;
    max-width: 80vw !important;
    margin-left: calc((900px - 80vw) / 2) !important;
}

/* ── 其他 ── */
[data-testid="stAlert"] { border-radius: 10px !important; font-size: 13px !important; }
[data-testid="stSpinner"] p { color: #6366f1 !important; font-size: 13px !important; }
.stCaption { color: rgba(0,0,0,0.35) !important; }
[data-testid="stModal"] > div { border-radius: 14px !important; background: #ffffff !important; }
</style>
""", unsafe_allow_html=True)


# ── 设置弹窗 ─────────────────────────────────────────
@st.dialog("API 配置")
def settings_dialog():
    st.markdown('<p style="font-size:13px;color:rgba(0,0,0,0.5);margin-bottom:12px;">填写千问大模型 API Key 以启用图片语义精判</p>', unsafe_allow_html=True)
    api_key = st.text_input("Qwen API Key", type="password",
                            placeholder="sk-xxxxxxxxxxxxxxxx",
                            value=st.session_state.get("api_key", ""))
    if st.button("保存配置", type="primary", use_container_width=True):
        if api_key:
            import config as _cfg
            _cfg.QWEN_API_KEY = api_key
            st.session_state["api_key"] = api_key
            st.success("API Key 已保存（当前会话有效）")
        else:
            st.warning("API Key 不能为空")


# ── 顶栏 ─────────────────────────────────────────────
st.markdown('<div class="topbar">', unsafe_allow_html=True)
st.markdown("""
    <div style="text-align:center;margin-bottom:8px;">
        <div style="font-size:13px;font-weight:600;color:#6366f1;letter-spacing:.18em;
                    text-transform:uppercase;margin-bottom:6px;opacity:0.7;">
            E-COMMERCE · IMAGE ANALYSIS
        </div>
        <div style="font-size:24px;font-weight:800;color:#1a1b2e;
                    letter-spacing:-0.03em;line-height:1.1;">
            电商链接图片相似度比对
        </div>
        <div style="width:32px;height:2px;background:linear-gradient(90deg,#6366f1,#8b5cf6);
                    border-radius:2px;margin:8px auto 0;"></div>
    </div>
""", unsafe_allow_html=True)

_spacer, _btn1, _btn2 = st.columns([9.08, 0.46, 0.46])
with _btn1:
    if st.button("刷新", key="refresh_btn", use_container_width=True):
        for k in ["url_a", "url_b"]:
            st.session_state[k] = ""
        st.rerun()
with _btn2:
    if st.button("设置", key="settings_btn", use_container_width=True):
        settings_dialog()

st.markdown('<div style="border-bottom:1px solid rgba(0,0,0,0.08);margin-top:-4px;"></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 主内容区 ─────────────────────────────────────────
st.markdown('<div class="main">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["单条比对", "批量比对"])

with tab1:
    # ── 输入区 ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([5, 5, 2])
    with c1:
        url1 = st.text_input("A", placeholder="粘贴图片 A URL...", label_visibility="collapsed", key="url_a")
    with c2:
        url2 = st.text_input("B", placeholder="粘贴图片 B URL...", label_visibility="collapsed", key="url_b")
    with c3:
        run = st.button("比 对", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if run:
        if not st.session_state.get("api_key", ""):
            st.warning("请先点击右上角「设置」按钮，填写 API Key 后再进行比对。")
            st.stop()
        with st.spinner("正在分析，请稍候..."):
            _t0 = time.time()
            result = compare(url1.strip(), url2.strip(), api_key=st.session_state.get("api_key", ""))
            _elapsed = time.time() - _t0

        if result.method == "error":
            st.error(f"比对失败：{result.error}")
        else:
            is_same = result.is_same
            score = result.similarity_score

            if is_same:
                v_bg = "#dcfce7"; v_bdr = "rgba(22,163,74,0.3)"
                v_clr = "#16a34a"; v_txt = "✓  图片一致"
                stamp_clr = "#16a34a"; stamp_txt = "相同"; stamp_bg = "rgba(22,163,74,0.08)"
            else:
                v_bg = "rgba(239,68,68,0.08)"; v_bdr = "rgba(239,68,68,0.25)"
                v_clr = "#dc2626"; v_txt = "✕  图片不一致"
                stamp_clr = "#dc2626"; stamp_txt = "不同"; stamp_bg = "rgba(239,68,68,0.06)"

            score_clr = "#16a34a" if score >= 80 else ("#d97706" if score >= 50 else "#dc2626")

            st.markdown(f"""
            <div class="card">
                <div class="card-label">比对结果</div>
                <div style="display:flex;align-items:center;justify-content:center;gap:28px;flex-wrap:wrap;">
                    <span style="background:{v_bg};border:1px solid {v_bdr};color:{v_clr};
                        border-radius:8px;padding:8px 18px;font-size:15px;font-weight:700;
                        white-space:nowrap;">{v_txt}</span>
                    <div style="text-align:center;">
                        <div style="font-size:11px;color:#94a3b8;
                            text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">相似度</div>
                        <div style="font-size:32px;font-weight:700;color:{score_clr};line-height:1;">{score}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:11px;color:#94a3b8;
                            text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">建议</div>
                        <div style="font-size:14px;font-weight:500;color:#374151;">{result.recommendation}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:11px;color:#94a3b8;
                            text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">耗时</div>
                        <div style="font-size:24px;font-weight:700;color:{v_clr};line-height:1;">
                            {_elapsed:.2f}<span style="font-size:12px;font-weight:400;
                            color:rgba(0,0,0,0.35);margin-left:2px;">s</span></div>
                    </div>
                </div>
                <div style="margin-top:10px;">
                    <span style="font-size:11px;color:#6366f1;background:rgba(99,102,241,0.08);
                        padding:3px 10px;border-radius:6px;border:1px solid rgba(99,102,241,0.2);
                        font-weight:500;">{result.method}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── 分析步骤 ──
            _status_icon = {"done": "✅", "skip": "⏭", "fail": "❌"}
            _status_clr  = {"done": "#16a34a", "skip": "#94a3b8", "fail": "#dc2626"}
            _steps_html = "".join([
                f'<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;">'
                f'<div style="min-width:22px;font-size:15px;line-height:1.6;">{_status_icon.get(s["status"], "●")}</div>'
                f'<div>'
                f'<div style="font-size:12px;font-weight:700;color:{_status_clr.get(s["status"], "#374151")};margin-bottom:2px;">步骤 {s["step"]}：{s["name"]}</div>'
                f'<div style="font-size:12px;color:rgba(0,0,0,0.55);line-height:1.7;">{s["detail"]}</div>'
                f'</div></div>'
                for s in result.steps
            ])
            st.markdown(f"""
            <div class="card">
                <div style="font-size:11px;color:#6366f1;font-weight:600;
                    letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px;">分析步骤</div>
                {_steps_html}
            </div>
            """, unsafe_allow_html=True)

        # ── 图片预览 ──
        st.markdown(f"""
        <div class="card">
            <div class="card-label">图片预览</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div>
                    <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">图片 A</div>
                    <div style="max-height:260px;overflow:hidden;border-radius:8px;background:#f8fafc;">
                        <img src="{url1}" style="width:100%;height:260px;object-fit:contain;display:block;"/>
                    </div>
                </div>
                <div>
                    <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">图片 B</div>
                    <div style="max-height:260px;overflow:hidden;border-radius:8px;background:#f8fafc;">
                        <img src="{url2}" style="width:100%;height:260px;object-fit:contain;display:block;"/>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">上传数据文件</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:13px;color:rgba(0,0,0,0.5);margin-bottom:16px;">
        Excel 需包含
        <code style="background:rgba(99,102,241,0.08);padding:2px 7px;border-radius:5px;
            color:#6366f1;font-weight:500;">宝贝ID</code>、
        <code style="background:rgba(99,102,241,0.08);padding:2px 7px;border-radius:5px;
            color:#6366f1;font-weight:500;">url1</code>
        和
        <code style="background:rgba(99,102,241,0.08);padding:2px 7px;border-radius:5px;
            color:#6366f1;font-weight:500;">url2</code>
        三列（宝贝ID 可为空）
    </p>
    """, unsafe_allow_html=True)

    _, stop_col = st.columns([9.4, 0.6])
    with stop_col:
        if st.button("⏹ 终止", key="stop_btn", use_container_width=True):
            st.session_state["batch_cancel"] = True
            st.rerun()

    uploaded = st.file_uploader("拖拽或点击上传 Excel 文件（.xlsx / .xls）",
                                type=["xlsx", "xls"], label_visibility="visible")

    import io as _io
    from openpyxl import Workbook as _Workbook
    _wb = _Workbook(); _ws = _wb.active
    _ws.append(["宝贝ID", "url1", "url2"])
    _ws.append(["123456789", "https://img.example.com/a.jpg", "https://img.example.com/b.jpg"])
    _buf = _io.BytesIO(); _wb.save(_buf)
    tmpl_col, _ = st.columns([2, 8])
    with tmpl_col:
        st.download_button("⬇ 下载模板", data=_buf.getvalue(),
                           file_name="比对模板.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded:
        try:
            df = pd.read_excel(uploaded)
            if "url1" not in df.columns or "url2" not in df.columns:
                st.error("格式错误：必须包含 url1 和 url2 两列")
                st.stop()

            st.markdown(f'<p style="font-size:13px;color:rgba(0,0,0,0.5);margin:8px 0 16px;">已解析 <strong style="color:#6366f1;font-size:15px;">{len(df)}</strong> 条记录</p>', unsafe_allow_html=True)

            _, bcol, _ = st.columns([3, 4, 3])
            with bcol:
                start_clicked = st.button("开始批量比对", type="primary", use_container_width=True)

            if start_clicked:
                    if not st.session_state.get("api_key", ""):
                        st.warning("请先点击右上角「设置」按钮，填写 API Key 后再进行批量比对。")
                        st.stop()
                    item_ids = df["宝贝ID"].astype(str).str.strip() if "宝贝ID" in df.columns else [""] * len(df)
                    pairs = list(zip(
                        item_ids,
                        df["url1"].astype(str).str.strip(),
                        df["url2"].astype(str).str.strip()
                    ))
                    pairs = [(iid, u1, u2) for iid, u1, u2 in pairs if u1 != "nan" and u2 != "nan"]
                    total = len(pairs)
                    if total == 0:
                        st.error("无有效数据（url1/url2 均不能为空）")
                        st.stop()

                    st.session_state["batch_cancel"] = False
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.markdown(f'<div style="text-align:center;font-size:13px;color:#6366f1;margin-top:4px;">⏳ 0 / {total} · 已用时 0.0s</div>', unsafe_allow_html=True)
                    start_time = time.time()
                    _api_key = st.session_state.get("api_key", "")

                    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
                    from config import BATCH_CONCURRENCY, COMPARE_TIMEOUT

                    results: list = [None] * total
                    done = 0

                    with ThreadPoolExecutor(max_workers=BATCH_CONCURRENCY) as executor:
                        fmap = {executor.submit(compare, u1, u2, _api_key): i
                                for i, (iid, u1, u2) in enumerate(pairs)}
                        for future in as_completed(fmap):
                            idx = fmap[future]
                            iid, u1, u2 = pairs[idx]
                            try:
                                results[idx] = future.result(timeout=COMPARE_TIMEOUT)
                            except FuturesTimeoutError:
                                results[idx] = CompareResult(
                                    url1=u1, url2=u2, is_same=False, similarity_score=0,
                                    recommendation="超时跳过", reason="处理超过30秒",
                                    method="error", error="timeout")
                            except Exception as e:
                                results[idx] = CompareResult(
                                    url1=u1, url2=u2, is_same=False, similarity_score=0,
                                    recommendation="处理异常", reason=str(e),
                                    method="error", error=str(e))
                            done += 1
                            elapsed = time.time() - start_time
                            remaining = (elapsed / done) * (total - done)
                            pct = int(done / total * 100)
                            progress_bar.progress(done / total)
                            status_text.markdown(
                                f'<div style="text-align:center;font-size:13px;color:#6366f1;margin-top:4px;">'
                                f'⏳ <strong>{done} / {total}</strong>（<strong>{pct}%</strong>）· 已用时 <strong>{elapsed:.1f}s</strong> · 预计剩余 <strong>{remaining:.0f}s</strong>'
                                f'</div>', unsafe_allow_html=True)
                            if st.session_state.get("batch_cancel"):
                                executor.shutdown(wait=False, cancel_futures=True)
                                status_text.markdown('<div style="text-align:center;font-size:13px;color:#d97706;font-weight:600;margin-top:4px;">⏹ 已终止</div>', unsafe_allow_html=True)
                                break

                    if not st.session_state.get("batch_cancel"):
                        progress_bar.progress(1.0)
                        status_text.markdown('<div style="text-align:center;font-size:13px;color:#16a34a;font-weight:600;margin-top:4px;">✓ 处理完成</div>', unsafe_allow_html=True)
                    # 结果持久化到 session_state，下载时不丢失
                    st.session_state["batch_results"] = results
                    st.session_state["batch_pairs"] = pairs

        except Exception as e:
            st.error(f"处理失败：{e}")

        # ── 结果展示（持久，下载不消失）──
        if st.session_state.get("batch_results"):
            results = st.session_state["batch_results"]
            pairs = st.session_state.get("batch_pairs", [])
            total = len(results)
            same_cnt = sum(1 for r in results if r and r.is_same)
            diff_cnt = total - same_cnt

            st.markdown(f"""
            <div style="display:flex;gap:12px;margin:20px 0 16px;flex-wrap:wrap;justify-content:center;">
                <div style="background:#ffffff;border:1px solid rgba(0,0,0,0.09);
                    border-radius:12px;padding:18px 28px;min-width:110px;text-align:center;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <div style="font-size:11px;color:#94a3b8;font-weight:600;
                        letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">总计</div>
                    <div style="font-size:32px;font-weight:700;color:#1a1b2e;line-height:1;">{total}</div>
                </div>
                <div style="background:#f0fdf4;border:1px solid rgba(22,163,74,0.2);
                    border-radius:12px;padding:18px 28px;min-width:110px;text-align:center;">
                    <div style="font-size:11px;color:#94a3b8;font-weight:600;
                        letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">图片一致</div>
                    <div style="font-size:32px;font-weight:700;color:#16a34a;line-height:1;">{same_cnt}</div>
                </div>
                <div style="background:#fff5f5;border:1px solid rgba(239,68,68,0.2);
                    border-radius:12px;padding:18px 28px;min-width:110px;text-align:center;">
                    <div style="font-size:11px;color:#94a3b8;font-weight:600;
                        letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">需调整</div>
                    <div style="font-size:32px;font-weight:700;color:#dc2626;line-height:1;">{diff_cnt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            _, dl_col, _ = st.columns([3, 4, 3])
            with dl_col:
                excel_bytes = generate_excel_bytes(results)
                st.download_button("⬇ 下载 Excel 报告", data=excel_bytes,
                                   file_name="比对结果.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True,
                                   key="dl_result")

st.markdown('</div>', unsafe_allow_html=True)
