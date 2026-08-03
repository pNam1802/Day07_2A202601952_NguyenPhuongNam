# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** PenguinsMadagascar
**Thành viên:** Nguyễn Phương Nam (2A202601952), Lương Trung Chiến (2A202601391), Nguyễn Hữu Hoàng Anh (2A202601357), Nguyễn Cao Nam (2A202601377))
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**

> Quy định học vụ dành cho sinh viên đại học HCMUT — đăng ký/rút môn học, học phí, đánh giá kết quả học tập, song ngành và kéo dài thời gian đào tạo. Toàn bộ lấy từ cổng hỗ trợ công khai BKSI (`mybk.hcmut.edu.vn/bksi/public`), nơi mỗi trang là một FAQ học vụ đã được nhà trường biên tập.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu                                                                  | Nguồn (Source URL)                                                                     | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán                                                   |
| - | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------ | ----------- | -------------------------------------------------------------------- |
| 1 | Đăng ký môn học - Quy định - Hướng dẫn chung (`course-registration`) | https://mybk.hcmut.edu.vn/bksi/public/vi/blog/dang-ky-mon-hoc-quy-trinh-huong-dan-chung | 2026-08-03 / not-stated  | 15.444      | `category=course-registration`, `document_type=student-guidance` |
| 2 | Đánh giá kết quả học tập (`conduct-grading`)                            | https://mybk.hcmut.edu.vn/bksi/public/vi/blog/danh-gia-ket-qua-hoc-tap                  | 2026-08-03 / not-stated  | 8.327       | `category=academic-assessment`, `document_type=policy-guidance`  |
| 3 | Học phí (`tuition-fees`)                                                     | https://mybk.hcmut.edu.vn/bksi/public/vi/blog/hoc-phi                                   | 2026-08-03 / not-stated  | 1.886       | `category=tuition`, `document_type=policy-guidance`              |
| 4 | Rút môn học (`course-withdrawal`)                                           | https://mybk.hcmut.edu.vn/bksi/public/vi/article/56                                     | 2026-08-03 / not-stated  | 1.772       | `category=course-withdrawal`, `document_type=procedure`          |
| 5 | Kéo dài thời gian đào tạo (`extended-study-duration`)                    | https://mybk.hcmut.edu.vn/bksi/public/vi/blog/keo-dai-thoi-gian-dao-tao                 | 2026-08-03 / not-stated  | 1.333       | `category=study-duration`, `document_type=procedure`             |
| 6 | Đào tạo song ngành (`double-major`)                                        | https://mybk.hcmut.edu.vn/bksi/public/vi/blog/do-tao-song-nganh                         | 2026-08-03 / not-stated  | 859         | `category=double-major`, `document_type=policy-guidance`         |

Tổng cộng **29.621 ký tự** trong `data/hcmut_bksi/`. Mọi tài liệu đều mang thêm bốn trường chung: `audience=student`, `department=academic-affairs`, `language=vi`, `license_or_permission=public-page`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [X] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [X] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

Ghi chú thu thập: crawl bằng `scripts/rebuild_hcmut_bksi.py` — kiểm tra `robots.txt`, chờ ≥1 giây giữa các request, chỉ nhận trang HTML/text công khai. Tất cả trang BKSI đều **không công bố ngày hiệu lực**, nên `document_version` ghi `not-stated` đúng theo quy ước ở `docs/DATA_COLLECTION.md`. Đây là một hạn chế thật của bộ dữ liệu: nhóm không kiểm chứng được độ mới của quy định, chỉ biết ngày mình lấy về.

