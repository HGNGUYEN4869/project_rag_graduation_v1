import json

# ====== Hàm ghi dữ liệu ra file JSON mới ======
def write_new_json(data, json_path):
    """
    Ghi mới dữ liệu Python (list/dict) ra file JSON.
    
    data: list hoặc dict
    json_path: đường dẫn file JSON để lưu
    """
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)  # ensure_ascii=False để giữ tiếng Việt

# ====== Hàm đọc dữ liệu từ file JSON ======
def read_json(json_path):
    """
    Đọc dữ liệu từ file JSON và trả về Python object (list/dict).
    
    json_path: đường dẫn file JSON
    return: list hoặc dict
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def write_next_json(data, json_path):
    """
    Ghi thêm dữ liệu Python (list/dict) vào file JSON.

    data: list hoặc dict
    json_path: đường dẫn file JSON để lưu
    """
    existing_data = []
    try:
      existing_data = read_json(json_path)
    except FileNotFoundError:
        write_new_json(data, json_path)
        return
    if isinstance(existing_data, list):
        existing_data.extend(data)
    elif isinstance(existing_data, dict):
        existing_data.update(data)
    write_new_json(existing_data, json_path)
