# UI 重设计实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重写 `image_comparator/app.py`，实现深色科技感 UI：顶栏居中标题 + 靠右按钮、胶囊 Tab、三列同行输入、横向结果数据条。

**Architecture:** 仅修改 `app.py` 一个文件，后端五个模块（comparator、phash、qwen_vl、downloader、reporter）完全不动。CSS 通过 `st.markdown` 注入，布局用 Streamlit 原生组件（`st.columns`、`st.tabs`、`st.text_input`、`st.button`）。

**Tech Stack:** Python 3.11+、Streamlit ≥1.35、openpyxl、pandas

---

## 文件结构

| 文件 | 操作 |
|---|---|
| `image_comparator/app.py` | 完整重写（唯一修改的文件） |

---

### Task 1: 全局 CSS + 页面配置

**Files:**
- Modify: `image_comparator/app.py`（全部替换）

- [ ] **Step 1: 写入页面配置和全局 CSS**

将 `app.py` 替换为以下内容（仅包含配置和 CSS，逻辑部分后续任务添加）：

```python
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
.stApp { background: #0f1117; }
.block-container { padding: 0 !important; max-width: 100% !important; }
footer, #MainMenu, header { visibility: hidden; }

/* ── 主内容区 ── */
.main { max-width: 860px; margin: 0 auto; padding: 28px 24px 60px; }

/* ── 顶栏 ── */
.topbar { padding: 22px 0 0; max-width: 860px; margin: 0 auto; }
.topbar-title {
    font-size: 24px; font-weight: 700; color: #fff;
    text-align: center; letter-spacing: -0.01em; margin-bottom: 10px;
}
.topbar-actions { display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 4px; }

/* ── st.tabs 胶囊样式 ── */
[data-testid="stTabs"] [role="tablist"] {
    background: rgba(255,255,255,0.06); border-radius: 10px;
    padding: 4px; gap: 2px; border: none !important;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 7px !important; font-size: 14px !important;
    font-weight: 500 !important; color: rgba(255,255,255,0.5) !important;
    padding: 6px 28px !important; border: none !important;
    background: transparent !important; transition: all .15s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important; box-shadow: 0 2px 10px rgba(99,102,241,0.4) !important;
}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {
    color: rgba(255,255,255,0.75) !important;
    background: rgba(255,255,255,0.06) !important;
}
[data-testid="stTabPanel"] { padding-top: 20px !important; background: transparent !important; }

/* ── 卡片 ── */
.card {
    background: #1a1b2e; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 20px 24px; margin-bottom: 14px;
    transition: border-color .2s;
}
.card:hover { border-color: rgba(99,102,241,0.3); }
.card-label {
    font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.35);
    letter-spacing: .08em; text-transform: uppercase; margin-bottom: 14px;
}

/* ── 输入框 ── */
.stTextInput input {
    background: #252640 !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important; color: #fff !important;
    font-size: 14px !important; padding: 10px 14px !important;
    height: auto !important; transition: all .18s !important;
}
.stTextInput input:focus {
    border-color: #6366f1 !important;
    background: rgba(99,102,241,0.08) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}
.stTextInput input::placeholder { color: rgba(255,255,255,0.25) !important; }
.stTextInput label { display: none !important; }

/* ── 按钮 ── */
.stButton button {
    border-radius: 9px !important; font-size: 14px !important;
    font-weight: 600 !important; height: 42px !important;
    padding: 0 20px !important; transition: all .18s !important;
    border: none !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #fff !important; box-shadow: 0 2px 12px rgba(99,102,241,0.35) !important;
}
.stButton button[kind="primary"]:hover {
    box-shadow: 0 4px 20px rgba(99,102,241,0.55) !important;
    transform: translateY(-1px) !important;
}
.stButton button[kind="primary"]:disabled {
    background: rgba(255,255,255,0.10) !important;
    color: rgba(255,255,255,0.3) !important;
    box-shadow: none !important; transform: none !important;
}
.stButton button:not([kind="primary"]) {
    background: rgba(255,255,255,0.07) !important;
    color: rgba(255,255,255,0.7) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
.stButton button:not([kind="primary"]):hover {
    background: rgba(255,255,255,0.12) !important; color: #fff !important;
}

/* ── 进度条 ── */
.stProgress > div { background: rgba(255,255,255,0.08) !important; border-radius: 99px !important; height: 5px !important; }
.stProgress > div > div { background: linear-gradient(90deg,#6366f1,#a78bfa) !important; border-radius: 99px !important; }

/* ── 文件上传 ── */
[data-testid="stFileUploader"] section {
    background: rgba(255,255,255,0.04) !important;
    border: 2px dashed rgba(99,102,241,0.35) !important;
    border-radius: 12px !important; padding: 28px !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #6366f1 !important; background: rgba(99,102,241,0.07) !important;
}
[data-testid="stFileUploader"] * { color: rgba(255,255,255,0.6) !important; }

/* ── 下载按钮 ── */
[data-testid="stDownloadButton"] button {
    background: rgba(255,255,255,0.07) !important; color: #818cf8 !important;
    border: 1px solid rgba(99,102,241,0.35) !important; border-radius: 9px !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    color: #fff !important; border-color: transparent !important;
}

/* ── 表格 ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid rgba(255,255,255,0.09); }
[data-testid="stDataFrame"] * { color: rgba(255,255,255,0.8) !important; }

/* ── 其他 ── */
[data-testid="stAlert"] { border-radius: 10px !important; font-size: 13px !important; }
[data-testid="stSpinner"] p { color: #818cf8 !important; font-size: 13px !important; }
.stCaption { color: rgba(255,255,255,0.4) !important; }
[data-testid="stModal"] > div { border-radius: 16px !important; background: #1e1f2e !important; }
</style>
""", unsafe_allow_html=True)
```

