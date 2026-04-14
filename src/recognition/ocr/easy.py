from collections import Counter

import cv2
import numpy as np
import easyocr

class EasyOCR:
    _instance = None
    def __new__(cls, langs='en', gpu=True, verbose=False, **kwargs):
        if cls._instance is None:
            cls._instance = super(EasyOCR, cls).__new__(cls)
        lang = langs.split(',')
        for l in lang:
            l = l.strip()
        cls._instance._reader = easyocr.Reader(lang, gpu=gpu, verbose=verbose)
        return cls._instance

    @staticmethod
    def _load_gray_roi(img, region=None) -> np.ndarray:
        """
        读取并裁剪 ROI，统一返回灰度图。
        :param img: 图像路径(str) 或 ndarray(BGR/Gray)
        :param region: (x, y, w, h)；如果 img 已经是裁剪后小图可传 None
        """
        if isinstance(img, str):
            gray = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
            if gray is None:
                raise ValueError(f"无法读取图像: {img}")
        elif isinstance(img, np.ndarray):
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img.copy()
        else:
            raise TypeError(f"不支持的类型: {type(img)}")

        if region is not None:
            x, y, w, h = map(int, region)
            gray = gray[y:y + h, x:x + w]
            if gray.size == 0:
                raise ValueError(f"region 裁剪结果为空: {region}")

        return gray

    def _preprocess_number(self, gray: np.ndarray, scale: int = 5) -> np.ndarray:
        """
        针对白色数字+深色/彩色背景的预处理。
        核心思路：直接高阈值提取亮字，再做轻度膨胀。
        """
        h, w = gray.shape[:2]
        scaled = cv2.resize(
            gray,
            (max(1, w * scale), max(1, h * scale)),
            interpolation=cv2.INTER_CUBIC
        )

        _, binary = cv2.threshold(scaled, 180, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.dilate(binary, kernel, iterations=1)

        inverted = cv2.bitwise_not(binary)  # 黑底白字 -> 白底黑字
        return inverted

    def _recognize_number_text(self, gray: np.ndarray, scale: int) -> str:
        processed = self._preprocess_number(gray, scale=scale)
        results = self._reader.readtext(
            processed,
            allowlist='0123456789',
            detail=0,
            paragraph=False,
        )
        return "".join(results).strip()

    def recognize_number_roi(self, img, region=None, scale: int = 5) -> int:
        """
        识别数字 ROI。

        :param img: 已裁剪小图(ndarray BGR/Gray) 或图像路径(str)
        :param region: (x, y, w, h)，传入则先裁剪；已裁剪传 None
        :param scale: 放大倍数，默认 5
        """
        gray = self._load_gray_roi(img, region=region)
        scales = range(max(1, scale - 2), scale + 3)
        recognized = []

        for current_scale in scales:
            text = self._recognize_number_text(gray, scale=current_scale)
            if text.isdigit():
                recognized.append((int(text), abs(current_scale - scale), current_scale == scale))

        if not recognized:
            return 0

        counts = Counter(value for value, _, _ in recognized)
        best_count = max(counts.values())
        best_values = [value for value, count in counts.items() if count == best_count]

        if len(best_values) == 1:
            return best_values[0]

        center_value = next(
            (value for value, _, is_center in recognized if is_center and value in best_values),
            None
        )
        if center_value is not None:
            return center_value

        return min(
            best_values,
            key=lambda value: (
                min(offset for candidate, offset, _ in recognized if candidate == value),
                len(str(value)),
                value,
            )
        )
