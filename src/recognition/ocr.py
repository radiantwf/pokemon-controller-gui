import re
import cv2
import numpy as np
import tempfile
import os
from rapidocr_onnxruntime import RapidOCR
import onnxruntime as ort


class RapidOCRWithStrictChars:
    """
    严格字符限制的 RapidOCR 封装类
    在模型解码阶段强制只输出白名单字符
    """

    def __init__(self, allowed_chars=None, upscale=2.5, enable_preprocess=True, **kwargs):
        """
        Args:
            allowed_chars: 严格限制的字符串，如 "0123456789.+-"
            upscale: ROI放大倍数（针对960x540小文字），默认2.5
            enable_preprocess: 是否启用预处理（锐化、去噪等）
            **kwargs: RapidOCR 的其他参数
        """
        if allowed_chars is None:
            raise ValueError("必须指定 allowed_chars 参数以启用严格字符限制")
        
        self.allowed_chars = allowed_chars
        self.allowed_chars_set = set(allowed_chars)  # 用于快速查找
        self.upscale = upscale
        self.enable_preprocess = enable_preprocess
        self._temp_dict_path = None
        
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
        
        # 创建严格限制的字典文件
        self._create_strict_dict()
        final_kwargs['rec_keys_path'] = self._temp_dict_path

        # 初始化引擎
        self.engine = RapidOCR(**final_kwargs)

    def _create_strict_dict(self):
        """
        创建严格限制的字典文件
        字典中只包含允许的字符，这样模型的输出索引就只对应这些字符
        """
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            suffix='.txt',
            delete=False
        )
        
        # 写入允许的字符
        for char in self.allowed_chars:
            temp_file.write(char + '\n')
        
        # 注意：必须添加特殊字符（blank用于CTC解码）
        if ' ' not in self.allowed_chars:
            temp_file.write(' \n')
        
        temp_file.close()
        self._temp_dict_path = temp_file.name

    def _filter_text_strict(self, text):
        """
        严格过滤文本，只保留白名单字符
        这是最后一道防线，确保绝对没有字典外字符
        
        Args:
            text: 原始识别文本
            
        Returns:
            过滤后的文本（只包含白名单字符）
        """
        if text is None:
            return None
        
        # 只保留白名单中的字符
        filtered = ''.join(c for c in text if c in self.allowed_chars_set)
        
        return filtered if filtered else None

    def _preprocess_roi(self, roi):
        """预处理ROI区域（放大、锐化、去噪）"""
        h, w = roi.shape[:2]
        
        # 1. 放大小图
        if h < 32:
            new_h = int(h * self.upscale)
            new_w = int(w * self.upscale)
            roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        if not self.enable_preprocess:
            return roi
        
        # 2. 去噪（可选）
        if roi.shape[0] > 0 and roi.shape[1] > 0:
            try:
                roi = cv2.fastNlMeansDenoisingColored(roi, None, 10, 10, 7, 21)
            except:
                pass
        
        # 3. 锐化
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]], dtype=np.float32)
        roi = cv2.filter2D(roi, -1, kernel)
        
        return roi

    def batch_recognize_regions(self, img, regions, return_details=False):
        """
        批量识别同一张图中的多个ROI区域（严格字符限制）
        
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
                    raw_text = result[0][1]
                    
                    # 严格过滤：只保留白名单字符
                    filtered_text = self._filter_text_strict(raw_text)
                    
                    result_item = {
                        'text': filtered_text,
                        'score': float(result[0][2]) if filtered_text else 0.0
                    }
                    
                    if return_details:
                        result_item['box'] = (x, y, w, h)
                        result_item['elapse'] = elapse
                        result_item['raw_text'] = raw_text  # 保留原始识别结果用于调试
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
        识别单个ROI区域（严格字符限制）
        
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
            filtered_text = self._filter_text_strict(raw_text)
            score = float(result[0][2]) if filtered_text else 0.0
            
            if return_raw:
                return filtered_text, score, raw_text
            return filtered_text, score
        
        if return_raw:
            return None, 0.0, None
        return None, 0.0

    def __call__(self, img, **kwargs):
        """识别图像（兼容原有接口，添加严格过滤）"""
        if isinstance(img, list):
            results = []
            for i in img:
                result, elapse = self.engine(i, **kwargs)
                if result:
                    # 过滤每个结果
                    filtered_result = []
                    for item in result:
                        bbox, text, score = item
                        filtered_text = self._filter_text_strict(text)
                        if filtered_text:  # 只保留有效结果
                            filtered_result.append([bbox, filtered_text, score])
                    results.append((filtered_result, elapse))
                else:
                    results.append((result, elapse))
            return results
        else:
            result, elapse = self.engine(img, **kwargs)
            if result:
                # 过滤结果
                filtered_result = []
                for item in result:
                    bbox, text, score = item
                    filtered_text = self._filter_text_strict(text)
                    if filtered_text:  # 只保留有效结果
                        filtered_result.append([bbox, filtered_text, score])
                return filtered_result, elapse
            return result, elapse

    def __del__(self):
        """析构时清理临时文件"""
        if self._temp_dict_path and os.path.exists(self._temp_dict_path):
            try:
                os.unlink(self._temp_dict_path)
            except:
                pass


# ========== 使用示例 ==========

if __name__ == "__main__":
    
    # 1. 初始化（严格限制：只识别数字和单位）
    ocr = RapidOCRWithStrictChars(
        allowed_chars="0123456789.+-/%K万亿",
        upscale=2.5,
        enable_preprocess=True,
    )
    
    # 2. 读取游戏截图（960x540）
    img = cv2.imread('game_960x540.png')
    
    # 3. 定义多个UI区域
    ui_regions = {
        'hp': (50, 25, 60, 15),
        'mp': (50, 45, 60, 15),
        'level': (120, 25, 40, 15),
        'damage': (250, 150, 40, 12),
        'gold': (800, 25, 80, 15),
        'exp': (150, 45, 100, 15),
    }
    
    # 4. 批量识别（启用详细模式查看过滤效果）
    results = ocr.batch_recognize_regions(img, ui_regions, return_details=True)
    
    # 5. 输出结果
    print("=" * 80)
    print("严格字符限制批量识别结果:")
    print("=" * 80)
    for name, data in results.items():
        if data['text']:
            info = f"{name:10s}: {data['text']:15s} (置信度: {data['score']:.3f})"
            # 如果有raw_text，显示过滤前后对比
            if 'raw_text' in data and data['raw_text'] != data['text']:
                info += f" [原始: {data['raw_text']}]"
            print(info)
        else:
            error_msg = data.get('error', '识别失败')
            print(f"{name:10s}: {error_msg}")
    print("=" * 80)
    
    # 6. 单个ROI识别（查看原始结果）
    text, score, raw = ocr.recognize_single_roi(
        img, (50, 25, 60, 15), return_raw=True
    )
    print(f"\n单个识别 - 血量:")
    print(f"  过滤后: {text} (置信度: {score:.3f})")
    print(f"  原始值: {raw}")
    
    # 7. 验证严格限制
    print(f"\n允许的字符集: {ocr.allowed_chars}")
    print(f"字符集大小: {len(ocr.allowed_chars)}")
