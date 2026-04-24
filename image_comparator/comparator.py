from dataclasses import dataclass, field
from downloader import download_image, DownloadError
from phash import compute_hamming_distance, classify_by_distance
from qwen_vl import call_qwen_vl, VLError


@dataclass
class CompareResult:
    url1: str
    url2: str
    is_same: bool
    similarity_score: int   # 0~100
    recommendation: str
    reason: str
    method: str             # "phash_same" | "phash_diff" | "qwen_vl" | "phash_fallback" | "error"
    error: str = ""
    steps: list = field(default_factory=list)  # 分析步骤列表


def _make_recommendation(is_same: bool) -> str:
    return "图片一致，无需调整" if is_same else "图片不一致，建议调整店铺链接主图"


def compare(url1: str, url2: str, api_key: str = "") -> CompareResult:
    """
    比对两张图片URL，返回 CompareResult。
    流程：下载 → pHash初筛 → 按需调用千问VL。
    """
    steps = []

    # 1. 下载图片
    try:
        img1 = download_image(url1)
        img2 = download_image(url2)
    except DownloadError as e:
        return CompareResult(
            url1=url1, url2=url2,
            is_same=False, similarity_score=0,
            recommendation="下载失败，无法判断",
            reason=str(e), method="error", error=str(e),
            steps=[{"step": 1, "name": "图片下载", "status": "fail", "detail": str(e)}]
        )

    # 2. pHash 初筛
    distance = compute_hamming_distance(img1, img2)
    phash_result = classify_by_distance(distance)
    steps.append({
        "step": 1,
        "name": "pHash 感知哈希",
        "status": "done",
        "detail": f"汉明距离 = {distance}，判定区间：{'直接判同' if phash_result.verdict == 'same' else '直接判异' if phash_result.verdict == 'different' else '模糊区间，进入大模型精判'}"
    })

    if phash_result.verdict == "same":
        steps.append({"step": 2, "name": "大模型精判", "status": "skip", "detail": "pHash 已高置信度判同，跳过"})
        return CompareResult(
            url1=url1, url2=url2,
            is_same=True,
            similarity_score=phash_result.similarity_score,
            recommendation=_make_recommendation(True),
            reason=f"图片高度相似（pHash汉明距离={distance}），为同一张图或轻微压缩版本",
            method="phash_same",
            steps=steps,
        )

    if phash_result.verdict == "different":
        steps.append({"step": 2, "name": "大模型精判", "status": "skip", "detail": "pHash 已高置信度判异，跳过"})
        return CompareResult(
            url1=url1, url2=url2,
            is_same=False,
            similarity_score=phash_result.similarity_score,
            recommendation=_make_recommendation(False),
            reason=f"图片差异明显（pHash汉明距离={distance}），判定为不同图片",
            method="phash_diff",
            steps=steps,
        )

    # 3. 模糊区间 → 调用千问VL
    try:
        vl_result = call_qwen_vl(url1, url2, api_key=api_key)
        steps.append({"step": 2, "name": "千问 VL 大模型精判", "status": "done", "detail": vl_result.reason})
        return CompareResult(
            url1=url1, url2=url2,
            is_same=vl_result.is_same,
            similarity_score=vl_result.similarity_score,
            recommendation=_make_recommendation(vl_result.is_same),
            reason=vl_result.reason,
            method="qwen_vl",
            steps=steps,
        )
    except VLError as e:
        steps.append({"step": 2, "name": "千问 VL 大模型精判", "status": "fail", "detail": f"调用失败：{e}，降级处理"})
        return CompareResult(
            url1=url1, url2=url2,
            is_same=False,
            similarity_score=phash_result.similarity_score,
            recommendation=_make_recommendation(False),
            reason=f"千问VL调用失败，降级判断（pHash汉明距离={distance}，处于模糊区间）",
            method="phash_fallback",
            steps=steps,
        )
