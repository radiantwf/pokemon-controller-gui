import re
import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

class OcrEngine:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OcrEngine, cls).__new__(cls)
            # Initialize RapidOCR
            # det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False because we want broad compatibility and onnxruntime default
            # We can expose these as parameters if needed, but for now default is fine.
            cls._instance.rapid_ocr = RapidOCR()
        return cls._instance

    def image_to_string(self, image, lang='chi_sim', config=''):
        """
        Mimics ocr.image_to_string using RapidOCR.
        
        :param image: numpy array (image) or path
        :param lang: language code (ignored as RapidOCR detects text)
        :param config: tesseract config string, we look for whitelist here.
        :return: Recognized text string
        """
        # Ensure image is in a format RapidOCR accepts. 
        # It accepts str(path), np.ndarray, bytes.
        # If image is a PIL Image, we might need to convert it, but based on codebase it's usually cv2 numpy array.
        
        # RapidOCR returns list of [box, text, score] or None
        # use_det=True, use_cls=False, use_rec=True is default. 
        # For single line/word recognition which is common in these scripts (psm 7), 
        # we might want to ensure we don't do too much layout analysis if not needed, 
        # but RapidOCR is generally robust.
        
        # Note: RapidOCR might return multiple text blocks. ocr.image_to_string joins them? 
        # Usually image_to_string returns a single string including newlines.
        
        try:
            result, _ = self.rapid_ocr(image)
        except Exception as e:
            # Fallback or error logging
            print(f"OCR Error: {e}")
            return ""
        
        if not result:
            return ""
        
        # Concatenate all text found
        # result is a list of [ [ [x,y],... ], "text", score ]
        # We just want the text.
        # Depending on the layout, we might want to join with newline or space.
        # Tesseract usually preserves layout. RapidOCR gives a list of blocks.
        # For now, let's join with newline to be safe for multiline, 
        # or just concatenation if it's single line.
        # Given the usage `psm 7` (Treat the image as a single text line), joining without separator or space might be closer,
        # but let's see. Most usages in this codebase seem to be short text or numbers.
        # " ".join might be safer to avoid merging words.
        
        full_text = " ".join([line[1] for line in result])
        
        # Handle whitelist if present in config
        whitelist = self._extract_whitelist(config)
        if whitelist:
            full_text = "".join([c for c in full_text if c in whitelist])
            
        return full_text

    def _extract_whitelist(self, config):
        if not config:
            return None
        # Look for tessedit_char_whitelist=...
        # It might be quoted or not.
        match = re.search(r'tessedit_char_whitelist=([^\s]+)', config)
        if match:
            return match.group(1)
        return None

# Global instance
_ocr_engine = OcrEngine()

def image_to_string(image, lang='chi_sim', config=''):
    return _ocr_engine.image_to_string(image, lang, config)
