# UI 重设计规格文档

## 目标

重设计 `image_comparator/app.py` 的 Streamlit 页面，解决现有页面视觉层级混乱、信息不清晰的问题。风格：深色科技感，深色背景 + 蓝紫渐变强调色。

## 设计决策（已确认）

- **整体布局**：紧凑单页，顶栏 + Tab + 内容区
- **输入区**：三列同行（A URL · B URL · 比对按钮）
- **结果区**：横向数据条（判定 · 相似度 · 建议 · 耗时）
- **顶栏**：标题第一行居中、大字加粗；[设置][刷新] 按钮第二行靠右

---

## 页面结构

```
┌─────────────────────────────────────────────────────┐
│         🔍 电商链接图片相似度比对                      │  居中，24px bold
│                               [设置]  [刷新]          │  靠右，次级按钮
│ ─────────────────────────────────────────────────── │
│ [单条模式] [批量模式]                                  │  胶囊 Tab
├─────────────────────────────────────────────────────┤
│ 输入区卡片                                            │
│ [图片 A URL...]   [图片 B URL...]   [比 对]           │  三列同行
├─────────────────────────────────────────────────────┤
│ 结果区卡片（比对后展开）                               │
│ [✓ 图片一致]  [92]  [建议文字]  [1.2s]               │  横排数据条
│ 分析说明（紫色背景框）                                 │
├─────────────────────────────────────────────────────┤
│ 图片预览卡片                                          │
│ [图片 A]                    [图片 B]                  │  两列
└─────────────────────────────────────────────────────┘
```

---

## 色彩规范

| 元素 | 值 |
|---|---|
| 页面背景 | `#0f1117` |
| 卡片背景 | `#1a1b2e` |
| 输入框背景 | `#252640` |
| 输入框边框 | `rgba(99,102,241,0.25)` |
| 输入框 focus 边框 | `#6366f1` |
| 主渐变（按钮/Tab 选中） | `#6366f1 → #8b5cf6` |
| 成功色 | `#34d399` |
| 失败色 | `#f87171` |
| 警告色 | `#f59e0b` |
| 主文字 | `#e5e7eb` |
| 次要文字 | `rgba(255,255,255,0.35)` |
| 分析说明背景 | `rgba(99,102,241,0.08)` |
| 分析说明边框 | `rgba(99,102,241,0.2)` |
| 内容最大宽度 | `860px` 居中 |

---

## 顶栏

```
行1（flex，justify-content: center）：
  🔍 电商链接图片相似度比对  — font-size: 24px, font-weight: 700, color: #fff

行2（flex，justify-content: flex-end）：
  [设置] [刷新]  — 次级按钮：background: rgba(255,255,255,0.07), border: 1px solid rgba(255,255,255,0.12)

分隔线：border-bottom: 1px solid rgba(255,255,255,0.06)
```

用 Streamlit `st.columns` 实现：
- 顶栏用两行 markdown HTML 实现（标题行 + 按钮行），按钮用实际 `st.button`
- 或：标题 markdown，按钮用 `st.columns([1,1])` 放最右列

---

## Tab 切换

使用 `st.tabs(["单条模式", "批量模式"])` 原生组件，CSS 覆盖为胶囊样式：

```css
[data-testid="stTabs"] [role="tablist"] {
  background: rgba(255,255,255,0.06);
  border-radius: 10px; padding: 4px; gap: 2px;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff; border-radius: 7px;
  box-shadow: 0 2px 10px rgba(99,102,241,0.4);
}
```

---

## 单条模式

### 输入区

三列同行（`st.columns([5, 5, 2])`）：
- 列1：`st.text_input`，label 隐藏，placeholder "粘贴图片 A URL..."
- 列2：`st.text_input`，label 隐藏，placeholder "粘贴图片 B URL..."
- 列3：`st.button("比 对", type="primary")`，两个 URL 都有值时启用

### 结果区（比对后展开，位于输入区下方）

横向数据条卡片（`display:flex; gap:24px; align-items:center`）：

| 子块 | 内容 |
|---|---|
| 判定 | 绿色/红色 pill badge（✓ 图片一致 / ✕ 图片不一致） |
| 相似度 | 大号数字（32px bold），颜色跟随分数（绿/黄/红） |
| 建议 | flex:1，中等字号，白色 |
| 耗时 | 紫色数字（`#818cf8`），单位 `s` |

分析说明：紫色背景圆角框，`result.reason` 内容，`result.method` 小标签。

### 图片预览（结果下方）

两列 `st.columns(2)`，`st.image()` 显示原图，加载失败显示占位框。

---

## 批量模式

### 上传区卡片

- 说明文字：Excel 需包含 `url1` `url2` 两列
- 下载模板按钮（靠左）
- `st.file_uploader`（`.xlsx/.xls`）

### 比对执行

上传后显示记录数，"开始批量比对" 按钮触发：
- `ThreadPoolExecutor` + `as_completed` 并发处理
- `st.progress` 实时进度条，显示 `done/total · 预计剩余 Xs`
- 每条超时 30s，超时返回 error CompareResult

### 统计卡片（完成后）

三张卡片横排：总计 / 图片一致（绿）/ 需调整（红），数字大字

### 结果表格

`st.dataframe`，不一致行红色高亮（`rgba(239,68,68,0.12)`）

### 下载按钮

"⬇ 下载 Excel 报告"

---

## CSS 关键样式

```css
/* 全局 */
.stApp { background: #0f1117; }
.block-container { padding: 0 !important; max-width: 100% !important; }
footer, #MainMenu, header { visibility: hidden; }

/* 主内容区 */
.main { max-width: 860px; margin: 0 auto; padding: 28px 24px 60px; }

/* 卡片 */
.card {
  background: #1a1b2e; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px; padding: 20px 24px; margin-bottom: 14px;
}

/* 输入框 */
.stTextInput input {
  background: #252640 !important;
  border: 1px solid rgba(99,102,241,0.25) !important;
  border-radius: 10px !important; color: #fff !important;
}
.stTextInput input:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.18) !important;
}

/* 主按钮 */
.stButton button[kind="primary"] {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  color: #fff !important;
  box-shadow: 0 2px 12px rgba(99,102,241,0.35) !important;
  border-radius: 9px !important;
}

/* 次级按钮 */
.stButton button:not([kind="primary"]) {
  background: rgba(255,255,255,0.07) !important;
  color: rgba(255,255,255,0.7) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: 9px !important;
}
```

---

## 不变的部分

- 后端逻辑：`comparator.py`、`phash.py`、`qwen_vl.py`、`downloader.py`、`reporter.py` 均不改动
- `@st.dialog("API 配置")` 设置弹窗逻辑不变，仅样式跟随深色主题
- 批量并发逻辑（`ThreadPoolExecutor + as_completed`）不变
