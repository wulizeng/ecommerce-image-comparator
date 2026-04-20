from dataclasses import dataclass
import imagehash
from PIL import Image
from config import PHASH_SAME_THRESHOLD, PHASH_DIFF_THRESHOLD


@dataclass
class PHashResult:
    hamming_distance: int
    verdict: str          # "same" | "different" | "uncertain"
    similarity_score: int # 0~100


def compute_hamming_distance(img1: Image.Image, img2: Image.Image) -> int:
    """计算两张图片的 pHash 汉明距离"""
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)
    return hash1 - hash2


def classify_by_distance(distance: int) -> PHashResult:
    """
    根据汉明距离给出初步判断。
    distance <= PHASH_SAME_THRESHOLD  → same
    distance >= PHASH_DIFF_THRESHOLD  → different
    中间区间                           → uncertain（交由VL裁判）
    """
    if distance <= PHASH_SAME_THRESHOLD:
        score = max(95, 100 - distance)
        return PHashResult(distance, "same", score)
    elif distance >= PHASH_DIFF_THRESHOLD:
        score = max(0, 30 - (distance - PHASH_DIFF_THRESHOLD) * 2)
        return PHashResult(distance, "different", score)
    else:
        return PHashResult(distance, "uncertain", 50)
