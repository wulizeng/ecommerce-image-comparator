# Railway 部署 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Streamlit 图片比对应用推送到 GitHub Private 仓库，通过 Railway 自动部署为可在线访问的 Web 应用，API Key 由用户在浏览器 Session 中自行输入，不持久化到服务器。

**Architecture:** 项目根目录新增 `Procfile`、`railway.toml`、`.gitignore` 三个部署配置文件；`config.py` 移除文件读取逻辑只保留环境变量回退；`app.py` 移除文件持久化函数，Key 只写入 `session_state`；`requirements.txt` 补充 `openai`、移除 `dashscope`。

**Tech Stack:** Python 3.11, Streamlit, Railway (Nixpacks), GitHub Private Repo, OpenAI SDK

---

## 文件结构

```
电商链接主图相似度比对/        ← 仓库根目录
├── Procfile                  ← 新增：Railway 启动命令
├── railway.toml              ← 新增：Railway 构建配置
├── .gitignore                ← 新增：排除敏感文件
└── image_comparator/
    ├── app.py                ← 修改：移除文件持久化逻辑
    ├── config.py             ← 修改：移除文件读取逻辑
    ├── requirements.txt      ← 修改：补充 openai，移除 dashscope
    └── ...（其余文件不变）
```

---

### Task 1: 添加 `.gitignore`

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: 在项目根目录创建 `.gitignore`**

文件内容：
```
image_comparator/.api_key.json
**/__pycache__/
*.pyc
.DS_Store
.env
.superpowers/
```

- [ ] **Step 2: 验证文件存在且内容正确**

```bash
cat .gitignore
```

期望输出包含 `image_comparator/.api_key.json` 等行。

- [ ] **Step 3: 提交**

```bash
git add .gitignore
git commit -m "chore: add .gitignore for deployment"
```

---

### Task 2: 添加 Railway 部署配置文件

**Files:**
- Create: `Procfile`
- Create: `railway.toml`

- [ ] **Step 1: 在项目根目录创建 `Procfile`**

文件内容：
```
web: streamlit run image_comparator/app.py --server.port=$PORT --server.address=0.0.0.0
```

- [ ] **Step 2: 在项目根目录创建 `railway.toml`**

文件内容：
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run image_comparator/app.py --server.port=$PORT --server.address=0.0.0.0"
healthcheckPath = "/"
restartPolicyType = "on_failure"
```

- [ ] **Step 3: 验证两个文件都存在**

```bash
cat Procfile
cat railway.toml
```

期望输出：`Procfile` 包含 `streamlit run`；`railway.toml` 包含 `[build]` 和 `[deploy]` 段。

- [ ] **Step 4: 提交**

```bash
git add Procfile railway.toml
git commit -m "chore: add Railway deployment config"
```

---

### Task 3: 更新 `requirements.txt`

**Files:**
- Modify: `image_comparator/requirements.txt`

- [ ] **Step 1: 编辑 `requirements.txt`**

将文件改为以下内容（移除 `dashscope`，新增 `openai`）：

```
Pillow>=10.0
imagehash>=4.3
httpx>=0.27
openpyxl>=3.1
streamlit>=1.35
pandas>=2.0
openai>=1.0
pytest>=8.0
pytest-asyncio>=0.23
```

- [ ] **Step 2: 验证内容**

```bash
cat image_comparator/requirements.txt
```

期望：包含 `openai>=1.0`，不包含 `dashscope`。

- [ ] **Step 3: 本地安装验证没有冲突**

```bash
cd image_comparator && pip install -r requirements.txt --dry-run 2>&1 | tail -5
```

期望：无报错（`--dry-run` 仅验证依赖可解析，不实际安装）。

- [ ] **Step 4: 提交**

```bash
cd ..
git add image_comparator/requirements.txt
git commit -m "chore: replace dashscope with openai in requirements"
```

---

### Task 4: 简化 `config.py`，移除文件读取逻辑

**Files:**
- Modify: `image_comparator/config.py`

当前 `config.py` 有 `_KEY_FILE`、`_read_saved_key()` 等文件读取逻辑。Railway 容器文件系统为临时存储，该逻辑在云端无意义且有副作用，需移除。

- [ ] **Step 1: 将 `config.py` 改为以下内容**

```python
import os

