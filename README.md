# RAG_v1 - PDF Text Extraction and Processing System

## Mô tả dự án

RAG_v1 là một hệ thống xử lý văn bản từ file PDF để tạo dữ liệu cho hệ thống RAG (Retrieval Augmented Generation). Dự án này có khả năng:

- Trích xuất văn bản từ PDF bao gồm cả text layer và OCR
- Xử lý và làm sạch văn bản tiếng Việt và tiếng Anh
- Chia nhỏ văn bản thành các chunk phù hợp cho RAG
- Lưu trữ dữ liệu dưới định dạng JSON

## Cấu trúc dự án

```
RAG_v1/
├── src/                          # Mã nguồn chính
│   ├── transcript.py            # Xử lý PDF và trích xuất văn bản
│   ├── transcriptToJson.py      # Utilities để đọc/ghi JSON
│   ├── chunking.py              # Chia nhỏ văn bản thành chunks
│   ├── openFileDialog.py        # Giao diện chọn file
│   └── enviroment/
│       └── envGlobal.py         # Cấu hình đường dẫn
├── Database/                     # Lưu trữ dữ liệu
│   ├── dataTest.json           # Dữ liệu raw từ PDF
│   └── dataTest_after_chunk.json # Dữ liệu sau khi chia chunk
└── README.md                    # Tài liệu này
```

## Tính năng chính

### 1. Trích xuất văn bản từ PDF
- **Text Layer Extraction**: Trích xuất văn bản trực tiếp từ PDF
- **OCR Processing**: Sử dụng Tesseract để đọc văn bản từ hình ảnh
- **Image Preprocessing**: Tối ưu hóa hình ảnh trước khi OCR
- **Multi-language Support**: Hỗ trợ tiếng Việt và tiếng Anh

### 2. Xử lý và làm sạch văn bản
- Loại bỏ ký tự đặc biệt và nhiễu
- Gộp các dòng văn bản liên quan
- Loại bỏ số trang tự động
- Chuẩn hóa tên sách và metadata

### 3. Chunking thông minh
- Chia văn bản theo câu với overlap
- Kiểm soát kích thước chunk (số từ)
- Tạo chunk_id duy nhất bằng MD5 hash
- Bảo toàn context giữa các chunk

## Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Tesseract OCR

### Cài đặt dependencies

Dự án sử dụng các thư viện Python sau:

**Cài đặt tất cả dependencies:**
```bash
pip install -r requirements.txt
```

**Hoặc cài đặt từng package riêng lẻ:**
```bash
# Dùng cách này nếu muốn kiểm soát version cụ thể
# Xử lý PDF
pip install pdfplumber>=0.10.0

# OCR và xử lý hình ảnh
pip install pytesseract>=0.3.10
pip install Pillow>=10.0.0
pip install opencv-python>=4.8.0
pip install numpy>=1.24.0

# GUI (thường có sẵn với Python)
# tkinter đã được cài đặt mặc định với Python
```

**Chi tiết các dependencies:**
- `pdfplumber`: Trích xuất văn bản và metadata từ PDF
- `pytesseract`: Python wrapper cho Tesseract OCR
- `Pillow (PIL)`: Xử lý và chỉnh sửa hình ảnh
- `opencv-python`: Xử lý hình ảnh nâng cao (resize, blur, threshold)
- `numpy`: Hỗ trợ tính toán array cho xử lý hình ảnh
- `tkinter`: Tạo giao diện chọn file (có sẵn với Python)

### Cài đặt Tesseract OCR

**Windows:**
1. Tải và cài đặt từ [GitHub Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Thêm đường dẫn Tesseract vào PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-vie  # Hỗ trợ tiếng Việt
```

**macOS:**
```bash
brew install tesseract
```

## Sử dụng

### 1. Xử lý PDF qua giao diện
```python
python src/openFileDialog.py
```

### 2. Xử lý PDF trực tiếp
```python
from src.transcript import load_pdf

# Xử lý một file PDF
load_pdf("path/to/your/file.pdf")
```
chạy file transcript.py để tải và transcript file
### 3. Chia chunk từ dữ liệu đã xử lý
```python
from src.chunking import process_transcript
from src.transcriptToJson import read_json, write_new_json

# Đọc dữ liệu raw
data = read_json("Database/dataTest.json")

# Chia chunk với cấu hình tùy chỉnh
chunks = process_transcript(data, max_words=200, overlap=50)

# Lưu kết quả
write_new_json(chunks, "Database/dataTest_after_chunk.json")
```

## Cấu hình

### Đường dẫn database
Chỉnh sửa file `src/enviroment/envGlobal.py`:

```python
DB_JSON = "path/to/raw/data.json"
DB_AFTER_CHUNK = "path/to/chunked/data.json"
```

### Tham số chunking
- `max_words`: Số từ tối đa trong một chunk (mặc định: 200)
- `overlap`: Số từ overlap giữa các chunk (mặc định: 50)
- `line_gap`: Khoảng cách dòng để gộp văn bản (mặc định: 15)

## Định dạng dữ liệu

### Raw data format (dataTest.json)
```json
{
  "Ten_Sach": [
    {
      "page": 1,
      "content": [
        "Câu văn bản đầu tiên...",
        "Câu văn bản thứ hai..."
      ]
    }
  ]
}
```

### Chunked data format (dataTest_after_chunk.json)
```json
[
  {
    "source": "Ten_Sach",
    "page": 1,
    "chunk_id": "md5_hash_unique",
    "text": "Nội dung chunk đã được xử lý..."
  }
]
```

## Xử lý lỗi thường gặp

### 1. Lỗi Tesseract không tìm thấy
```bash
# Kiểm tra cài đặt
tesseract --version

# Thêm vào PATH trên Windows
set PATH=%PATH%;C:\Program Files\Tesseract-OCR
```

### 2. Lỗi encoding
Đảm bảo file JSON được lưu với encoding UTF-8 để hỗ trợ tiếng Việt.

### 3. Memory issues với PDF lớn
- Xử lý từng trang một
- Giảm resolution khi chuyển đổi hình ảnh
- Tăng bộ nhớ virtual nếu cần

## Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## License

Dự án này được phân phối dưới MIT License. Xem file `LICENSE` để biết thêm chi tiết.

## Tác giả

- **Thuoc** - Developer chính

## Ghi chú

- Dự án này được tối ưu cho văn bản tiếng Việt
- Hỗ trợ xử lý PDF có cả text layer và image-based content
- Phù hợp cho việc tạo dataset cho các hệ thống RAG và chatbot