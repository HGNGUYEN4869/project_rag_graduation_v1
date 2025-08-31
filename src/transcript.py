import pdfplumber
import pytesseract
from PIL import Image
import uuid
import cv2
import numpy as np
from transcriptToJson import write_new_json
from enviroment.envGlobal import DB_JSON
from PIL import Image
import re
import os

def preprocess_image(pil_image):
    img = np.array(pil_image.convert("L"))
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(img)

def ocr_pytesseract(pil_image):
    pil_image = preprocess_image(pil_image)
    text = pytesseract.image_to_string(pil_image, lang="vie+eng")
    return text.strip()

def extract_page_elements(page, path, page_num):
    elements = []

    # 1. Text thật (theo dòng)
    lines = page.extract_text_lines() if hasattr(page, "extract_text_lines") else None
    if not lines:
        # fallback nếu không có extract_text_lines
        text = page.extract_text()
        if text:
            elements.append({
                "id": str(uuid.uuid4()),
                "text": text.strip(),
                "top": 0,
                "metadata": {"page": page_num, "source": path, "type": "text"}
            })
    else:
        for line in lines:
            elements.append({
                "id": str(uuid.uuid4()),
                "text": line["text"].strip(),
                "top": line["top"],
                "metadata": {"page": page_num, "source": path, "type": "text"}
            })

    # 2. Ảnh chứa chữ
    for img in page.images:
        try:
            x0, top, x1, bottom = img["x0"], img["top"], img["x1"], img["bottom"]
            pil_image = page.within_bbox((x0, top, x1, bottom)).to_image(resolution=300).original
            text_img = ocr_pytesseract(pil_image)
            if text_img:
                elements.append({
                    "id": str(uuid.uuid4()),
                    "text": text_img,
                    "top": top,
                    "metadata": {
                        "page": page_num,
                        "source": path,
                        "type": "ocr_text"
                    }
                })
        except Exception as e:
            print(f"⚠️ OCR lỗi ở trang {page_num}: {e}")

    # 3. Sắp xếp theo vị trí top (từ trên xuống)
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
            elements = []
            # Lấy text thật (text layer)
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                for line in text.split("\n"):
                    if re.match(r"^\s*trang\s*\d+\s*$", line.strip(), re.IGNORECASE): 
                        continue
                    bbox = page.chars[0] if page.chars else {"top":0}
                    elements.append({"text": line, "top": bbox["top"] if "top" in bbox else 0})
            # else:
            #     # OCR nếu không có text layer
            #     pil_image = page.to_image(resolution=300).original
                # ocr_text = pytesseract.image_to_string(pil_image, lang="vie+eng")
                # for i, line in enumerate(ocr_text.split("\n")):
                #     if re.match(r"^\s*trang\s*\d+\s*$", line.strip(), re.IGNORECASE):
                #         continue
                #     elements.append({"text": line, "top": i*20})  # giả định khoảng cách dòng

            merged_content = merge_lines(elements)
            if merged_content:
                data.append({"page": page_num, "content": merged_content})
    final_data = {book_name: data}
    write_new_json(final_data, DB_JSON)
    os.startfile(DB_JSON)
