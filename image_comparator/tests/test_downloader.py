import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io

from downloader import download_image, DownloadError


def test_download_image_returns_pil_image():
    """下载成功时返回 PIL Image 对象"""
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
