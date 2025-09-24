import pdfplumber
import pytesseract
from PIL import Image
import uuid
import numpy as np
from docx import Document
from transcriptToJson import write_next_json
from enviroment.envGlobal import DB_JSON
from PIL import Image
import re
import os

# def preprocess_image(pil_image):
#     img = np.array(pil_image.convert("L"))
#     img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
#     img = cv2.GaussianBlur(img, (3, 3), 0)
#     img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
#     return Image.fromarray(img)

# def ocr_pytesseract(pil_image):
#     pil_image = preprocess_image(pil_image)
#     text = pytesseract.image_to_string(pil_image, lang="vie+eng")
#     return text.strip()

def extract_page_elements(page, path, page_num):
    elements = []

    # 1. Text thật (text layer)
    text = page.extract_text(x_tolerance=2, y_tolerance=2)
    if text:
        for line in text.split("\n"):
            # Bỏ dòng "trang X"
            if re.match(r"^\s*trang\s*\d+\s*$", line.strip(), re.IGNORECASE):
                continue
            bbox = page.chars[0] if page.chars else {"top": 0}
            elements.append({
                "id": str(uuid.uuid4()),
                "text": line.strip(),
                "top": bbox["top"] if "top" in bbox else 0,
                "metadata": {
                    "page": page_num,
                    "source": path,
                    "type": "text"
                }
            })
    else:
        # 2. OCR fallback nếu không có text layer
        pil_image = page.to_image(resolution=300).original
        ocr_text = pytesseract.image_to_string(pil_image, lang="vie+eng")
        for i, line in enumerate(ocr_text.split("\n")):
            if re.match(r"^\s*trang\s*\d+\s*$", line.strip(), re.IGNORECASE):
                continue
            elements.append({
                "id": str(uuid.uuid4()),
                "text": line.strip(),
                "top": i * 20,  # giả định khoảng cách dòng
                "metadata": {
                    "page": page_num,
                    "source": path,
                    "type": "ocr_text"
                }
            })

    # 3. Sắp xếp theo vị trí top
    elements.sort(key=lambda x: x["top"])
    return elements

def clean_text(text: str) -> str:
    # Loại ký tự lạ
    text = re.sub(r"[^0-9A-Za-zÀ-ỹ\s\.,:;()\-\+]", "", text)
    # Xóa khoảng trắng thừa
    return re.sub(r"\s+", " ", text).strip()

def merge_lines(elements, line_gap=15):
    merged = []
    buffer = ""
    prev_top = None

    for el in elements:
        text = clean_text(el["text"])
        if not text:
            continue
        top = el["top"]

        if prev_top is not None and (top - prev_top > line_gap or buffer.endswith(('.', ':', ';'))):
            merged.append(buffer.strip())
            buffer = text
        else:
            buffer += " " + text

        prev_top = top

    if buffer:
        merged.append(buffer.strip())
    return merged


# chuẩn hóa tên sách 
def normalize_book_name(file_path: str) -> str:
    # Lấy tên file không có đuôi .pdf
    name = os.path.splitext(os.path.basename(file_path))[0]
    # Bỏ ký tự đặc biệt, chỉ giữ chữ, số, khoảng trắng
    name = re.sub(r"[^0-9A-Za-zÀ-ỹ\s]", "", name)
    # Đổi khoảng trắng thành dấu _
    name = re.sub(r"\s+", "_", name)
    return name.strip("_")

def load_pdf(file_path):
    data = []
    book_name = normalize_book_name(file_path)
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            elements = extract_page_elements(page, file_path, page_num)

            # Merge lại thành đoạn text hoàn chỉnh
            merged_content = merge_lines(elements)
            if merged_content:
                data.append({"page": page_num, "content": merged_content})
            # elements = []
            # # Lấy text thật (text layer)
            # text = page.extract_text(x_tolerance=2, y_tolerance=2)
            # if text:
            #     for line in text.split("\n"):
            #         if re.match(r"^\s*trang\s*\d+\s*$", line.strip(), re.IGNORECASE): 
            #             continue
            #         bbox = page.chars[0] if page.chars else {"top":0}
            #         elements.append({"text": line, "top": bbox["top"] if "top" in bbox else 0})
            # # else:
            # #     # OCR nếu không có text layer
            # #     pil_image = page.to_image(resolution=300).original
            #     # ocr_text = pytesseract.image_to_string(pil_image, lang="vie+eng")
            #     # for i, line in enumerate(ocr_text.split("\n")):
            #     #     if re.match(r"^\s*trang\s*\d+\s*$", line.strip(), re.IGNORECASE):
            #     #         continue
            #     #     elements.append({"text": line, "top": i*20})  # giả định khoảng cách dòng

            # merged_content = merge_lines(elements)
            # if merged_content:
            #     data.append({"page": page_num, "content": merged_content})
    final_data = {book_name: data}
    write_next_json(final_data, DB_JSON)
    os.startfile(DB_JSON)

def load_docx(file_path):
    data = []
    book_name = normalize_book_name(file_path)

    doc = Document(file_path)
    page_num = 1  # Word không có khái niệm page, tạm để 1
    merged_content = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            merged_content.append(text)

    if merged_content:
        data.append({"page": page_num, "content": merged_content})

    final_data = {book_name: data}
    write_next_json(final_data, DB_JSON)
    os.startfile(DB_JSON)
