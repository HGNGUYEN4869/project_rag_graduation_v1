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

def sentence_split(text: str) -> List[str]:
    # Regex tách câu cơ bản
    sentences = re.split(r'(?<!\d)\.(?!\d)\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_sentences(sentences: List[str], max_words=500, overlap=100):
    chunks = []
    buffer = []
    word_count = 0

    for sentence in sentences:
        words = sentence.split()

        # Nếu câu dài hơn max_words thì tự cắt nhỏ
        if len(words) > max_words:
            for i in range(0, len(words), max_words):
                sub_chunk = words[i:i+max_words]
                if buffer:
                    chunks.append(" ".join(buffer))
                buffer = sub_chunk
                word_count = len(buffer)
            continue

        # Nếu thêm câu này vượt max_words thì đóng chunk cũ
        if word_count + len(words) > max_words:
            chunks.append(" ".join(buffer))
            # overlap tính theo số từ cuối cùng
            buffer = buffer[-overlap:] + words
            word_count = len(buffer)
        else:
            buffer.extend(words)
            word_count += len(words)

    if buffer:
        chunks.append(" ".join(buffer))

    return chunks

def make_chunk_id(doc_name: str, page_num: int, chunk_text: str) -> str:
    """Tạo chunk_id duy nhất từ doc_name + page_num + text"""
    raw = f"{doc_name}-{page_num}-{chunk_text}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()  # hoặc dùng sha1/sha256 tùy ý

def process_transcript(data: dict[str, any], max_words=200, overlap=50) -> List[dict[str, any]]:
    """
    Nhận transcript JSON → tách câu → chunk → dataset cho RAG.
    
    Trả về list các dict: { "source": ..., "page": ..., "chunk_id": ..., "text": ... }
    """
    dataset = []
    for doc_name, pages in data.items():
        for page in pages:
            page_num = page["page"]
            # Gộp content (list câu raw) thành text
            text = " ".join(page["content"])
            # Tách câu
            sentences = sentence_split(text)
            # Chunk
            chunks = chunk_sentences(sentences, max_words=max_words, overlap=overlap)

            for chunk in chunks:
                dataset.append({
                    "source": doc_name,
                    "page": page_num,
                    "chunk_id": make_chunk_id(doc_name, page_num, chunk),
                    "text": chunk
                })
    return dataset


# ====================== DEMO ======================
if __name__ == "__main__":
    transcript_data = read_json(DB_JSON)

    dataset = process_transcript(transcript_data, max_words=30, overlap=10)
    write_new_json(dataset, DB_AFTER_CHUNK)
    os.startfile(DB_AFTER_CHUNK)
