import json
import re
import base64
import httpx
from dataclasses import dataclass
from openai import OpenAI
from config import QWEN_API_KEY, QWEN_API_BASE, QWEN_VL_MODEL


class VLError(Exception):
    """千问VL API调用失败"""
    pass


@dataclass
class VLResult:
    is_same: bool
    similarity_score: int  # 0~100
    reason: str


_SYSTEM_PROMPT = """你是一个电商视觉比对系统的图像分析模块。

你只有一个功能：判断两张商品图片是否相同。

判定为**不同**的标准（满足任意一条即判为不同）：
- 商品本身不同（款式、颜色、材质、种类）
- 图片构图/拍摄角度明显不同
- 图片排版布局不同（文字位置、背景色块、装饰元素位置差异）
- 图片上的文字/宣传语/排版风格有差异

判定为**相同**的标准（必须同时满足）：
- 商品款式、颜色、背景场景完全一致
- 构图、模特姿势、拍摄角度完全一致
- 图片上的文字排版、布局、装饰元素基本一致（允许轻微缩放/压缩差异）

严禁事项：
- 严禁因价格、金额不同而判定图片不同
"""

_PROMPT = """请判断上方两张图片是否相同。

判断时必须遵守：
1. 比较商品的外观（款式/颜色/材质）和整体构图
2. 比较图片上的文字排版、宣传语位置、装饰元素是否一致
3. 文字/排版不同应判为不同（即使商品是同一款）
4. 价格、金额数字不同忽略，不影响判断

请只返回如下JSON，不要输出其他任何内容：
{"is_same": true或false, "similarity_score": 0到100的整数, "reason": "一句话描述画面差异或相同原因"}"""


def _url_to_base64(url: str) -> str:
    """将图片 URL 下载后转为 base64，供 API 使用"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.taobao.com/",
    }
    resp = httpx.get(url, timeout=15, follow_redirects=True, headers=headers)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
    b64 = base64.b64encode(resp.content).decode()
    return f"data:{content_type};base64,{b64}"


def call_qwen_vl(url1: str, url2: str, api_key: str = "") -> VLResult:
    """
    调用千问 VL 模型判断两张图片是否相同（OpenAI 兼容接口）。
    失败时抛出 VLError。
    api_key 优先使用调用方传入的值，其次回退到 config/env。
    """
    import config as _config
    resolved_key = api_key or _config.QWEN_API_KEY or QWEN_API_KEY
    if not resolved_key:
        raise VLError("未配置 API Key，请在设置中填写")

    try:
        client = OpenAI(api_key=resolved_key, base_url=_config.QWEN_API_BASE)

        # 转 base64 避免网关无法访问外部图片 URL
        img1_b64 = _url_to_base64(url1)
        img2_b64 = _url_to_base64(url2)

        response = client.chat.completions.create(
            model=_config.QWEN_VL_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": _SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _PROMPT},
                        {"type": "image_url", "image_url": {"url": img1_b64}},
                        {"type": "image_url", "image_url": {"url": img2_b64}},
                    ],
                }
            ],
            max_tokens=256,
        )

        if response is None or not response.choices:
            raise VLError("API 返回为空，请检查 API Key 是否有效")

        raw_text = response.choices[0].message.content

        match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
        if not match:
            raise VLError(f"模型未返回有效JSON: {raw_text}")
        data = json.loads(match.group())

        is_same = bool(data["is_same"])
        reason = str(data["reason"])
        score = int(data["similarity_score"])

        return VLResult(
            is_same=is_same,
            similarity_score=score,
            reason=reason,
        )
    except VLError:
        raise
    except Exception as e:
        raise VLError(f"千问VL调用失败: {e}") from e
