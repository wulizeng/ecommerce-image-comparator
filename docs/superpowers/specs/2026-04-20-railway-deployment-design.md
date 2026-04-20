# Railway 部署设计

## 目标

将现有 Streamlit 应用（电商链接图片相似度比对）部署到 Railway，通过 GitHub Private 仓库实现自动 CI/CD，供内部用户通过浏览器在线访问。

## 架构

- **代码托管**：GitHub Private 仓库
- **部署平台**：Railway（关联 GitHub，自动构建部署）
- **API Key 策略**：Session 级别，每个用户在浏览器 Session 中独立持有自己的 Key，不持久化到服务器

## 文件变更

### 新增文件

**`Procfile`**（项目根目录）
```
web: streamlit run image_comparator/app.py --server.port=$PORT --server.address=0.0.0.0
```

**`railway.toml`**（项目根目录）
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run image_comparator/app.py --server.port=$PORT --server.address=0.0.0.0"
healthcheckPath = "/"
restartPolicyType = "on_failure"
```

**`.gitignore`**（项目根目录）
```
image_comparator/.api_key.json
image_comparator/__pycache__/
**/__pycache__/
*.pyc
.DS_Store
.env
```

### 修改文件

**`image_comparator/requirements.txt`**
- 新增 `openai>=1.0`（`qwen_vl.py` 依赖，当前缺失）
- 移除 `dashscope>=1.14`（已弃用，改用 openai SDK）

**`image_comparator/config.py`**
- 移除 `_KEY_FILE`、`_read_saved_key()` 的文件读取逻辑
- `QWEN_API_KEY` 只从环境变量读取：`os.getenv("QWEN_API_KEY", "")`
- 保留其余配置不变

**`image_comparator/app.py`**
- 移除 `_KEY_FILE` 常量
- 移除 `_load_api_key()` 函数及调用
- 移除 `_save_api_key()` 函数及调用
- `settings_dialog()` 中"保存配置"仅写入 `st.session_state["api_key"]` 和 `config.QWEN_API_KEY`，不写文件

## API Key 流程

```
用户打开 URL
    → 点击右上角"设置"
    → 输入自己的 API Key → 保存
    → Key 存入 session_state（仅当前浏览器 Tab 有效）
    → 正常使用单条/批量比对
    → 关闭页面或刷新后需重新输入
```

- 多用户之间 Key 完全隔离（Streamlit session 机制保证）
- 服务器不保存任何 Key
- Railway 无需配置 `QWEN_API_KEY` 环境变量

## 部署流程

1. 在项目根目录初始化 Git，添加 `.gitignore`
2. 在 GitHub 创建 Private 仓库，推送代码
3. Railway 创建新项目 → Deploy from GitHub repo → 选择该仓库
4. Railway 自动检测 `Procfile` / `railway.toml`，构建并部署
5. Railway 生成访问 URL，分发给内部用户
6. 后续更新：本地修改代码 → `git push` → Railway 自动重新部署

## 约束

- `.api_key.json` 必须在 `.gitignore` 中，不能上传到 GitHub
- Railway 容器文件系统为临时存储，重启后会丢失，因此不在服务器写文件
- 本地开发仍可使用 `.api_key.json`（`config.py` 保留 `os.getenv` 兜底）
