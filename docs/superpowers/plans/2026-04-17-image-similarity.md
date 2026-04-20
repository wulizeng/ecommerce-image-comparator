# 电商主图相似度比对系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Streamlit Web 应用，用户输入图片URL（单对或批量CSV），通过 pHash 初筛 + 千问VL 精判的融合方案，输出图片相似度分数与是否需要调整的结论。

**Architecture:** pHash 计算汉明距离做快速初筛（距离<5判同，>15判异），仅在模糊区间（5~15）调用千问VL-Max API做语义裁判；Streamlit 作为 Web UI 层，comparator.py 编排核心逻辑，各模块单一职责。

**Tech Stack:** Python 3.10+, Streamlit, imagehash, Pillow, httpx, dashscope (千问VL-Max), openpyxl

---

## 文件结构

```
image_comparator/
├── app.py               # Streamlit Web UI
├── config.py            # 配置：API Key、阈值、并发数
├── downloader.py        # 图片下载：URL → PIL Image
├── phash.py             # pHash 计算 + 汉明距离判断
├── qwen_vl.py           # 千问VL-Max API 封装
├── comparator.py        # 编排核心逻辑
├── reporter.py          # 生成 Excel 文件
├── requirements.txt     # 依赖
└── tests/
    ├── test_phash.py
    ├── test_downloader.py
    ├── test_comparator.py
    └── test_reporter.py
```

---

## Task 1: 项目初始化 + 依赖配置

**Files:**
- Create: `image_comparator/requirements.txt`
- Create: `image_comparator/config.py`

- [ ] **Step 1: 创建项目目录**

```bash
mkdir -p image_comparator/tests
touch image_comparator/__init__.py
touch image_comparator/tests/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```
Pillow>=10.0
imagehash>=4.3
dashscope>=1.14
httpx>=0.27
openpyxl>=3.1
streamlit>=1.35
pytest>=8.0
pytest-asyncio>=0.23
```

- [ ] **Step 3: 安装依赖**

```bash
cd image_comparator
pip install -r requirements.txt
```

Expected: 所有包安装成功，无报错。

- [ ] **Step 4: 创建 config.py**

```python
import os

# 千问 API Key，优先从环境变量读取
QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "sk-your-key-here")

# pHash 汉明距离阈值
PHASH_SAME_THRESHOLD: int = 5    # 距离 <= 5 → 直接判同
PHASH_DIFF_THRESHOLD: int = 15   # 距离 >= 15 → 直接判异

# 批量模式并发数
BATCH_CONCURRENCY: int = 10

# 图片下载超时（秒）
DOWNLOAD_TIMEOUT: int = 10

# 千问VL模型名称
QWEN_VL_MODEL: str = "qwen-vl-max"
```

- [ ] **Step 5: Commit**

```bash
cd image_comparator
git add requirements.txt config.py
git commit -m "feat: init project with config and dependencies"
```

---

## Task 2: 图片下载模块

**Files:**
- Create: `image_comparator/downloader.py`
- Create: `image_comparator/tests/test_downloader.py`

- [ ] **Step 1: 写失败测试**

创建 `image_comparator/tests/test_downloader.py`：

```python
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io

from downloader import download_image, DownloadError


