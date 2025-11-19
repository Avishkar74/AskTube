from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np

try:
    import faiss  # type: ignore
except Exception as e:  # noqa: BLE001
    raise RuntimeError("faiss-cpu must be installed in backend env") from e

_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _normalize(v: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    return v / norms


def _chunk_text(text: str, chunk_chars: int = 800) -> List[Dict[str, object]]:
    if not text:
        return []
    chunks: List[Dict[str, object]] = []
    start_idx = 0
    n = len(text)
    while start_idx < n:
        end_idx = min(start_idx + chunk_chars, n)
        chunk_text = text[start_idx:end_idx].strip()
        if chunk_text:
            chunks.append({"text": chunk_text, "start": None, "end": None})
        if end_idx == n:
            break
        start_idx = end_idx
    return chunks


def _chunk_segments(segments: List[Dict], chunk_chars: int = 800) -> List[Dict[str, object]]:
    chunks: List[Dict[str, object]] = []
    acc_text: List[str] = []
    acc_len = 0
    current_start: Optional[float] = None
    last_end: Optional[float] = None
    for seg in segments:
        seg_text = (seg.get("text") or "").strip()
        if not seg_text:
            continue
        seg_start = float(seg.get("start") or 0.0)
        seg_dur = float(seg.get("duration") or 0.0)
        seg_end = seg_start + seg_dur
        if current_start is None:
            current_start = seg_start
        # If adding this segment exceeds chunk size, flush current chunk
        if acc_len + len(seg_text) + (1 if acc_text else 0) > chunk_chars and acc_text:
            chunks.append({
                "text": " ".join(acc_text).strip(),
                "start": current_start,
                "end": last_end,
            })
            acc_text = []
            acc_len = 0
            current_start = seg_start
        # Append segment
        acc_text.append(seg_text)
        acc_len += len(seg_text) + (1 if acc_text else 0)
        last_end = seg_end
    # Flush remaining
    if acc_text:
        chunks.append({
            "text": " ".join(acc_text).strip(),
            "start": current_start,
            "end": last_end,
        })
    return chunks


def _paths(base_dir: Path, video_id: str) -> Tuple[Path, Path]:
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / f"{video_id}.index", base_dir / f"{video_id}.meta.json"


def build_index(
    video_id: str,
    transcript_text: Optional[str] = None,
    transcript_segments: Optional[List[Dict]] = None,
    base_dir: Optional[Path] = None,
) -> None:
    base_dir = base_dir or Path(__file__).resolve().parents[3] / "backend_data" / "faiss"
    index_path, meta_path = _paths(base_dir, video_id)

    # Prefer segment-aware chunking when available
    if transcript_segments:
        chunk_objects = _chunk_segments(transcript_segments)
    else:
        chunk_objects = _chunk_text(transcript_text or "")

    chunks = [c.get("text", "") for c in chunk_objects]
    if not chunks:
        raise ValueError("No transcript content to index")

    model = _get_model()
    emb = model.encode(chunks, convert_to_numpy=True)
    emb = _normalize(emb.astype("float32"))

    d = emb.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(emb)
    faiss.write_index(index, str(index_path))

    # Persist text with timing (if any)
    meta_chunks = []
    for c in chunk_objects:
        meta_chunks.append({
            "text": c.get("text"),
            "start": c.get("start"),
            "end": c.get("end"),
        })
    meta = {"video_id": video_id, "chunks": meta_chunks}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def has_index(video_id: str, base_dir: Optional[Path] = None) -> bool:
    base_dir = base_dir or Path(__file__).resolve().parents[3] / "backend_data" / "faiss"
    index_path, meta_path = _paths(base_dir, video_id)
    return index_path.exists() and meta_path.exists()


def retrieve(video_id: str, query: str, top_k: int = 5, base_dir: Optional[Path] = None) -> List[Dict[str, object]]:
    base_dir = base_dir or Path(__file__).resolve().parents[3] / "backend_data" / "faiss"
    index_path, meta_path = _paths(base_dir, video_id)
    if not index_path.exists() or not meta_path.exists():
        return []

    index = faiss.read_index(str(index_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    raw_chunks = meta.get("chunks", [])
    # Support both string-only and dict chunks
    if raw_chunks and isinstance(raw_chunks[0], dict):
        chunks_text = [c.get("text", "") for c in raw_chunks]
    else:
        chunks_text = list(raw_chunks)
    if not chunks_text:
        return []

    model = _get_model()
    q = model.encode([query], convert_to_numpy=True)
    q = _normalize(q.astype("float32"))

    k = min(top_k, len(chunks_text))
    D, I = index.search(q, k=k)
    inds = I[0].tolist()
    scores = D[0].tolist()
    results: List[Dict[str, object]] = []
    for rank, idx in enumerate(inds):
        if 0 <= idx < len(chunks_text):
            start = None
            end = None
            if raw_chunks and isinstance(raw_chunks[0], dict):
                start = raw_chunks[idx].get("start")
                end = raw_chunks[idx].get("end")
            results.append({
                "text": chunks_text[idx],
                "score": float(scores[rank]) if rank < len(scores) else None,
                "chunk_index": int(idx),
                "start_sec": start,
                "end_sec": end,
            })
    return results


def get_index_stats(video_id: str, base_dir: Optional[Path] = None) -> Dict[str, int]:
    """Return simple stats for an index: currently chunk_count only.

    If no index exists, returns {"chunk_count": 0}.
    """
    base_dir = base_dir or Path(__file__).resolve().parents[3] / "backend_data" / "faiss"
    index_path, meta_path = _paths(base_dir, video_id)
    if not index_path.exists() or not meta_path.exists():
        return {"chunk_count": 0}
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        chunks = meta.get("chunks", [])
        return {"chunk_count": len(chunks)}
    except Exception:
        return {"chunk_count": 0}


def retrieve_by_timestamp(video_id: str, time_sec: float, window: int = 0, base_dir: Optional[Path] = None) -> List[Dict[str, object]]:
    """Retrieve chunk(s) closest to or containing the given timestamp.

    window: number of neighboring chunks to include on each side.
    """
    base_dir = base_dir or Path(__file__).resolve().parents[3] / "backend_data" / "faiss"
    index_path, meta_path = _paths(base_dir, video_id)
    if not index_path.exists() or not meta_path.exists():
        return []
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    raw_chunks = meta.get("chunks", [])
    if not raw_chunks:
        return []
    # Normalize to dict chunks with text/start/end
    chunks = []
    for c in raw_chunks:
        if isinstance(c, dict):
            chunks.append({
                "text": c.get("text"),
                "start": c.get("start"),
                "end": c.get("end"),
            })
        else:
            chunks.append({"text": c, "start": None, "end": None})
    # Find chunk containing or nearest to time_sec
    def contains(i: int) -> bool:
        s = chunks[i].get("start")
        e = chunks[i].get("end")
        return s is not None and e is not None and s <= time_sec <= e

    idx = None
    for i in range(len(chunks)):
        if contains(i):
            idx = i
            break
    if idx is None:
        # choose nearest by start time
        best_i = None
        best_delta = 1e9
        for i, ch in enumerate(chunks):
            s = ch.get("start")
            if s is None:
                continue
            delta = abs(s - time_sec)
            if delta < best_delta:
                best_delta = delta
                best_i = i
        if best_i is None:
            return []
        idx = best_i
    # Collect with window neighbors
    start_i = max(0, idx - window)
    end_i = min(len(chunks) - 1, idx + window)
    out: List[Dict[str, object]] = []
    for j in range(start_i, end_i + 1):
        ch = chunks[j]
        out.append({
            "text": ch.get("text"),
            "score": None,
            "chunk_index": j,
            "start_sec": ch.get("start"),
            "end_sec": ch.get("end"),
        })
    return out


def get_chunks(video_id: str, base_dir: Optional[Path] = None) -> List[Dict[str, object]]:
    """Return all RAG chunks for a video with their indices and times (if present)."""
    base_dir = base_dir or Path(__file__).resolve().parents[3] / "backend_data" / "faiss"
    index_path, meta_path = _paths(base_dir, video_id)
    if not index_path.exists() or not meta_path.exists():
        return []
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        raw_chunks = meta.get("chunks", [])
        out: List[Dict[str, object]] = []
        for i, c in enumerate(raw_chunks):
            if isinstance(c, dict):
                out.append({
                    "text": c.get("text"),
                    "start_sec": c.get("start"),
                    "end_sec": c.get("end"),
                    "chunk_index": i,
                })
            else:
                out.append({
                    "text": c,
                    "start_sec": None,
                    "end_sec": None,
                    "chunk_index": i,
                })
        return out
    except Exception:
        return []