# 千问 API Key：优先读环境变量（供本地 .env 或 CI 注入），云端由用户在 Session 中输入
QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")

# API 接入点（公司网关）
QWEN_API_BASE: str = "https://ai-aigw.semir.com/bailian-tongyi-outside/v1"

# pHash 汉明距离阈值
PHASH_SAME_THRESHOLD: int = 2    # 距离 <= 2 → 直接判同
PHASH_DIFF_THRESHOLD: int = 25   # 距离 >= 25 → 直接判异

# 批量模式并发数
BATCH_CONCURRENCY: int = 10

# 图片下载超时（秒）
DOWNLOAD_TIMEOUT: int = 10

# 千问VL模型名称
QWEN_VL_MODEL: str = "qwen-vl-max"

# 单条比对最长等待时间（秒）
COMPARE_TIMEOUT: int = 30
```

- [ ] **Step 2: 验证文件内容**

```bash
cat image_comparator/config.py
```

期望：不含 `_KEY_FILE`、`_read_saved_key`、`json`、`open(`。

- [ ] **Step 3: 提交**

```bash
git add image_comparator/config.py
git commit -m "refactor: remove file-based API key persistence from config"
```

---

### Task 5: 简化 `app.py`，移除文件持久化逻辑

**Files:**
- Modify: `image_comparator/app.py`（第 1-33 行、第 206-214 行）

- [ ] **Step 1: 删除 `app.py` 顶部的文件持久化代码**

将文件开头从：
```python
import time
import os
import json
import streamlit as st
import pandas as pd
from comparator import compare, CompareResult
from reporter import generate_excel_bytes

_KEY_FILE = os.path.join(os.path.dirname(__file__), ".api_key.json")

def _load_api_key():
    """从本地文件加载 API Key 到 session_state 和 config"""
    if "api_key" not in st.session_state:
        if os.path.exists(_KEY_FILE):
            try:
                data = json.load(open(_KEY_FILE))
                key = data.get("api_key", "")
                if key:
                    import config as _cfg
                    _cfg.QWEN_API_KEY = key
                    st.session_state["api_key"] = key
            except Exception:
                pass

def _save_api_key(key: str):
    """持久化 API Key 到本地文件"""
    try:
        with open(_KEY_FILE, "w") as f:
            json.dump({"api_key": key}, f)
    except Exception:
        pass

_load_api_key()
```

改为：
```python
import time
import streamlit as st
import pandas as pd
from comparator import compare, CompareResult
from reporter import generate_excel_bytes
```

- [ ] **Step 2: 修改 `settings_dialog()` 中的保存逻辑**

将 `settings_dialog()` 函数中的保存按钮代码从：
```python
    if st.button("保存配置", type="primary", use_container_width=True):
            if api_key:
                import config as _cfg
                _cfg.QWEN_API_KEY = api_key
                st.session_state["api_key"] = api_key
                _save_api_key(api_key)
                st.success("API Key 已保存")
            else:
                st.warning("API Key 不能为空")
```

改为：
```python
    if st.button("保存配置", type="primary", use_container_width=True):
        if api_key:
            import config as _cfg
            _cfg.QWEN_API_KEY = api_key
            st.session_state["api_key"] = api_key
            st.success("API Key 已保存（当前会话有效）")
        else:
            st.warning("API Key 不能为空")
```

- [ ] **Step 3: 验证 `app.py` 不含文件持久化代码**

```bash
grep -n "_KEY_FILE\|_load_api_key\|_save_api_key\|api_key.json\|json.dump\|json.load" image_comparator/app.py
```

期望：**无任何输出**（即这些字符串已全部移除）。

- [ ] **Step 4: 本地快速启动验证应用可运行**

```bash
cd image_comparator && streamlit run app.py --server.headless true &
sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
```

期望输出：`200`（应用正常响应）。停止测试服务：

```bash
pkill -f "streamlit run app.py"
```

- [ ] **Step 5: 提交**

```bash
cd ..
git add image_comparator/app.py
git commit -m "refactor: remove file-based API key persistence, session-only storage"
```

---

### Task 6: 初始化 Git 仓库并推送到 GitHub

**Files:** 无代码变更，仅 Git 操作

- [ ] **Step 1: 在项目根目录初始化 Git（如果尚未初始化）**

```bash
cd /Users/apple/Documents/AI/商品链接图片分析/电商链接主图相似度比对
git init
```

如果已是 git 仓库（`git status` 正常），跳过此步。

- [ ] **Step 2: 在 GitHub 创建 Private 仓库**

打开 https://github.com/new，填写：
- Repository name: `ecommerce-image-comparator`（或其他名称）
- Visibility: **Private**
- 不勾选 "Initialize with README"（本地已有文件）
- 点击 "Create repository"

- [ ] **Step 3: 关联远程仓库并推送**

将下面的 `YOUR_GITHUB_USERNAME` 替换为实际 GitHub 用户名：

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/ecommerce-image-comparator.git
git branch -M main
git push -u origin main
```

- [ ] **Step 4: 验证推送成功**

打开 GitHub 仓库页面，确认以下文件存在：
- `Procfile`
- `railway.toml`
- `.gitignore`
- `image_comparator/app.py`
- `image_comparator/config.py`
- `image_comparator/requirements.txt`

确认以下文件**不存在**：
- `image_comparator/.api_key.json`

---

### Task 7: Railway 创建项目并部署

**Files:** 无代码变更，仅 Railway 平台操作

- [ ] **Step 1: 登录 Railway**

打开 https://railway.app，用 GitHub 账号登录（推荐，方便后续关联仓库）。

- [ ] **Step 2: 创建新项目**

点击 "New Project" → 选择 "Deploy from GitHub repo" → 授权 Railway 访问 GitHub → 选择 `ecommerce-image-comparator` 仓库。

- [ ] **Step 3: 等待首次构建完成**

Railway 自动检测 `railway.toml` 并开始构建（Nixpacks 自动检测 Python 环境）。
在 Railway 控制台 Deployments 页面查看构建日志，等待状态变为 **Active**。

- [ ] **Step 4: 获取访问 URL**

构建成功后，在 Railway 项目 Settings → Domains，点击 "Generate Domain" 生成访问地址（格式如 `https://xxx.up.railway.app`）。

- [ ] **Step 5: 验证应用可访问**

在浏览器打开 Railway 生成的 URL，确认：
- 页面正常加载，显示"电商链接图片相似度比对"标题
- 点击右上角"设置"，可输入 API Key
- 输入 Key 后点击"保存配置"，提示"API Key 已保存（当前会话有效）"

- [ ] **Step 6: 验证单条比对功能**

在设置中输入有效 API Key，在"单条比对"标签输入两个阿里云图片 URL，点击"比对"，验证结果正常返回。

---

### Task 8: 验证自动部署流程

**Files:** 无���码变更，验证 CI/CD 链路

- [ ] **Step 1: 在本地修改一行代码（测试用）**

编辑 `image_comparator/app.py`，将页面标题中的 `page_icon="🔍"` 改为 `page_icon="🛍️"`：

```python
st.set_page_config(page_title="电商链接图片相似度比对", layout="wide", page_icon="🛍️")
```

- [ ] **Step 2: 提交并推送**

```bash
git add image_comparator/app.py
git commit -m "test: verify Railway auto-deploy"
git push
```

- [ ] **Step 3: 观察 Railway 自动重新部署**

打开 Railway 控制台 Deployments 页面，确认新的部署自动触发并完成。

- [ ] **Step 4: 改回原始 icon**

```python
st.set_page_config(page_title="电商链接图片相似度比对", layout="wide", page_icon="🔍")
```

```bash
git add image_comparator/app.py
git commit -m "chore: restore page icon"
git push
```
