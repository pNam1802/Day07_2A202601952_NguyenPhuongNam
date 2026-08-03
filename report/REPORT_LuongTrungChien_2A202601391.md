# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lương Trung Chiến
**Nhóm:** PenguinsMadagasccar
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Khi hai đoạn văn bản có độ tương tự cosine cao, nghĩa là hướng của vector biểu diễn hai đoạn văn đó rất giống nhau. Về mặt ý nghĩa, cả hai văn bản thường nói về cùng một chủ đề hoặc truyền tải ý tưởng gần giống nhau, dù số từ hay độ dài có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A : `Tôi thích ăn phở sáng.`
- Câu B : `Sáng nay tôi ăn phở rất ngon.`
- Tại sao tương đồng : `Hai câu này đều nói về việc ăn phở vào buổi sáng, nên vector embedding của chúng có hướng gần nhau.`

**Ví dụ có độ tương tự THẤP:**

- Câu A: `Tối nay tôi xem phim.`
- Câu B: `Ngày mai tôi đi mua rau.`
- Tại sao khác: `Hai câu này nói về hai hoạt động khác nhau, chủ đề khác nhau nên các vector sẽ lệch nhau nhiều.`

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> 1. Cosine similarity đo “góc” giữa hai vector, nên nó tập trung vào sự giống nhau về hướng nội dung, không bị ảnh hưởng nhiều bởi độ lớn (length) của vector.

2. Với văn bản, hai câu có cùng ý nhưng khác số lượng từ hoặc khác cường độ biểu đạt vẫn có thể có vector dài khác nhau. Cosine similarity vẫn so sánh tốt vì nó loại bỏ yếu tố độ dài.
3. Euclidean distance lại đo “khoảng cách thực” giữa hai điểm, nên nếu một vector dài hơn do văn bản dài hơn, khoảng cách có thể lớn ngay cả khi nội dung vẫn giống nhau. Vì vậy cosine similarity thường phù hợp hơn cho embeddings văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:*

1. `Với chunk_size = 500 và overlap = 50:`
   - `Số chunk bằng ceil((10000 - 50) / (500 - 50))`
   - `= ceil(9950 / 450)`
   - `= ceil(22.11...)`
   - `= 23 chunks`

> *Đáp án:* `= 23 chunks`

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> `Nếu tăng overlap = 100:`

- `Số chunk = ceil((10000 - 100) / (500 - 100))`
  `= ceil(9900 / 400)`
  `= ceil(24.75)`
  `= 25 chunks`

> `==> Thay đổi khi tăng độ chồng chéo`

- `Số chunk tăng từ 23 lên 25.`
- `Lý do: khi overlap lớn hơn, mỗi chunk mới dịch chuyển ít hơn so với chunk trước, nên cần nhiều chunk hơn để che phủ toàn bộ tài liệu.`

> `==> Tại sao muốn tăng overlap?`

- `Giúp giữ lại ngữ cảnh ở ranh giới giữa các chunk`
- `Giảm khả năng mất thông tin khi một ý nằm giữa hai chunk`
- `Thường cải thiện chất lượng truy vấn/khả năng trả lời, vì nội dung quan trọng có thể xuất hiện trong nhiều chunk khác nhau`

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

