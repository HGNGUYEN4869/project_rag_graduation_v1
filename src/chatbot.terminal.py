import os
import faiss
import pickle
import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings
import ollama
# ==== 1. Đường dẫn tới FAISS index + metadata ====
from enviroment.envGlobal import INDEX_PATH, META_PATH

# ==== 2. Load FAISS index + metadata ====
index = faiss.read_index(INDEX_PATH)
with open(META_PATH, "rb") as f:
    metadatas = pickle.load(f)

print(f"✅ Loaded index with {index.ntotal} vectors")

# ==== 3. Load embedding model ====
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ==== 4. Vòng lặp hỏi đáp ====
while True:
    query = input("\n💬 Câu hỏi của bạn (gõ 'exit' để thoát): ")
    if query.lower() == "exit":
        print("👋 Tạm biệt!")
        break

    # → Embed query
    query_vec = np.array([embedding_model.embed_query(query)], dtype="float32")

    # → Search top-3 kết quả
    D, I = index.search(query_vec, k=3)

    # → Lấy context
    contexts = []
    for idx in I[0]:
        meta = metadatas[idx]
        contexts.append(f"Trang {meta['page']} ({meta['book']})")

    context_text = "\n".join(contexts)

    # → Prompt cho LLM
    prompt = f"""
    Bạn là trợ lý AI. Dựa trên nội dung từ các trang sau:
    {context_text}

    Trả lời ngắn gọn và dễ hiểu cho câu hỏi:
    {query}
    """

    # → Gọi Ollama để sinh câu trả lời
    response = ollama.chat(model="llama3.1", messages=[{"role": "user", "content": prompt}])

    print("\n🤖 Trả lời:")
    print(response["message"]["content"])
