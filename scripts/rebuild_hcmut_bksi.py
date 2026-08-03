#!/usr/bin/env python3
"""Rebuild the HCMUT BKSI corpus from a manifest CSV.

This helper reads a manifest with either a ``source_url`` or ``url`` column,
fetches each public page one by one, and writes one cleaned Markdown file per
document plus a fresh ``sources.csv`` manifest.

It is intentionally conservative:
- checks robots.txt before fetching
- waits between requests
- accepts only HTML/text pages
- keeps one output file per source row

Use it to regenerate ``data/hcmut_bksi`` into a new directory or to refresh the
existing corpus after the source pages change.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from fetch_public_pages import (
    build_metadata,
    existing_manifest,
    extract_content,
    fetch,
    markdown_document,
    robots_allowed,
    write_manifest,
)


def load_manifest_rows(path: Path) -> list[dict[str, str]]:
    """Load a CSV manifest that uses either ``source_url`` or ``url``."""
    with path.open(encoding="utf-8", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if not reader.fieldnames:
            raise ValueError("Input CSV must have headers.")

        rows: list[dict[str, str]] = []
        for number, row in enumerate(reader, start=2):
            cleaned = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            url = cleaned.get("source_url") or cleaned.get("url")
            if not url:
                print(f"Skipping row {number}: missing source_url/url", file=sys.stderr)
                continue
            cleaned["source_url"] = url
            rows.append(cleaned)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild the BKSI corpus from a CSV manifest.")
    parser.add_argument(
        "input_csv",
        type=Path,
        nargs="?",
        default=Path("data/hcmut_bksi/sources.csv"),
        help="Manifest CSV with source_url/url and optional metadata columns",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/hcmut_bksi_rebuilt"),
        help="Directory for generated .md files and a new sources.csv",
    )
    parser.add_argument("--delay", type=float, default=1.0, help="Minimum seconds between requests")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout in seconds")
    parser.add_argument(
        "--user-agent",
        default="Day7DataFoundationsCourse/1.0 (+educational-lab)",
        help="HTTP User-Agent",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace existing Markdown files")
    parser.add_argument(
        "--min-content-length",
        type=int,
        default=80,
        help="Minimum extracted content length before skipping a page",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.delay < 1:
        print("--delay must be at least 1 second to respect source websites.", file=sys.stderr)
        return 2
    if not args.input_csv.is_file():
        print(f"Input file not found: {args.input_csv}", file=sys.stderr)
        return 2

    try:
        rows = load_manifest_rows(args.input_csv)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "sources.csv"
    manifest = existing_manifest(manifest_path)
    successful = 0
    failed = 0

    for index, row in enumerate(rows):
        url = row["source_url"]
        if not robots_allowed(url, args.user_agent):
            failed += 1
            continue
        if index:
            time.sleep(args.delay)

        try:
            final_url, body, content_type = fetch(url, args.user_agent, args.timeout)
            title, content = extract_content(body, content_type)
            if len(content) < args.min_content_length:
                raise ValueError("extracted content is too short; use another source or clean it manually")

            metadata = build_metadata(row, final_url, title)
            source_name = Path(row.get("file_path", "")).name
            output_name = source_name if Path(source_name).suffix.lower() == ".md" else f"{metadata['doc_id']}.md"
            output_path = args.output_dir / output_name
            if output_path.exists() and not args.overwrite:
                raise FileExistsError(f"{output_path} exists (use --overwrite to replace it)")

            output_path.write_text(markdown_document(metadata, content), encoding="utf-8")
            manifest[metadata["doc_id"]] = {
                **metadata,
                "doc_id": metadata["doc_id"],
                "file_path": str(output_path),
                "license_or_permission": row.get("license_or_permission") or "public-source",
            }
            successful += 1
            print(f"Saved {output_path}")
        except (OSError, ValueError, TimeoutError) as error:
            failed += 1
            print(f"Skipping {url}: {error}", file=sys.stderr)

    write_manifest(manifest_path, manifest)
    print(f"Finished: {successful} saved, {failed} skipped. Manifest: {manifest_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
