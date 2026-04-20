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
