import io
import httpx
from PIL import Image
from config import DOWNLOAD_TIMEOUT

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.taobao.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


class DownloadError(Exception):
    """图片下载失败"""
    pass


def download_image(url: str) -> Image.Image:
    """
    下载图片URL并返回PIL Image对象。
    失败时抛出 DownloadError。
    """
    try:
        response = httpx.get(url, timeout=DOWNLOAD_TIMEOUT, follow_redirects=True,
                             headers=_HEADERS)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    except httpx.TimeoutException as e:
        raise DownloadError(f"下载超时: {url}") from e
    except httpx.HTTPStatusError as e:
        raise DownloadError(f"HTTP错误 {e.response.status_code}: {url}") from e
    except Exception as e:
        raise DownloadError(f"下载失败: {url} — {e}") from e
