# import re
# import os
# from typing import List
# from transcriptToJson import read_json, write_next_json
# from enviroment.envGlobal import DB_JSON, DB_AFTER_CHUNK 

# def sentence_split(text: str) -> List[str]:
#     # Regex tách câu cơ bản
#     sentences = re.split(r'(?<!\d)\.(?!\d)\s+', text)
#     return [s.strip() for s in sentences if s.strip()]

# def chunk_sentences(sentences: List[str], max_words=300, overlap=100):
#     chunks = []
#     buffer = []
#     word_count = 0

#     for sentence in sentences:
#         words = sentence.split()

#         # Nếu câu dài hơn max_words thì tự cắt nhỏ
#         if len(words) > max_words:
#             for i in range(0, len(words), max_words):
#                 sub_chunk = words[i:i+max_words]
#                 if buffer:
#                     chunks.append(" ".join(buffer))
#                 buffer = sub_chunk
#                 word_count = len(buffer)
#             continue

#         # Nếu thêm câu này vượt max_words thì đóng chunk cũ
#         if word_count + len(words) > max_words:
#             chunks.append(" ".join(buffer))
#             # overlap tính theo số từ cuối cùng
#             buffer = buffer[-overlap:] + words
#             word_count = len(buffer)
#         else:
#             buffer.extend(words)
#             word_count += len(words)

#     if buffer:
#         chunks.append(" ".join(buffer))

#     return chunks

# def process_transcript(data: dict[str, any], max_words=200, overlap=50) -> List[dict[str, any]]:
#     """
#     Nhận transcript JSON → tách câu → chunk → dataset cho RAG.
    
#     Trả về list các dict: { "source": ..., "page": ..., "chunk_id": ..., "text": ... }
#     """
#     dataset = []
#     for doc_name, pages in data.items():
#         for page in pages:
#             page_num = page["page"]
#             # Gộp content (list câu raw) thành text
#             text = " ".join(page["content"])
#             # Tách câu
#             sentences = sentence_split(text)
#             # Chunk
#             chunks = chunk_sentences(sentences, max_words=max_words, overlap=overlap)

#             for i, chunk in enumerate(chunks):
#                 dataset.append({
#                     "source": doc_name,
#                     "page": page_num,
#                     "chunk_id": f"{doc_name}_p{page_num}_c{i+1}",
#                     "text": chunk
#                 })
#     return dataset


# # ====================== DEMO ======================
# if __name__ == "__main__":
#     transcript_data = read_json(DB_JSON)

#     dataset = process_transcript(transcript_data, max_words=30, overlap=10)
#     write_next_json(dataset, DB_AFTER_CHUNK)
#     os.startfile(DB_AFTER_CHUNK)
import re
import os
import hashlib
from typing import List
from transcriptToJson import read_json, write_new_json
from enviroment.envGlobal import DB_JSON, DB_AFTER_CHUNK

def custom_sentence_split(text: str) -> List[str]:
    """
    Tách text thành các câu theo quy tắc:
    - Nếu có dấu ":" thì gom ":" và các dòng sau bắt đầu bằng "-" hoặc "." vào cùng một chunk.
    - Nếu không có ":" thì tách theo dấu chấm "." (mỗi câu một chunk, giữ lại dấu chấm).
    """
    sentences = []
    buffer = []

    lines = text.splitlines()
    inside_colon_block = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Nếu gặp ":" → bắt đầu block đặc biệt
        if ":" in stripped and not inside_colon_block:
            if buffer:
                sentences.extend(buffer)
                buffer = []
            buffer.append(stripped)
            inside_colon_block = True
            continue

        if inside_colon_block:
            if stripped.startswith("-") or stripped.startswith("+") or stripped.startswith("*"):
                buffer.append(stripped)
                continue
            else:
                # kết thúc block
                sentences.append(" ".join(buffer))
                buffer = []
                inside_colon_block = False
                # xử lý dòng hiện tại như bình thường
                parts = re.findall(r'[^.]+(?:\.)?', stripped)
                for part in parts:
                    if part.strip():
                        sentences.append(part.strip())
                continue

        # Bình thường: tách theo dấu chấm, nhưng giữ dấu chấm
        parts = re.findall(r'[^.]+(?:\.)?', stripped)
        for part in parts:
            if part.strip():
                sentences.append(part.strip())

    if buffer:
        sentences.append(" ".join(buffer))

    return [s.strip() for s in sentences if s.strip()]


