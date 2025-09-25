"""

Usage:
    python src/chunking.py rule --max_chars 800
    python src/chunking.py semantic --max_chars 500 --n_clusters 8
"""

import json
import re
import uuid
import sys
import argparse
from typing import List, Dict

# --- Rule-based: heading + câu ---
import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab")

nltk.download("punkt", quiet=True)
from nltk.tokenize import sent_tokenize

def chunk_by_heading_and_sentence(paragraphs: List[str], max_chars: int) -> List[Dict]:
    chunks = []
    buffer = ""

    heading_pattern = re.compile(r"^(CHƯƠNG|Mục|[0-9]+\.[0-9]+)")

    for par in paragraphs:
        if heading_pattern.match(par.strip()):
            if buffer:
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": buffer.strip(),
                    "chars": len(buffer)
                })
                buffer = ""
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": par.strip(),
                "chars": len(par.strip())
            })
        else:
            sentences = sent_tokenize(par)
            for s in sentences:
                if len(buffer) + len(s) < max_chars:
                    buffer += " " + s
                else:
                    chunks.append({
                        "id": str(uuid.uuid4()),
                        "text": buffer.strip(),
                        "chars": len(buffer)
                    })
                    buffer = s
    if buffer:
        chunks.append({
            "id": str(uuid.uuid4()),
            "text": buffer.strip(),
            "chars": len(buffer)
        })
    return chunks


# --- Semantic: embedding + clustering ---
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering

model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_by_embedding_clustering(paragraphs: List[str], max_chars: int, n_clusters: int) -> List[Dict]:
    sentences = []
    for par in paragraphs:
        sentences.extend(sent_tokenize(par))

    if not sentences:
        return []

    embeddings = model.encode(sentences)

    clustering = AgglomerativeClustering(n_clusters=min(n_clusters, len(sentences)))
    labels = clustering.fit_predict(embeddings)

    chunks = []
    for label in set(labels):
        group = [s for i, s in enumerate(sentences) if labels[i] == label]
        text = " ".join(group)
        if len(text) > max_chars:
            for i in range(0, len(text), max_chars):
                sub = text[i:i+max_chars]
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": sub.strip(),
                    "chars": len(sub)
                })
        else:
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text.strip(),
                "chars": len(text)
            })
    return chunks


# --- Process JSON ---
from enviroment.envGlobal import DB_JSON, DB_AFTER_CHUNK

def process_input(mode: str, max_chars: int, n_clusters: int, input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    results = []

    for book_name, pages in db.items():
        print(f"Processing book: {book_name} ...")

        paragraphs = []
        for page in pages:
            paragraphs.extend(page.get("content", []))

        if mode == "rule":
            chunks = chunk_by_heading_and_sentence(paragraphs, max_chars)
        elif mode == "semantic":
            chunks = chunk_by_embedding_clustering(paragraphs, max_chars, n_clusters)
        else:
            raise ValueError("Mode must be 'rule' or 'semantic'")

        out_obj = {
            "book": book_name,
            "mode": mode,
            "settings": {
                "max_chars": max_chars,
                "n_clusters": n_clusters if mode == "semantic" else None
            },
            "chunks": chunks
        }
        results.append(out_obj)

    with open(output_path, "w", encoding="utf-8") as wf:
        json.dump(results, wf, ensure_ascii=False, indent=2)

    print(f"✅ Saved {sum(len(b['chunks']) for b in results)} chunks -> {output_path}")

def run_chunking(mode: str, max_chars: int = 800, n_clusters: int = 5,
                 input_path: str = DB_JSON, output_path: str = DB_AFTER_CHUNK):
    """
    Run chunking process with given parameters.
    """
    process_input(mode, max_chars, n_clusters, input_path, output_path)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Chunk text by rule or semantic clustering")
#     parser.add_argument("mode", choices=["rule", "semantic"], help="Chunking mode")
#     parser.add_argument("--max_chars", type=int, default=800, help="Max characters per chunk")
#     parser.add_argument("--n_clusters", type=int, default=5, help="Number of clusters (semantic mode only)")
#     args = parser.parse_args()

#     run_chunking(args.mode, args.max_chars, args.n_clusters, DB_JSON, DB_AFTER_CHUNK)


#Chunk theo heading + câu (rule-based), chunk tối đa 800 ký tự
#python src/chunking.py rule --max_chars 800

#Chunk theo semantic clustering, chunk tối đa 500 ký tự, 8 cụm
#python src/chunking.py semantic --max_chars 500 --n_clusters 8