- [ ] **Step 2: 启动应用验证 CSS 加载（无报错即可）**

```bash
cd image_comparator
streamlit run app.py
```

Expected: 浏览器打开，背景变为深色 `#0f1117`，无 Python 报错。关闭后继续。

- [ ] **Step 3: Commit**

```bash
git add image_comparator/app.py
git commit -m "feat: add dark theme CSS for UI redesign"
```

---

### Task 2: 顶栏（标题居中 + 按钮靠右）+ 设置弹窗

**Files:**
- Modify: `image_comparator/app.py`（在 CSS 之后追加）

- [ ] **Step 1: 追加设置弹窗 + 顶栏代码**

在 Task 1 的 CSS `st.markdown` 之后，追加：

```python
# ── 设置弹窗 ─────────────────────────────────────────
@st.dialog("API 配置")
def settings_dialog():
    st.markdown('<p style="font-size:13px;color:rgba(255,255,255,0.5);margin-bottom:12px;">填写千问大模型 API Key 以启用图片语义精判</p>', unsafe_allow_html=True)
    api_key = st.text_input("Qwen API Key", type="password",
                            placeholder="sk-xxxxxxxxxxxxxxxx",
                            value=st.session_state.get("api_key", ""))
    if st.button("保存配置", type="primary", use_container_width=True):
        if api_key:
            import config, dashscope
            config.QWEN_API_KEY = api_key
            dashscope.api_key = api_key
            st.session_state["api_key"] = api_key
            st.success("API Key 已保存")
        else:
            st.warning("API Key 不能为空")


# ── 顶栏 ─────────────────────────────────────────────
st.markdown("""
<div style="max-width:860px;margin:0 auto;padding:22px 24px 0;">
    <div style="font-size:24px;font-weight:700;color:#fff;text-align:center;
                letter-spacing:-0.01em;margin-bottom:10px;">
        🔍 电商链接图片相似度比对
    </div>
</div>
""", unsafe_allow_html=True)

_spacer, _btn1, _btn2 = st.columns([8, 1, 1])
with _btn1:
    if st.button("设置", key="settings_btn", use_container_width=True):
        settings_dialog()
with _btn2:
    if st.button("刷新", key="refresh_btn", use_container_width=True):
        st.rerun()

st.markdown('<div style="border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:0;"></div>', unsafe_allow_html=True)
```

- [ ] **Step 2: 验证顶栏渲染**

```bash
streamlit run app.py
```

Expected: 顶部显示居中白色大标题，右侧有「设置」「刷新」两个次级按钮，下方有分隔线。点击「设置」弹出 API 配置弹窗。

- [ ] **Step 3: Commit**

```bash
git add image_comparator/app.py
git commit -m "feat: add topbar with centered title and right-aligned action buttons"
```

---

### Task 3: Tab 切换 + 主内容区骨架

**Files:**
- Modify: `image_comparator/app.py`（在顶栏之后追加）

- [ ] **Step 1: 追加主内容区和 Tab 骨架**

