from openFileDialog import open_file_dialog
from enviroment.envGlobal import DB_JSON, DB_AFTER_CHUNK
from build_index import build_faiss_index
from chatbot_terminal import load_faiss_index, answer_query

open_file_dialog();
# Chạy hàm open_file_dialog để mở hộp thoại chọn file và xử lý
# Sau khi chọn file, hàm này sẽ gọi load_pdf hoặc load_docx và sau đó chạy chunking

# Gọi hàm để build index
index, metadata = build_faiss_index()

print("Số lượng vectors:", index.ntotal)
print("Metadata mẫu:", metadata[:20])  # In ra 20 metadata đầu tiên
index, metadatas, embedding_model = load_faiss_index()

# 5. Vòng lặp hỏi đáp
while True:
    query = input("\n💬 Câu hỏi của bạn (gõ 'exit' để thoát): ")
    if query.lower() == "exit":
        print("👋 Tạm biệt!")
        break

    answer = answer_query(query, index, metadatas, embedding_model, k=3, model="llama3.1")
    print("\n🤖 Trả lời:")
    print(answer)