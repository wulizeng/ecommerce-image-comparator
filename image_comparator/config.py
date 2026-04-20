import os

# 千问 API Key：优先读环境变量（供本地 .env 或 CI 注入），云端由用户在 Session 中输入
QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")

# API 接入点（公司网关）
QWEN_API_BASE: str = "https://ai-aigw.semir.com/bailian-tongyi-outside/v1"

# pHash 汉明距离阈值
PHASH_SAME_THRESHOLD: int = 2    # 距离 <= 2 → 直接判同（几乎完全一致）
PHASH_DIFF_THRESHOLD: int = 25   # 距离 >= 25 → 直接判异（明显不同内容）

# 批量模式并发数
BATCH_CONCURRENCY: int = 10

# 图片下载超时（秒）
DOWNLOAD_TIMEOUT: int = 10

# 千问VL模型名称
QWEN_VL_MODEL: str = "qwen-vl-max"

# 单条比对最长等待时间（秒），超时直接标记为 error 并跳过
COMPARE_TIMEOUT: int = 30
