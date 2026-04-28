from typing import List, Tuple


class OcrEngine:
    def __init__(self):
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
            self._engine = RapidOCR()
        except ImportError:
            self._engine = None

    def recognize(self, image_bytes: bytes) -> List[Tuple[str, float]]:
        if self._engine is None:
            return []

        try:
            import numpy as np
            import cv2

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return []

            result, elapse = self._engine(img)

            if result is None:
                return []

            ocr_results = []
            for line in result:
                text = line[1]
                confidence = line[2]
                ocr_results.append((text, confidence))

            return ocr_results

        except Exception:
            return []

    def recognize_from_base64(self, base64_str: str) -> List[Tuple[str, float]]:
        try:
            import base64
            image_bytes = base64.b64decode(base64_str)
            return self.recognize(image_bytes)
        except Exception:
            return []

    def is_available(self) -> bool:
        return self._engine is not None
