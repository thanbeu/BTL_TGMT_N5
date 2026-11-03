# OCR VISION ADVANCED

Ứng dụng desktop nhận diện văn bản trong ảnh bằng Python, OpenCV và EasyOCR.

## Chức năng
- Chọn ảnh JPG/PNG/BMP/WEBP.
- Tiền xử lý ảnh: grayscale, Gaussian Blur, CLAHE, Adaptive Threshold.
- Nhận diện tiếng Việt và tiếng Anh bằng EasyOCR.
- Mở webcam, xem hình trực tiếp và chụp khung hình.
- So sánh ảnh gốc và ảnh đã tiền xử lý.
- Hiển thị văn bản, số từ, số ký tự, số vùng chữ, thời gian và độ tin cậy trung bình.
- Đánh giá CER/WER với văn bản chuẩn.
- Xuất TXT, Word và PDF.

## Yêu cầu
Khuyến nghị Windows 10/11, Python 3.10–3.12. Nên dùng Python 3.12 để tương thích tốt với PyTorch trên Windows.

## Cài đặt trên Windows
Mở PowerShell tại thư mục dự án:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```

Chạy:

```powershell
python main.py
```

Lần đầu EasyOCR tải mô hình về máy, cần Internet. Những lần sau có thể dùng mô hình đã lưu trong cache.

## Cách sử dụng
1. Chọn ảnh hoặc bật Camera.
2. Nếu dùng camera, nhấn Chụp khung hình.
3. Nhấn Tiền xử lý để xem ảnh đã tăng tương phản và nhị phân hóa.
4. Nhấn Nhận diện OCR.
5. Để đánh giá, nhập chính xác nội dung có trong ảnh vào ô văn bản chuẩn, sau đó nhấn Tính CER / WER.
6. Nhấn Xuất báo cáo để lưu DOCX, PDF hoặc TXT.

## Đánh giá
- CER: tỷ lệ lỗi ký tự (Character Error Rate).
- WER: tỷ lệ lỗi từ (Word Error Rate).
- Character Accuracy = max(0, 1 - CER).
- Word Accuracy = max(0, 1 - WER).

CER/WER có thể lớn hơn 1 trong trường hợp chèn nhiều ký tự/từ; vì vậy Accuracy được chặn tối thiểu ở 0%. Độ tin cậy EasyOCR không phải là accuracy đo trên tập dữ liệu.

## Lưu ý kỹ thuật
- Ảnh quá mờ, nghiêng, độ phân giải thấp hoặc ánh sáng không đều có thể làm giảm chất lượng.
- Bản demo dùng CPU (`gpu=False`), tốc độ phụ thuộc cấu hình máy.
- Nếu webcam mặc định không hoạt động, kiểm tra quyền Camera trong Windows Settings > Privacy & security > Camera.
- Không nên dùng kết quả OCR làm căn cứ duy nhất cho tài liệu pháp lý hoặc dữ liệu quan trọng; cần kiểm tra lại văn bản.
