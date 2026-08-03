#!/usr/bin/env python3
"""Chạy 5 benchmark query của nhóm trên từng chiến lược chunking.

Dùng cho Bài tập 3.4 (REPORT_NHOM.md mục 3 + REPORT_CANHAN.md mục 5).

    set EMBEDDING_PROVIDER=local        # Windows; bash: export EMBEDDING_PROVIDER=local
    python scripts/run_benchmark.py

Mặc định dùng embedder local đa ngữ. Mock embedder chỉ băm MD5 cả chuỗi nên
điểm gần như ngẫu nhiên — script sẽ cảnh báo nếu bạn lỡ chạy bằng mock.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import build_knowledge_base  # noqa: E402
from src.chunking import (  # noqa: E402
    FixedSizeChunker,
    RecursiveChunker,
    SectionChunker,
    SentenceChunker,
)

# Bộ câu hỏi nhóm thống nhất; doc_id kỳ vọng dùng để chấm tự động.
BENCHMARK = [
    ("Rút môn học thì nhận điểm gì và có phải đóng học phí cho môn đó không?", "course-withdrawal", None),
    ("Hạn chót nộp 100% học phí học kỳ 1 và học kỳ 2 là khi nào?", "tuition-fees", None),
    ("Các học phần tốt nghiệp được xếp loại ĐẠT khi đạt mức điểm nào?", "conduct-grading", None),
    ("Sinh viên được kéo dài thời gian đào tạo tối đa bao nhiêu học kỳ?", "extended-study-duration", None),
    (
        "Muốn học ngành thứ hai thì nộp đơn ở đâu và cần điều kiện gì trước đó?",
        "double-major",
        {"category": "double-major"},
    ),
]

# Mỗi thành viên một chiến lược khác nhau (Bài tập 3.1), chạy trên cùng corpus.
STRATEGIES = {
    "section (Nam)": lambda: SectionChunker(max_chars=800),
    "fixed_size (Chiến)": lambda: FixedSizeChunker(chunk_size=400, overlap=80),
    "by_sentences (Hoàng Anh)": lambda: SentenceChunker(max_sentences_per_chunk=5),
    "recursive (Cao Nam)": lambda: RecursiveChunker(chunk_size=500),
}


def get_embedder():
    """Trả về (embedding_fn, tên backend) theo biến môi trường EMBEDDING_PROVIDER."""
    provider = os.environ.get("EMBEDDING_PROVIDER", "mock").lower()
    if provider == "local":
        from src.embeddings import LocalEmbedder

        return LocalEmbedder(), "local"
    if provider == "openai":
        from src.embeddings import OpenAIEmbedder

        return OpenAIEmbedder(), "openai"

    from src.embeddings import MockEmbedder

    print(
        "CẢNH BÁO: đang dùng mock embedder — điểm gần như ngẫu nhiên, KHÔNG dùng\n"
        "         để kết luận chiến lược nào tốt hơn. Đặt EMBEDDING_PROVIDER=local.\n",
        file=sys.stderr,
    )
    return MockEmbedder(), "mock"


def score_query(results: list[dict], expected_doc_id: str) -> int:
    """Chấm theo docs/SCORING.md: 2 nếu top-1 đúng, 1 nếu trong top-3, 0 nếu không."""
    hits = [r["metadata"].get("doc_id") for r in results]
    if hits and hits[0] == expected_doc_id:
        return 2
    return 1 if expected_doc_id in hits[:3] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/hcmut_bksi", type=Path)
    parser.add_argument("--top-k", default=3, type=int)
    args = parser.parse_args()

    embedding_fn, backend = get_embedder()
    print(f"Embedder: {backend} | corpus: {args.data_dir} | top_k={args.top_k}\n")

    totals: dict[str, int] = {}
    for name, make_chunker in STRATEGIES.items():
        store = build_knowledge_base(args.data_dir, embedding_fn, chunker=make_chunker())
        print(f"{'=' * 78}\n{name}  ({store.get_collection_size()} chunks)\n{'=' * 78}")

        total = 0
        for index, (query, expected, filters) in enumerate(BENCHMARK, start=1):
            results = store.search(query, top_k=args.top_k)
            points = score_query(results, expected)
            total += points

            print(f"\n[{index}] {query}")
            print(f"    kỳ vọng: {expected}  ->  {points}/2 điểm")
            for rank, result in enumerate(results, start=1):
                snippet = " ".join(result["content"].split())[:70]
                mark = "*" if result["metadata"].get("doc_id") == expected else " "
                print(f"   {mark}{rank}. {result['metadata'].get('doc_id'):26} "
                      f"{result['score']:.4f}  {snippet}…")

            if filters:
                filtered = store.search_with_filter(query, top_k=args.top_k, metadata_filter=filters)
                filtered_points = score_query(filtered, expected)
                print(f"    + lọc metadata {filters}  ->  {filtered_points}/2 điểm")
                for rank, result in enumerate(filtered, start=1):
                    snippet = " ".join(result["content"].split())[:70]
                    print(f"    {rank}. {result['metadata'].get('doc_id'):26} "
                          f"{result['score']:.4f}  {snippet}…")

        totals[name] = total
        print(f"\n-> {name}: {total}/10 điểm\n")

    print("=" * 78)
    for name, total in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        print(f"{name:14} {total:2}/10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
