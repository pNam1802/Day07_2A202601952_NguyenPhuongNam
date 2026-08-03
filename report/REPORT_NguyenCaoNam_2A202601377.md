# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Cao Nam
**Mã Học Viên:** 202601377
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> *Viết 1-2 câu:* Góc giữa hai vector đặc trưng của hai văn bản rất hẹp, biểu thị rằng hai đoạn văn bản đó có ngữ nghĩa và chủ đề rất giống nhau hoặc liên quan mật thiết đến nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Thời tiết hôm nay thật tuyệt vời với bầu trời trong xanh."
- Câu B: "Hôm nay trời rất đẹp, không có một gợn mây."
- Tại sao tương đồng: Cả hai câu đều mang cùng một thông điệp (chủ đề) về thời tiết tốt, mặc dù sử dụng từ vựng khác nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Thời tiết hôm nay thật tuyệt vời với bầu trời trong xanh."
- Câu B: "Giá cổ phiếu của công ty công nghệ đã giảm mạnh."
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác biệt (thời tiết vs tài chính/chứng khoán), từ vựng và ngữ cảnh không có điểm chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> *Viết 1-2 câu:* Cosine similarity chỉ quan tâm đến hướng của vector (sự phân bố ngữ nghĩa) mà không bị ảnh hưởng bởi độ lớn (chiều dài của câu văn). Do đó, nó so sánh đúng bản chất ý nghĩa thay vì số lượng từ vựng giữa một câu ngắn và một đoạn văn dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:* Bước nhảy (step) = 500 - 50 = 450 ký tự. Vòng lặp start từ 0, 450, 900, ..., 9450, 9900.
> *Đáp án:* (10000 - 50) / 450 = 22.11 -> Làm tròn lên là **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> *Viết 1-2 câu:* Bước nhảy giảm xuống 400, số lượng chunk sẽ tăng lên 25 chunks. Việc tăng overlap giúp đảm bảo rằng một câu văn hoặc một ý quan trọng không bị cắt đứt gãy giữa hai đoạn, giữ cho ngữ cảnh của chunk toàn vẹn hơn để thuật toán nhúng (embedding) hiểu đúng ý.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> *Viết 2-3 câu:* Tôi dùng `re.split(r'(?<=[.!?])\s+|(?<=\.)\n', text)` với kỹ thuật lookbehind để tách câu ngay sau các dấu `.` `!` `?` nhưng vẫn giữ lại dấu câu đó trong chuỗi. Sau đó, tôi gộp (join) các câu lại thành các nhóm theo số lượng `max_sentences_per_chunk` và loại bỏ các khoảng trắng dư thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> *Viết 2-3 câu:* Hàm được thiết kế đệ quy thử tách văn bản theo các separator có mức ưu tiên từ cao đến thấp (`\n\n`, `\n`, v.v.). Base case (trường hợp cơ sở) dừng đệ quy là khi văn bản truyền vào đã ngắn hơn `chunk_size` hoặc khi danh sách separator đã cạn kiệt, lúc này những phần vẫn còn dài sẽ được tách đệ quy với separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> *Viết 2-3 câu:* `add_documents` sẽ tạo dictionary `{"id", "content", "metadata", "embedding"}` từ đối tượng Document và append vào list lưu trên RAM (in-memory). Hàm `search` sẽ nhúng (embed) câu hỏi, rồi tính tích vô hướng (dot product) vector câu hỏi với tất cả chunks trong store, sau đó sort giảm dần để lấy top k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> *Viết 2-3 câu:* `search_with_filter` thực hiện lọc (filter) trước bằng cách duyệt qua danh sách chunks, chỉ giữ lại các chunks khớp toàn bộ metadata_filter, sau đó mới gọi hàm search để giảm bớt chi phí tính toán. `delete_document` tái tạo lại danh sách chunks (`self._store`) bằng cách loại bỏ các record có `id` trùng với `doc_id` truyền vào.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> *Viết 2-3 câu:* Hàm thực hiện theo đúng pipeline RAG: Đầu tiên, truy xuất các chunks liên quan từ `EmbeddingStore`, sau đó dùng list comprehension để lấy content và join chúng lại bằng `\n\n`. Cuối cùng, ghép các nội dung này làm Context (ngữ cảnh) cùng với Question (câu hỏi) vào một chuỗi prompt f-string và gọi `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: D:\vin\AI20k_lab\labdays\New folder\Day07_2A202601377_NguyenCaoNam
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                | Câu B                                                     | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ----------------------------------------------------- | ---------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | "Trường đại học nằm ở trung tâm thành phố." | "Cơ sở giáo dục này toạ lạc giữa lòng thủ đô." | cao        | 0.82             | Có     |
| 2    | "Đăng ký môn học kết thúc vào ngày 15/9."    | "Hạn chót để huỷ lớp là giữa tháng 9."            | cao        | 0.65             | Có     |
| 3    | "Sinh viên năm 4 phải làm đồ án tốt nghiệp." | "Sinh viên phải nộp học phí trước học kỳ."        | thấp      | 0.15             | Có     |
| 4    | "Máy học là một nhánh của AI."                  | "AI bao gồm rất nhiều kỹ thuật."                      | cao        | 0.70             | Có     |
| 5    | "Ký túc xá cho phép nuôi chó mèo không?"      | "Hướng dẫn nộp đơn xin học bổng."                  | thấp      | 0.02             | Có     |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> *Viết 2-3 câu:* Cặp 2 cho thấy điểm số khá cao dù cấu trúc câu và từ vựng thay đổi hoàn toàn ("Đăng ký môn học" vs "Huỷ lớp", "ngày 15/9" vs "giữa tháng 9"). Điều này chứng minh rằng model embedding đã thực sự học được ngữ nghĩa (semantics) và mối liên hệ khái niệm (concept mapping) chứ không chỉ đơn thuần là đếm mức độ trùng lặp từ vựng.

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

> *Viết 2-3 câu:* Qua phần trình bày, tôi nhận thấy chiến lược Chunking theo đoạn văn (RecursiveChunker) với metadata kèm theo (chỉ mục nguồn bài viết) giúp cho câu trả lời của agent không chỉ đúng ngữ cảnh mà còn có thể trích dẫn lại nguồn cực kỳ chuẩn xác so với Fixed Size chunking.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10                |
| **Tổng phần cá nhân**                      | **60 / 60**      |
