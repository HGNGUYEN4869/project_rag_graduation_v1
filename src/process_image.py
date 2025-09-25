# process_image.py
import os
import json
import uuid
from PIL import Image
import pytesseract

# Optional: BLIP (captioning) / LLaVA wrapper
# from transformers import BlipProcessor, BlipForConditionalGeneration
# OR implement llava_client that sends image to LLaVA inference endpoint

def ocr_image(image_path, lang="vie+eng"):
    """Trả về text OCR (chuẩn)"""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()

def caption_blip(image_path, blip_processor=None, blip_model=None):
    """
    Nếu bạn có BLIP loaded, dùng nó. 
    Hoặc thay bằng llava_caption(image_path) nếu bạn gọi LLaVA inference endpoint.
    """
    if blip_processor and blip_model:
        img = Image.open(image_path).convert("RGB")
        inputs = blip_processor(images=img, return_tensors="pt")
        out_ids = blip_model.generate(**inputs, max_length=128)
        caption = blip_processor.decode(out_ids[0], skip_special_tokens=True)
        return caption
    else:
        # fallback: trả empty hoặc simple placeholder
        return ""

def llava_caption_via_api(image_path, api_endpoint: str, api_key: str = None):
    """
    Nếu bạn có LLaVA inference server, gọi HTTP POST với image multipart và nhận caption.
    Implement theo endpoint bạn có.
    """
    import requests
    files = {"image": open(image_path, "rb")}
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    resp = requests.post(api_endpoint, files=files, headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json().get("caption") or resp.text

def extract_chart_data_deplot(image_path, deplot_func=None):
    """
    Gọi DePlot or chart-to-data extractor.
    Nếu bạn đã tích hợp DePlot, truyền function thực thi tại deplot_func(image_path) -> dict(data,csv...).
    """
    if deplot_func:
        return deplot_func(image_path)  # expected to return structured dict
    # fallback: None
    return None

def process_and_annotate_image(image_path, out_dir=None, llava_endpoint=None, deplot_func=None):
    """
    Trả về dict:
    {
      "id":..., "path":..., "ocr_text":"...", "caption":"...", "chart_data": {...} or None
    }
    """
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    item = {"id": str(uuid.uuid4()), "path": image_path}
    # OCR
    try:
        item["ocr_text"] = ocr_image(image_path)
    except Exception as e:
        item["ocr_text"] = ""
        item["ocr_error"] = str(e)

    # Caption using LLaVA (if endpoint) else BLIP fallback
    cap = ""
    try:
        if llava_endpoint:
            cap = llava_caption_via_api(image_path, llava_endpoint)
        else:
            cap = caption_blip(image_path)  # maybe empty if no model loaded
    except Exception as e:
        cap = ""
        item["caption_error"] = str(e)
    item["caption"] = cap

    # Chart extraction via DePlot
    try:
        chart = extract_chart_data_deplot(image_path, deplot_func=deplot_func)
        item["chart_data"] = chart
    except Exception as e:
        item["chart_data"] = None
        item["chart_error"] = str(e)

    return item