> 1. ``Trước hết chia nhỏ văn bản bằng hai phương pháp phù hợp với nội dung — tách theo câu để giữ từng câu có nghĩa hoặc tách theo các separator tự nhiên như đoạn mới, dấu chấm, khoảng trắng khi cần chia theo cấu trúc lớn hơn.``
> 2. ``Sau đó mỗi document được nạp vào store dưới dạng record gồm id, content, metadata và embedding của nội dung đó; khi tìm kiếm mình nhúng truy vấn và so sánh với embedding của các record bằng cosine similarity để lấy top-k kết quả có hướng vector giống nhất; nếu cần lọc theo điều kiện bổ sung thì áp metadata filter trước, chỉ tính tương đồng trên tập con phù hợp; cuối cùng mình tạo prompt RAG bằng cách ghép các chunk ngữ cảnh liên quan vào phần context rồi gọi LLM để sinh câu trả lời, nhằm đảm bảo model trả lời dựa trên thông tin đã được truy xuất.``

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> `Dùng regex để tách câu theo dấu chấm, chấm than, chấm hỏi, đồng thời giữ lại khoảng trắng và tránh tách sai với các trường hợp tên viết tắt hay chữ số.`
> `Xử lý edge case bằng cách loại bỏ đoạn rỗng và gộp các câu quá ngắn vào chunk kế tiếp nếu cần để không tạo ra nhiều chunk vô nghĩa..`

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> `Thuật toán dùng kiểu đệ quy: nếu văn bản đã nhỏ hơn chunk_size, trả nguyên; còn không thì tìm điểm ngắt tốt nhất theo các ký tự ngắt (ví dụ \n\n, ., ,) theo thứ tự ưu tiên.`
> `Base case là khi đoạn văn bản đủ nhỏ để đưa vào một chunk, hoặc không còn điểm ngắt tự nhiên nào thì cắt thẳng theo chunk_size..`

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> `Lưu trữ mỗi document cùng với embedding và metadata vào một danh sách/structure nội bộ; khi thêm thì tính embedding cho content rồi ghi vào store.`
> `Tìm kiếm bằng cách tính cosine similarity giữa embedding truy vấn và embedding của các chunk rồi sắp xếp để lấy top-k kết quả.`

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `Xử lý edge case bằng cách loại bỏ đoạn rỗng và gộp các câu quá ngắn vào chunk kế tiếp nếu cần để không tạo ra nhiều chunk vô nghĩa..`
> `Xử lý edge case bằng cách loại bỏ đoạn rỗng và gộp các câu quá ngắn vào chunk kế tiếp nếu cần để không tạo ra nhiều chunk vô nghĩa..`

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> `Cấu trúc prompt đặt rõ vai trò của agent, yêu cầu trả lời dựa trên ngữ cảnh được cung cấp và không tưởng tượng thông tin.`
> `nject context bằng cách ghép top-k chunk nội dung vào prompt trước câu hỏi, để model có đủ thông tin tham chiếu khi sinh câu trả lời.`

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
(venv) PS C:\Users\PC ACER\OneDrive\Desktop\Day07_2A202601391_LuongTrungChien> pytest tests/ -v  
========================================== test session starts ===========================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\PC ACER\OneDrive\Desktop\Day07_2A202601391_LuongTrungChien\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\PC ACER\OneDrive\Desktop\Day07_2A202601391_LuongTrungChien
plugins: anyio-4.14.2
collected 42 items                                                                                

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED               [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                        [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                 [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                  [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                       [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED       [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED             [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED              [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED            [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                              [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED              [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                         [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                     [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                               [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED      [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED          [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED    [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED          [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                              [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                  [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                        [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED             [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED               [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED   [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                         [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                        [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                   [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED               [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED          [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED              [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                    [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED              [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED         [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED        [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED       [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

=========================================== 42 passed in 0.12s ===========================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                                    | Câu B                                                                  | Dự đoán | Điểm thực tế | Đúng? |
| ---- | --------------------------------------------------------- | ----------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | Tôi đi học bằng xe đạp                              | Sáng nay tôi đạp xe đến trường.                                 | cao        | 0.0940           | Đúng  |
| 2    | Tôi đăng ký học phần online vào tuần sau          | Tuần tới tôi sẽ đăng kí học trực tuyến                        | cao        | 0.0780           | Đúng  |
| 3    | Học bổng giành cho sinh viên giỏi                    | Tối nay tôi đi xem phim cùng bạn                                   | thấp      | 0.0079           | Đúng  |
| 4    | Quy định kí trúc xá yêu cầu nộp phí trước      | Bài tập lập trình phải nộp qua hệ thống LMS                     | thấp      | 0.0435           | Đúng  |
| 5    | Chương trình học bổng hỗ trợ sinh viên khó khăn | Các suất học bổng được cấp cho sinh viên có hoàn cảnh khó. | Cao        | -0.1263          | Sai     |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> ``Kết quả bất ngờ nhất là cặp 5: hai câu về học bổng và hoàn cảnh khó khăn lẽ ra có ý nghĩa gần nhau, nhưng điểm cosine lại âm. Điều này cho thấy embeddings không chỉ dựa vào một vài từ giống nhau mà còn phụ thuộc vào cách mô hình mã hoá toàn bộ ngữ cảnh; với mock/embedder đơn giản, đôi khi những câu có ý nghĩa gần nhau vẫn không được biểu diễn thật sự tương đồng.``

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query)                                                                           | Top-1 Chunk truy xuất được (tóm tắt)                                                                            | Điểm Score | Có liên quan không? (Relevant)                  | Câu trả lời của Agent (tóm tắt)                                                                                                                                        |
| - | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | Rút môn học thì nhận điểm gì và có phải đóng học phí cho môn đó không?   | `course-withdrawal`: điều kiện rút môn, nhận điểm R (điểm 17) và vẫn phải nộp đủ học phí.         | 0,6414       | Có — top-1                                       | Nhận điểm R (điểm 17); môn rút không tính vào bảng điểm nhưng vẫn phải nộp đủ học phí.                                                                  |
| 2 | Hạn chót nộp 100% học phí học kỳ 1 và học kỳ 2 là khi nào?                      | `conduct-grading`: mục “Điểm đạt của các học phần tốt nghiệp”, không chứa thời hạn nộp học phí. | 0,5698       | Không — chunk đúng không có trong top-3      | Không trả lời đúng được hạn chót vì ngữ cảnh truy xuất không chứa mục “Thời gian nộp học phí”; đáp án chuẩn là kết thúc tuần 4 của học kỳ. |
| 3 | Các học phần tốt nghiệp được xếp loại ĐẠT khi đạt mức điểm nào?           | `conduct-grading`: mục “Điểm đạt của các học phần tốt nghiệp”.                                         | 0,7701       | Có — top-1                                       | Phải đạt từ mức C trở lên, tương đương từ 5,5 theo thang điểm 10.                                                                                             |
| 4 | Sinh viên được kéo dài thời gian đào tạo tối đa bao nhiêu học kỳ?            | `extended-study-duration`: các trường hợp và giới hạn kéo dài thời gian đào tạo.                       | 0,7430       | Có — top-1                                       | Tối đa 1 học kỳ chính với sinh viên chính quy và 2 học kỳ chính với sinh viên vừa làm vừa học; chỉ xét một lần.                                        |
| 5 | Muốn học ngành thứ hai thì nộp đơn ở đâu và cần điều kiện gì trước đó? | `double-major`: mục “Quy trình” đào tạo song ngành.                                                         | 0,4899       | Có — top-1; lọc metadata vẫn giữ đúng top-1 | Hoàn thành học phần tốt nghiệp ngành thứ nhất, xin xác nhận của Trưởng Khoa quản lý ngành thứ hai rồi nộp đơn tại Phòng Đào tạo.                  |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Điều đáng chú ý nhất là các chiến lược rất khác nhau về số lượng và độ dài chunk nhưng kết quả chỉ chênh nhau 1 điểm; chất lượng dữ liệu và cách diễn đạt truy vấn có ảnh hưởng lớn hơn việc chỉ tinh chỉnh kích thước chunk. Từ thử nghiệm nhóm, tôi cũng thấy lọc theo `category` là một lưới an toàn hữu ích: nó đưa chunk `double-major` từ hạng 3 lên hạng 1 với `RecursiveChunker`, trong khi các metadata đồng nhất như `audience` hay `language` không giúp thu hẹp kết quả.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10                |
| **Tổng phần cá nhân**                      | **60/ 60**       |
