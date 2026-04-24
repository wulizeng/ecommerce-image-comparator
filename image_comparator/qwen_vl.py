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

你只有一个功能：判断两张商品图片的**视觉画面**是否相同。

严禁事项：
- 严禁因价格、金额、数字不同而判定图片不同

判断依据（仅限以下内容）：
- 商品的外形、轮廓、款式
- 商品的颜色、花纹、材质纹理
- 构图、拍摄角度、背景
- 主体物体的种类和数量

规则：完全忽略图片上所有价格、金额信息，只看视觉画面本身。"""

_PROMPT = """请判断上方两张图片的视觉画面是否相同。

判断时必须遵守：
1. 只比较商品的外观视觉内容（形状/颜色/构图/背景）
2. 价格、文字、数字、标签全部忽略，不影响判断
3. 只有商品实体画面不同才能判为 false

请只返回如下JSON，不要输出其他任何内容：
{"is_same": true或false, "similarity_score": 0到100的整数, "reason": "一句话描述画面视觉差异（禁止提及价格文字）"}"""


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
