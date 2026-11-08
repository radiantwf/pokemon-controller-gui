import cv2
import numpy as np
from difflib import SequenceMatcher
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR as RapidOCREngine
from recognition.scripts.games.pokemon.champions.teamid.locale import Dict, DictTag
from recognition.scripts.games.pokemon.champions.teamid.chinese import fix_error_text


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

    @staticmethod
    def _ensure_bgr(img):
        if img.ndim == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img

    @staticmethod
    def _normalize_text(text):
        return " ".join(str(text or "").split()).strip()

    @staticmethod
    def _add_border(img, border=8):
        value = 255 if img.ndim == 2 else (255, 255, 255)
        return cv2.copyMakeBorder(
            img, border, border, border, border, cv2.BORDER_CONSTANT, value=value
        )

    @staticmethod
    def _is_name_field(field_name):
        return str(field_name or "").lower() in {"name", "pokemon", "roi_0", "0"}

    @staticmethod
    def _field_to_dict_tag(field_name):
        field = str(field_name or "").lower()
        if field in {"name", "pokemon", "roi_0", "0"}:
            return DictTag.POKEMON
        if field in {"ability", "roi_1", "1"}:
            return DictTag.ABILITY
        if field in {"item", "roi_2", "2"}:
            return DictTag.ITEM
        if field.startswith("move") or field in {"roi_3", "roi_4", "roi_5", "roi_6", "3", "4", "5", "6"}:
            return DictTag.MOVE
        return None

    @classmethod
    def _correct_text_by_dict(cls, text, field_name):
        tag = cls._field_to_dict_tag(field_name)
        normalized = Dict.correct_zh_text(tag, text)
        if not tag or not normalized:
            return text

        terms = Dict.zh_terms(tag)
        if normalized in terms or Dict.is_ambiguous_form_suffix_prefix(tag, normalized):
            return normalized

        best_term = None
        best_score = 0.0
        for term in terms:
            if not term:
                continue
            ratio = SequenceMatcher(None, normalized, term).ratio()
            length_delta = abs(len(term) - len(normalized))
            substring_bonus = 0.18 if normalized in term and length_delta <= 1 else 0.0
            prefix_bonus = 0.08 if term.startswith(normalized) or normalized.startswith(term) else 0.0
            score = ratio + substring_bonus + prefix_bonus - length_delta * 0.03
            if score > best_score:
                best_score = score
                best_term = term

        if best_term is None:
            return normalized

        # 短词经常因背景干扰漏掉一个字，例如“仆刀”识别成“刀”。
        if len(normalized) <= 2:
            threshold = 0.76
        elif len(normalized) == len(best_term):
            threshold = 0.64
        else:
            threshold = 0.72

        if best_score >= threshold:
            return best_term
        return normalized

    @classmethod
    def _should_prefer_text(cls, text, score, best, field_name=None):
        tag = cls._field_to_dict_tag(field_name)
        text_in_dict = Dict.is_exact_zh_text(tag, text)
        best_text = str(best["text"] or "")
        best_in_dict = Dict.is_exact_zh_text(tag, best_text)
        best_score = float(best["score"] or 0.0)

        if text_in_dict and not best_in_dict:
            return True
        if best_in_dict and not text_in_dict:
            return False

        rank = score + min(len(text), 8) * 0.03
        best_rank = best_score + min(len(best_text), 8) * 0.03
        if rank > best_rank:
            return True

        if tag != DictTag.MOVE or not best_text:
            return False

        normalized = Dict.normalize_zh_text(text)
        normalized_best = Dict.normalize_zh_text(best_text)
        if (
            len(normalized) > len(normalized_best)
            and normalized.startswith(normalized_best)
            and score >= best_score - 0.12
        ):
            return True

        return False

    @staticmethod
    def _flatten_horizontal_stripes(gray):
        width = gray.shape[1]
        kernel_width = max(17, (width // 3) | 1)
        background = cv2.GaussianBlur(gray, (kernel_width, 1), 0)
        flattened = cv2.addWeighted(gray, 1.7, background, -0.7, 128)
        return cv2.normalize(flattened, None, 0, 255, cv2.NORM_MINMAX)

    @staticmethod
    def _build_text_mask(resized):
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        border_pixels = np.concatenate([
            resized[0, :, :],
            resized[-1, :, :],
            resized[:, 0, :],
            resized[:, -1, :],
        ], axis=0)
        bg_gray = int(np.median(cv2.cvtColor(border_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY)))
        bright_mask = cv2.inRange(gray, min(255, max(130, bg_gray + 16)), 255)
        white_mask = cv2.inRange(hsv, (0, 0, 135), (179, 135, 255))

        flattened = RapidOCR._flatten_horizontal_stripes(gray)
        _, flat_mask = cv2.threshold(flattened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if np.mean(flat_mask) > 127:
            flat_mask = cv2.bitwise_not(flat_mask)

        text_mask = cv2.bitwise_or(bright_mask, white_mask)
        text_mask = cv2.bitwise_or(text_mask, flat_mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        return text_mask

    def _preprocess_basic_text_roi(self, roi, field_name=None):
        """
        针对 outputs/poke{i} 中已裁剪的中文 basic 小图构建候选图。
        这些图通常是白字/浅色描边叠在紫色横纹背景上，单一路径容易被横纹干扰。
        """
        roi = self._ensure_bgr(roi)
        h, w = roi.shape[:2]
        if h <= 0 or w <= 0:
            return []

        target_h = 72 if h < 40 else 64
        scale = max(1.0, min(3.0, target_h / float(h)))
        resized = cv2.resize(
            roi,
            (max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
            interpolation=cv2.INTER_CUBIC,
        )

        candidates = [self._add_border(self._preprocess_roi(resized), border=6)]

        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 4))
        enhanced_gray = clahe.apply(gray)
        enhanced_bgr = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
        blurred = cv2.GaussianBlur(enhanced_bgr, (0, 0), sigmaX=0.8)
        enhanced_bgr = cv2.addWeighted(enhanced_bgr, 1.5, blurred, -0.5, 0)
        candidates.append(self._add_border(enhanced_bgr, border=6))

        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_inverse = cv2.bitwise_not(otsu)
        otsu_inverse = cv2.morphologyEx(
            otsu_inverse,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
            iterations=1,
        )
        candidates.append(self._add_border(otsu_inverse, border=10))

        text_mask = self._build_text_mask(resized)

        if not self._is_name_field(field_name):
            flattened = self._flatten_horizontal_stripes(gray)
            flat_bgr = cv2.cvtColor(flattened, cv2.COLOR_GRAY2BGR)
            flat_blur = cv2.GaussianBlur(flat_bgr, (0, 0), sigmaX=0.8)
            flat_bgr = cv2.addWeighted(flat_bgr, 1.6, flat_blur, -0.6, 0)
            candidates.append(self._add_border(flat_bgr, border=8))

            binary_full = np.full(text_mask.shape, 255, dtype=np.uint8)
            binary_full[text_mask > 0] = 0
            candidates.append(self._add_border(binary_full, border=10))

        points = cv2.findNonZero(text_mask)
        if points is not None:
            x, y, tw, th = cv2.boundingRect(points)
            pad = max(6, min(14, th // 3)) if not self._is_name_field(field_name) else max(4, min(12, th // 3))
            x0 = max(0, x - pad)
            y0 = max(0, y - pad)
            x1 = min(resized.shape[1], x + tw + pad)
            y1 = min(resized.shape[0], y + th + pad)
            mask_crop = text_mask[y0:y1, x0:x1]
            binary = np.full(mask_crop.shape, 255, dtype=np.uint8)
            binary[mask_crop > 0] = 0
            candidates.append(self._add_border(binary, border=10))
            candidates.append(self._add_border(resized[y0:y1, x0:x1], border=8))

        return candidates

    @classmethod
    def _pick_best_text(cls, results, field_name=None):
        best = {"text": None, "score": 0.0, "raw_text": None}
        for result in results:
            if not result:
                continue
            for item in result:
                if not isinstance(item, (list, tuple)) or len(item) < 3:
                    continue
                raw_text = str(item[1])
                text = RapidOCR._normalize_text(fix_error_text(raw_text))
                text = cls._correct_text_by_dict(text, field_name)
                if not text:
                    continue
                try:
                    score = float(item[2])
                except (TypeError, ValueError):
                    score = 0.0
                if cls._should_prefer_text(text, score, best, field_name=field_name):
                    best = {"text": text, "score": score, "raw_text": raw_text}
        return best

    def recognize_basic_roi(self, img, preprocess=True, return_raw=False, field_name=None):
        """
        识别 outputs/poke{i} 下已经裁剪好的中文 basic 字段小图。
        """
        if isinstance(img, str):
            roi = cv2.imread(img)
            if roi is None:
                raise ValueError(f"无法读取图像: {img}")
        else:
            roi = img.copy()

        candidates = self._preprocess_basic_text_roi(roi, field_name=field_name) if preprocess else [roi]
        raw_results = []
        for candidate in candidates:
            try:
                result, _ = self.engine(candidate)
                raw_results.append(result)
                if not result:
                    relaxed_result, _ = self.relaxed_engine(candidate)
                    raw_results.append(relaxed_result)
            except Exception:
                continue

        best = self._pick_best_text(raw_results, field_name=field_name)
        if return_raw:
            return best["text"], best["score"], best["raw_text"], raw_results
        return best["text"], best["score"]

    def recognize_basic_dir(self, poke_dir, fields=None):
        """
        从 outputs/poke{i} 目录识别 basic 信息，返回字段字典。
        默认识别 name/ability/item/move1..move4。
        """
        base = Path(poke_dir)
        fields = fields or ("name", "ability", "item", "move1", "move2", "move3", "move4")
        results = {}
        for field in fields:
            image_path = base / f"{field}.png"
            if not image_path.exists():
                results[field] = {"text": None, "score": 0.0, "error": "image not found"}
                continue
            try:
                text, score = self.recognize_basic_roi(str(image_path), field_name=field)
                results[field] = {"text": text, "score": score}
            except Exception as e:
                results[field] = {"text": None, "score": 0.0, "error": str(e)}
        return results

    @staticmethod
    def _fix_result(result):
        if not result:
            return result

        fixed_result = []
        for item in result:
            if isinstance(item, list) and len(item) >= 2:
                fixed_item = item.copy()
                fixed_item[1] = fix_error_text(str(fixed_item[1]))
                fixed_result.append(fixed_item)
            elif isinstance(item, tuple) and len(item) >= 2:
                fixed_item = list(item)
                fixed_item[1] = fix_error_text(str(fixed_item[1]))
                fixed_result.append(tuple(fixed_item))
            else:
                fixed_result.append(item)
        return fixed_result

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
            candidates = self._preprocess_basic_text_roi(roi, field_name=name) or [self._preprocess_roi(roi)]

            # 识别
            try:
                raw_results = []
                elapse = None
                for candidate in candidates:
                    result, current_elapse = self.engine(candidate)
                    raw_results.append(result)
                    if elapse is None:
                        elapse = current_elapse
                    if not result:
                        relaxed_result, _ = self.relaxed_engine(candidate)
                        raw_results.append(relaxed_result)

                best = self._pick_best_text(raw_results, field_name=name)
                if best["text"]:
                    result_item = {
                        'text': best["text"],
                        'score': float(best["score"])
                    }

                    if return_details:
                        result_item['box'] = (x, y, w, h)
                        result_item['elapse'] = elapse
                        result_item['raw_text'] = best["raw_text"]
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
            text = fix_error_text(str(raw_text))
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
                result = self._fix_result(result)
                results.append((result, elapse))
            return results
        else:
            result, elapse = self.engine(img, **kwargs)
            result = self._fix_result(result)
            return result, elapse
