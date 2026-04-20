# UI 重设计 V2 规格文档

## 目标

重设计 `image_comparator/app.py`，解决视觉层级混乱、样式廉价的问题。
风格：明亮简约风，白底卡片 + 柔和阴影 + 紫色胶囊 Tab。

## 设计决策

| 项目 | 决策 |
|---|---|
| 视觉风格 | B — 明亮简约风 |
| 切换方式 | `st.tabs()` + CSS 胶囊覆盖 |
| 结果展示 | 横向数据条（判定·相似度·建议·耗时） |
| 图片预览 | 两列自适应高度 |
| 最大内容宽度 | 900px 居中 |

---

## 页面结构

```
┌─────────────────────────────────────────────┐
│   🔍 电商链接图片相似度比对   [设置]  [刷新]  │  标题居中，按钮靠右
│                                              │
│  [单条比对]  [批量比对]  ← 胶囊 Tab          │
├─────────────────────────────────────────────┤
│  [图片 A URL...]  [图片 B URL...]  [比 对]   │  输入卡片
├─────────────────────────────────────────────┤
│  [✓一致]  [92]  [建议文字]  [1.2s]           │  结果卡片（比对后出现）
│  分析说明（浅紫背景框）                       │
├─────────────────────────────────────────────┤
│  [图片 A]              [图片 B]              │  预览卡片（比对后出现）
└─────────────────────────────────────────────┘
```

---

## 色彩规范

| 元素 | 值 |
|---|---|
| 页面背景 | `#f8fafc` |
| 卡片背景 | `#ffffff` |
| 卡片边框 | `rgba(99,102,241,0.1)` |
| 卡片阴影 | `0 2px 8px rgba(99,102,241,0.06)` |
| Tab 容器背景 | `#f1f5f9` |
| Tab 选中背景 | `linear-gradient(135deg,#6366f1,#8b5cf6)` |
| 主按钮背景 | `linear-gradient(135deg,#6366f1,#8b5cf6)` |
| 输入框背景 | `#f8fafc` |
| 输入框边框 | `rgba(99,102,241,0.2)` |
| 成功色 | `#16a34a`，背景 `#dcfce7`，边框 `rgba(22,163,74,0.3)` |
| 失败色 | `#dc2626`，背景 `rgba(239,68,68,0.08)`，边框 `rgba(239,68,68,0.25)` |
| 耗时颜色 | `#6366f1` |
| 主文字 | `#1e293b` |
| 次要文字 | `#94a3b8` |
| 分析说明背景 | `rgba(99,102,241,0.06)` |
| 分析说明边框 | `rgba(99,102,241,0.18)` |

---

## 顶栏

- 行1：`🔍 电商链接图片相似度比对`，22px bold，居中，`color:#1a1b2e`
- 行2：`st.columns([1.2, 1.2, 5.2, 0.5, 0.5])` — [单条比对][批量比对][空白][设置][刷新]
  - 单条比对/批量比对：通过 `session_state["mode"]` 控制 `type="primary"/"secondary"`
  - 设置/刷新：次级按钮
- 分隔线：`border-bottom: 1px solid rgba(0,0,0,0.08)`

---

## 单条比对

### 输入区卡片

`st.columns([5, 5, 2])`，包裹在 `.card` 内：
- 列1：`st.text_input`，label 隐藏，placeholder "粘贴图片 A URL..."
- 列2：`st.text_input`，label 隐藏，placeholder "粘贴图片 B URL..."
- 列3：`st.button("比 对", type="primary")`，始终可点击

### 结果区卡片（比对后展开）

横向 flex 数据条：

| 子块 | 内容 |
|---|---|
| 判定徽章 | 绿色/红色 pill（✓ 图片一致 / ✕ 图片不一致） |
| 相似度 | 32px bold 数字，颜色跟随分数 |
| 建议 | flex:1，14px，`#374151` |
| 耗时 | `#6366f1`，24px bold |

分析说明：浅紫圆角框，`result.reason`，`result.method` 小标签。

### 图片预览卡片（比对后展开）

`st.columns(2)`，`st.image()` 自适应高度，加载失败显示占位框。

---

## 批量比对

### 上传区卡片

- 说明文字：Excel 需包含 `url1` `url2` 两列
- 下载模板按钮（靠左 `st.columns([2,8])`）
- `st.file_uploader`（`.xlsx/.xls`）

### 比对执行

- 上传后显示记录数
- "开始批量比对" 按钮
- `ThreadPoolExecutor` + `as_completed`，`BATCH_CONCURRENCY` 并发
- `st.progress` 实时进度：`done/total · 预计剩余 Xs`
- 每条超时 `COMPARE_TIMEOUT` 秒，超时返回 error CompareResult

### 完成后

- 三张统计卡片横排：总计 / 图片一致（绿）/ 需调整（红）
- `st.dataframe`，不一致行红色高亮
- "⬇ 下载 Excel 报告" 下载按钮

---

## CSS 关键样式

```css
/* 全局 */
.stApp { background: #f8fafc; }
.block-container { padding: 0 !important; max-width: 100% !important; }
footer, #MainMenu, header { visibility: hidden; }

/* 内容最大宽度 */
.main { max-width: 900px; margin: 0 auto; padding: 0 24px 60px; }
.topbar { max-width: 900px; margin: 0 auto; padding: 10px 24px 0; }

/* 卡片 */
.card {
  background: #ffffff;
  border: 1px solid rgba(99,102,241,0.1);
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(99,102,241,0.06);
}

/* Tab 胶囊 */
[data-testid="stTabs"] [role="tablist"] {
  background: #f1f5f9;
  border-radius: 10px; padding: 4px; gap: 4px;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: linear-gradient(135deg,#6366f1,#8b5cf6);
  color: #fff; border-radius: 7px;
  box-shadow: 0 2px 8px rgba(99,102,241,0.3);
}

/* 输入框 */
.stTextInput input {
  background: #f8fafc !important;
  border: 1.5px solid rgba(99,102,241,0.2) !important;
  border-radius: 8px !important;
  height: 40px !important;
}
.stTextInput input:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* 主按钮 */
.stButton button[kind="primary"] {
  background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
  color: #fff !important; height: 40px !important;
}

/* 次级按钮 */
.stButton button:not([kind="primary"]) {
  background: #ffffff !important;
  border: 1.5px solid rgba(0,0,0,0.12) !important;
  color: rgba(0,0,0,0.55) !important;
}
```

---

## 不变的部分

- 后端：`comparator.py`、`phash.py`、`qwen_vl.py`、`downloader.py`、`reporter.py` 均不改动
- `@st.dialog("API 配置")` 设置弹窗逻辑不变，样式跟随明亮主题
- 并发逻辑（`ThreadPoolExecutor + as_completed`）不变
- `session_state["mode"]` 模式切换逻辑保留（配合 Tab 组件）
