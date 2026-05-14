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
    def _add_white_border(img: np.ndarray, border: int = 12):
        value = 255 if img.ndim == 2 else (255, 255, 255)
        return cv2.copyMakeBorder(
            img, border, border, border, border, cv2.BORDER_CONSTANT, value=value
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
        return self._add_white_border(processed, border=12)

    def _build_color_number_image(self, roi: np.ndarray, text_mask: np.ndarray,
                                  border: int = 16) -> np.ndarray:
        roi, _ = self._crop_text_by_mask(roi, text_mask, pad=4)
        return self._add_white_border(roi, border=border)

    def _build_binary_number_image(self, binary: np.ndarray, border: int = 12) -> np.ndarray:
        return self._add_white_border(cv2.bitwise_not(binary), border=border)

    def _build_fast_number_image(self, gray: np.ndarray, scale: int = 1) -> np.ndarray:
        """
        champions_row 使用的旧版快速数字预处理。
        仅保留轻量放大、轻模糊、二值化和极弱膨胀，控制 EasyOCR 调用前的准备成本。
        """
        scaled = self._resize_roi(gray, scale)
        blurred = cv2.GaussianBlur(scaled, (3, 3), 0)
        _, binary = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.dilate(binary, kernel, iterations=1)
        return self._build_binary_number_image(binary, border=12)

    def _build_number_vote_candidates(self, gray: np.ndarray, scale: int = 3):
        """
        为单数字/短数字 ROI 构建轻量多路候选。
        核心遵循：放大 + 轻模糊 + 二值化，不做强膨胀，尽量保留数字 1 的原始结构。
        """
        scaled = self._resize_roi(gray, scale)
        blurred = cv2.GaussianBlur(scaled, (3, 3), 0)

        _, otsu = cv2.threshold(
            scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        _, otsu_blur = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        otsu_inv = cv2.bitwise_not(otsu)
        otsu_blur_inv = cv2.bitwise_not(otsu_blur)

        return [
            {
                "name": "scaled_gray",
                "image": self._add_white_border(scaled, border=12),
                "weight": 0.0,
            },
            {
                "name": "blurred_gray",
                "image": self._add_white_border(blurred, border=12),
                "weight": 0.05,
            },
            {
                "name": "otsu",
                "image": self._add_white_border(otsu, border=12),
                "weight": 0.18,
            },
            {
                "name": "otsu_inv",
                "image": self._add_white_border(otsu_inv, border=12),
                "weight": 0.18,
            },
            {
                "name": "otsu_blur",
                "image": self._add_white_border(otsu_blur, border=12),
                "weight": 0.22,
            },
            {
                "name": "otsu_blur_inv",
                "image": self._add_white_border(otsu_blur_inv, border=12),
                "weight": 0.22,
            },
        ]

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

    def _read_number_text(self, img: np.ndarray):
        results = self._reader.readtext(
            img,
            allowlist='0123456789.%',
            decoder='beamsearch',
            beamWidth=10,
            detail=1,
            paragraph=False,
            contrast_ths=0.05,
            adjust_contrast=0.7,
        )
        if not results:
            return "", 0.0

        texts = []
        scores = []
        for item in results:
            if len(item) < 3:
                continue
            texts.append(str(item[1]).strip())
            try:
                scores.append(float(item[2]))
            except (TypeError, ValueError):
                continue

        return "".join(texts).strip(), (float(np.mean(scores)) if scores else 0.0)

    def _recognize_champions_row_number_candidates(self, roi: np.ndarray, scale: int,
                                                   include_fallback: bool = False):
        """
        champions_row 数字候选图生成。
        恢复为多路投票改造前的快速路径，只保留少量高价值候选。
        """
        scaled_roi = self._resize_roi(roi, scale)
        color_roi, tight_mask = self._build_champions_row_number_mask(
            scaled_roi, tight=True
        )
        tight_crop, _ = self._crop_text_by_mask(color_roi, tight_mask, pad=2)
        tight_gray = cv2.cvtColor(tight_crop, cv2.COLOR_BGR2GRAY)

        candidates = [
            {
                "name": "tight_color",
                "image": self._add_white_border(tight_crop, border=16),
                "weight": 0.28,
            },
            {
                "name": "tight_binary",
                "image": self._build_fast_number_image(tight_gray, scale=1),
                "weight": 0.2,
            },
        ]

        if include_fallback:
            _, full_mask = self._build_champions_row_number_mask(
                scaled_roi, tight=False
            )
            candidates.extend([
                {
                    "name": "full_mask",
                    "image": self._build_masked_number_image(scaled_roi, full_mask),
                    "weight": 0.1,
                },
                {
                    "name": "raw_roi",
                    "image": self._add_white_border(scaled_roi, border=12),
                    "weight": 0.02,
                },
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

        grouped = {}
        for item in recognized:
            grouped.setdefault(item["value"], []).append(item)

        def ranking(value):
            items = grouped[value]
            count = len(items)
            total_score = sum(candidate["score"] for candidate in items)
            total_confidence = sum(candidate["confidence"] for candidate in items)
            best_confidence = max(candidate["confidence"] for candidate in items)
            center_hits = sum(1 for candidate in items if candidate["is_center"])
            min_offset = min(candidate["offset"] for candidate in items)
            return (
                count,
                total_score,
                total_confidence,
                center_hits,
                best_confidence,
                -min_offset,
                -len(str(value)),
                -abs(value - scale),
                -value,
            )

        return max(grouped, key=ranking)

    def _collect_number_candidates(self, candidates, offset: int, is_center: bool):
        recognized = []
        for candidate in candidates:
            raw_text, confidence = self._read_number_text(candidate["image"])
            text = self._normalize_number_text(raw_text)
            if not text:
                continue

            try:
                value = float(text)
            except ValueError:
                continue

            score = (
                candidate.get("weight", 0.0)
                + confidence
                - offset * 0.08
                + (0.05 if is_center else 0.0)
            )
            recognized.append({
                "value": value,
                "text": text,
                "score": score,
                "confidence": confidence,
                "offset": offset,
                "is_center": is_center,
                "source": candidate.get("name", "unknown"),
            })
        return recognized

    @staticmethod
    def _extract_digit_foreground_mask(gray: np.ndarray) -> np.ndarray:
        """
        从小数字 ROI 中提取前景笔画。
        数字背景通常比较统一，用边框灰度估计背景，再取与背景差异明显的像素。
        """
        if gray.size == 0:
            return np.zeros_like(gray, dtype=np.uint8)

        scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        blurred = cv2.GaussianBlur(scaled, (3, 3), 0)

        border_pixels = np.concatenate([
            blurred[0, :],
            blurred[-1, :],
            blurred[:, 0],
            blurred[:, -1],
        ], axis=0)
        bg_gray = int(np.median(border_pixels))
        diff = cv2.absdiff(blurred, np.full_like(blurred, bg_gray))

        _, otsu_mask = cv2.threshold(
            diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        fixed_threshold = 16
        _, fixed_mask = cv2.threshold(diff, fixed_threshold, 255, cv2.THRESH_BINARY)
        mask = cv2.bitwise_and(otsu_mask, fixed_mask)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if num_labels <= 1:
            return mask

        cleaned = np.zeros_like(mask)
        min_area = max(8, int(mask.shape[0] * mask.shape[1] * 0.003))
        for label in range(1, num_labels):
            if stats[label, cv2.CC_STAT_AREA] >= min_area:
                cleaned[labels == label] = 255
        return cleaned

    @staticmethod
    def _looks_like_single_one(gray: np.ndarray) -> bool:
        """
        判断单个数字 ROI 是否更像 1。
        该规则只用于修正 OCR 将单独的 1 误判为 4 的情况，要求非常保守：
        前景必须是窄高结构，并且中部不能有明显横杠。
        """
        mask = EasyOCR._extract_digit_foreground_mask(gray)
        points = cv2.findNonZero(mask)
        if points is None:
            return False

        x, y, w, h = cv2.boundingRect(points)
        roi_h = mask.shape[0]
        if h < roi_h * 0.35 or w < 2:
            return False

        cropped = mask[y:y + h, x:x + w]
        aspect = w / float(h)
        density = cv2.countNonZero(cropped) / float(w * h)

        middle = cropped[int(h * 0.38):max(int(h * 0.62), int(h * 0.38) + 1), :]
        middle_columns = np.count_nonzero(np.any(middle > 0, axis=0)) / float(w)
        middle_row_peak = np.max(np.count_nonzero(middle > 0, axis=1)) / float(w)

        upper_left = cropped[:max(1, int(h * 0.55)), :max(1, int(w * 0.45))]
        upper_left_ratio = cv2.countNonZero(upper_left) / max(1, cv2.countNonZero(cropped))

        # 4 的中部横杠会带来较宽的横向覆盖；1 通常是窄竖线，最多带短衬线。
        if aspect <= 0.42 and middle_columns <= 0.62 and middle_row_peak <= 0.70:
            return True

        # 对带描边/抗锯齿导致稍宽的 1 留一点余量，但限制左上区域，避免把 4 改成 1。
        return (
            aspect <= 0.50
            and density <= 0.48
            and middle_columns <= 0.54
            and middle_row_peak <= 0.62
            and upper_left_ratio <= 0.28
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
            recognized.extend(
                self._collect_number_candidates(
                    self._build_number_vote_candidates(gray, scale=current_scale),
                    offset=abs(current_scale - scale),
                    is_center=current_scale == scale,
                )
            )

        value = self._select_number_value(recognized, scale)
        if value == 4.0 and self._looks_like_single_one(gray):
            return 1.0
        return value

    def recognize_champions_row_number_roi(self, img, region=None, scale: int = 5) -> float:
        """
        champions_row 专用数字识别。
        为了比对速度，恢复为修改多路投票前的快速识别路径。
        """
        roi = self._load_color_roi(img, region=region)
        recognized = []

        # 快速路径：优先只试中心 scale 的两个高价值候选，显著减少 EasyOCR 调用次数。
        primary_results = self._collect_number_candidates(
            self._recognize_champions_row_number_candidates(
                roi, scale, include_fallback=False
            ),
            offset=0,
            is_center=True,
        )
        recognized.extend(primary_results)
        primary_texts = [item["value"] for item in primary_results]

        if len(primary_texts) >= 2 and len(set(primary_texts)) == 1:
            return primary_texts[0]

        # 只有快速路径不稳定时，才扩大到相邻 scale，并补充更慢的兜底候选。
        fallback_scales = []
        if scale > 1:
            fallback_scales.append(scale - 1)
        fallback_scales.append(scale + 1)

        for current_scale in fallback_scales:
            recognized.extend(
                self._collect_number_candidates(
                    self._recognize_champions_row_number_candidates(
                        roi, current_scale, include_fallback=True
                    ),
                    offset=abs(current_scale - scale),
                    is_center=False,
                )
            )

        return self._select_number_value(recognized, scale)
