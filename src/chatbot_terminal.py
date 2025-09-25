# import os
# import faiss
# import pickle
# import numpy as np
# from langchain_community.embeddings import HuggingFaceEmbeddings
# import ollama
# # ==== 1. Đường dẫn tới FAISS index + metadata ====
# from enviroment.envGlobal import INDEX_PATH, META_PATH

# # ==== 2. Load FAISS index + metadata ====
# index = faiss.read_index(INDEX_PATH)
# with open(META_PATH, "rb") as f:
#     metadatas = pickle.load(f)

# print(f"✅ Loaded index with {index.ntotal} vectors")

# # ==== 3. Load embedding model ====
# embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# # ==== 4. Vòng lặp hỏi đáp ====
# while True:
#     query = input("\n💬 Câu hỏi của bạn (gõ 'exit' để thoát): ")
#     if query.lower() == "exit":
#         print("👋 Tạm biệt!")
#         break

#     # → Embed query
#     query_vec = np.array([embedding_model.embed_query(query)], dtype="float32")

#     # → Search top-3 kết quả
#     D, I = index.search(query_vec, k=3)

#     # → Lấy context
#     contexts = []
#     for idx in I[0]:
#         meta = metadatas[idx]
#         contexts.append(f"Trang {meta['page']} ({meta['book']})")

#     context_text = "\n".join(contexts)

#     # → Prompt cho LLM
#     prompt = f"""
#     Bạn là trợ lý AI. Dựa trên nội dung từ các trang sau:
#     {context_text}

#     Trả lời ngắn gọn và dễ hiểu cho câu hỏi:
#     {query}
#     """

#     # → Gọi Ollama để sinh câu trả lời
#     response = ollama.chat(model="llama3.1", messages=[{"role": "user", "content": prompt}])

#     print("\n🤖 Trả lời:")
#     print(response["message"]["content"])
import faiss
import pickle
import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings
import ollama
from enviroment.envGlobal import INDEX_PATH, META_PATH


def load_faiss_index(index_path: str = INDEX_PATH, meta_path: str = META_PATH,
                     model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Load FAISS index, metadata và embedding model.
    """
    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        metadatas = pickle.load(f)

    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    print(f"✅ Loaded index with {index.ntotal} vectors")

    return index, metadatas, embedding_model


def answer_query(query: str, index, metadatas, embedding_model, k: int = 3, model: str = "llama3.1") -> str:
    """
    Trả lời câu hỏi dựa trên FAISS index + Ollama.
    - query: câu hỏi của user
    - index: FAISS index
    - metadatas: metadata của từng vector
    - embedding_model: model để embed query
    - k: số kết quả top-k để lấy context
    - model: model LLM của Ollama
    """

    # → Embed query
    query_vec = np.array([embedding_model.embed_query(query)], dtype="float32")

    # → Search top-k kết quả
    D, I = index.search(query_vec, k=k)

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
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])

    return response["message"]["content"]