Mỗi trang BKSI kèm khoảng 1.500 ký tự footer giống hệt nhau (menu "Thông tin phổ biến", "Tags", chính sách cookie). Nhóm đã cắt bỏ trước khi ingest — với bốn tài liệu ngắn, phần này từng chiếm 44-64% nội dung và sẽ sinh ra hàng loạt chunk gần trùng nhau **giữa các văn bản khác nhau**, đúng loại nhiễu làm hỏng xếp hạng truy xuất.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata    | Kiểu  | Ví dụ giá trị                                        | Tại sao hữu ích cho truy xuất (retrieval)?                                                                                                                                |
| -------------------- | ------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `doc_id`           | string | `tuition-fees`                                         | Khóa ổn định, trùng tên file; dùng cho`delete_document()` và để truy vết chunk về đúng văn bản gốc.                                                        |
| `source_url`       | string | `https://mybk.hcmut.edu.vn/.../hoc-phi`                | Trích dẫn nguồn kèm câu trả lời, cho phép người đọc tự kiểm chứng.                                                                                             |
| `retrieved_at`     | date   | `2026-08-03`                                           | Đánh giá độ mới; quy định học vụ thay đổi theo năm học.                                                                                                         |
| `document_version` | string | `not-stated`                                           | Ghi nhận rõ nguồn không nêu phiên bản, tránh ngộ nhận đây là bản mới nhất.                                                                                    |
| `category`         | enum   | `tuition`, `course-withdrawal`                       | **Trường lọc chính.** Mỗi tài liệu một giá trị riêng nên `search_with_filter()` khoanh được đúng văn bản khi từ khóa xuất hiện ở nhiều nơi. |
| `document_type`    | enum   | `procedure`, `policy-guidance`, `student-guidance` | Phân biệt "các bước phải làm" với "quy định/điều kiện" — hai kiểu câu hỏi rất khác nhau của sinh viên.                                                   |
| `audience`         | enum   | `student`                                              | Bắt buộc theo K3. Hiện cả 6 tài liệu đều`student` nên **không có tác dụng lọc** (xem mục 4).                                                           |
| `department`       | string | `academic-affairs`                                     | Cùng lý do: hiện đồng nhất, để dành cho khi mở rộng sang thư viện / ký túc xá.                                                                                |
| `language`         | enum   | `vi`                                                   | Chuẩn bị cho corpus song ngữ; hiện đồng nhất.                                                                                                                          |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=200)` trên 3 tài liệu đại diện (một dài, một trung bình, một ngắn):

| Tài liệu                               | Chiến lược (Strategy)           | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                                                            |
| ---------------------------------------- | ---------------------------------- | ----------------- | --------------------- | ------------------------------------------------------------------------------------------ |
| `course-registration` (15.444 ký tự) | FixedSizeChunker (`fixed_size`)  | 78                | 198,0                 | Không — cắt giữa câu, nhiều chunk mở đầu bằng nửa từ.                          |
| `course-registration`                  | SentenceChunker (`by_sentences`) | 34                | 451,8                 | Khá — trọn câu, nhưng gộp 3 câu thuộc 3 mục khác nhau.                           |
| `course-registration`                  | RecursiveChunker (`recursive`)   | 118               | 129,1                 | Kém — vỡ vụn nhất, mỗi gạch đầu dòng thành một chunk rời.                     |
| `tuition-fees` (1.886 ký tự)         | FixedSizeChunker                   | 10                | 188,6                 | Không — tách "kết thúc ở tuần 4" khỏi tiêu đề mục "Thời gian nộp học phí". |
| `tuition-fees`                         | SentenceChunker                    | 6                 | 312,2                 | Khá.                                                                                      |
| `tuition-fees`                         | RecursiveChunker                   | 14                | 132,9                 | Kém.                                                                                      |
| `double-major` (859 ký tự)           | FixedSizeChunker                   | 5                 | 171,8                 | Không.                                                                                    |
| `double-major`                         | SentenceChunker                    | 1                 | 857,0                 | Cả văn bản dồn thành**một** chunk — quá thô.                                |
| `double-major`                         | RecursiveChunker                   | 5                 | 170,4                 | Kém.                                                                                      |

Toàn corpus: `fixed_size` 151 chunk (avg 196,2) · `by_sentences` 70 chunk (avg 420,7) · `recursive` 215 chunk (avg 136,0).

Hai nhận xét quan trọng rút ra từ baseline:

1. Văn bản BKSI dùng rất nhiều gạch đầu dòng ngắn, nên `RecursiveChunker` gặp separator `"\n\n"` liên tục và cắt **vụn hơn cả** `FixedSizeChunker` (215 vs 151 chunk) — ngược với trực giác "đệ quy thì thông minh hơn".
2. `SentenceChunker` phụ thuộc dấu chấm câu, mà nhiều dòng trong corpus kết thúc bằng dấu hai chấm hoặc không có dấu chấm. Hệ quả là chunk dài bất thường: `double-major` bị gộp thành đúng 1 chunk 857 ký tự.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Phương Nam**

- **Loại chiến lược:** custom — `SectionChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Mỗi trang BKSI là một FAQ gồm các mục đánh số ("1. Thanh toán học phí", "2. Thời gian nộp học phí", "Bước 1)"), và mỗi mục trả lời trọn vẹn đúng một câu hỏi của sinh viên. Cắt đúng ranh giới mục giữ nguyên cụm "tiêu đề mục + điều kiện + ngoại lệ" trong cùng một chunk, thay vì xé giữa câu như `FixedSizeChunker`. Mục nào dài hơn `max_chars` thì giao lại cho `RecursiveChunker` để không sinh chunk quá lớn làm loãng vector.
- **Code snippet (nếu custom):** (bản đầy đủ trong `src/chunking.py`)

