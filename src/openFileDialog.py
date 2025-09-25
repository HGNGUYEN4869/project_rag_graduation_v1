import tkinter as tk
from tkinter import filedialog
import os
from transcript import load_document  # import hàm load_document từ file transcript.py

def open_file_dialog():
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính

    file_paths = filedialog.askopenfilenames(
        title="Chọn một hoặc nhiều file PDF để xử lý",
        # filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        filetypes=[
        ("Tài liệu", "*.pdf *.doc *.docx"),
        ("PDF files", "*.pdf"),
        ("Word files", "*.doc *.docx"),
        ("All files", "*.*")
        ]
    )
    
    if file_paths:
        print("📂 Các file đã chọn:")
        for path in file_paths:
            print(f"   - {path}")
            try:
                load_document(path)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý {path}: {e}")
    else:
        print("❌ Không có file nào được chọn.")

if __name__ == "__main__":
    open_file_dialog()