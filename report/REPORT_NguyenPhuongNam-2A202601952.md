# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Phương Nam
**Mã SV:** 2A202601952
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao nghĩa là chúng biểu đạt ý nghĩa tương đồng hoặc nói về cùng một chủ đề — các vector embedding của chúng trỏ về cùng một hướng trong không gian nhiều chiều, cho dù độ dài hay từ ngữ cụ thể có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Học phí học kỳ này cần nộp trước ngày 15."
- Câu B: "Sinh viên phải thanh toán tiền học trước ngày 15 trong học kỳ."
- Tại sao tương đồng: Cả hai câu đều truyền đạt cùng một thông tin (deadline nộp học phí), chỉ dùng từ ngữ khác nhau. Embedding sẽ ánh xạ chúng gần nhau vì ngữ nghĩa giống nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thư viện mở cửa từ 7 giờ sáng đến 9 giờ tối."
- Câu B: "Quy trình đăng ký học bổng cần nộp đơn trước tháng 10."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau (giờ mở cửa thư viện vs. học bổng), không chia sẻ ngữ nghĩa chung nên vector embedding sẽ trỏ về các hướng rất khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài (magnitude) của vector — văn bản dài hơn thường có vector có độ dài lớn hơn, dẫn đến khoảng cách lớn hơn ngay cả khi nội dung tương đồng. Cosine similarity chỉ đo **góc** giữa hai vector (bỏ qua độ dài), nên nó phản ánh đúng hơn sự tương đồng về ngữ nghĩa bất kể độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính theo công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
>
> `= làm_tròn_lên((10000 - 50) / (500 - 50))`
> `= làm_tròn_lên(9950 / 450)`
> `= làm_tròn_lên(22.11...)`
>
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks` — tăng thêm 2 chunks. Tăng overlap giúp mỗi chunk chia sẻ thêm nội dung với chunk liền kề, đảm bảo thông tin quan trọng nằm ở ranh giới giữa hai chunk không bị bỏ sót khi truy xuất — rất hữu ích khi ngữ cảnh liên tục qua nhiều câu.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split` với pattern `(?<=[.!?])\s+|(?<=\.)\n` (lookbehind) để tách câu ngay sau dấu kết thúc câu mà không mất ký tự. Sau đó gom các câu thành nhóm theo `max_sentences_per_chunk`, join bằng dấu cách và strip whitespace. Trường hợp ngoại lệ: text rỗng trả về `[]`, câu cuối không có dấu kết thúc vẫn được đưa vào nhóm cuối.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử từng separator theo thứ tự ưu tiên: nếu separator hiện tại tồn tại trong text thì tách, gom các phần lại cho đến khi vượt `chunk_size` thì lưu chunk và đệ quy phần quá dài với separator tiếp theo. Base case là: text đã vừa `chunk_size` (trả ngay) hoặc hết separator (trả text nguyên). Trường hợp separator rỗng `""` dùng `FixedSizeChunker` làm fallback.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được embed thành vector float bằng `embedding_fn`, sau đó lưu cùng `content`, `metadata` (đã gắn `doc_id`) vào `self._store` (list of dict). Khi search: embed query → tính dot product với tất cả vectors đã lưu (mock embedder trả vector đã normalize nên dot ≈ cosine similarity) → sắp xếp giảm dần → trả `top_k` kết quả đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc trước** — chỉ giữ các record mà metadata thỏa mãn tất cả điều kiện filter, rồi chạy `_search_records` trên tập đã lọc. `delete_document` lọc loại các record có `metadata["doc_id"] == doc_id` ra khỏi `self._store`, trả `True` nếu có record nào bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất. Xây dựng prompt theo mẫu RAG: liệt kê các chunk với số thứ tự `[1]`, `[2]`, `[3]` làm ngữ cảnh, sau đó đặt câu hỏi ở cuối. Gọi `llm_fn(prompt)` và trả kết quả — không có logic nào khác trong agent, tất cả "trí tuệ" đến từ LLM và chất lượng retrieval.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-9.1.1, pluggy-1.5.0
rootdir: D:\Vin\Day07_2A202601952_NguyenPhuongNam
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.15s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42** ✅

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

*Phần này sẽ được hoàn thành ở Giai đoạn 2 khi chạy `compute_similarity()` trên dữ liệu thật.*

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Học phí học kỳ cần nộp trước ngày 15" | "Sinh viên phải thanh toán tiền học trước ngày 15" | cao | *(chờ kết quả)* | |
| 2 | "Thư viện mở cửa từ 7h sáng đến 9h tối" | "Quy trình đăng ký học bổng cần nộp đơn trước tháng 10" | thấp | *(chờ kết quả)* | |
| 3 | "Đăng ký học phần qua cổng thông tin sinh viên" | "Sinh viên đăng ký môn học trên hệ thống trực tuyến" | cao | *(chờ kết quả)* | |
| 4 | "Ký túc xá A có phòng đôi và phòng bốn người" | "Học bổng khuyến khích học tập dành cho sinh viên xuất sắc" | thấp | *(chờ kết quả)* | |
| 5 | "Sinh viên cần photo CCCD khi làm thẻ thư viện" | "Mang theo chứng minh nhân dân để đăng ký thẻ thư viện" | cao | *(chờ kết quả)* | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *(Sẽ điền sau khi chạy thực tế ở Giai đoạn 2)*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

*Phần này sẽ được hoàn thành ở Giai đoạn 2 sau khi nhóm thống nhất 5 câu hỏi đánh giá và bộ tài liệu.*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Sẽ điền sau buổi thảo luận nhóm)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | *(chờ Giai đoạn 2)* / 5 |
| Kết quả truy xuất của tôi (Competition Results) | *(chờ Giai đoạn 2)* / 10 |
| **Tổng phần cá nhân** | **45+ / 60** |