```python
class SectionChunker:
    # "1. Thanh toán học phí", "2- Quy định", "Bước 1)" hoặc tiêu đề markdown.
    SECTION_PATTERN = re.compile(r"^(?:#{1,6}\s|\d+\s*[.)-]\s|Bước\s+\d+\s*[.)])", re.M)

    def __init__(self, max_chars: int = 800) -> None:
        self.max_chars = max_chars

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        boundaries = [match.start() for match in self.SECTION_PATTERN.finditer(text)]
        if not boundaries:
            return RecursiveChunker(chunk_size=self.max_chars).chunk(text)

        # Phần mở đầu trước mục đầu tiên (nếu có) được giữ làm một chunk riêng.
        starts = ([0] if boundaries[0] > 0 else []) + boundaries
        sections = [text[a:b].strip() for a, b in zip(starts, starts[1:] + [len(text)])]

        chunks: list[str] = []
        for section in sections:
            if not section:
                continue
            if len(section) <= self.max_chars:
                chunks.append(section)
            else:
                chunks.extend(RecursiveChunker(chunk_size=self.max_chars).chunk(section))
        return chunks
```

Kết quả trên toàn corpus: **60 chunk, avg 491,9** (min 135 / max 798).

Một chi tiết phải sửa sau khi kiểm tra output thật: bản đầu tiên sinh ra chunk chỉ chứa đúng dòng tiêu đề (`# Học phí`, 9 ký tự) — vector của một chuỗi 9 ký tự không mang thông tin nào để truy xuất. Tham số `min_chars=120` gộp mục quá ngắn sang mục kế tiếp, nhờ đó tiêu đề tài liệu trở thành ngữ cảnh cho mục đầu tiên thay vì đứng lẻ.

**Thành viên 2 — Lương Trung Chiến**

- **Loại chiến lược:** `FixedSizeChunker` tinh chỉnh — `chunk_size=400, overlap=80`
- **Mô tả & lý do chọn:** Giữ nguyên chiến lược đơn giản nhất nhưng nắn hai tham số để chữa đúng điểm yếu của nó ở baseline. Nâng `chunk_size` từ 200 lên 400 vì một mục FAQ của BKSI trung bình dài ~440 ký tự — mức 200 cắt đôi gần như mọi mục. Thêm `overlap=80` (20%) để câu bị cắt ngang ranh giới vẫn còn nguyên vẹn ở một trong hai chunk liền kề, tránh mất thông tin kiểu "kết thúc ở tuần 4 của học kỳ" bị tách khỏi tiêu đề mục. Vai trò trong nhóm: đường cơ sở công bằng để đo xem ba chiến lược có cấu trúc kia thật sự hơn được bao nhiêu.
- **Code snippet (nếu custom):** không custom — dùng lớp có sẵn:

```python
FixedSizeChunker(chunk_size=400, overlap=80)
```

Kết quả: **94 chunk, avg 390,0** (min 84 / max 400).

