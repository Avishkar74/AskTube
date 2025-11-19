"""
Conversation memory manager for chat functionality.

Refactored to use generic LLM backend abstraction (`llm_backend.get_backend`) so
both local Ollama models and cloud Gemini can be used uniformly.

Features:
 - Persistent JSON file conversation history
 - Transcript association per (user, video)
 - Backend-agnostic prompt construction (single string prompt)
 - Optional conversation summarization hook (future extension)
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from llm_backend import get_backend, LLMBackend
from config import settings
from rag_embeddings import embed_query, get_embedding_model
from rag_faiss_store import FaissVectorStore


class ConversationManager:
    """Manages conversations with persistent history using a chosen LLM backend."""

    def __init__(
        self,
        storage_dir: str = "conversations",
        max_history: int = 10,
        backend_type: str = "ollama",
        model: Optional[str] = None,
        backend: Optional[LLMBackend] = None,
        temperature: float = 0.3,
        max_output_tokens: int = 512,
        use_rag: Optional[bool] = None,
    ):
        """Initialize conversation manager.

        Args:
            storage_dir: Directory to store conversation files
            max_history: Max messages (user+assistant pairs * 2) retained strictly
            backend_type: 'ollama' or 'gemini'
            model: Optional model name (uses backend defaults if None)
            backend: Optional pre-instantiated backend (primarily for testing)
            temperature: Generation temperature for responses
            max_output_tokens: Max tokens for assistant response
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        self.backend_type = backend_type.lower()
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.use_rag = settings.USE_RAG if use_rag is None else use_rag

        # Allow injection for tests; otherwise construct backend
        self.backend = backend if backend is not None else get_backend(self.backend_type, self.model)

    def _get_conversation_path(self, user_id: str, video_id: str) -> Path:
        """Get path to conversation file."""
        filename = f"{user_id}_{video_id}.json"
        return self.storage_dir / filename

    def load_conversation(
        self, user_id: str, video_id: str
    ) -> Dict[str, Any]:
        """Load conversation history from storage.

        Args:
            user_id: User identifier
            video_id: Video identifier

        Returns:
            Conversation data with messages and metadata
        """
        conv_path = self._get_conversation_path(user_id, video_id)

        if not conv_path.exists():
            return {
                "user_id": user_id,
                "video_id": video_id,
                "messages": [],
                "transcript": "",  # avoid None which breaks prompt slicing
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

        try:
            with open(conv_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted file, return empty conversation
            return {
                "user_id": user_id,
                "video_id": video_id,
                "messages": [],
                "transcript": "",  # fallback to empty string
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

    def save_conversation(self, conversation: Dict[str, Any]) -> None:
        """Save conversation to storage.

        Args:
            conversation: Conversation data to save
        """
        user_id = conversation["user_id"]
        video_id = conversation["video_id"]
        conv_path = self._get_conversation_path(user_id, video_id)

        conversation["updated_at"] = datetime.now().isoformat()

        try:
            with open(conv_path, "w", encoding="utf-8") as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save conversation: {e}")

    def add_message(
        self,
        user_id: str,
        video_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Add a message to conversation history.

        Args:
            user_id: User identifier
            video_id: Video identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata for the message
        """
        conversation = self.load_conversation(user_id, video_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if metadata:
            message["metadata"] = metadata

        conversation["messages"].append(message)

        # Trim old messages if exceeding max_history
        if len(conversation["messages"]) > self.max_history * 2:
            # Keep system context + recent messages
            conversation["messages"] = conversation["messages"][
                -(self.max_history * 2) :
            ]

        self.save_conversation(conversation)

    def set_transcript(
        self, user_id: str, video_id: str, transcript: str
    ) -> None:
        """Set the transcript for a conversation.

        Args:
            user_id: User identifier
            video_id: Video identifier
            transcript: Video transcript text
        """
        conversation = self.load_conversation(user_id, video_id)
        conversation["transcript"] = transcript
        self.save_conversation(conversation)

    def _build_prompt(self, transcript: str, history: List[Dict[str, Any]], user_message: str) -> str:
        """Construct a single prompt string including system instructions, limited history, and new user input."""
        system_prompt = (
            "You are a helpful AI assistant helping users learn from YouTube videos.\n\n"
            "You have access to the video's transcript and can answer questions about: \n"
            "- The content and main topics covered\n"
            "- Specific details or explanations\n"
            "- Clarifications on concepts\n"
            "- Connections between ideas\n"
            "- Practical applications\n\n"
            "Provide clear, accurate, and helpful responses based strictly on the transcript content.\n"
            "If unsure or content is not present, say you don't find it in the transcript.\n"
        )

        # Format limited history
        formatted_history = []
        for msg in history[-self.max_history:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted_history.append(f"{role}: {msg['content']}")
        history_block = "\n".join(formatted_history)

        prompt = (
            f"{system_prompt}\nVIDEO TRANSCRIPT (truncated):\n---\n{transcript[:15000]}\n---\n\n"
            f"Conversation History:\n{history_block}\n\nUser: {user_message}\nAssistant:"  # trailing Assistant: encourages completion
        )
        return prompt

    def _build_rag_prompt(
        self,
        user_message: str,
        history: List[Dict[str, Any]],
        video_id: str,
    ) -> Optional[str]:
        """Build a retrieval-augmented prompt using FAISS top-k chunks for the given video.

        Returns None if retrieval fails or yields no results, so caller can fallback.
        """
        try:
            dim = get_embedding_model().get_sentence_embedding_dimension()
            store = FaissVectorStore(dim)
            store.load()

            qv = embed_query(user_message)
            results = store.search(qv, top_k=settings.TOP_K)
            # Filter to current video_id first
            vid_results = [r for r in results if r.metadata.get("video_id") == video_id]
            if not vid_results:
                vid_results = results

            if not vid_results:
                return None

            # Compose citations/context
            context_lines = []
            for r in vid_results:
                cid = r.metadata.get("chunk_id")
                txt = (r.metadata.get("text") or "").strip()
                if not txt:
                    continue
                context_lines.append(f"[c{cid}] {txt}")

            # History formatting
            formatted_history = []
            for msg in history[-self.max_history:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                formatted_history.append(f"{role}: {msg['content']}")
            history_block = "\n".join(formatted_history)

            system_prompt = (
                "You are a helpful AI assistant helping users learn from a YouTube video.\n\n"
                "Answer STRICTLY using the provided context chunks. Cite sources inline using the chunk id like [c3].\n"
                "If the answer is not in the context, say you don't find it in the transcript/context.\n"
            )

            context_block = "\n".join(context_lines)

            prompt = (
                f"{system_prompt}\n"
                f"Context Chunks (most relevant first):\n---\n{context_block}\n---\n\n"
                f"Conversation History:\n{history_block}\n\n"
                f"User: {user_message}\nAssistant:"
            )
            return prompt
        except Exception:
            return None

    def chat(
        self,
        user_id: str,
        video_id: str,
        message: str,
        transcript: Optional[str] = None,
    ) -> str:
        """Send a chat message and get a response using configured backend."""
        conversation = self.load_conversation(user_id, video_id)

        # Attach transcript if newly provided
        if transcript and not conversation.get("transcript"):
            self.set_transcript(user_id, video_id, transcript)
            conversation = self.load_conversation(user_id, video_id)

        stored_transcript = conversation.get("transcript") or ""

        # Prefer RAG prompt if enabled
        prompt = None
        if self.use_rag:
            prompt = self._build_rag_prompt(message, conversation.get("messages", []), video_id)
        if not prompt:
            prompt = self._build_prompt(stored_transcript, conversation.get("messages", []), message)

        # Optional debug: print prompt if environment variable set
        try:
            import os
            if os.getenv("ASKTUBE_DEBUG_PROMPT") == "1":
                print("\n[DEBUG] Prompt Sent To Backend:\n" + "="*40 + "\n" + prompt + "\n" + "="*40 + "\n")
        except Exception:
            pass

        try:
            response = self.backend.generate(prompt, max_tokens=self.max_output_tokens, temperature=self.temperature)
        except Exception as e:
            # Graceful fallback if backend fails; include minimal diagnostic
            response = (
                "(Fallback response) Unable to reach LLM backend. "
                "Summary of your request: " + message[:240]
            )
            try:
                print(f"[WARN] Backend generate failed: {e}")
            except Exception:
                pass
        if not isinstance(response, str):
            response = "(Fallback response) Backend returned no text."

        # Persist messages
        self.add_message(user_id, video_id, "user", message)
        self.add_message(user_id, video_id, "assistant", response)
        return response

    def clear_conversation(self, user_id: str, video_id: str) -> bool:
        """Clear conversation history.

        Args:
            user_id: User identifier
            video_id: Video identifier

        Returns:
            True if cleared, False if didn't exist
        """
        conv_path = self._get_conversation_path(user_id, video_id)

        if conv_path.exists():
            conv_path.unlink()
            return True

        return False

    def list_conversations(self, user_id: Optional[str] = None) -> List[Dict]:
        """List all conversations, optionally filtered by user.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation metadata
        """
        conversations = []

        for conv_file in self.storage_dir.glob("*.json"):
            try:
                with open(conv_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if user_id and data.get("user_id") != user_id:
                    continue

                conversations.append(
                    {
                        "user_id": data.get("user_id"),
                        "video_id": data.get("video_id"),
                        "message_count": len(data.get("messages", [])),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                    }
                )
            except (json.JSONDecodeError, IOError):
                continue

        return sorted(conversations, key=lambda x: x["updated_at"], reverse=True)


if __name__ == "__main__":
    # Simple local test (will use Ollama by default). Ensure Ollama & model are available.
    manager = ConversationManager(backend_type="ollama", model="qwen2.5:7b")
    user_id = "test_user"
    video_id = "test_video"
    manager.set_transcript(user_id, video_id, "This is a short transcript about Python lists and loops.")
    r1 = manager.chat(user_id, video_id, "Summarize the topic.")
    print("Response 1:", r1[:300])
    r2 = manager.chat(user_id, video_id, "Give one example.")
    print("Response 2:", r2[:300])
