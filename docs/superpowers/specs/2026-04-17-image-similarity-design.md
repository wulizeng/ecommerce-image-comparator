# 电商主图相似度比对系统 — 设计文档

**日期：** 2026-04-17  
**状态：** 待实现

---

## 背景与目标

电商运营人员需要比对不同店铺/链接下的商品主图，判断是否为同一张图片。若相同则无需调整，若不同则提示用户修改对应链接的主图。由于各平台有反爬机制，系统不做链接抓取，由用户直接提供图片URL进行比对。

---

## 核心需求

- **模式B：** 用户输入两个图片URL，输出是否相同 + 相似度分数 + 建议
- **模式C：** 用户上传CSV（每行一对URL），批量处理，输出Excel报告
- **准确率目标：** 98%+，需能容忍平台压缩/水印/轻微缩放带来的差异

---

## 技术方案：pHash 初筛 + 千问VL 精判

### 判断流程

```
图片URL A + 图片URL B
        ↓
  [并发下载图片]
        ↓
  [pHash 计算汉明距离]
        ├── 距离 < 5   → 判定：相同（similarity=95~100）
        ├── 距离 > 15  → 判定：不同（similarity=0~30）
        └── 距离 5~15  → 调用千问VL-Max精判
                              ↓
                    返回 is_same + score + reason
```

### 阈值说明

| 汉明距离 | 含义 | 处理方式 |
|---------|------|---------|
| 0~4 | 几乎完全相同（压缩/缩放） | 直接判同 |
| 5~15 | 模糊区间 | 千问VL裁判 |
| 16+ | 明显不同 | 直接判异 |

---

## 模块设计

```
image_comparator/
├── app.py               # Streamlit Web UI 入口
├── downloader.py        # 并发下载图片URL → PIL Image对象
├── phash.py             # pHash计算 + 汉明距离
├── qwen_vl.py           # 千问VL-Max API封装
├── comparator.py        # 编排：pHash初筛 → 按需调用VL
├── reporter.py          # 生成Excel下载文件
├── config.py            # API Key、阈值、并发数等配置
└── requirements.txt     # 依赖：Pillow, imagehash, dashscope, openpyxl, httpx, streamlit
```

### 各模块职责

**downloader.py**
- 使用 `httpx` 异步并发下载
- 超时处理（10s），失败重试1次
- 返回 PIL Image 对象 + Base64字符串（供VL使用）

**phash.py**
- 使用 `imagehash` 库的 `phash()` 方法
- 计算两图汉明距离
- 返回距离值和初步判断（same/different/uncertain）

**qwen_vl.py**
- 调用 `dashscope` SDK 的 `Qwen-VL-Max` 模型
- 传入两张图片的URL（VL模型支持直接传URL，无需Base64）
- Prompt返回结构化JSON：`{is_same, similarity_score, reason}`
- 异常处理：API失败时降级为 pHash 结果

**comparator.py**
- 单对比对入口：`compare(url1, url2) -> CompareResult`
- 批量入口：`compare_batch(pairs) -> List[CompareResult]`
- 并发控制：批量时最多10个并发（避免API限流）

**reporter.py**
- 单对：输出JSON到控制台
- 批量：生成Excel，列包括：url1、url2、is_same、similarity_score、recommendation、reason

---

## 输出格式

### 单对输出（JSON）

```json
{
  "url1": "https://img.example.com/a.jpg",
  "url2": "https://img.example.com/b.jpg",
  "is_same": true,
  "similarity_score": 97,
  "recommendation": "图片一致，无需调整",
  "reason": "两张图片为同一商品主图，存在轻微压缩差异",
  "method": "phash"
}
```

### 批量输出（Excel列）

| url1 | url2 | is_same | similarity_score | recommendation | reason | method |
|------|------|---------|-----------------|---------------|--------|--------|

`method` 字段记录判断来源：`phash_same` / `phash_diff` / `qwen_vl`

---

## Web UI 使用方式

```bash
# 启动
streamlit run app.py
# 浏览器自动打开 http://localhost:8501
```

### 界面布局

**单对模式：**
- 输入框1：图片URL A
- 输入框2：图片URL B
- 按钮：开始比对
- 结果区：显示两张图片预览 + 相似度分数 + 结论（相同/不同）+ 原因

**批量模式：**
- 上传CSV文件（格式：url1, url2 两列）
- 按钮：开始批量比对
- 进度条：显示处理进度
- 结果表格：标红"需调整"行，支持下载Excel

---

## 配置项（config.py）

```python
QWEN_API_KEY = "sk-xxx"          # 千问API Key
PHASH_SAME_THRESHOLD = 5         # 汉明距离 ≤ 5 → 相同
PHASH_DIFF_THRESHOLD = 15        # 汉明距离 ≥ 15 → 不同
BATCH_CONCURRENCY = 10           # 批量并发数
DOWNLOAD_TIMEOUT = 10            # 图片下载超时秒数
```

---

## 依赖

```
Pillow>=10.0
imagehash>=4.3
dashscope>=1.14
httpx>=0.27
openpyxl>=3.1
streamlit>=1.35
```

---

## 验证方式

1. 准备测试用例：完全相同的图、压缩后的图、加水印的图、相似但不同的图
2. 运行单对模式验证输出格式
3. 准备10行CSV运行批量模式，验证Excel输出
4. 统计pHash命中率（method字段），确认千问VL仅在模糊区间被调用
