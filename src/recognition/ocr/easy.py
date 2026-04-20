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

    @staticmethod
    def _load_color_roi(img, region=None) -> np.ndarray:
        """
        读取并裁剪 ROI，统一返回 BGR 图。
        :param img: 图像路径(str) 或 ndarray(BGR/Gray)
        :param region: (x, y, w, h)；如果 img 已经是裁剪后小图可传 None
        """
        if isinstance(img, str):
            color = cv2.imread(img)
            if color is None:
                raise ValueError(f"无法读取图像: {img}")
        elif isinstance(img, np.ndarray):
            color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
        else:
            raise TypeError(f"不支持的类型: {type(img)}")

        if region is not None:
            x, y, w, h = map(int, region)
            color = color[y:y + h, x:x + w]
            if color.size == 0:
                raise ValueError(f"region 裁剪结果为空: {region}")

        return color

    @staticmethod
    def _ensure_bgr(img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img

    @staticmethod
    def _resize_roi(roi: np.ndarray, scale: float) -> np.ndarray:
        h, w = roi.shape[:2]
        return cv2.resize(
            roi,
            (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
            interpolation=cv2.INTER_CUBIC
        )

    @staticmethod
    def _crop_text_by_mask(roi: np.ndarray, text_mask: np.ndarray, pad=None):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        text_mask = cv2.dilate(text_mask, kernel, iterations=1)

        points = cv2.findNonZero(text_mask)
        if points is not None:
            x, y, w, h = cv2.boundingRect(points)
            if pad is None:
                pad = max(3, min(10, max(w, h) // 10))
            x0 = max(0, x - pad)
            y0 = max(0, y - pad)
            x1 = min(roi.shape[1], x + w + pad)
            y1 = min(roi.shape[0], y + h + pad)
            return roi[y0:y1, x0:x1], text_mask[y0:y1, x0:x1]
        return roi, text_mask

    def _build_masked_number_image(self, roi: np.ndarray, text_mask: np.ndarray) -> np.ndarray:
        roi, text_mask = self._crop_text_by_mask(roi, text_mask)
        processed = np.full(text_mask.shape, 255, dtype=np.uint8)
        processed[text_mask > 0] = 0
        processed = cv2.copyMakeBorder(
            processed, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255
        )
        return processed

    def _build_color_number_image(self, roi: np.ndarray, text_mask: np.ndarray,
                                  border: int = 16) -> np.ndarray:
        roi, _ = self._crop_text_by_mask(roi, text_mask, pad=4)
        return cv2.copyMakeBorder(
            roi, border, border, border, border, cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )

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

    def _build_champions_row_number_mask(self, roi: np.ndarray, tight: bool = False):
        """
        champions_row 数字常见于彩色底上的亮数字/百分号。
        这里复用文本识别的颜色思路：先估计背景色，再提亮字、蓝色边缘与偏离背景的区域。
        """
        roi = self._ensure_bgr(roi)
        b, g, r = cv2.split(roi)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        border_pixels = np.concatenate([
            roi[0, :, :],
            roi[-1, :, :],
            roi[:, 0, :],
            roi[:, -1, :],
        ], axis=0)
        bg_color = np.median(border_pixels, axis=0).astype(np.uint8)
        bg_gray = int(np.mean(bg_color))

        color_distance = np.max(
            np.abs(roi.astype(np.int16) - bg_color.astype(np.int16)),
            axis=2
        ).astype(np.uint8)
        _, distance_mask = cv2.threshold(color_distance, 20, 255, cv2.THRESH_BINARY)

        bright_threshold = min(245, max(150, bg_gray + 18))
        bright_mask = cv2.inRange(gray, bright_threshold, 255)

        blue_score = np.clip(
            b.astype(np.int16) - np.maximum(g, r).astype(np.int16),
            0,
            255
        ).astype(np.uint8)
        _, blue_mask = cv2.threshold(
            blue_score, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        white_mask = cv2.inRange(hsv, (0, 0, 150), (179, 110, 255))

        if tight:
            text_mask = cv2.bitwise_or(bright_mask, white_mask)
            text_mask = cv2.bitwise_or(text_mask, blue_mask)
        else:
            text_mask = cv2.bitwise_or(distance_mask, bright_mask)
            text_mask = cv2.bitwise_or(text_mask, white_mask)
            text_mask = cv2.bitwise_or(text_mask, blue_mask)

        return roi, text_mask

    def _recognize_number_text(self, gray: np.ndarray, scale: int) -> str:
        processed = self._preprocess_number(gray, scale=scale)
        results = self._reader.readtext(
            processed,
            allowlist='0123456789.%',
            detail=0,
            paragraph=False,
        )
        return "".join(results).strip()

    def _read_number_text(self, img: np.ndarray) -> str:
        results = self._reader.readtext(
            img,
            allowlist='0123456789.%',
            detail=0,
            paragraph=False,
        )
        return "".join(results).strip()

    def _recognize_champions_row_number_candidates(self, roi: np.ndarray, scale: int,
                                                   include_fallback: bool = False):
        """
        champions_row 数字候选图生成。
        默认只保留最快且效果最稳定的彩色紧裁图和亮字二值图，
        在快速路径失败时再补充掩码图与原图兜底。
        """
        scaled_roi = self._resize_roi(roi, scale)
        color_roi, tight_mask = self._build_champions_row_number_mask(
            scaled_roi, tight=True
        )
        gray = cv2.cvtColor(scaled_roi, cv2.COLOR_BGR2GRAY)
        binary = self._preprocess_number(gray, scale=1)

        candidates = [
            self._build_color_number_image(color_roi, tight_mask),
            binary,
        ]

        if include_fallback:
            _, full_mask = self._build_champions_row_number_mask(
                scaled_roi, tight=False
            )
            candidates.extend([
                self._build_masked_number_image(scaled_roi, full_mask),
                scaled_roi,
            ])

        return candidates

    @staticmethod
    def _normalize_number_text(text: str) -> str:
        text = str(text or "").replace('%', '').strip()
        text = "".join(ch for ch in text if ch.isdigit() or ch == '.')
        if not text:
            return ""

        if text.count('.') <= 1:
            return text

        integer_part, *decimal_parts = text.split('.')
        decimal_part = "".join(decimal_parts)
        if not integer_part:
            integer_part = "0"
        return f"{integer_part}.{decimal_part}" if decimal_part else integer_part

    @staticmethod
    def _select_number_value(recognized, scale: int) -> float:
        if not recognized:
            return 0.0

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
                abs(value - scale),
                len(str(value)),
                value,
            )
        )

    def recognize_number_roi(self, img, region=None, scale: int = 5) -> float:
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
            text = self._normalize_number_text(
                self._recognize_number_text(gray, scale=current_scale)
            )
            if not text:
                continue
            try:
                recognized.append((float(text), abs(current_scale - scale), current_scale == scale))
            except ValueError:
                continue

        return self._select_number_value(recognized, scale)

    def recognize_champions_row_number_roi(self, img, region=None, scale: int = 5) -> float:
        """
        champions_row 专用数字识别。
        复用文本识别里的颜色裁切思路，同时保留原有亮字二值化兜底。
        """
        roi = self._load_color_roi(img, region=region)
        recognized = []

        # 快速路径：优先只试中心 scale 的两个高价值候选，显著减少 EasyOCR 调用次数。
        primary_texts = []
        for candidate in self._recognize_champions_row_number_candidates(
            roi, scale, include_fallback=False
        ):
            text = self._normalize_number_text(self._read_number_text(candidate))
            if not text:
                continue
            try:
                value = float(text)
            except ValueError:
                continue
            recognized.append((value, 0, True))
            primary_texts.append(value)

        if len(primary_texts) >= 2 and len(set(primary_texts)) == 1:
            return primary_texts[0]

        # 只有快速路径不稳定时，才扩大到相邻 scale，并补充更慢的兜底候选。
        fallback_scales = []
        if scale > 1:
            fallback_scales.append(scale - 1)
        fallback_scales.append(scale + 1)

        for current_scale in fallback_scales:
            for candidate in self._recognize_champions_row_number_candidates(
                roi, current_scale, include_fallback=True
            ):
                text = self._normalize_number_text(self._read_number_text(candidate))
                if not text:
                    continue
                try:
                    recognized.append(
                        (float(text), abs(current_scale - scale), False)
                    )
                except ValueError:
                    continue

        return self._select_number_value(recognized, scale)