def chunk_sentences(sentences: List[str], max_words=500, overlap=100):
    chunks = []
    buffer = []
    word_count = 0

    for sentence in sentences:
        words = sentence.split()

        # Nếu câu dài hơn max_words, để nguyên câu thành một chunk riêng
        # KHÔNG cắt nhỏ câu để tránh phá vỡ ngữ nghĩa
        if len(words) > max_words:
            # Nếu buffer có nội dung, đóng chunk cũ trước
            if buffer:
                chunks.append(" ".join(buffer))
                buffer = []
                word_count = 0
            # Tạo chunk riêng cho câu dài này
            chunks.append(sentence.strip())
            continue

        # Nếu thêm câu này vượt max_words thì đóng chunk cũ
        if word_count + len(words) > max_words:
            if buffer:  # Đảm bảo buffer không rỗng
                chunks.append(" ".join(buffer))
            # Bắt đầu chunk mới với overlap từ chunk cũ
            if overlap > 0 and len(buffer) > overlap:
                buffer = buffer[-overlap:]
                word_count = len(buffer)
            else:
                buffer = []
                word_count = 0
            # Thêm câu hiện tại vào buffer mới
            buffer.extend(words)
            word_count += len(words)
        else:
            # Thêm câu vào buffer hiện tại
            buffer.extend(words)
            word_count += len(words)

    # Đóng chunk cuối cùng nếu còn dữ liệu
    if buffer:
        chunks.append(" ".join(buffer))

    return chunks


def make_chunk_id(doc_name: str, page_num: int, chunk_text: str) -> str:
    """Tạo chunk_id duy nhất từ doc_name + page_num + text"""
    raw = f"{doc_name}-{page_num}-{chunk_text}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def process_transcript(data: dict[str, any], max_words=80, overlap=20) -> List[dict[str, any]]:
    dataset = []
    for doc_name, pages in data.items():
        for page in pages:
            page_num = page["page"]
            text = " ".join(page["content"])
            sentences = custom_sentence_split(text)
            chunks = chunk_sentences(sentences, max_words=max_words, overlap=overlap)

            for chunk in chunks:
                dataset.append({
                    "source": doc_name,
                    "page": page_num,
                    "chunk_id": make_chunk_id(doc_name, page_num, chunk),
                    "text": chunk
                })
    return dataset


def test_chunking_quality(chunks: List[str]) -> dict:
    """
    Kiểm tra chất lượng chunking:
    - Số chunk bị cắt giữa từ
    - Độ dài trung bình của chunk
    - Chunk ngắn nhất/dài nhất
    """
    stats = {
        "total_chunks": len(chunks),
        "broken_chunks": 0,
        "avg_words": 0,
        "min_words": float('inf'),
        "max_words": 0,
        "broken_examples": []
    }
    
    total_words = 0
    for i, chunk in enumerate(chunks):
        words = chunk.split()
        word_count = len(words)
        total_words += word_count
        
        # Cập nhật min/max
        stats["min_words"] = min(stats["min_words"], word_count)
        stats["max_words"] = max(stats["max_words"], word_count)
        
        # Kiểm tra chunk bị cắt - cải thiện logic
        chunk_text = chunk.strip()
        
        # Chunk bị cắt nếu:
        # 1. Không kết thúc bằng dấu câu phổ biến
        # 2. Bắt đầu bằng chữ thường (có thể là tiếp tục từ chunk trước)
        # 3. Kết thúc giữa từ (không có khoảng trắng cuối)
        is_broken = False
        
        # Kiểm tra kết thúc không đúng
        if not chunk_text.endswith(('.', '!', '?', ':', ';', '-', ')', ']', '}', '"', "'")):
            # Kiểm tra xem có phải chunk cuối không
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1].strip()
                # Nếu chunk tiếp theo bắt đầu bằng chữ thường, có thể bị cắt
                if next_chunk and next_chunk[0].islower():
                    is_broken = True
        
        if is_broken:
            stats["broken_chunks"] += 1
            if len(stats["broken_examples"]) < 5:  # Lưu 5 ví dụ
                stats["broken_examples"].append({
                    "chunk_id": i,
                    "text": chunk_text[:80] + "..." if len(chunk_text) > 80 else chunk_text
                })
    
    stats["avg_words"] = total_words / len(chunks) if chunks else 0
    stats["broken_percentage"] = (stats["broken_chunks"] / len(chunks)) * 100 if chunks else 0
    
    return stats


