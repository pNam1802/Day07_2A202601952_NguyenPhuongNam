# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hữu Hoàng Anh
**Nhóm:** PeigunsMadagascar
**Ngày:** 3/8

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau, nên hai đoạn văn bản thường có nội dung hoặc ý nghĩa tương tự. Điểm càng gần 1 thì mức tương đồng càng cao.
**Ví dụ có độ tương tự CAO:**
- Câu A:
- Câu B:
- Tại sao tương đồng:

**Ví dụ có độ tương tự THẤP:**
- Câu A:
- Câu B:
- Tại sao khác:

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity so sánh hướng của các vector, nên tập trung vào sự gần nhau về ngữ nghĩa thay vì độ dài vector. Vì vậy nó thường phù hợp hơn Euclidean distance khi so sánh text embeddings.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23
> *Đáp án:* 23

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*Số chunk tăng lên 24: ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 24. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa các chunk, nhưng làm tăng số chunk và chi phí lưu trữ/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

Triển khai từng thành phần theo luồng xử lý RAG: chia văn bản thành chunk, tạo/lưu embedding, tìm kiếm các chunk liên quan, rồi đưa chúng vào prompt cho agent. Mỗi hàm xử lý cả trường hợp biên như văn bản rỗng, vector có độ dài bằng 0 và không có kết quả phù hợp.
### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*
dùng regex (?<=[.!?])\s+ để tách văn bản sau dấu ., !, hoặc ? khi phía sau là khoảng trắng hoặc xuống dòng. Mỗi câu được loại bỏ khoảng trắng thừa rồi gom tối đa theo max_sentences_per_chunk; văn bản rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*
Thuật toán lần lượt thử các separator \n\n, \n, . , khoảng trắng và cuối cùng là chuỗi rỗng để cắt theo ký tự. Base case là khi đoạn văn không vượt chunk_size; nếu không còn separator phù hợp thì cắt trực tiếp thành các đoạn có độ dài tối đa chunk_size.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*
Mỗi document được embed và lưu trong bộ nhớ dưới dạng id, content, metadata và embedding. Khi tìm kiếm, truy vấn cũng được embed, sau đó tính dot product với từng embedding và sắp xếp kết quả giảm dần theo score.
**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*
search_with_filter() lọc các record theo metadata trước, sau đó chỉ tìm kiếm trên các record phù hợp. delete_document() duyệt store và loại bỏ mọi record có metadata["doc_id"] trùng với document cần xoá.
### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*
lấy các top-k chunk liên quan từ EmbeddingStore, rồi ghép nội dung chúng thành phần Context. Sau đó hàm tạo prompt gồm Context, Question và Answer, rồi truyền prompt vào llm_fn để sinh câu trả lời dựa trên thông tin đã truy xuất.
---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên đăng ký học phần trên cổng học vụ. | Người học đăng ký môn trong hệ thống học vụ. | cao | 0.2480 | Không |
| 2 | Thư viện cho mượn tài liệu. | Thư viện có dịch vụ mượn sách. | cao | -0.0427 | Không |
| 3 | Sinh viên bị trùng lịch học. | Người học cần điều chỉnh lớp khi lịch bị xung đột. | cao | 0.0981 | Không |
| 4 | Thư viện là nơi học tập. | Học phần tiên quyết cần được kiểm tra. | thấp | 0.0268 | Có |
| 5 | Mượn sách cần thẻ định danh. | Đóng học phí trực tuyến. | thấp | 0.1756 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*
Cặp 2 bất ngờ nhất vì hai câu đều nói về dịch vụ mượn tài liệu của thư viện nhưng điểm similarity lại âm. Điều này cho thấy mock embedding không biểu diễn ngữ nghĩa đáng tin cậy; embedding thật cần được huấn luyện để các câu cùng nghĩa có vector gần nhau.
---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 3/ 5 |
| Hướng tiếp cận của tôi (My Approach) |7 / 10 |
| Hoàn thiện code (Core Implementation — tests) |20 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) |5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) |5 / 10 |
| **Tổng phần cá nhân** | **40 / 60** |