在顶栏代码之后追加：

```python
# ── 主内容区 ─────────────────────────────────────────
st.markdown('<div class="main">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["单条模式", "批量模式"])

with tab1:
    st.write("单条模式占位")  # Task 4 替换

with tab2:
    st.write("批量模式占位")  # Task 5 替换

st.markdown('</div>', unsafe_allow_html=True)
```

- [ ] **Step 2: 验证 Tab 渲染**

```bash
streamlit run app.py
```

Expected: 顶栏下方出现深色胶囊样式 Tab，「单条模式」选中时蓝紫渐变高亮，点击「批量模式」可切换，两个 Tab 均正常显示占位文字。

- [ ] **Step 3: Commit**

```bash
git add image_comparator/app.py
git commit -m "feat: add tab navigation with capsule style"
```

---

### Task 4: 单条模式（输入区 + 结果区 + 图片预览）

**Files:**
- Modify: `image_comparator/app.py`（替换 tab1 的 `st.write("单条模式占位")`）

- [ ] **Step 1: 替换 tab1 占位为完整单条模式代码**

将 `with tab1:` 块内容替换为：

```python
with tab1:
    # ── 输入区（三列同行）──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([5, 5, 2])
    with c1:
        url1 = st.text_input("A", placeholder="粘贴图片 A URL...", label_visibility="collapsed")
    with c2:
        url2 = st.text_input("B", placeholder="粘贴图片 B URL...", label_visibility="collapsed")
    with c3:
        run = st.button("比 对", type="primary", use_container_width=True,
                        disabled=not (url1 and url2))
    st.markdown('</div>', unsafe_allow_html=True)

    if run:
        with st.spinner("正在分析，请稍候..."):
            _t0 = time.time()
            result = compare(url1.strip(), url2.strip())
            _elapsed = time.time() - _t0

        # ── 结果区（横向数据条）──
        if result.method == "error":
            st.error(f"比对失败：{result.error}")
        else:
            is_same = result.is_same
            score = result.similarity_score

            if is_same:
                v_bg = "rgba(16,185,129,0.15)"; v_bdr = "rgba(16,185,129,0.4)"
                v_clr = "#34d399"; v_txt = "✓  图片一致"
            else:
                v_bg = "rgba(239,68,68,0.12)"; v_bdr = "rgba(239,68,68,0.35)"
                v_clr = "#f87171"; v_txt = "✕  图片不一致"

            score_clr = "#34d399" if score >= 80 else ("#f59e0b" if score >= 50 else "#f87171")

            st.markdown(f"""
            <div class="card">
                <div class="card-label">比对结果</div>
                <div style="display:flex;align-items:center;gap:28px;flex-wrap:wrap;">
                    <span style="background:{v_bg};border:1px solid {v_bdr};color:{v_clr};
                        border-radius:8px;padding:8px 18px;font-size:15px;font-weight:700;
                        white-space:nowrap;">{v_txt}</span>
                    <div style="text-align:center;">
                        <div style="font-size:11px;color:rgba(255,255,255,0.35);
                            text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">相似度</div>
                        <div style="font-size:32px;font-weight:700;color:{score_clr};line-height:1;">{score}</div>
                    </div>
                    <div style="flex:1;min-width:140px;">
                        <div style="font-size:11px;color:rgba(255,255,255,0.35);
                            text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">建议</div>
                        <div style="font-size:14px;font-weight:500;color:#e5e7eb;">{result.recommendation}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:11px;color:rgba(255,255,255,0.35);
                            text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">耗时</div>
                        <div style="font-size:24px;font-weight:700;color:#818cf8;line-height:1;">
                            {_elapsed:.2f}<span style="font-size:12px;font-weight:400;
                            color:rgba(255,255,255,0.35);margin-left:2px;">s</span></div>
                    </div>
                </div>
                <div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
                    border-radius:10px;padding:14px 16px;margin-top:18px;">
                    <div style="font-size:11px;color:#818cf8;font-weight:600;
                        letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px;">分析说明</div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.7);line-height:1.8;">{result.reason}</div>
                </div>
                <div style="margin-top:10px;">
                    <span style="font-size:11px;color:#818cf8;background:rgba(99,102,241,0.12);
                        padding:3px 10px;border-radius:6px;border:1px solid rgba(99,102,241,0.25);
                        font-weight:500;">{result.method}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── 图片预览 ──
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">图片预览</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2, gap="medium")
        with pc1:
            st.caption("图片 A")
            try:
                st.image(url1, use_container_width=True)
            except Exception:
                st.markdown('<div style="background:rgba(255,255,255,0.04);border:1.5px dashed rgba(99,102,241,0.3);border-radius:10px;padding:40px;text-align:center;color:rgba(255,255,255,0.25);font-size:13px;">加载失败</div>', unsafe_allow_html=True)
        with pc2:
            st.caption("图片 B")
            try:
                st.image(url2, use_container_width=True)
            except Exception:
                st.markdown('<div style="background:rgba(255,255,255,0.04);border:1.5px dashed rgba(99,102,241,0.3);border-radius:10px;padding:40px;text-align:center;color:rgba(255,255,255,0.25);font-size:13px;">加载失败</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
```

