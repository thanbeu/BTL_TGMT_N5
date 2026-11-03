import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import cv2
import threading
import queue
import time
from pathlib import Path

from core.image_processing import preprocess_image, deskew_image
from core.ocr_engine import OCREngine
from core.accuracy import evaluate_ocr
from core.camera import Camera
from exports.report_export import export_txt, export_docx, export_pdf

BG = "#F1F5F9"
NAVY = "#142B4A"
BLUE = "#2563EB"
GREEN = "#15803D"

class OCRWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR VISION | Computer Vision")
        self.root.geometry("1320x850")
        self.root.minsize(1100, 720)
        self.root.configure(bg=BG)

        self.engine = OCREngine(["vi", "en"], gpu=False)
        self.image_rgb = None
        self.processed_rgb = None
        self.display_rgb = None
        self.results = []
        self.extracted_text = ""
        self.average_confidence = 0.0
        self.processing_time = 0.0
        self.source_name = "Chưa chọn"
        self.evaluation = None
        self.camera = None
        self.camera_running = False
        self.camera_frame = None
        self.q = queue.Queue()

        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        header = tk.Frame(self.root, bg=NAVY, height=86)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="OCR VISION", bg=NAVY, fg="white",
                 font=("Segoe UI", 23, "bold")).pack(anchor="w", padx=24, pady=(12, 0))
        tk.Label(header, text="OPTICAL CHARACTER RECOGNITION • COMPUTER VISION",
                 bg=NAVY, fg="#BFDBFE", font=("Segoe UI", 9)).pack(anchor="w", padx=27)

        toolbar = tk.Frame(self.root, bg="white")
        toolbar.pack(fill="x", padx=16, pady=12)
        self.button(toolbar, "Chọn ảnh", self.choose_image).pack(side="left", padx=5, pady=9)
        self.button(toolbar, "Tiền xử lý", self.process_image, "#475569").pack(side="left", padx=5)
        self.button(toolbar, "Nhận diện OCR", self.run_ocr, BLUE).pack(side="left", padx=5)
        self.button(toolbar, "Camera", self.toggle_camera, "#7C3AED").pack(side="left", padx=5)
        self.button(toolbar, "Chụp khung hình", self.capture_camera, "#0F766E").pack(side="left", padx=5)
        self.button(toolbar, "Xuất báo cáo", self.export_report, GREEN).pack(side="left", padx=5)
        self.button(toolbar, "Xóa", self.clear_all, "#64748B").pack(side="left", padx=5)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        left = tk.Frame(main, bg="white")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(main, bg="white", width=480)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))
        right.pack_propagate(False)

        tk.Label(left, text="ẢNH GỐC / ẢNH ĐÃ XỬ LÝ", bg="white", fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=10)

        self.tabs = ttk.Notebook(left)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.original_panel = tk.Label(self.tabs, text="Chọn ảnh hoặc mở camera",
                                       bg="#EAF0F8", fg="#64748B")
        self.processed_panel = tk.Label(self.tabs, text="Ảnh sau tiền xử lý sẽ hiển thị ở đây",
                                        bg="#EAF0F8", fg="#64748B")
        self.tabs.add(self.original_panel, text="Ảnh gốc")
        self.tabs.add(self.processed_panel, text="Ảnh tiền xử lý")

        tk.Label(right, text="KẾT QUẢ NHẬN DIỆN", bg="white", fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=10)
        self.output = tk.Text(right, wrap="word", font=("Segoe UI", 11),
                              bg="#F8FAFC", fg="#172554", relief="flat",
                              padx=12, pady=12)
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.output.insert("1.0", "Văn bản OCR sẽ hiển thị tại đây.")
        self.output.config(state="disabled")

        eval_frame = tk.LabelFrame(right, text="Đánh giá độ chính xác",
                                   bg="white", fg=NAVY, padx=8, pady=8)
        eval_frame.pack(fill="x", padx=12, pady=5)
        tk.Label(eval_frame, text="Nhập văn bản chuẩn để so sánh:",
                 bg="white").pack(anchor="w")
        self.reference = tk.Text(eval_frame, height=3, font=("Segoe UI", 10))
        self.reference.pack(fill="x", pady=4)
        self.button(eval_frame, "Tính CER / WER", self.evaluate).pack(anchor="e")
        self.eval_label = tk.Label(eval_frame, text="CER: -- | WER: --",
                                   bg="white", fg=GREEN, font=("Segoe UI", 10, "bold"))
        self.eval_label.pack(anchor="w", pady=(5, 0))

        stats = tk.Frame(self.root, bg="white")
        stats.pack(fill="x", padx=16, pady=(0, 10))
        self.stat_labels = {}
        for title in ["Ký tự", "Từ", "Vùng chữ", "Thời gian", "Tin cậy TB"]:
            cell = tk.Frame(stats, bg="white")
            cell.pack(side="left", fill="x", expand=True, pady=9)
            tk.Label(cell, text=title.upper(), bg="white", fg="#64748B",
                     font=("Segoe UI", 8, "bold")).pack()
            value = tk.Label(cell, text="0", bg="white", fg=BLUE,
                             font=("Segoe UI", 14, "bold"))
            value.pack()
            self.stat_labels[title] = value

        self.status = tk.Label(self.root, text="Sẵn sàng", anchor="w",
                               bg=NAVY, fg="white", padx=12, pady=5)
        self.status.pack(fill="x", side="bottom")

    def button(self, parent, text, command, color=BLUE):
        return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                         activebackground=color, activeforeground="white",
                         relief="flat", padx=12, pady=8,
                         font=("Segoe UI", 9, "bold"), cursor="hand2")

    def show_image(self, panel, rgb):
        if rgb is None:
            return
        image = Image.fromarray(rgb)
        image.thumbnail((650, 570), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        panel.configure(image=photo, text="")
        panel.image = photo

    def choose_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp *.webp")]
        )
        if not path:
            return
        try:
            image = Image.open(path).convert("RGB")
            self.image_rgb = np.array(image)
            self.display_rgb = self.image_rgb.copy()
            self.source_name = Path(path).name
            self.processed_rgb = None
            self.results = []
            self.extracted_text = ""
            self.show_image(self.original_panel, self.image_rgb)
            self.output_text("Đã tải ảnh. Nhấn Tiền xử lý hoặc Nhận diện OCR.")
            self.status.config(text=f"Đã tải: {self.source_name}")
            self.reset_stats()
        except Exception as exc:
            messagebox.showerror("Lỗi ảnh", str(exc))

    def process_image(self):
        if self.image_rgb is None:
            messagebox.showwarning("Thiếu ảnh", "Hãy chọn ảnh trước.")
            return
        try:
            gray, enhanced, binary = preprocess_image(self.image_rgb)
            # OCR chạy trên ảnh nhị phân RGB; ảnh tăng tương phản cũng được giữ để tham khảo.
            self.processed_rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
            self.show_image(self.processed_panel, self.processed_rgb)
            self.tabs.select(1)
            self.status.config(text="Đã tiền xử lý: grayscale, Gaussian Blur, CLAHE, Adaptive Threshold.")
        except Exception as exc:
            messagebox.showerror("Lỗi xử lý ảnh", str(exc))

    def run_ocr(self):
        if self.image_rgb is None:
            messagebox.showwarning("Thiếu ảnh", "Hãy chọn ảnh hoặc chụp từ camera.")
            return
        source = self.processed_rgb if self.processed_rgb is not None else self.image_rgb.copy()
        self.status.config(text="Đang nhận diện OCR. Lần đầu có thể cần tải mô hình...")
        threading.Thread(target=self.ocr_worker, args=(source,), daemon=True).start()
        self.root.after(100, self.poll_queue)

    def ocr_worker(self, image):
        try:
            start = time.time()
            results = self.engine.recognize(image)
            elapsed = time.time() - start
            self.q.put(("ok", results, elapsed))
        except Exception as exc:
            self.q.put(("error", str(exc)))

    def poll_queue(self):
        try:
            item = self.q.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll_queue)
            return
        if item[0] == "error":
            self.status.config(text="Nhận diện thất bại.")
            messagebox.showerror("Lỗi OCR", item[1])
            return
        _, results, elapsed = item
        self.results = results
        self.processing_time = elapsed
        text, confidence, _ = self.engine.format_results(results)
        self.extracted_text = text
        self.average_confidence = confidence
        self.output_text(text if text else "Không phát hiện được văn bản.")
        self.update_stats()
        self.draw_boxes()
        self.status.config(text=f"Hoàn tất OCR trong {elapsed:.2f} giây.")

    def draw_boxes(self):
        if self.image_rgb is None:
            return
        image = Image.fromarray(self.image_rgb.copy())
        draw = ImageDraw.Draw(image)
        for item in self.results:
            pts = [(int(p[0]), int(p[1])) for p in item[0]]
            draw.polygon(pts, outline=(22, 163, 74), width=3)
        self.show_image(self.original_panel, np.array(image))

    def output_text(self, text):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.config(state="disabled")

    def update_stats(self):
        words = self.extracted_text.split()
        values = {
            "Ký tự": len(self.extracted_text),
            "Từ": len(words),
            "Vùng chữ": len(self.results),
            "Thời gian": f"{self.processing_time:.2f}s",
            "Tin cậy TB": f"{self.average_confidence*100:.1f}%"
        }
        for key, value in values.items():
            self.stat_labels[key].config(text=str(value))

    def reset_stats(self):
        for label in self.stat_labels.values():
            label.config(text="0")
        self.eval_label.config(text="CER: -- | WER: --")
        self.evaluation = None

    def evaluate(self):
        reference = self.reference.get("1.0", "end").strip()
        if not self.extracted_text:
            messagebox.showwarning("Thiếu kết quả", "Hãy chạy OCR trước.")
            return
        try:
            self.evaluation = evaluate_ocr(reference, self.extracted_text)
            m = self.evaluation
            self.eval_label.config(
                text=f"CER: {m['cer']:.2%} | WER: {m['wer']:.2%} | "
                     f"Char Acc: {m['character_accuracy']:.2%}"
            )
            self.status.config(text="Đã đánh giá kết quả với văn bản chuẩn.")
        except Exception as exc:
            messagebox.showerror("Không thể đánh giá", str(exc))

    def toggle_camera(self):
        if self.camera_running:
            self.stop_camera()
            return
        try:
            self.camera = Camera(1)
            self.camera.open()
            self.camera_running = True
            self.status.config(text="Camera đang hoạt động. Nhấn Chụp khung hình để lấy ảnh.")
            self.camera_loop()
        except Exception as exc:
            messagebox.showerror("Lỗi camera", str(exc))

    def camera_loop(self):
        if not self.camera_running:
            return
        try:
            frame = self.camera.read()
            self.camera_frame = frame
            self.show_image(self.original_panel, frame)
            self.root.after(30, self.camera_loop)
        except Exception as exc:
            self.stop_camera()
            messagebox.showerror("Camera", str(exc))

    def capture_camera(self):
        if not self.camera_running or self.camera_frame is None:
            messagebox.showwarning("Camera", "Hãy bật camera trước.")
            return
        self.image_rgb = self.camera_frame.copy()
        self.display_rgb = self.image_rgb.copy()
        self.processed_rgb = None
        self.source_name = "camera_capture"
        self.show_image(self.original_panel, self.image_rgb)
        self.status.config(text="Đã chụp ảnh từ camera. Có thể tiền xử lý và nhận diện.")
        self.stop_camera()

    def stop_camera(self):
        self.camera_running = False
        if self.camera:
            self.camera.close()
            self.camera = None
        self.status.config(text="Camera đã dừng.")

    def export_report(self):
        if not self.extracted_text:
            messagebox.showwarning("Chưa có dữ liệu", "Hãy nhận diện ảnh trước khi xuất báo cáo.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word", "*.docx"), ("PDF", "*.pdf"), ("Text", "*.txt")],
            initialfile="bao_cao_ocr.docx"
        )
        if not path:
            return
        metrics = {
            "Số ký tự": len(self.extracted_text),
            "Số từ": len(self.extracted_text.split()),
            "Số vùng văn bản": len(self.results),
            "Thời gian xử lý (giây)": f"{self.processing_time:.2f}",
            "Độ tin cậy trung bình": f"{self.average_confidence:.4f}"
        }
        try:
            suffix = Path(path).suffix.lower()
            if suffix == ".docx":
                export_docx(path, self.source_name, self.extracted_text, metrics, self.evaluation)
            elif suffix == ".pdf":
                export_pdf(path, self.source_name, self.extracted_text, metrics, self.evaluation)
            else:
                export_txt(self.extracted_text, path)
            messagebox.showinfo("Thành công", f"Đã xuất tệp:\n{path}")
        except Exception as exc:
            messagebox.showerror("Lỗi xuất báo cáo", str(exc))

    def clear_all(self):
        self.stop_camera()
        self.image_rgb = self.processed_rgb = self.display_rgb = None
        self.results = []
        self.extracted_text = ""
        self.output_text("Văn bản OCR sẽ hiển thị tại đây.")
        self.original_panel.configure(image="", text="Chọn ảnh hoặc mở camera")
        self.processed_panel.configure(image="", text="Ảnh sau tiền xử lý sẽ hiển thị ở đây")
        self.original_panel.image = None
        self.processed_panel.image = None
        self.reset_stats()
        self.status.config(text="Đã xóa dữ liệu.")

    def on_close(self):
        self.stop_camera()
        self.root.destroy()

def launch():
    root = tk.Tk()
    OCRWindow(root)
    root.mainloop()
