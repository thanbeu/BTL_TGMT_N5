import cv2
import numpy as np

def preprocess_image(rgb_image):
    """
    Nhận ảnh RGB (numpy array), trả về ảnh xám và ảnh nhị phân đã tiền xử lý.
    """
    if rgb_image is None or rgb_image.size == 0:
        raise ValueError("Ảnh đầu vào không hợp lệ.")

    gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Tự động chọn ngưỡng thích nghi để xử lý điều kiện chiếu sáng không đều.
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 11
    )
    return gray, enhanced, binary

def deskew_image(gray):
    """Hiệu chỉnh góc nghiêng ước lượng; trả lại ảnh xám đã xoay."""
    if gray is None or gray.size == 0:
        raise ValueError("Ảnh xám không hợp lệ.")
    inverted = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(inverted > 0))
    if len(coords) < 20:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    h, w = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (w, h), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
