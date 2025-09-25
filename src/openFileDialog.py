import tkinter as tk
from tkinter import filedialog
import os
from transcript import load_pdf, load_docx  # import hàm load_pdf và load_docx từ file transcript.py
from chunking import run_chunking
from enviroment.envGlobal import DB_JSON, DB_AFTER_CHUNK

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
    run_chunking("semantic", max_chars=500, n_clusters=8, input_path=DB_JSON, output_path=DB_AFTER_CHUNK)