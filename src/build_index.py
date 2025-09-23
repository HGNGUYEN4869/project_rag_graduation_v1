import json
import faiss
import numpy as np
import pickle
from enviroment.envGlobal import DB_JSON, OUTPUT_DIR
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

# ==== 1. Load JSON
with open(DB_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

book_name, pages = list(data.items())[0]

documents, metadatas = [], []

# ==== 2. Mỗi page = 1 document
for page in pages:
    page_num = page["page"]
    text = " ".join(page["content"]).strip()
    if not text:
        continue
    documents.append(text)
    metadatas.append({
        "book": book_name,
        "page": page_num
    })

# ==== 3. Embed toàn bộ
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

embeddings = []
for doc in documents:
    vector = embedding_model.embed_query(doc)
    embeddings.append(vector)

embeddings = np.array(embeddings).astype("float32")

# ==== 4. Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print(f"Index built: {index.ntotal} pages")

# ==== 5. Save index + metadata
os.makedirs(OUTPUT_DIR, exist_ok=True)

faiss.write_index(index, os.path.join(OUTPUT_DIR, "faiss_index.idx"))
with open(os.path.join(OUTPUT_DIR, "faiss_metadata.pkl"), "wb") as f:
    pickle.dump(metadatas, f)


print("✅ Index + metadata saved.")