**Thành viên 3 — Nguyễn Hữu Hoàng Anh**

- **Loại chiến lược:** `SentenceChunker` tinh chỉnh — `max_sentences_per_chunk=5`
- **Mô tả & lý do chọn:** Baseline dùng 3 câu/chunk tạo ra các chunk quá ngắn so với một mục quy định hoàn chỉnh, trong khi văn bản học vụ thường cần cả cụm "điều kiện → ngoại lệ → nơi nộp" mới trả lời trọn câu hỏi. Nâng lên 5 câu/chunk gom đủ ngữ cảnh mà vẫn cắt ở ranh giới câu, không bao giờ xé giữa câu như cắt theo độ dài. Đây là chiến lược cho chunk **dài nhất** trong nhóm nên dùng để kiểm chứng giả thuyết "chunk dài giữ ngữ cảnh tốt hơn nhưng làm loãng embedding".
- **Code snippet (nếu custom):** không custom — dùng lớp có sẵn:

```python
SentenceChunker(max_sentences_per_chunk=5)
```

Kết quả: **43 chunk, avg 685,5** (min 246 / max 1.331). Độ lệch min-max lớn nhất nhóm, do nhiều dòng trong corpus kết thúc bằng dấu hai chấm nên bộ tách câu không nhận ra ranh giới.

**Thành viên 4 — Nguyễn Cao Nam**

- **Loại chiến lược:** `RecursiveChunker` tinh chỉnh — `chunk_size=500`
- **Mô tả & lý do chọn:** Baseline `chunk_size=200` cho kết quả tệ nhất (215 chunk, avg 136,0) vì corpus dày gạch đầu dòng: thuật toán gặp separator `"\n\n"` liên tục và tách mỗi gạch đầu dòng thành một chunk rời rạc. Nâng ngưỡng lên 500 khiến nhiều gạch đầu dòng liên tiếp được gộp lại trước khi chạm giới hạn, nên các bước trong cùng một quy trình nằm chung một chunk. Đây là phép thử trực tiếp cho câu hỏi: `RecursiveChunker` thua ở baseline là do thuật toán sai hay chỉ do tham số đặt quá nhỏ?
- **Code snippet (nếu custom):** không custom — dùng lớp có sẵn:

```python
RecursiveChunker(chunk_size=500)
```

Kết quả: **81 chunk, avg 363,8** (min 65 / max 500) — giảm được 62% số chunk so với baseline `chunk_size=200`.

### So Sánh Giữa Các Thành Viên