# ====================== DEMO ======================
if __name__ == "__main__":
    print("🔄 Đang xử lý dữ liệu...")
    transcript_data = read_json(DB_JSON)

    # Tùy chỉnh tham số chunking để tạo chunks ngắn hơn
    # max_words: 80-100 từ cho RAG tốt hơn (dễ đọc, ít nhiễu)
    # overlap: 20-30% để giữ context liên tục
    dataset = process_transcript(transcript_data, max_words=80, overlap=20)
    
    # Test chất lượng chunking
    chunk_texts = [item["text"] for item in dataset]
    stats = test_chunking_quality(chunk_texts)
    
    print(f"\n📊 THỐNG KÊ CHUNKING:")
    print(f"   • Tổng số chunks: {stats['total_chunks']}")
    print(f"   • Chunks bị cắt: {stats['broken_chunks']} ({stats['broken_percentage']:.1f}%)")
    print(f"   • Số từ trung bình: {stats['avg_words']:.1f}")
    print(f"   • Số từ min/max: {stats['min_words']}/{stats['max_words']}")
    
    # Đánh giá chất lượng
    if stats['broken_percentage'] < 10:
        print("   ✅ Chất lượng chunking: TỐT")
    elif stats['broken_percentage'] < 20:
        print("   ⚠️  Chất lượng chunking: KHẤP KHỂNH")
    else:
        print("   ❌ Chất lượng chunking: CẦN CẢI THIỆN")
    
    if stats["broken_examples"]:
        print(f"\n⚠️  VÍ DỤ CHUNKS BỊ CẮT:")
        for ex in stats["broken_examples"]:
            print(f"   Chunk {ex['chunk_id']}: {ex['text']}")
    
    write_new_json(dataset, DB_AFTER_CHUNK)
    print(f"\n✅ Đã lưu {len(dataset)} chunks vào {DB_AFTER_CHUNK}")
    
    # Hiển thị một vài chunk mẫu với độ dài
    print(f"\n📋 MỘT VÀI CHUNK MẪU:")
    for i, item in enumerate(dataset[:5]):
        word_count = len(item['text'].split())
        print(f"   Chunk {i+1} ({word_count} từ): {item['text'][:80]}...")
        if word_count > 100:
            print(f"      ⚠️  Chunk này quá dài!")
    
    # Thống kê độ dài chunks
    word_counts = [len(item['text'].split()) for item in dataset]
    long_chunks = [w for w in word_counts if w > 100]
    very_long_chunks = [w for w in word_counts if w > 150]
    
    print(f"\n📏 PHÂN TÍCH ĐỘ DÀI CHUNKS:")
    print(f"   • Chunks > 100 từ: {len(long_chunks)}/{len(dataset)} ({len(long_chunks)/len(dataset)*100:.1f}%)")
    print(f"   • Chunks > 150 từ: {len(very_long_chunks)}/{len(dataset)} ({len(very_long_chunks)/len(dataset)*100:.1f}%)")
    if long_chunks:
        print(f"   • Chunks dài nhất: {max(word_counts)} từ")
        print(f"   • Chunks ngắn nhất: {min(word_counts)} từ")
    
    # Mở file để kiểm tra
    os.startfile(DB_AFTER_CHUNK)
