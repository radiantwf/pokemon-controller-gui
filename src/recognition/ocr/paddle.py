import cv2
import numpy as np
from paddleocr import PaddleOCR


class PaddleOCRWrapper:
    """
    PaddleOCR 封装类。
    提供英文区域识别与数字区域识别能力，并保持与现有 OCR 调用接口兼容。
    """
    _instance = None

    def __new__(cls, lang='en', use_angle_cls=False, **kwargs):
        if cls._instance is None:
            cls._instance = super(PaddleOCRWrapper, cls).__new__(cls)
            init_kwargs = {
                'lang': lang,
                'use_textline_orientation': bool(use_angle_cls),
                'use_doc_orientation_classify': False,
                'use_doc_unwarping': False,
            }
            init_kwargs.update(kwargs)
            cls._instance.ocr = PaddleOCR(**init_kwargs)
        return cls._instance

    @staticmethod
    def _load_image(img):
        if isinstance(img, str):
            loaded = cv2.imread(img)
            if loaded is None:
                raise ValueError(f"无法读取图像: {img}")
            return loaded
        return img

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
    def _ensure_bgr(img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img

    def _preprocess_english_roi(self, roi: np.ndarray, upscale: float = 3.0,
                                enable_preprocess: bool = True) -> np.ndarray:
        """沿用 RapidOCR 的英文区域预处理思路。"""
        h, w = roi.shape[:2]

        target_min_h = 48
        if h > 0 and target_min_h and upscale and upscale > 1:
            scale = target_min_h / float(h)
            scale = max(1.0, min(float(upscale), scale))
            new_h = max(1, int(round(h * scale)))
            new_w = max(1, int(round(w * scale)))
            roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        if not enable_preprocess:
            return self._ensure_bgr(roi)

        roi = self._ensure_bgr(roi)

        if roi.shape[0] > 0 and roi.shape[1] > 0:
            try:
                roi = cv2.fastNlMeansDenoisingColored(roi, None, 7, 7, 7, 21)
            except Exception:
                pass

        try:
            lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge((l, a, b))
            roi = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        except Exception:
            pass

        blurred = cv2.GaussianBlur(roi, (0, 0), sigmaX=1.0)
        roi = cv2.addWeighted(roi, 1.6, blurred, -0.6, 0)

        return roi

    def _preprocess_number(self, gray: np.ndarray, scale: int = 5) -> np.ndarray:
        """
        数字 ROI 预处理。
        先复用英文识别的增强链路，再补充适合亮色数字的二值化结果。
        """
        english_processed = self._preprocess_english_roi(
            gray,
            upscale=float(scale),
            enable_preprocess=True
        )
        english_gray = cv2.cvtColor(english_processed, cv2.COLOR_BGR2GRAY)

        _, otsu = cv2.threshold(
            english_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        _, bright = cv2.threshold(english_gray, 180, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        otsu = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel, iterations=1)
        bright = cv2.dilate(bright, kernel, iterations=1)
        bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel, iterations=1)

        return {
            "english": english_processed,
            "otsu": self._ensure_bgr(cv2.bitwise_not(otsu)),
            "bright": self._ensure_bgr(cv2.bitwise_not(bright)),
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(str(text).split()).strip()

    @staticmethod
    def _extract_digits(text: str) -> str:
        return "".join(ch for ch in str(text) if ch.isdigit())

    @staticmethod
    def _score_number_text(text: str, score: float) -> tuple:
        digits = PaddleOCRWrapper._extract_digits(text)
        stripped = "".join(str(text).split())
        non_digits = max(0, len(stripped) - len(digits))
        final_score = (
            len(digits) * 100.0
            + float(score) * 10.0
            - non_digits * 25.0
        )
        return final_score, digits

    @staticmethod
    def _parse_result(result):
        """
        兼容 PaddleOCR 新旧版本的返回结构。
        新版 `predict()` 返回 dict 列表，旧版 `ocr()` 返回嵌套列表。
        """
        if not result:
            return "", 0.0

        first = result[0]

        if isinstance(first, dict):
            texts = [str(text).strip() for text in first.get('rec_texts', []) if str(text).strip()]
            scores = [float(score) for score in first.get('rec_scores', [])]
            text = " ".join(texts).strip()
            score = float(np.mean(scores)) if scores else 0.0
            return text, score

        if isinstance(first, list):
            lines = first
            texts = []
            scores = []
            for line in lines:
                if len(line) >= 2 and isinstance(line[1], (list, tuple)) and len(line[1]) >= 2:
                    texts.append(str(line[1][0]).strip())
                    scores.append(float(line[1][1]))
            text = " ".join([text for text in texts if text]).strip()
            score = float(np.mean(scores)) if scores else 0.0
            return text, score

        return "", 0.0

    def batch_recognize_regions(self, img, regions, return_details=False,
                                upscale: float = 3.0, enable_preprocess: bool = True):
        """
        批量识别同一张图中的多个英文 ROI 区域，接口兼容 RapidOCR。
        """
        img = self._load_image(img)

        is_dict = isinstance(regions, dict)
        if is_dict:
            region_items = list(regions.items())
        else:
            region_items = [(f"roi_{i}", box) for i, box in enumerate(regions)]

        results = {} if is_dict else []

        for name, box in region_items:
            x, y, w, h = box
            try:
                roi = img[y:y+h, x:x+w].copy()
                processed_roi = self._preprocess_english_roi(
                    roi,
                    upscale=upscale,
                    enable_preprocess=enable_preprocess
                )

                result = self.ocr.predict(processed_roi)
                text, score = self._parse_result(result)
                res_dict = {'text': self._normalize_text(text), 'score': score}

                if return_details:
                    res_dict['box'] = box
                    res_dict['raw'] = result
            except Exception as e:
                res_dict = {'text': '', 'score': 0.0, 'error': str(e)}
                if return_details:
                    res_dict['box'] = box

            if is_dict:
                results[name] = res_dict
            else:
                results.append(res_dict)

        return results

    def recognize_single_roi(self, img, box, preprocess=True, return_raw=False,
                             upscale: float = 3.0):
        """
        识别单个英文 ROI 区域，接口兼容 RapidOCR。
        """
        img = self._load_image(img)

        x, y, w, h = box
        roi = img[y:y+h, x:x+w].copy()

        if preprocess:
            roi = self._preprocess_english_roi(
                roi,
                upscale=upscale,
                enable_preprocess=True
            )

        result = self.ocr.predict(roi)

        text, score = self._parse_result(result)
        text = self._normalize_text(text)

        if return_raw:
            return text, score, result
        return text, score

    def recognize_english_roi(self, img, region=None, detail: int = 1,
                              scale: float = 2.0, preprocess: bool = True):
        """
        英文 ROI 识别接口。
        :param detail: 0 仅返回文本；1 返回包含文本与置信度的字典
        """
        if region is not None:
            text, score = self.recognize_single_roi(
                img,
                region,
                preprocess=preprocess,
                return_raw=False,
                upscale=scale
            )
        else:
            image = self._load_image(img)
            processed = self._preprocess_english_roi(
                image,
                upscale=scale,
                enable_preprocess=preprocess
            ) if preprocess else self._ensure_bgr(image)
            result = self.ocr.predict(processed)
            text, score = self._parse_result(result)
            text = self._normalize_text(text)

        if detail == 0:
            return text

        return {
            "text": text,
            "raw_text": text,
            "results": [],
            "preprocess": "rapidocr_style" if preprocess else "none",
            "confidence": score,
        }

    def recognize_number_roi(self, img, region=None, scale: int = 5) -> int:
        """
        数字 ROI 识别接口。
        复用英文识别增强链路，并对数字友好的多个候选图结果择优。
        """
        gray = self._load_gray_roi(img, region=region)
        candidates = self._preprocess_number(gray, scale=scale)

        best_score = float("-inf")
        best_digits = ""

        for processed in candidates.values():
            result = self.ocr.predict(processed)
            text, score = self._parse_result(result)
            candidate_score, digits = self._score_number_text(text, score)
            if candidate_score > best_score:
                best_score = candidate_score
                best_digits = digits

        return int(best_digits) if best_digits else 0