| Thành viên            | Chiến lược (Strategy)                                      | Số chunk / avg | Điểm truy xuất (/10) | Điểm mạnh                                                                                                                        | Điểm yếu                                                                                                                 |
| ----------------------- | ------------------------------------------------------------- | --------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Nguyễn Phương Nam    | `SectionChunker` (custom, `max_chars=800, min_chars=120`) | 60 / 491,9      | **8**             | Chunk trùng khớp đơn vị FAQ; giữ điều kiện và ngoại lệ đi cùng nhau. Ít chunk nhất mà vẫn đạt điểm cao nhất. | Phụ thuộc việc nguồn đánh số mục đều đặn; corpus khác định dạng sẽ rơi hết về`RecursiveChunker`.      |
| Lương Trung Chiến    | `FixedSizeChunker` (`chunk_size=400, overlap=80`)         | 94 / 390,0      | **8**             | Độ dài chunk đồng đều nhất (min 84 / max 400), dễ dự đoán chi phí embedding; overlap cứu được câu bị cắt ngang. | Vẫn cắt giữa câu và giữa mục — ranh giới do đếm ký tự quyết định, không theo ngữ nghĩa.                  |
| Nguyễn Hữu Hoàng Anh | `SentenceChunker` (`max_sentences_per_chunk=5`)           | 43 / 685,5      | **8**             | Không bao giờ xé giữa câu; ít chunk nhất nên chi phí embedding thấp nhất.                                                | Chunk dài nhất và lệch nhất (min 246 / max 1.331) — một vector phải "gánh" quá nhiều ý, dễ loãng ngữ nghĩa. |
| Nguyễn Cao Nam         | `RecursiveChunker` (`chunk_size=500`)                     | 81 / 363,8      | **7**             | Tôn trọng ranh giới đoạn/dòng có sẵn; giảm 62% số chunk so với baseline 200.                                             | Chunk ngắn và rời rạc nhất → là chiến lược duy nhất tuột hạng ở câu 5 (xem mục 3).                          |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> Ba chiến lược đầu **hòa nhau ở 8/10**, `RecursiveChunker` kém hơn đúng 1 điểm — nghĩa là với corpus này, cách chunking gần như **không quyết định** kết quả: cả bốn cùng đúng ở câu 1, 3, 4 và cùng sai ở câu 2. Nếu phải chọn, nhóm chọn `SectionChunker` vì nó đạt điểm cao nhất với **ít chunk nhất (60 so với 94)** — cùng chất lượng truy xuất nhưng rẻ hơn 36% chi phí embedding và lưu trữ, đồng thời mỗi chunk trả về là một mục FAQ đọc được trọn vẹn nên câu trả lời của agent có ngữ cảnh sạch hơn.
>
> Điều đáng nói hơn con số: khác biệt giữa các chiến lược (1 điểm) nhỏ hơn nhiều so với khác biệt do **cách đặt câu hỏi** gây ra. Cùng chiến lược `SectionChunker`, câu 2 hỏi "Hạn chót nộp 100% học phí học kỳ 1 và học kỳ 2" cho 0/2, nhưng diễn đạt lại theo đúng từ ngữ tài liệu ("Thời gian nộp học phí HK1 HK2") thì chunk đúng nhảy từ hạng 9 (0,5283) lên hạng 1 với **0,8831**. Tinh chỉnh chunking không cứu được vấn đề đó.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query)                                                                                                          | Câu trả lời chuẩn (Gold Answer)                                                                                                                                                                                                                                   | Chunk nào chứa thông tin?                                                 |
| - | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1 | Rút môn học thì nhận điểm gì và có phải đóng học phí cho môn đó không?                                  | Nhận**điểm R (điểm 17)**. Sinh viên vẫn **phải nộp đủ học phí**, kể cả môn nhận điểm R. Môn được rút không tính vào bảng điểm nhưng vẫn tính học phí.                                                                  | `course-withdrawal`, mục 1 "Điều kiện Rút môn học"                  |
| 2 | Hạn chót nộp 100% học phí học kỳ 1 và học kỳ 2 là khi nào?                                                     | **Kết thúc ở tuần 4 của học kỳ**, thời gian thanh toán trong 1 tuần; tuần học tính theo biểu đồ năm học.                                                                                                                                      | `tuition-fees`, mục 2 "Thời gian nộp học phí"                         |
| 3 | Các học phần tốt nghiệp được xếp loại ĐẠT khi đạt mức điểm nào?                                          | Chỉ được xếp ĐẠT khi có điểm đánh giá**từ mức C trở lên (từ 5,5 theo thang điểm 10)**. Áp dụng cho Thực tập ngoài trường, Đồ án chuyên ngành, Khóa luận tốt nghiệp.                                                         | `conduct-grading`, mục 4 "Điểm đạt của các học phần tốt nghiệp" |
| 4 | Sinh viên được kéo dài thời gian đào tạo tối đa bao nhiêu học kỳ?                                           | Hiệu trưởng xem xét kéo dài**tối đa 01 học kỳ chính** với sinh viên chính quy, **tối đa 02 học kỳ chính** với sinh viên vừa làm vừa học (khóa 2021 về sau); mỗi sinh viên chỉ được xét **không quá một lần**. | `extended-study-duration`                                                  |
| 5 | **(cần lọc metadata)** Muốn học ngành thứ hai thì nộp đơn ở đâu và cần điều kiện gì trước đó? | Phải**hoàn thành học phần tốt nghiệp của ngành thứ nhất**, sau đó nộp đơn tại **PHÒNG ĐÀO TẠO**, đơn có **xác nhận của Trưởng Khoa quản lý ngành thứ 2** (nên tư vấn với Trưởng Khoa trước khi nộp).      | `double-major`, mục 1 "Quy trình"                                        |

