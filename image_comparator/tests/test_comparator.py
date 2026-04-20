import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from comparator import compare, compare_batch, CompareResult
from phash import PHashResult
from qwen_vl import VLResult


def make_image():
    return Image.new("RGB", (10, 10), color=(100, 100, 100))


@patch("comparator.download_image")
@patch("comparator.compute_hamming_distance")
@patch("comparator.classify_by_distance")
def test_compare_phash_same(mock_classify, mock_distance, mock_download):
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
    from qwen_vl import VLError
    mock_download.return_value = make_image()
    mock_distance.return_value = 10
    mock_classify.return_value = PHashResult(10, "uncertain", 50)
    mock_vl.side_effect = VLError("API超时")

    result = compare("https://a.com/1.jpg", "https://a.com/2.jpg")

    assert result.method == "phash_fallback"
    assert result.is_same is False


@patch("comparator.compare")
def test_compare_batch_preserves_order(mock_compare):
    """批量比对结果顺序与输入一致"""
    def make_result(u1, u2, same):
        return CompareResult(url1=u1, url2=u2, is_same=same, similarity_score=90,
                             recommendation="test", reason="test", method="phash_same")
    mock_compare.side_effect = [
        make_result("u1", "u2", True),
        make_result("u3", "u4", False),
        make_result("u5", "u6", True),
    ]

    pairs = [("u1", "u2"), ("u3", "u4"), ("u5", "u6")]
    results = compare_batch(pairs)

    assert len(results) == 3
    assert results[0].url1 == "u1" and results[0].is_same is True
    assert results[1].url1 == "u3" and results[1].is_same is False
    assert results[2].url1 == "u5" and results[2].is_same is True


@patch("comparator.download_image")
def test_compare_download_error(mock_download):
    """下载失败时返回 method=error"""
    from downloader import DownloadError
    mock_download.side_effect = DownloadError("404 Not Found")

    result = compare("https://a.com/invalid.jpg", "https://a.com/2.jpg")

    assert result.method == "error"
    assert result.is_same is False
    assert "404" in result.error
