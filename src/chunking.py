from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Tách câu theo các dấu kết thúc câu phổ biến
        # Dùng re.split với lookbehind để giữ lại dấu câu
        sentence_pattern = r'(?<=[.!?])\s+|(?<=\.)\n'
        raw_sentences = re.split(sentence_pattern, text)

        # Lọc bỏ các phần tử rỗng, strip whitespace
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        if not sentences:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = " ".join(group).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\\n\\n", "\\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Nếu không có separators nào được cung cấp, dùng FixedSizeChunker làm fallback
        if not self.separators:
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(text)
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Nếu text vừa với chunk_size, trả về luôn
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text.strip() else []

        # Nếu hết separator, trả về text nguyên
        if not remaining_separators:
            return [current_text]

        sep = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Nếu separator là chuỗi rỗng (""), chia theo từng ký tự / dùng fixed chunker
        if sep == "":
            return FixedSizeChunker(chunk_size=self.chunk_size, overlap=0).chunk(current_text)

        # Thử tách bằng separator hiện tại
        if sep in current_text:
            parts = current_text.split(sep)
        else:
            # Separator không có trong text, thử separator tiếp theo
            return self._split(current_text, next_separators)

        chunks: list[str] = []
        current_group = ""

        for part in parts:
            # Nếu part rỗng thì bỏ qua
            if not part:
                continue

            candidate = (current_group + sep + part).lstrip(sep) if current_group else part

            if len(candidate) <= self.chunk_size:
                current_group = candidate
            else:
                # Lưu group hiện tại nếu có
                if current_group:
                    chunks.append(current_group)
                    current_group = ""

                # Part này có thể vẫn quá dài → đệ quy với separator tiếp theo
                if len(part) > self.chunk_size:
                    sub_chunks = self._split(part, next_separators)
                    chunks.extend(sub_chunks)
                else:
                    current_group = part

        # Phần còn lại
        if current_group:
            chunks.append(current_group)

        return [c for c in chunks if c.strip()]


class SectionChunker:
    """
    Split text on the numbered-section headings used by the BKSI corpus.

    Lý do thiết kế: mỗi trang BKSI là một FAQ gồm các mục đánh số ("1. Thanh
    toán học phí", "2. Thời gian nộp học phí"), mỗi mục trả lời trọn một câu
    hỏi. Cắt đúng ranh giới mục giữ nguyên cặp "tiêu đề mục + điều kiện + ngoại
    lệ" trong cùng một chunk, thay vì xé giữa câu như cắt theo độ dài cố định.

    Mục dài hơn max_chars được giao lại cho RecursiveChunker để không tạo ra
    chunk quá lớn làm loãng embedding.
    """

    # "1. Thanh toán học phí", "2- Quy định", "Bước 1)" hoặc tiêu đề markdown.
    SECTION_PATTERN = re.compile(r"^(?:#{1,6}\s|\d+\s*[.)-]\s|Bước\s+\d+\s*[.)])", re.M)

    def __init__(self, max_chars: int = 800, min_chars: int = 120) -> None:
        self.max_chars = max_chars
        self.min_chars = min_chars

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
        # Mục quá ngắn (thường chỉ là dòng tiêu đề) được dồn sang mục kế tiếp:
        # embedding của một chunk 9 ký tự không mang thông tin nào để truy xuất.
        pending = ""
        for section in sections:
            if not section:
                continue
            section = f"{pending}\n\n{section}" if pending else section
            pending = ""

            if len(section) < self.min_chars:
                pending = section
            elif len(section) <= self.max_chars:
                chunks.append(section)
            else:
                chunks.extend(RecursiveChunker(chunk_size=self.max_chars).chunk(section))

        if pending:
            # Mục ngắn cuối cùng không có gì phía sau để gộp: nối vào chunk trước.
            if chunks:
                chunks[-1] = f"{chunks[-1]}\n\n{pending}"
            else:
                chunks.append(pending)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))

    # Bảo vệ chia cho 0
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        result = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = (sum(len(c) for c in chunks) / count) if count > 0 else 0.0
            result[name] = {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }

        return result
