import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR


class RapidOCRWithStrictChars:
    """
    RapidOCR 封装类
    支持ROI放大与可选预处理
    """

    def __init__(self, upscale=2.5, enable_preprocess=True, **kwargs):
        """
        Args:
            upscale: ROI放大倍数（针对960x540小文字），默认2.5
            enable_preprocess: 是否启用预处理（锐化、去噪等）
            **kwargs: RapidOCR 的其他参数
        """
        self.upscale = upscale
        self.enable_preprocess = enable_preprocess

        # Default parameters
        default_kwargs = {
            # === 检测模块参数 ===
            'det_use_cuda': False,
            'det_limit_side_len': 960,
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
        self.engine = RapidOCR(**final_kwargs)

    def _preprocess_roi(self, roi):
        """预处理ROI区域（放大、锐化、去噪）"""
        h, w = roi.shape[:2]

        # 1. 放大小图
        if min(h, w) < 32 and self.upscale and self.upscale != 1:
            new_h = max(1, int(round(h * self.upscale)))
            new_w = max(1, int(round(w * self.upscale)))
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
