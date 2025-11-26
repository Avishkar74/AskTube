from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None  # type: ignore

from config import settings


@dataclass
class SearchResult:
    index: int
    score: float
    metadata: Dict


class FaissVectorStore:
    def __init__(self, dim: int, index_path: str | None = None, metadata_path: str | None = None):
        self.dim = dim
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        # Align with config Settings: FAISS_META_PATH
        self.metadata_path = metadata_path or settings.FAISS_META_PATH
        self.index: "faiss.IndexFlatIP | None" = None
        self.metadata: List[Dict] = []

    def _new_index(self) -> faiss.IndexFlatIP:
        self._require_faiss()
        # Inner product index; embeddings are normalized at creation for cosine similarity
        return faiss.IndexFlatIP(self.dim)

    def load(self) -> None:
        self._require_faiss()
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = self._new_index()

        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = []

    def save(self) -> None:
        if self.index is None:
            return
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def reset(self) -> None:
        self.index = self._new_index()
        self.metadata = []

    def add(self, vectors: List[List[float]], metadatas: List[Dict]) -> None:
        import numpy as np  # local import to avoid global hard dep in tests

        if self.index is None:
            self.load()

        # Ensure shapes
        arr = np.array(vectors, dtype="float32")
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dim}, got {arr.shape}")

        # FAISS IP expects normalized vectors for cosine similarity; embeddings are already normalized in wrapper
        self.index.add(arr)
        self.metadata.extend(metadatas)

    def search(self, query_vector: List[float], top_k: int) -> List[SearchResult]:
        import numpy as np

        if self.index is None:
            self.load()

        q = np.array([query_vector], dtype="float32")
        scores, idxs = self.index.search(q, top_k)
        results: List[SearchResult] = []
        for i, score in zip(idxs[0], scores[0]):
            if i == -1:
                continue
            md = self.metadata[i] if i < len(self.metadata) else {}
            results.append(SearchResult(index=int(i), score=float(score), metadata=md))
        return results

    def _require_faiss(self) -> None:
        if faiss is None:  # pragma: no cover
            raise RuntimeError(
                "FAISS is required for RAG. Please install 'faiss-cpu' (CPU) or 'faiss-gpu'."
            )
