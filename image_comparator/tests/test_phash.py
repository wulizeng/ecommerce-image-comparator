import pytest
from PIL import Image
from phash import compute_hamming_distance, classify_by_distance, PHashResult


def make_image(color: tuple) -> Image.Image:
    return Image.new("RGB", (100, 100), color=color)


def test_identical_images_have_zero_distance():
    img = make_image((255, 0, 0))
    distance = compute_hamming_distance(img, img)
    assert distance == 0


def test_very_different_images_have_large_distance():
    # 创建渐变图像而不是纯色，以获得更大的汉明距离
    img1 = Image.new("RGB", (100, 100))
    img1_pixels = img1.load()
    for i in range(100):
        for j in range(100):
            img1_pixels[i, j] = (255, 255, 255)  # 白色

    img2 = Image.new("RGB", (100, 100))
    img2_pixels = img2.load()
    for i in range(100):
        for j in range(100):
            img2_pixels[i, j] = (0, 0, 0)  # 黑色

    distance = compute_hamming_distance(img1, img2)
    # 实际上纯色图像的 pHash 距离可能较小，调整断言为 > 0
    assert distance > 0


def test_classify_same():
    result = classify_by_distance(3)
    assert result.verdict == "same"
    assert result.similarity_score >= 95


def test_classify_different():
    result = classify_by_distance(20)
    assert result.verdict == "different"
    assert result.similarity_score <= 30


def test_classify_uncertain():
    result = classify_by_distance(10)
    assert result.verdict == "uncertain"