**Vì sao câu 5 cần lọc metadata:** cụm "nộp đơn" còn xuất hiện trong `tuition-fees` ("nộp đơn tại P. Công tác Sinh viên" để xin vay/miễn/giảm học phí), còn "học phần tốt nghiệp" lại là chủ đề chính của `conduct-grading`. Truy vấn thuần ngữ nghĩa dễ kéo nhầm hai văn bản đó lên đầu. Gọi `search_with_filter(query, {"category": "double-major"})` khoanh đúng văn bản trước khi xếp hạng.

Bộ câu hỏi phủ 5/6 tài liệu và bốn dạng khác nhau: hệ quả của một hành động (1), mốc thời hạn (2), ngưỡng điểm số (3), giới hạn định lượng theo đối tượng (4), quy trình + nơi nộp hồ sơ (5).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

Chạy bằng `python scripts/run_benchmark.py` với `EMBEDDING_PROVIDER=local` (mô hình `paraphrase-multilingual-MiniLM-L12-v2`), `top_k=3`, trên cả bốn chiến lược của nhóm.

| # | Câu hỏi                            | Chiến lược tốt nhất cho câu này                              | Có chunk liên quan trong top-3?                                 | Ghi chú                                                                                                                      |
| - | ------------------------------------ | ------------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1 | Rút môn học nhận điểm gì      | Cả 4 (hòa, 2/2)                                                   | Có — top-1 đúng ở cả 4                                      | Từ khóa "rút môn học" là duy nhất trong corpus, không chiến lược nào sai được.                                 |
| 2 | Hạn nộp 100% học phí             | **Không chiến lược nào (0/2 ở cả 4)**                  | **Không**                                                  | Lỗi chung của cả nhóm — phân tích ở mục 4. Chunk đúng chỉ xếp hạng 9 (0,5283) trong khi top-1 sai đạt 0,5698. |
| 3 | Điểm đạt học phần tốt nghiệp | Cả 4 (hòa, 2/2)                                                   | Có — top-1 đúng ở cả 4                                      | Cụm "học phần tốt nghiệp" xuất hiện nguyên văn trong tài liệu.                                                     |
| 4 | Kéo dài thời gian đào tạo      | Cả 4 (hòa, 2/2)                                                   | Có — top-1 đúng ở cả 4                                      | Tên tài liệu trùng gần như nguyên văn với câu hỏi.                                                                 |
| 5 | Nộp đơn học ngành thứ hai      | `SectionChunker`, `FixedSizeChunker`, `SentenceChunker` (2/2) | Có ở cả 4, nhưng`RecursiveChunker` chỉ đạt hạng 3 (1/2) | **Lọc metadata kéo `RecursiveChunker` từ 1/2 lên 2/2.**                                                           |

