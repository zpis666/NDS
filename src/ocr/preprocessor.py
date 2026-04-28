import numpy as np


class ImagePreprocessor:
    @staticmethod
    def preprocess(image_bytes: bytes) -> bytes:
        try:
            import cv2

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return image_bytes

            img = ImagePreprocessor._resize_if_needed(img)
            img = ImagePreprocessor._enhance_contrast(img)
            img = ImagePreprocessor._binarize(img)

            _, buffer = cv2.imencode('.png', img)
            return buffer.tobytes()

        except Exception:
            return image_bytes

    @staticmethod
    def _resize_if_needed(img, max_size=2000):
        import cv2
        h, w = img.shape[:2]

        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return img

    @staticmethod
    def _enhance_contrast(img):
        import cv2

        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        lab = cv2.merge([l, a, b])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return img

    @staticmethod
    def _binarize(img):
        import cv2

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        return img

    @staticmethod
    def preprocess_for_id_card(image_bytes: bytes) -> bytes:
        try:
            import cv2

            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return image_bytes

            img = ImagePreprocessor._resize_if_needed(img, 1000)
            img = ImagePreprocessor._enhance_contrast(img)

            _, buffer = cv2.imencode('.png', img)
            return buffer.tobytes()

        except Exception:
            return image_bytes
