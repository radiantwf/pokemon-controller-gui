import cv2
import numpy as np
import easyocr


# 初始化一次即可复用（首次会下载模型）
_reader = easyocr.Reader(['en'], gpu=True, verbose=False)


class EasyOCR:
    def __init__(self):
        self.reader = _reader

    @staticmethod
    def _ensure_white_bg_black_text(img: np.ndarray) -> np.ndarray:
        """
        统一成白底黑字，便于 EasyOCR 识别。
        """
        if img.ndim != 2:
            raise ValueError("预处理图像必须是单通道灰度图")
        return cv2.bitwise_not(img) if float(np.mean(img)) < 127 else img

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
    def _postprocess_english_text(text: str) -> str:
        """
        对英文结果做轻量纠错：
        - 单独字符 'l' 更可能是大写 'I'
        - 位于单词开头且后续多为小写时，'l' 纠正为 'I'
        """
        if not text:
            return text

        words = []
        for word in text.split():
            if word == 'l':
                words.append('I')
                continue
            if len(word) >= 2 and word[0] == 'l' and word[1:].islower():
                words.append('I' + word[1:])
                continue
            words.append(word)

        return ' '.join(words)

    @staticmethod
    def _score_ocr_results(results) -> tuple:
        """
        给 OCR 候选结果打分，综合考虑：
        - 平均置信度
        - 文本长度
        - 有效英文/数字字符数量
        - 垃圾字符惩罚
        """
        if not results:
            return -1e9, "", "", 0.0

        texts = []
        confs = []
        for item in results:
            if len(item) >= 3:
                texts.append(str(item[1]))
                confs.append(float(item[2]))

        raw_text = " ".join(texts).strip()
        text = EasyOCR._postprocess_english_text(raw_text)

        valid_chars = sum(ch.isalnum() or ch in " -_/.:,%()[]'" for ch in text)
        bad_chars = max(0, len(text) - valid_chars)
        alpha_num = sum(ch.isalnum() for ch in text)

        avg_conf = float(np.mean(confs)) if confs else 0.0
        score = (
            avg_conf * 100.0
            + len(text) * 0.8
            + alpha_num * 0.2
            - bad_chars * 1.5
        )

        return score, raw_text, text, avg_conf

    def _preprocess_english_candidates(self, gray: np.ndarray, scale: int = 4):
        """
        英文识别预处理：参考数字识别的“阈值提白”思路，
        同时保留对通用英文更稳的增强方案，生成多个候选图像后择优。
        返回值为 [(name, image), ...]
        """
        h, w = gray.shape[:2]
        scaled = cv2.resize(
            gray,
            (max(1, w * scale), max(1, h * scale)),
            interpolation=cv2.INTER_CUBIC
        )

        # 1) 对比度增强
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(scaled)

        # 2) 去噪，同时保留边缘
        denoised = cv2.bilateralFilter(enhanced, 5, 30, 30)

        # 3) 轻微锐化
        sharpen_kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ], dtype=np.float32)
        sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)

        # 4) 候选一：Otsu 二值化
        _, otsu = cv2.threshold(
            sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # 5) 候选二：自适应二值化
        adaptive = cv2.adaptiveThreshold(
            sharpened,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            9
        )

        # 6) 候选三：仿数字识别的亮字阈值分离
        #    适合“英文偏亮、背景偏暗或偏花”的情况
        _, bright = cv2.threshold(sharpened, 185, 255, cv2.THRESH_BINARY)

        # 7) 形态学增强，让字母笔画更完整
        kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))

        otsu = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        adaptive = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        bright = cv2.dilate(bright, kernel_close, iterations=1)
        bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel_open, iterations=1)

        # 8) 全部统一成白底黑字
        candidates = [
            ("gray", self._ensure_white_bg_black_text(sharpened)),
            ("otsu", self._ensure_white_bg_black_text(otsu)),
            ("adaptive", self._ensure_white_bg_black_text(adaptive)),
            ("bright", self._ensure_white_bg_black_text(bright)),
        ]

        return candidates

    def recognize_english_roi(self, img, region=None, scale: int = 4, detail: int = 1):
        """
        识别英文 ROI。
        改进点：
        - 借鉴数字识别里的“亮字阈值分离”思路
        - 同时生成 gray / otsu / adaptive / bright 多个候选图
        - 对多次 OCR 结果按置信度和文本质量择优

        :param img: 已裁剪小图(ndarray BGR/Gray) 或图像路径(str)
        :param region: (x, y, w, h)，传入则先裁剪；已裁剪传 None
        :param scale: 放大倍数，默认 4
        :param detail: 1 返回详细结果，0 只返回文本
        :return:
            detail=0 -> str
            detail=1 -> {
                "text": ...,
                "raw_text": ...,
                "results": ...,
                "preprocess": ...,
                "confidence": ...
            }
        """
        gray = self._load_gray_roi(img, region=region)
        candidates = self._preprocess_english_candidates(gray, scale=scale)

        allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_/.:,%()[]' "

        best = {
            "score": -1e9,
            "text": "",
            "raw_text": "",
            "results": [],
            "preprocess": None,
            "confidence": 0.0,
        }

        for name, processed in candidates:
            results = self.reader.readtext(
                processed,
                detail=1,
                paragraph=False,
                allowlist=allowlist
            )

            score, raw_text, text, avg_conf = self._score_ocr_results(results)

            if score > best["score"]:
                best.update({
                    "score": score,
                    "text": text,
                    "raw_text": raw_text,
                    "results": results,
                    "preprocess": name,
                    "confidence": avg_conf,
                })

        if detail == 0:
            return best["text"]

        return {
            "text": best["text"],
            "raw_text": best["raw_text"],
            "results": best["results"],
            "preprocess": best["preprocess"],
            "confidence": best["confidence"],
        }

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

    def recognize_number_roi(self, img, region=None, scale: int = 5) -> int:
        """
        识别数字 ROI。

        :param img: 已裁剪小图(ndarray BGR/Gray) 或图像路径(str)
        :param region: (x, y, w, h)，传入则先裁剪；已裁剪传 None
        :param scale: 放大倍数，默认 5
        """
        gray = self._load_gray_roi(img, region=region)
        processed = self._preprocess_number(gray, scale=scale)

        results = self.reader.readtext(
            processed,
            allowlist='0123456789',
            detail=0,
            paragraph=False,
        )

        text = "".join(results).strip()
        return int(text) if text.isdigit() else 0