- [ ] **Step 2: 验证单条模式**

```bash
streamlit run app.py
```

Expected:
1. 单条模式 Tab 下显示一行三列输入框 + 「比 对」按钮（未填写时灰色禁用）
2. 填入两个合法图片 URL 后按钮变为紫色可点击
3. 点击「比 对」显示 spinner，结果展示横向数据条（判定徽章 · 相似度数字 · 建议 · 耗时）
4. 分析说明紫色背景框正常显示
5. 图片预览卡片显示两张图片

- [ ] **Step 3: Commit**

```bash
git add image_comparator/app.py
git commit -m "feat: implement single comparison mode with inline result bar"
```

---

### Task 5: 批量模式（上传 + 并发比对 + 结果表格）

**Files:**
- Modify: `image_comparator/app.py`（替换 tab2 的 `st.write("批量模式占位")`）

- [ ] **Step 1: 替换 tab2 占位为完整批量模式代码**

将 `with tab2:` 块内容替换为：

```python
with tab2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-label">上传数据文件</div>', unsafe_allow_html=True)
    st.markdown("""
    <p style="font-size:13px;color:rgba(255,255,255,0.45);margin-bottom:16px;">
        Excel 需包含
        <code style="background:rgba(99,102,241,0.15);padding:2px 7px;border-radius:5px;
            color:#818cf8;font-weight:500;">url1</code>
        和
        <code style="background:rgba(99,102,241,0.15);padding:2px 7px;border-radius:5px;
            color:#818cf8;font-weight:500;">url2</code>
        两列
    </p>
    """, unsafe_allow_html=True)

    tmpl_col, _ = st.columns([2, 8])
    with tmpl_col:
        import io as _io
        from openpyxl import Workbook as _Workbook
        _wb = _Workbook(); _ws = _wb.active
        _ws.append(["url1", "url2"])
        _ws.append(["https://img.example.com/a.jpg", "https://img.example.com/b.jpg"])
        _buf = _io.BytesIO(); _wb.save(_buf)
        st.download_button("⬇ 下载模板", data=_buf.getvalue(),
                           file_name="比对模板.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    uploaded = st.file_uploader("拖拽或点击上传 Excel 文件（.xlsx / .xls）",
                                type=["xlsx", "xls"], label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded:
        try:
            df = pd.read_excel(uploaded)
            if "url1" not in df.columns or "url2" not in df.columns:
                st.error("格式错误：必须包含 url1 和 url2 两列")
                st.stop()

            st.markdown(f'<p style="font-size:13px;color:rgba(255,255,255,0.45);margin:8px 0 16px;">已解析 <strong style="color:#818cf8;font-size:15px;">{len(df)}</strong> 条记录</p>', unsafe_allow_html=True)

            bcol, _ = st.columns([2, 8])
            with bcol:
                if st.button("开始批量比对", type="primary", use_container_width=True):
                    pairs = list(zip(df["url1"].astype(str).str.strip(),
                                     df["url2"].astype(str).str.strip()))
                    pairs = [(u1, u2) for u1, u2 in pairs if u1 != "nan" and u2 != "nan"]
                    total = len(pairs)
                    if total == 0:
                        st.error("无有效数据（url1/url2 均不能为空）")
                        st.stop()

                    progress_bar = st.progress(0, text=f"0 / {total}")
                    start_time = time.time()

                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    from config import BATCH_CONCURRENCY, COMPARE_TIMEOUT

                    results: list[CompareResult | None] = [None] * total
                    done = 0

                    with ThreadPoolExecutor(max_workers=BATCH_CONCURRENCY) as executor:
                        fmap = {executor.submit(compare, u1, u2): i
                                for i, (u1, u2) in enumerate(pairs)}
                        for future in as_completed(fmap):
                            idx = fmap[future]
                            try:
                                results[idx] = future.result(timeout=COMPARE_TIMEOUT)
                            except TimeoutError:
                                u1, u2 = pairs[idx]
                                results[idx] = CompareResult(
                                    url1=u1, url2=u2, is_same=False, similarity_score=0,
                                    recommendation="超时跳过", reason="处理超过30秒",
                                    method="error", error="timeout")
                            except Exception as e:
                                u1, u2 = pairs[idx]
                                results[idx] = CompareResult(
                                    url1=u1, url2=u2, is_same=False, similarity_score=0,
                                    recommendation="处理异常", reason=str(e),
                                    method="error", error=str(e))
                            done += 1
                            elapsed = time.time() - start_time
                            remaining = (elapsed / done) * (total - done)
                            progress_bar.progress(done / total,
                                text=f"{done} / {total}  ·  预计剩余 {remaining:.0f}s")

                    progress_bar.progress(1.0, text="✓ 处理完成")
                    same_cnt = sum(1 for r in results if r.is_same)
                    diff_cnt = total - same_cnt

                    st.markdown(f"""
                    <div style="display:flex;gap:12px;margin:20px 0 16px;flex-wrap:wrap;">
                        <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);
                            border-radius:12px;padding:18px 28px;min-width:110px;">
                            <div style="font-size:11px;color:rgba(255,255,255,0.35);font-weight:600;
                                letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">总计</div>
                            <div style="font-size:32px;font-weight:700;color:#fff;line-height:1;">{total}</div>
                        </div>
                        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);
                            border-radius:12px;padding:18px 28px;min-width:110px;">
                            <div style="font-size:11px;color:rgba(255,255,255,0.35);font-weight:600;
                                letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">图片一致</div>
                            <div style="font-size:32px;font-weight:700;color:#34d399;line-height:1;">{same_cnt}</div>
                        </div>
                        <div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);
                            border-radius:12px;padding:18px 28px;min-width:110px;">
                            <div style="font-size:11px;color:rgba(255,255,255,0.35);font-weight:600;
                                letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">需调整</div>
                            <div style="font-size:32px;font-weight:700;color:#f87171;line-height:1;">{diff_cnt}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    table_data = [{
                        "url1": r.url1, "url2": r.url2,
                        "是否相同": "是" if r.is_same else "否",
                        "相似度": r.similarity_score,
                        "建议": r.recommendation,
                        "原因": r.reason,
                        "方式": r.method,
                    } for r in results]

                    result_df = pd.DataFrame(table_data)

                    def hl(row):
                        if row["是否相同"] == "否":
                            return ["background-color:rgba(239,68,68,0.12);color:#f87171"] * len(row)
                        return [""] * len(row)

                    st.dataframe(result_df.style.apply(hl, axis=1),
                                 use_container_width=True, height=400)

                    dl_col, _ = st.columns([2, 8])
                    with dl_col:
                        excel_bytes = generate_excel_bytes(results)
                        st.download_button("⬇ 下载 Excel 报告", data=excel_bytes,
                                           file_name="比对结果.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True)
        except Exception as e:
            st.error(f"处理失败：{e}")
```

- [ ] **Step 2: 验证批量模式**

```bash
streamlit run app.py
```

Expected:
1. 切换到「批量模式」Tab，显示上传区卡片
2. 「下载模板」按钮可下载含 url1/url2 表头的 xlsx
3. 上传合法 Excel 后显示记录数和「开始批量比对」按钮
4. 点击开始后显示实时进度条（`done/total · 预计剩余 Xs`）
5. 完成后显示三张统计卡片（总计/一致/需调整），结果表格不一致行红色高亮，下载按钮可用

- [ ] **Step 3: 全量验证**

```bash
streamlit run app.py
```

完整走一遍所有功能：
- 顶栏标题居中、设置/刷新按钮靠右
- 单条模式：输入 → 比对 → 查看结果 → 图片预览
- 批量模式：上传 → 比对 → 下载报告
- 点击「设置」弹出 API Key 配置弹窗，保存正常

- [ ] **Step 4: Commit**

```bash
git add image_comparator/app.py
git commit -m "feat: implement batch mode and complete UI redesign"
```
