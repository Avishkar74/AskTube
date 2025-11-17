#!/usr/bin/env python3
"""
Minimal RAG chat prompt test using a fake backend to avoid LLM calls.
Builds a ConversationManager with use_rag=True and verifies the prompt
includes retrieved context chunks and citations.
"""
from pathlib import Path

from conversation_manager import ConversationManager
from rag_indexer import index_transcript


class FakeBackend:
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.3):
        self.last_prompt = prompt
        return "[fake-response]"


def main() -> int:
    # Ensure an indexed transcript exists
    video_id = "GuyZspG3-Po"
    transcript_file = Path("outputs") / f"{video_id}.txt"
    if not transcript_file.exists():
        print("[FAIL] Expected transcript file not found:", transcript_file)
        return 1

    text = transcript_file.read_text(encoding="utf-8")
    idx_res = index_transcript(video_id, text, force_reindex=False)
    if not (idx_res.get("indexed") or idx_res.get("skipped")):
        print("[FAIL] Indexing step failed:", idx_res)
        return 1

    # Build manager with fake backend and RAG enabled
    fake = FakeBackend()
    m = ConversationManager(backend=fake, use_rag=True)
    user_id = "rag_user"
    m.set_transcript(user_id, video_id, text)

    # Perform a chat call
    _ = m.chat(user_id, video_id, "What are the key points?")

    # Verify prompt contains context section and citations
    prompt = fake.last_prompt or ""
    has_context = "Context Chunks" in prompt
    has_citation = "[c" in prompt
    if has_context and has_citation:
        print("[PASS] RAG prompt includes context and citations")
        return 0
    else:
        print("[FAIL] RAG prompt missing context/citations")
        print(prompt[:500])
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
