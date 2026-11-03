import re
from jiwer import cer, wer

def normalize_text(text):
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text

def evaluate_ocr(reference, hypothesis):
    """
    So sánh văn bản OCR với văn bản chuẩn.
    CER/WER càng thấp càng tốt; Accuracy ước lượng = max(0, 1 - error rate).
    """
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)

    if not ref:
        raise ValueError("Văn bản chuẩn không được để trống.")

    character_error = cer(ref, hyp)
    word_error = wer(ref, hyp)

    return {
        "cer": character_error,
        "wer": word_error,
        "character_accuracy": max(0.0, 1.0 - character_error),
        "word_accuracy": max(0.0, 1.0 - word_error),
    }