def test_download_image_returns_pil_image():
    """下载成功时返回 PIL Image 对象"""
    # 创建一个 1x1 红色像素的假图片字节
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    fake_bytes = buf.getvalue()

    with patch("downloader.httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = fake_bytes
        mock_get.return_value = mock_resp

        result = download_image("https://example.com/test.jpg")

    assert isinstance(result, Image.Image)


def test_download_image_raises_on_http_error():
    """HTTP 错误时抛出 DownloadError"""
    with patch("downloader.httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_resp

        with pytest.raises(DownloadError):
            download_image("https://example.com/missing.jpg")


def test_download_image_raises_on_timeout():
    """下载超时时抛出 DownloadError"""
    import httpx
    with patch("downloader.httpx.get", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(DownloadError):
            download_image("https://example.com/slow.jpg")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd image_comparator
pytest tests/test_downloader.py -v
```

Expected: `ImportError: cannot import name 'download_image'`

- [ ] **Step 3: 实现 downloader.py**

```python
import io
import httpx
from PIL import Image
from config import DOWNLOAD_TIMEOUT


class DownloadError(Exception):
    """图片下载失败"""
    pass


def download_image(url: str) -> Image.Image:
    """
    下载图片URL并返回PIL Image对象。
    失败时抛出 DownloadError。
    """
    try:
        response = httpx.get(url, timeout=DOWNLOAD_TIMEOUT, follow_redirects=True)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    except httpx.TimeoutException as e:
        raise DownloadError(f"下载超时: {url}") from e
    except httpx.HTTPStatusError as e:
        raise DownloadError(f"HTTP错误 {e.response.status_code}: {url}") from e
    except Exception as e:
        raise DownloadError(f"下载失败: {url} — {e}") from e
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_downloader.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add downloader.py tests/test_downloader.py
git commit -m "feat: add image downloader with error handling"
```

---

## Task 3: pHash 相似度计算模块

**Files:**
- Create: `image_comparator/phash.py`
- Create: `image_comparator/tests/test_phash.py`

- [ ] **Step 1: 写失败测试**

创建 `image_comparator/tests/test_phash.py`：

```python
import pytest
from PIL import Image
from phash import compute_hamming_distance, classify_by_distance, PHashResult


def make_image(color: tuple) -> Image.Image:
    return Image.new("RGB", (100, 100), color=color)


def test_identical_images_have_zero_distance():
    img = make_image((255, 0, 0))
    distance = compute_hamming_distance(img, img)
    assert distance == 0


def test_very_different_images_have_large_distance():
    img1 = make_image((255, 255, 255))  # 白色
    img2 = make_image((0, 0, 0))        # 黑色
    distance = compute_hamming_distance(img1, img2)
    assert distance > 15


def test_classify_same():
    result = classify_by_distance(3)
    assert result.verdict == "same"
    assert result.similarity_score >= 95


def test_classify_different():
    result = classify_by_distance(20)
    assert result.verdict == "different"
    assert result.similarity_score <= 30


def test_classify_uncertain():
    result = classify_by_distance(10)
    assert result.verdict == "uncertain"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_phash.py -v
```

Expected: `ImportError: cannot import name 'compute_hamming_distance'`

- [ ] **Step 3: 实现 phash.py**

```python
from dataclasses import dataclass
import imagehash
from PIL import Image
from config import PHASH_SAME_THRESHOLD, PHASH_DIFF_THRESHOLD


@dataclass
class PHashResult:
    hamming_distance: int
    verdict: str          # "same" | "different" | "uncertain"
    similarity_score: int # 0~100


def compute_hamming_distance(img1: Image.Image, img2: Image.Image) -> int:
    """计算两张图片的 pHash 汉明距离"""
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)
    return hash1 - hash2


def classify_by_distance(distance: int) -> PHashResult:
    """
    根据汉明距离给出初步判断。
    distance <= PHASH_SAME_THRESHOLD  → same
    distance >= PHASH_DIFF_THRESHOLD  → different
    中间区间                           → uncertain（交由VL裁判）
    """
    if distance <= PHASH_SAME_THRESHOLD:
        # 距离越小，分数越高
        score = max(95, 100 - distance)
        return PHashResult(distance, "same", score)
    elif distance >= PHASH_DIFF_THRESHOLD:
        # 距离越大，分数越低
        score = max(0, 30 - (distance - PHASH_DIFF_THRESHOLD) * 2)
        return PHashResult(distance, "different", score)
    else:
        return PHashResult(distance, "uncertain", 50)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_phash.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add phash.py tests/test_phash.py
git commit -m "feat: add phash similarity calculation with threshold classification"
```

---

## Task 4: 千问VL API 封装模块

**Files:**
- Create: `image_comparator/qwen_vl.py`
- Create: `image_comparator/tests/test_qwen_vl.py`

- [ ] **Step 1: 写失败测试**

创建 `image_comparator/tests/test_qwen_vl.py`：

```python
import pytest
from unittest.mock import patch, MagicMock
from qwen_vl import call_qwen_vl, VLResult, VLError


def make_mock_response(content: str):
    mock = MagicMock()
    mock.output.choices[0].message.content = [{"text": content}]
    mock.status_code = 200
    return mock


def test_call_qwen_vl_returns_vl_result_when_same():
    fake_json = '{"is_same": true, "similarity_score": 95, "reason": "同一张图"}'
    with patch("qwen_vl.MultiModalConversation.call", return_value=make_mock_response(fake_json)):
        result = call_qwen_vl("https://a.com/1.jpg", "https://a.com/2.jpg")

    assert isinstance(result, VLResult)
    assert result.is_same is True
    assert result.similarity_score == 95
    assert "同一张图" in result.reason


def test_call_qwen_vl_returns_vl_result_when_different():
    fake_json = '{"is_same": false, "similarity_score": 10, "reason": "完全不同的商品"}'
    with patch("qwen_vl.MultiModalConversation.call", return_value=make_mock_response(fake_json)):
        result = call_qwen_vl("https://a.com/1.jpg", "https://a.com/2.jpg")

    assert result.is_same is False
    assert result.similarity_score == 10


def test_call_qwen_vl_raises_vl_error_on_api_failure():
    with patch("qwen_vl.MultiModalConversation.call", side_effect=Exception("API Error")):
        with pytest.raises(VLError):
            call_qwen_vl("https://a.com/1.jpg", "https://a.com/2.jpg")
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_qwen_vl.py -v
```

Expected: `ImportError: cannot import name 'call_qwen_vl'`

- [ ] **Step 3: 实现 qwen_vl.py**

```python
import json
import re
from dataclasses import dataclass
import dashscope
from dashscope import MultiModalConversation
from config import QWEN_API_KEY, QWEN_VL_MODEL

dashscope.api_key = QWEN_API_KEY


class VLError(Exception):
    """千问VL API调用失败"""
    pass


@dataclass
class VLResult:
    is_same: bool
    similarity_score: int  # 0~100
    reason: str


_PROMPT = """你是一个电商图片审核专家。请判断以下两张商品图片是否为同一张图片（允许轻微的压缩、缩放、水印差异）。

请只返回如下JSON格式，不要有其他内容：
{"is_same": true或false, "similarity_score": 0到100的整数, "reason": "简要说明"}"""


def call_qwen_vl(url1: str, url2: str) -> VLResult:
    """
    调用千问VL-Max判断两张图片是否相同。
    失败时抛出 VLError。
    """
    try:
        messages = [
            {
                "role": "user",
                "content": [
                    {"image": url1},
                    {"image": url2},
                    {"text": _PROMPT},
                ],
            }
        ]
        response = MultiModalConversation.call(model=QWEN_VL_MODEL, messages=messages)
        raw_text = response.output.choices[0].message.content[0]["text"]

        # 提取JSON（防止模型在JSON前后输出多余文字）
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise VLError(f"模型未返回有效JSON: {raw_text}")
        data = json.loads(match.group())

        return VLResult(
            is_same=bool(data["is_same"]),
            similarity_score=int(data["similarity_score"]),
            reason=str(data["reason"]),
        )
    except VLError:
        raise
    except Exception as e:
        raise VLError(f"千问VL调用失败: {e}") from e
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_qwen_vl.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add qwen_vl.py tests/test_qwen_vl.py
git commit -m "feat: add Qwen-VL-Max API wrapper with structured output parsing"
```

---

## Task 5: 比对编排模块

**Files:**
- Create: `image_comparator/comparator.py`
- Create: `image_comparator/tests/test_comparator.py`

- [ ] **Step 1: 写失败测试**

创建 `image_comparator/tests/test_comparator.py`：

```python
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from comparator import compare, CompareResult
from phash import PHashResult
from qwen_vl import VLResult


def make_image():
    return Image.new("RGB", (10, 10), color=(100, 100, 100))


@patch("comparator.download_image")
@patch("comparator.compute_hamming_distance")
@patch("comparator.classify_by_distance")
def test_compare_phash_same(mock_classify, mock_distance, mock_download):
    """pHash 直接判同，不调用VL"""
    mock_download.return_value = make_image()
    mock_distance.return_value = 2
    mock_classify.return_value = PHashResult(2, "same", 98)

    result = compare("https://a.com/1.jpg", "https://a.com/2.jpg")

    assert isinstance(result, CompareResult)
    assert result.is_same is True
    assert result.similarity_score == 98
    assert result.method == "phash_same"


@patch("comparator.download_image")
@patch("comparator.compute_hamming_distance")
@patch("comparator.classify_by_distance")
def test_compare_phash_different(mock_classify, mock_distance, mock_download):
    """pHash 直接判异，不调用VL"""
    mock_download.return_value = make_image()
    mock_distance.return_value = 25
    mock_classify.return_value = PHashResult(25, "different", 5)

    result = compare("https://a.com/1.jpg", "https://a.com/2.jpg")

    assert result.is_same is False
    assert result.method == "phash_diff"


@patch("comparator.call_qwen_vl")
@patch("comparator.download_image")
@patch("comparator.compute_hamming_distance")
@patch("comparator.classify_by_distance")
def test_compare_uncertain_calls_vl(mock_classify, mock_distance, mock_download, mock_vl):
    """pHash 模糊区间时调用千问VL"""
    mock_download.return_value = make_image()
    mock_distance.return_value = 10
    mock_classify.return_value = PHashResult(10, "uncertain", 50)
    mock_vl.return_value = VLResult(True, 88, "同一商品，背景略有不同")

    result = compare("https://a.com/1.jpg", "https://a.com/2.jpg")

    mock_vl.assert_called_once()
    assert result.is_same is True
    assert result.similarity_score == 88
    assert result.method == "qwen_vl"


@patch("comparator.call_qwen_vl")
@patch("comparator.download_image")
@patch("comparator.compute_hamming_distance")
@patch("comparator.classify_by_distance")
def test_compare_vl_fallback_on_error(mock_classify, mock_distance, mock_download, mock_vl):
    """VL调用失败时降级使用pHash结果"""
    from qwen_vl import VLError
    mock_download.return_value = make_image()
    mock_distance.return_value = 10
    mock_classify.return_value = PHashResult(10, "uncertain", 50)
    mock_vl.side_effect = VLError("API超时")

    result = compare("https://a.com/1.jpg", "https://a.com/2.jpg")

    # 降级：uncertain → 判为不同（保守策略）
    assert result.method == "phash_fallback"
    assert result.is_same is False
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_comparator.py -v
```

Expected: `ImportError: cannot import name 'compare'`

- [ ] **Step 3: 实现 comparator.py**

```python
from dataclasses import dataclass
from downloader import download_image, DownloadError
from phash import compute_hamming_distance, classify_by_distance
from qwen_vl import call_qwen_vl, VLError


@dataclass
class CompareResult:
    url1: str
    url2: str
    is_same: bool
    similarity_score: int   # 0~100
    recommendation: str     # "图片一致，无需调整" | "图片不一致，建议调整"
    reason: str
    method: str             # "phash_same" | "phash_diff" | "qwen_vl" | "phash_fallback" | "error"
    error: str = ""         # 下载失败等错误信息


def _make_recommendation(is_same: bool) -> str:
    return "图片一致，无需调整" if is_same else "图片不一致，建议调整店铺链接主图"


def compare(url1: str, url2: str) -> CompareResult:
    """
    比对两张图片URL，返回 CompareResult。
    流程：下载 → pHash初筛 → 按需调用千问VL。
    """
    # 1. 下载图片
    try:
        img1 = download_image(url1)
        img2 = download_image(url2)
    except DownloadError as e:
        return CompareResult(
            url1=url1, url2=url2,
            is_same=False, similarity_score=0,
            recommendation="下载失败，无法判断",
            reason=str(e), method="error", error=str(e)
        )

    # 2. pHash 初筛
    distance = compute_hamming_distance(img1, img2)
    phash_result = classify_by_distance(distance)

    if phash_result.verdict == "same":
        return CompareResult(
            url1=url1, url2=url2,
            is_same=True,
            similarity_score=phash_result.similarity_score,
            recommendation=_make_recommendation(True),
            reason=f"图片高度相似（pHash汉明距离={distance}），为同一张图或轻微压缩版本",
            method="phash_same",
        )

    if phash_result.verdict == "different":
        return CompareResult(
            url1=url1, url2=url2,
            is_same=False,
            similarity_score=phash_result.similarity_score,
            recommendation=_make_recommendation(False),
            reason=f"图片差异明显（pHash汉明距离={distance}），判定为不同图片",
            method="phash_diff",
        )

    # 3. 模糊区间 → 调用千问VL
    try:
        vl_result = call_qwen_vl(url1, url2)
        return CompareResult(
            url1=url1, url2=url2,
            is_same=vl_result.is_same,
            similarity_score=vl_result.similarity_score,
            recommendation=_make_recommendation(vl_result.is_same),
            reason=vl_result.reason,
            method="qwen_vl",
        )
    except VLError:
        # 降级：保守策略，模糊区间判为不同
        return CompareResult(
            url1=url1, url2=url2,
            is_same=False,
            similarity_score=phash_result.similarity_score,
            recommendation=_make_recommendation(False),
            reason=f"千问VL调用失败，降级判断（pHash汉明距离={distance}，处于模糊区间）",
            method="phash_fallback",
        )


def compare_batch(pairs: list[tuple[str, str]]) -> list[CompareResult]:
    """
    批量比对，顺序执行（Streamlit中使用，避免异步复杂度）。
    pairs: [(url1, url2), ...]
    """
    return [compare(url1, url2) for url1, url2 in pairs]
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_comparator.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add comparator.py tests/test_comparator.py
git commit -m "feat: add comparator orchestration with phash+vl fusion and fallback"
```

---

## Task 6: Excel 报告生成模块

**Files:**
- Create: `image_comparator/reporter.py`
- Create: `image_comparator/tests/test_reporter.py`

- [ ] **Step 1: 写失败测试**

创建 `image_comparator/tests/test_reporter.py`：

```python
import io
import pytest
import openpyxl
from comparator import CompareResult
from reporter import generate_excel_bytes


def make_result(is_same: bool) -> CompareResult:
    return CompareResult(
        url1="https://a.com/1.jpg",
        url2="https://a.com/2.jpg",
        is_same=is_same,
        similarity_score=95 if is_same else 10,
        recommendation="图片一致，无需调整" if is_same else "图片不一致，建议调整店铺链接主图",
        reason="测试原因",
        method="phash_same" if is_same else "phash_diff",
    )


def test_generate_excel_bytes_returns_bytes():
    results = [make_result(True), make_result(False)]
    data = generate_excel_bytes(results)
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_generate_excel_has_correct_columns():
    results = [make_result(True)]
    data = generate_excel_bytes(results)
    wb = openpyxl.load_workbook(io.BytesIO(data))
    ws = wb.active
    headers = [ws.cell(1, col).value for col in range(1, 8)]
    assert headers == ["url1", "url2", "is_same", "similarity_score", "recommendation", "reason", "method"]


def test_generate_excel_row_count():
    results = [make_result(True), make_result(False), make_result(True)]
    data = generate_excel_bytes(results)
    wb = openpyxl.load_workbook(io.BytesIO(data))
    ws = wb.active
    # 1行标题 + 3行数据
    assert ws.max_row == 4
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_reporter.py -v
```

Expected: `ImportError: cannot import name 'generate_excel_bytes'`

- [ ] **Step 3: 实现 reporter.py**

```python
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from comparator import CompareResult

_RED_FILL = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
_HEADERS = ["url1", "url2", "is_same", "similarity_score", "recommendation", "reason", "method"]


def generate_excel_bytes(results: list[CompareResult]) -> bytes:
    """
    将比对结果列表生成 Excel 文件字节。
    不同图片（is_same=False）的行用红色背景标注。
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "比对结果"

    ws.append(_HEADERS)

    for result in results:
        row = [
            result.url1,
            result.url2,
            "是" if result.is_same else "否",
            result.similarity_score,
            result.recommendation,
            result.reason,
            result.method,
        ]
        ws.append(row)
        # 不同图片行标红
        if not result.is_same:
            for col in range(1, len(_HEADERS) + 1):
                ws.cell(ws.max_row, col).fill = _RED_FILL

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_reporter.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add reporter.py tests/test_reporter.py
git commit -m "feat: add excel reporter with red highlight for mismatched images"
```

---

## Task 7: Streamlit Web UI

**Files:**
- Create: `image_comparator/app.py`

- [ ] **Step 1: 实现 app.py**

```python
import io
import streamlit as st
import pandas as pd
from comparator import compare, compare_batch, CompareResult
from reporter import generate_excel_bytes

st.set_page_config(page_title="电商主图相似度比对", layout="wide")
st.title("电商主图相似度比对工具")
st.caption("支持单对比对和批量CSV比对，使用 pHash + 千问VL 融合判断")

mode = st.radio("选择模式", ["单对比对", "批量比对（CSV）"], horizontal=True)

# ── 单对模式 ──────────────────────────────────────────
if mode == "单对比对":
    col1, col2 = st.columns(2)
    with col1:
        url1 = st.text_input("图片URL A", placeholder="https://img.example.com/a.jpg")
    with col2:
        url2 = st.text_input("图片URL B", placeholder="https://img.example.com/b.jpg")

    if st.button("开始比对", type="primary", disabled=not (url1 and url2)):
        with st.spinner("正在比对中..."):
            result = compare(url1.strip(), url2.strip())

        # 展示图片预览
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            try:
                st.image(url1, caption="图片 A", use_column_width=True)
            except Exception:
                st.warning("图片A预览失败")
        with img_col2:
            try:
                st.image(url2, caption="图片 B", use_column_width=True)
            except Exception:
                st.warning("图片B预览失败")

        # 展示结果
        if result.method == "error":
            st.error(f"比对失败：{result.error}")
        else:
            if result.is_same:
                st.success(f"✅ {result.recommendation}")
            else:
                st.error(f"❌ {result.recommendation}")

            col_score, col_method = st.columns(2)
            col_score.metric("相似度分数", f"{result.similarity_score} / 100")
            col_method.metric("判断方式", result.method)
            st.info(f"原因：{result.reason}")

# ── 批量模式 ──────────────────────────────────────────
else:
    st.markdown("**CSV格式要求：** 两列，列名为 `url1` 和 `url2`，每行一对图片URL")
    uploaded = st.file_uploader("上传 CSV 文件", type=["csv"])

    if uploaded and st.button("开始批量比对", type="primary"):
        try:
            df = pd.read_csv(uploaded)
            if "url1" not in df.columns or "url2" not in df.columns:
                st.error("CSV 格式错误：必须包含 url1 和 url2 两列")
                st.stop()

            pairs = list(zip(df["url1"].astype(str), df["url2"].astype(str)))
            results: list[CompareResult] = []

            progress = st.progress(0, text="处理中...")
            for i, (u1, u2) in enumerate(pairs):
                results.append(compare(u1.strip(), u2.strip()))
                progress.progress((i + 1) / len(pairs), text=f"已处理 {i+1}/{len(pairs)}")

            progress.empty()
            st.success(f"比对完成！共 {len(results)} 条，其中 {sum(1 for r in results if not r.is_same)} 条需调整")

            # 结果表��
            table_data = [
                {
                    "url1": r.url1,
                    "url2": r.url2,
                    "是否相同": "是" if r.is_same else "否",
                    "相似度": r.similarity_score,
                    "建议": r.recommendation,
                    "原因": r.reason,
                    "方式": r.method,
                }
                for r in results
            ]
            result_df = pd.DataFrame(table_data)

            # 对"否"行用颜色标注
            def highlight_row(row):
                return ["background-color: #ffcccc"] * len(row) if row["是否相同"] == "否" else [""] * len(row)

            st.dataframe(result_df.style.apply(highlight_row, axis=1), use_container_width=True)

            # 下载Excel
            excel_bytes = generate_excel_bytes(results)
            st.download_button(
                label="下载 Excel 报告",
                data=excel_bytes,
                file_name="比对结果.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        except Exception as e:
            st.error(f"处理失败：{e}")
```

- [ ] **Step 2: 启动并手动验证**

```bash
cd image_comparator
streamlit run app.py
```

在浏览器 `http://localhost:8501` 验证：
1. 单对模式：输入两个可访问的图片URL，点击"开始比对"，确认显示图片预览 + 分数 + 结论
2. 批量模式：上传包含3行的CSV，确认进度条运行，结果表格显示，下载Excel可打开

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add streamlit web ui with single and batch comparison modes"
```

---

## Task 8: 运行全量测试 + 最终验证

- [ ] **Step 1: 运行全量测试**

```bash
cd image_comparator
pytest tests/ -v
```

Expected: 全部 passed，无 failed/error

- [ ] **Step 2: 准备测试CSV**

创建 `tests/sample.csv`：

```csv
url1,url2
https://img.alicdn.com/imgextra/i1/O1CN01example1_!!6000000000000-0-tps-800-800.jpg,https://img.alicdn.com/imgextra/i1/O1CN01example1_!!6000000000000-0-tps-800-800.jpg
```

（使用真实可访问的图片URL替换上面示例URL，测试批量流程）

- [ ] **Step 3: 端到端验证**

```bash
streamlit run app.py
```

验证清单：
- [ ] 单对模式：相同URL → 显示"✅ 图片一致"，分数>=95
- [ ] 单对模式：不同URL → 显示"❌ 图片不一致"，分数<50
- [ ] 批量模式：上传CSV → 进度条显示 → 结果表格含红色高亮行 → Excel可下载
- [ ] method 字段显示正确（phash_same / phash_diff / qwen_vl）

- [ ] **Step 4: 最终 Commit**

```bash
git add tests/sample.csv
git commit -m "test: add sample csv for end-to-end verification"
```