**Tổng điểm:** `SectionChunker` 8/10 · `FixedSizeChunker` 8/10 · `SentenceChunker` 8/10 · `RecursiveChunker` 7/10.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có, và đo được chính xác ở **câu 5**. Không lọc, `RecursiveChunker` xếp `course-registration` (0,5904) và `extended-study-duration` (0,5126) lên trên chunk đúng của `double-major` (0,5109) — chỉ được 1/2 điểm. Thêm `search_with_filter(query, metadata_filter={"category": "double-major"})` thì chunk đúng lên top-1 và đạt 2/2.
>
> Nhưng cần nói thẳng: với ba chiến lược còn lại, lọc metadata **không thay đổi gì** vì chúng vốn đã đúng top-1. Lọc metadata ở đây đóng vai trò *lưới an toàn* cho chiến lược chunking yếu hơn, chứ không phải thứ nâng trần chất lượng. Và nó chỉ hoạt động nhờ `category` có giá trị phân biệt từng tài liệu — bốn trường đồng nhất (`audience`, `department`, `language`, `license_or_permission`) hoàn toàn vô dụng khi lọc.
>
> Hạn chế của phép đo này: bộ lọc được đặt thủ công theo câu hỏi. Trong hệ thống thật, agent phải tự suy ra `category` từ câu hỏi của người dùng — đó là một bài toán phân loại riêng mà lab này chưa động tới.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> 1. **Làm sạch dữ liệu ăn đứt việc chỉnh tham số chunking.** Footer lặp lại của BKSI chiếm 44-64% nội dung bốn tài liệu ngắn. Giữ nguyên thì mọi chiến lược đều sinh ra một nhóm chunk gần trùng nhau giữa các văn bản khác nhau — nhiễu này không có giá trị `chunk_size` nào cứu được.
> 2. **"Đệ quy" không đồng nghĩa với "thông minh hơn".** Trên corpus nhiều gạch đầu dòng, `RecursiveChunker` cắt vụn hơn cả `FixedSizeChunker` (215 vs 151 chunk ở baseline), và sau khi tinh chỉnh vẫn là chiến lược duy nhất tuột điểm ở câu 5 (7/10 so với 8/10). Chiến lược tốt nhất phụ thuộc vào *cấu trúc* văn bản, không phải độ tinh vi của thuật toán.
> 3. **Metadata chỉ đáng giá khi nó phân biệt được.** Nhóm gán 9 trường nhưng 4 trường (`audience`, `department`, `language`, `license_or_permission`) đồng nhất trên cả 6 tài liệu nên vô dụng khi lọc; chỉ `category` và `document_type` thực sự thu hẹp được không gian tìm kiếm.

**Bài học rút ra khi so sánh trong nhóm:**

> Bốn chiến lược rất khác nhau về hình dạng chunk (43 đến 94 chunk, avg 363,8 đến 685,5) nhưng chỉ chênh nhau **1 điểm** trên bộ benchmark, và **sai giống hệt nhau** ở câu 2. Kết luận ngược với kỳ vọng ban đầu của nhóm: trên corpus nhỏ và đã được làm sạch, chọn chiến lược chunking nào gần như không quyết định chất lượng truy xuất. Cái quyết định là (1) dữ liệu có sạch boilerplate không, và (2) từ ngữ câu hỏi có khớp với từ ngữ tài liệu không.
>
> Vì vậy tiêu chí chọn của nhóm chuyển từ "chiến lược nào truy xuất tốt hơn" sang "chiến lược nào đạt cùng chất lượng với chi phí thấp nhất và chunk đọc được nhất" — `SectionChunker` thắng ở tiêu chí đó (60 chunk so với 94 của `FixedSizeChunker`).

### Phân tích lỗi (Failure Analysis — Bài tập 3.5)

**Câu hỏi thất bại:** Câu 2 — *"Hạn chót nộp 100% học phí học kỳ 1 và học kỳ 2 là khi nào?"*. Cả **4/4 chiến lược đều 0/2 điểm**: không chiến lược nào đưa được `tuition-fees` vào top-3.

**Hệ thống trả về gì thay vào đó:** ba chunk của `conduct-grading` và `course-registration` nói về điểm số và chuẩn sinh viên, với score 0,5584-0,5698. Chunk đúng — mục "2. Thời gian nộp học phí" chứa nguyên văn *"100% học phí: Kết thúc ở tuần 4 của học kỳ"* — chỉ xếp **hạng 9 với 0,5283**.

**Tại sao:**

1. **Lệch vốn từ vựng, không phải lỗi chunking.** Câu hỏi dùng "hạn chót", "học kỳ 1 và học kỳ 2"; tài liệu viết "Thời gian nộp học phí", "HK1 và HK2". Mô hình `paraphrase-multilingual-MiniLM-L12-v2` không nối được viết tắt "HK1" với "học kỳ 1". Bằng chứng: giữ nguyên corpus và chiến lược, chỉ đổi câu hỏi thành *"Thời gian nộp học phí HK1 HK2"* thì chunk đúng lên top-1 với **0,8831** — cao hơn 0,35 so với lần chạy thất bại.
2. **Phổ điểm bị nén.** Chênh lệch giữa top-1 sai (0,5698) và chunk đúng ở hạng 9 (0,5283) chỉ là **0,0415**. Mô hình thấy mọi văn bản hành chính-học vụ tiếng Việt đều "hơi giống nhau", nên nhiễu nhỏ cũng đủ đảo thứ hạng. Đây là lý do chunking không cứu được: chunk đúng vẫn nằm đó, chỉ là không nổi lên nổi.
3. **Không phải do chunk quá to hay quá nhỏ.** Bốn chiến lược có avg từ 363,8 đến 685,5 ký tự và đều sai — nếu nguyên nhân là kích thước chunk thì ít nhất một chiến lược đã phải đúng.

