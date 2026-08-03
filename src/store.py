from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        embedding = self._embedding_fn(doc.content)
        # Gắn doc_id vào metadata để phục vụ delete_document và search_with_filter
        metadata = dict(doc.metadata)
        metadata["doc_id"] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if not records:
            return []

        query_vec = self._embedding_fn(query)

        # Tính dot product (embeddings đã được normalize nên dot ≈ cosine similarity)
        scored = []
        for record in records:
            score = _dot(query_vec, record["embedding"])
            scored.append({
                "content": record["content"],
                "score": score,
                "metadata": record["metadata"],
                "id": record["id"],
            })

        # Sắp xếp giảm dần theo score
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        if self._use_chroma and self._collection is not None:
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            for doc in docs:
                record = self._make_record(doc)
                ids.append(f"{doc.id}_{self._next_index}")
                self._next_index += 1
                documents.append(record["content"])
                embeddings.append(record["embedding"])
                metadatas.append(record["metadata"])
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_vec = self._embedding_fn(query)
            n_results = min(top_k, self._collection.count())
            if n_results == 0:
                return []
            chroma_results = self._collection.query(
                query_embeddings=[query_vec],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
            results = []
            for i, doc_content in enumerate(chroma_results["documents"][0]):
                # ChromaDB trả distances (L2), chuyển sang score = 1 - distance
                distance = chroma_results["distances"][0][i]
                results.append({
                    "content": doc_content,
                    "score": 1.0 - distance,
                    "metadata": chroma_results["metadatas"][0][i],
                })
            return results
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            query_vec = self._embedding_fn(query)
            total = self._collection.count()
            if total == 0:
                return []
            # ChromaDB hỗ trợ where filter
            try:
                chroma_results = self._collection.query(
                    query_embeddings=[query_vec],
                    n_results=min(top_k, total),
                    where=metadata_filter,
                    include=["documents", "metadatas", "distances"],
                )
                results = []
                for i, doc_content in enumerate(chroma_results["documents"][0]):
                    distance = chroma_results["distances"][0][i]
                    results.append({
                        "content": doc_content,
                        "score": 1.0 - distance,
                        "metadata": chroma_results["metadatas"][0][i],
                    })
                return results
            except Exception:
                pass

        # In-memory: lọc trước theo metadata, rồi tìm kiếm
        filtered = [
            record for record in self._store
            if all(record["metadata"].get(k) == v for k, v in metadata_filter.items())
        ]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            # Tìm và xóa tất cả chunks có doc_id trong metadata
            try:
                existing = self._collection.get(where={"doc_id": doc_id})
                if existing and existing["ids"]:
                    self._collection.delete(ids=existing["ids"])
                    return True
                return False
            except Exception:
                pass

        # In-memory
        before = len(self._store)
        self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id]
        after = len(self._store)
        return after < before
