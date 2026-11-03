import numpy as np
import easyocr

class OCREngine:
    def __init__(self, languages=None, gpu=False):
        self.languages = languages or ["vi", "en"]
        self.gpu = gpu
        self.reader = None

    def load(self):
        if self.reader is None:
            self.reader = easyocr.Reader(
                self.languages, gpu=self.gpu, verbose=False
            )
        return self.reader

    def recognize(self, image, detail=True):
        if image is None:
            raise ValueError("Không có ảnh để nhận diện.")
        reader = self.load()
        arr = np.asarray(image)
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        return reader.readtext(
            arr, detail=1 if detail else 0,
            paragraph=False, decoder="greedy"
        )

    @staticmethod
    def format_results(results):
        lines = []
        confidences = []
        for item in results:
            if len(item) >= 3:
                lines.append(str(item[1]))
                confidences.append(float(item[2]))
        text = "\n".join(lines)
        average = sum(confidences) / len(confidences) if confidences else 0.0
        return text, average, confidences
