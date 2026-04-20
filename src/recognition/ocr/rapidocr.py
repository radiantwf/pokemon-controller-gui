import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR as RapidOCREngine


class RapidOCR:
    """
    RapidOCR 封装类
    支持ROI放大与可选预处理
    """

    def __init__(self, upscale=2.0, enable_preprocess=True, **kwargs):
        """
        Args:
            upscale: ROI最大放大倍数（针对1920x1080小文字），默认2.0
            enable_preprocess: 是否启用预处理（锐化、去噪等）
            **kwargs: RapidOCR 的其他参数
        """
        self.upscale = upscale
        self.enable_preprocess = enable_preprocess

        # Default parameters
        default_kwargs = {
            # === 检测模块参数 ===
            'det_use_cuda': False,
            'det_limit_side_len': 1920,
            'det_limit_type': 'max',
            'det_thresh': 0.25,
            'det_box_thresh': 0.45,
            'det_unclip_ratio': 2.2,
            'det_db_score_mode': 'slow',
            'det_model_path': None,

            # === 识别模块参数 ===
            'rec_batch_num': 6,
            'rec_img_shape': [3, 48, 320],
            'rec_model_path': None,

            # === 全局参数 ===
            'use_angle_cls': False,
            'use_text_det': False,
            'min_height': 25,
            'width_height_ratio': 8,
            'text_score': 0.5,
            'print_verbose': False,

            # === 图像尺寸限制 ===
            'max_side_len': 2000,
            'min_side_len': 30,
        }

        # Update defaults with provided kwargs
        final_kwargs = default_kwargs.copy()
        final_kwargs.update(kwargs)

        # 初始化引擎
        self.engine = RapidOCREngine(**final_kwargs)
        relaxed_kwargs = final_kwargs.copy()
        relaxed_kwargs["text_score"] = min(float(relaxed_kwargs.get("text_score", 0.5)), 0.1)
        self.relaxed_engine = RapidOCREngine(**relaxed_kwargs)

    def _preprocess_roi(self, roi):
        """预处理ROI区域（放大、锐化、去噪）"""
        h, w = roi.shape[:2]

        # 1. 放大小图
        target_min_h = 48
        if h > 0 and target_min_h and self.upscale and self.upscale > 1:
            scale = target_min_h / float(h)
            scale = max(1.0, min(float(self.upscale), scale))
            new_h = max(1, int(round(h * scale)))
            new_w = max(1, int(round(w * scale)))
            roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        if not self.enable_preprocess:
            return roi

        if roi.ndim == 2:
            roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)

        # 2. 去噪（可选）
        if roi.shape[0] > 0 and roi.shape[1] > 0:
            try:
                roi = cv2.fastNlMeansDenoisingColored(roi, None, 7, 7, 7, 21)
            except Exception:
                pass

        # 3. 锐化
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

    def _upscale_text_roi(self, roi):
        """放大小文字区域，提升 OCR 对短文本的稳定性。"""
        if roi.ndim == 2:
            roi = cv2.cvtColor(roi, cv2.COLOR_GRAY2BGR)

        h, w = roi.shape[:2]
        target_min_h = 48
        if h > 0 and target_min_h and self.upscale and self.upscale > 1:
            scale = target_min_h / float(h)
            scale = max(1.0, min(float(self.upscale), scale))
            new_h = max(1, int(round(h * scale)))
            new_w = max(1, int(round(w * scale)))
            roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        return roi

    def _crop_text_by_mask(self, roi, text_mask, pad=None):
        """根据文本掩码裁剪文本区域，减少大面积背景对识别的干扰。"""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        text_mask = cv2.dilate(text_mask, kernel, iterations=1)

        points = cv2.findNonZero(text_mask)
        if points is not None:
            x, y, w, h = cv2.boundingRect(points)
            if pad is None:
                pad = max(4, min(12, max(w, h) // 10))
            x0 = max(0, x - pad)
            y0 = max(0, y - pad)
            x1 = min(roi.shape[1], x + w + pad)
            y1 = min(roi.shape[0], y + h + pad)
            return roi[y0:y1, x0:x1], text_mask[y0:y1, x0:x1]
        return roi, text_mask

    def _build_masked_text_image(self, roi, text_mask):
        """根据文本掩码裁剪文字区域，并转成 OCR 更容易识别的白底黑字。"""
        roi, text_mask = self._crop_text_by_mask(roi, text_mask)

        processed = np.full(text_mask.shape, 255, dtype=np.uint8)
        processed[text_mask > 0] = 0
        processed = cv2.copyMakeBorder(
            processed, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=255
        )
        return cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)

    def _build_color_text_image(self, roi, text_mask, border=16, scale=4, pad=4):
        """
        根据文本掩码裁剪彩色文本区域，并补白边后放大。
        对蓝字白描边这类 UI 文本，彩色图往往比二值图更容易被 RapidOCR 识别。
        """
        roi, _ = self._crop_text_by_mask(roi, text_mask, pad=pad)
        roi = cv2.copyMakeBorder(
            roi, border, border, border, border, cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )
        return cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    def _build_green_bg_blue_text_mask(self, roi, include_gray=True, tight=False):
        """构建绿背景蓝字白描边场景的文本掩码。"""
        roi = self._upscale_text_roi(roi)

        b, g, _ = cv2.split(roi)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        border_pixels = np.concatenate([
            roi[0, :, :],
            roi[-1, :, :],
            roi[:, 0, :],
            roi[:, -1, :],
        ], axis=0)
        bg_color = np.median(border_pixels, axis=0).astype(np.uint8)
        color_distance = np.max(
            np.abs(roi.astype(np.int16) - bg_color.astype(np.int16)),
            axis=2
        ).astype(np.uint8)
        _, distance_mask = cv2.threshold(color_distance, 24, 255, cv2.THRESH_BINARY)

        blue_score = cv2.subtract(b, g)
        _, blue_mask = cv2.threshold(blue_score, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        white_mask = cv2.inRange(hsv, (0, 0, 145), (179, 110, 255))

        if tight:
            text_mask = cv2.bitwise_or(blue_mask, white_mask)
        else:
            text_mask = cv2.bitwise_or(distance_mask, blue_mask)
            text_mask = cv2.bitwise_or(text_mask, white_mask)

        if include_gray:
            gray_inv = cv2.bitwise_not(gray)
            _, gray_mask = cv2.threshold(gray_inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text_mask = cv2.bitwise_or(text_mask, gray_mask)
        return roi, text_mask

    def _build_light_bg_blue_text_mask(self, roi, include_gray=True):
        """构建浅色背景蓝字白描边场景的文本掩码。"""
        roi = self._upscale_text_roi(roi)

        b, g, r = cv2.split(roi)
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
        _, distance_mask = cv2.threshold(color_distance, 16, 255, cv2.THRESH_BINARY)

        blue_score = np.clip(
            b.astype(np.int16) - np.maximum(g, r).astype(np.int16),
            0,
            255
        ).astype(np.uint8)
        _, blue_mask = cv2.threshold(blue_score, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        dark_mask = cv2.inRange(gray, 0, max(0, bg_gray - 12))

        text_mask = cv2.bitwise_or(distance_mask, blue_mask)
        text_mask = cv2.bitwise_or(text_mask, dark_mask)
        if include_gray:
            gray_inv = cv2.bitwise_not(gray)
            _, gray_mask = cv2.threshold(gray_inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text_mask = cv2.bitwise_or(text_mask, gray_mask)
        return roi, text_mask

    def _preprocess_green_bg_blue_text_roi(self, roi):
        """
        针对绿色背景、蓝色文字、白色描边的文字区域做专用预处理。
        该分支尽量保持绿底识别的稳定性。
        """
        roi, text_mask = self._build_green_bg_blue_text_mask(roi)
        return self._build_masked_text_image(roi, text_mask)

    def _preprocess_light_bg_blue_text_roi(self, roi):
        """
        针对白色或浅色背景、蓝色文字、白色描边的文字区域做专用预处理。
        避免绿底规则对白底样本造成误伤。
        """
        roi, text_mask = self._build_light_bg_blue_text_mask(roi)
        return self._build_masked_text_image(roi, text_mask)

    def batch_recognize_regions(self, img, regions, return_details=False):
        """
        批量识别同一张图中的多个ROI区域

        Args:
            img: 输入图像（numpy array 或 路径字符串）
            regions: 字典格式 {'名称': (x, y, w, h), ...} 或 列表格式 [(x, y, w, h), ...]
            return_details: 是否返回详细信息（包括坐标、置信度等）

        Returns:
            字典格式: {'名称': {'text': '结果', 'score': 0.95, 'box': (x,y,w,h)}, ...}
            或列表格式: [{'text': '结果', 'score': 0.95, 'box': (x,y,w,h)}, ...]
        """
        # 读取图像
        if isinstance(img, str):
            img = cv2.imread(img)
            if img is None:
                raise ValueError(f"无法读取图像: {img}")

        # 处理regions格式
        is_dict = isinstance(regions, dict)
        if is_dict:
            region_items = list(regions.items())
        else:
            region_items = [(f"roi_{i}", box) for i, box in enumerate(regions)]

        results = {} if is_dict else []

        # 批量处理
        for name, box in region_items:
            x, y, w, h = box

            # 裁剪ROI
            try:
                roi = img[y:y+h, x:x+w].copy()
            except Exception as e:
                result_item = {
                    'text': None,
                    'score': 0.0,
                    'error': f'裁剪失败: {str(e)}'
                }
                if return_details:
                    result_item['box'] = (x, y, w, h)

                if is_dict:
                    results[name] = result_item
                else:
                    results.append(result_item)
                continue

            # 预处理
            roi_processed = self._preprocess_roi(roi)

            # 识别
            try:
                result, elapse = self.engine(roi_processed)

                if result and len(result) > 0:
                    text = result[0][1]
                    result_item = {
                        'text': text,
                        'score': float(result[0][2])
                    }

                    if return_details:
                        result_item['box'] = (x, y, w, h)
                        result_item['elapse'] = elapse
                else:
                    result_item = {
                        'text': None,
                        'score': 0.0
                    }
                    if return_details:
                        result_item['box'] = (x, y, w, h)

            except Exception as e:
                result_item = {
                    'text': None,
                    'score': 0.0,
                    'error': f'识别失败: {str(e)}'
                }
                if return_details:
                    result_item['box'] = (x, y, w, h)

            # 添加到结果
            if is_dict:
                results[name] = result_item
            else:
                results.append(result_item)

        return results

    def recognize_single_roi(self, img, box, preprocess=True, return_raw=False):
        """
        识别单个ROI区域

        Args:
            img: 输入图像
            box: (x, y, w, h) 坐标
            preprocess: 是否预处理
            return_raw: 是否返回原始识别结果（用于调试）

        Returns:
            (text, score) 元组 或 (text, score, raw_text) 元组
        """
        if isinstance(img, str):
            img = cv2.imread(img)

        x, y, w, h = box
        roi = img[y:y+h, x:x+w].copy()

        if preprocess:
            roi = self._preprocess_roi(roi)

        result, _ = self.engine(roi)

        if result and len(result) > 0:
            raw_text = result[0][1]
            text = raw_text
            score = float(result[0][2])

            if return_raw:
                return text, score, raw_text
            return text, score

        if return_raw:
            return None, 0.0, None
        return None, 0.0

    def recognize_champions_row_text_roi(self, img, box, return_raw=False):
        """
        识别Champions选择行的文本区域。

        Args:
            img: 输入图像
            box: (x, y, w, h) 坐标
            return_raw: 是否返回原始识别结果（用于调试）

        Returns:
            (text, score) 元组 或 (text, score, raw_text) 元组
        """
        if isinstance(img, str):
            img = cv2.imread(img)

        x, y, w, h = box
        roi = img[y:y+h, x:x+w].copy()

        green_roi, green_color_mask = self._build_green_bg_blue_text_mask(
            roi.copy(), include_gray=False, tight=True
        )
        light_roi, light_color_mask = self._build_light_bg_blue_text_mask(roi.copy(), include_gray=False)

        candidates = [
            self._build_color_text_image(green_roi, green_color_mask),
            self._build_color_text_image(light_roi, light_color_mask),
            self._preprocess_green_bg_blue_text_roi(roi),
            self._preprocess_light_bg_blue_text_roi(roi),
            self._preprocess_roi(roi.copy()),
            roi,
        ]

        best_text = None
        best_score = 0.0
        best_raw_text = None

        for candidate in candidates:
            result, _ = self.engine(candidate)
            if not result or len(result) == 0:
                continue
            raw_text = result[0][1]
            text = raw_text.strip()
            score = float(result[0][2])
            if score > best_score:
                best_text = text
                best_raw_text = raw_text
                best_score = score

        if best_text is not None:
            if return_raw:
                return best_text, best_score, best_raw_text
            return best_text, best_score

        # 严格阈值下全部失败时，再启用宽松兜底，避免影响正常样本速度和精度。
        relaxed_candidates = [
            self._build_color_text_image(green_roi, green_color_mask, border=12, scale=4, pad=1),
            self._build_color_text_image(green_roi, green_color_mask, border=12, scale=4, pad=2),
            self._build_color_text_image(green_roi, green_color_mask),
            self._build_color_text_image(light_roi, light_color_mask),
            self._preprocess_green_bg_blue_text_roi(roi),
            self._preprocess_light_bg_blue_text_roi(roi),
            self._preprocess_roi(roi.copy()),
            roi,
        ]

        for candidate in relaxed_candidates:
            result, _ = self.relaxed_engine(candidate)
            if not result or len(result) == 0:
                continue
            raw_text = result[0][1]
            score = float(result[0][2])
            text = raw_text.strip()
            if len(text.strip()) < 2:
                continue
            if score > best_score:
                best_text = text.strip()
                best_raw_text = raw_text
                best_score = score

        if best_text is not None:
            if return_raw:
                return best_text, best_score, best_raw_text
            return best_text, best_score

        if return_raw:
            return None, 0.0, None
        return None, 0.0

    def __call__(self, img, **kwargs):
        """识别图像（兼容原有接口）"""
        if isinstance(img, list):
            results = []
            for i in img:
                result, elapse = self.engine(i, **kwargs)
                results.append((result, elapse))
            return results
        else:
            result, elapse = self.engine(img, **kwargs)
            return result, elapse
