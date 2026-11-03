import cv2

class Camera:
    def __init__(self, index=0):
        self.index = index
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.index)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            raise RuntimeError(
                "Không mở được camera. Hãy kiểm tra quyền camera hoặc thử camera index 1."
            )
        return True

    def read(self):
        if self.cap is None:
            raise RuntimeError("Camera chưa được mở.")
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("Không đọc được khung hình từ camera.")
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