**Đề xuất cải thiện, theo thứ tự đáng làm trước:**

1. **Chuẩn hóa viết tắt khi ingest** — bung "HK1" → "HK1 (học kỳ 1)", "SV" → "SV (sinh viên)", "LVTN" → "LVTN (luận văn tốt nghiệp)". Rẻ nhất, đánh trúng nguyên nhân số 1, và có lợi cho mọi câu hỏi chứ không riêng câu 2.
2. **Kết hợp tìm kiếm từ khóa với vector (hybrid search)** — BM25 sẽ bắt được cụm chính xác "100% học phí" mà embedding bỏ lỡ, rồi hợp nhất hai bảng xếp hạng. Xử lý được cả nguyên nhân số 2.
3. **Nhúng thêm tiêu đề tài liệu vào từng chunk** — mọi chunk của `tuition-fees` mang sẵn chuỗi "Học phí" sẽ được điểm cộng khi câu hỏi nhắc tới học phí. `SectionChunker` với `min_chars` đã làm điều này cho chunk đầu tiên; nên áp dụng cho tất cả.
4. **Dùng mô hình embedding mạnh hơn cho tiếng Việt** (ví dụ `vietnamese-sbert`, hoặc `multilingual-e5-base`) để giãn phổ điểm — tốn kém nhất nên để sau cùng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> 1. Chọn nguồn có công bố ngày hiệu lực để `document_version` không phải ghi `not-stated` cho cả 6 tài liệu — hiện nhóm không có cách nào kiểm chứng quy định còn hiệu lực hay không.
> 2. Thiết kế `audience` với giá trị thật sự phân hóa (thêm tài liệu cho `faculty`/`staff`, hoặc tách chính quy / vừa làm vừa học), vì đây là trường K3 bắt buộc mà nhóm lại để đồng nhất.
> 3. Cân bằng độ dài tài liệu: `course-registration` (15.444 ký tự) dài gấp 18 lần `double-major` (859 ký tự), khiến số chunk dồn hẳn về một văn bản và làm lệch xếp hạng truy xuất.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                   | Điểm tự đánh giá |
| -------------------------------------------- | ---------------------- |
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10                |
| Thiết kế chiến lược (Strategy Design)   | 14 / 15                |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10                 |
| Thuyết trình (Demo)                        | 5 / 5                  |
| **Tổng phần nhóm**                  | **37 / 40**      |

Căn cứ tự chấm: **Lựa chọn tài liệu 10/10** — 6 tài liệu công khai đúng chủ đề K3, đủ 5 trường metadata bắt buộc cộng 4 trường mở rộng, `sources.csv` khớp 1-1, đã cắt boilerplate và ghi rõ hạn chế `document_version: not-stated`. **Thiết kế chiến lược 14/15** — bốn chiến lược thật sự khác nhau kèm lý do bám vào đặc điểm corpus, có một chiến lược custom, và kết luận dựa trên số đo chứ không phỏng đoán; trừ 1 điểm vì các tham số (`max_chars=800`, `chunk_size=400/500`) chọn theo suy luận từ độ dài mục trung bình chứ chưa quét thử nhiều giá trị. **Chất lượng truy xuất 8/10** — đúng theo điểm benchmark đo được của chiến lược tốt nhất; 2 điểm mất ở câu 2 là thật và nhóm đã phân tích nguyên nhân thay vì đổi câu hỏi cho dễ. **Thuyết trình 5/5** — có ba insight ngược trực giác kèm số liệu chứng minh và một phân tích lỗi truy được tới tận nguyên nhân gốc.
