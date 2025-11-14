"""
Conversation memory manager for chat functionality.

Manages conversation history with file-based persistence.
Supports context-aware Q&A about video transcripts.
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser


class ConversationManager:
    """Manages conversations with persistent history."""

    def __init__(
        self,
        storage_dir: str = "conversations",
        max_history: int = 10,
        model: str = "gemini-2.0-flash-lite",
        api_key: Optional[str] = None,
    ):
        """Initialize conversation manager.

        Args:
            storage_dir: Directory to store conversation files
            max_history: Maximum number of messages to keep in context
            model: Gemini model to use
            api_key: Google API key (if None, will try to load from env)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        self.model = model

        # Get API key
        if api_key is None:
            import os
            from dotenv import load_dotenv

            load_dotenv()
            api_key = (
                os.getenv("GOOGLE_API_KEY")
                or os.getenv("google_api_key")
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("gemini_api_key")
            )

        if not api_key:
            raise ValueError("API key required")

        self.api_key = api_key

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
                "transcript": None,
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
                "transcript": None,
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

    def get_messages_as_langchain(
        self, user_id: str, video_id: str
    ) -> List[Any]:
        """Get messages formatted for LangChain.

        Args:
            user_id: User identifier
            video_id: Video identifier

        Returns:
            List of LangChain message objects
        """
        conversation = self.load_conversation(user_id, video_id)
        messages = []

        for msg in conversation["messages"]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        return messages

    def chat(
        self,
        user_id: str,
        video_id: str,
        message: str,
        transcript: Optional[str] = None,
    ) -> str:
        """Send a chat message and get response.

        Args:
            user_id: User identifier
            video_id: Video identifier
            message: User's message
            transcript: Video transcript (optional, will use stored if available)

        Returns:
            Assistant's response
        """
        # Load or set transcript
        conversation = self.load_conversation(user_id, video_id)

        if transcript and not conversation.get("transcript"):
            self.set_transcript(user_id, video_id, transcript)
            conversation = self.load_conversation(user_id, video_id)

        stored_transcript = conversation.get("transcript", "")

        # Build the prompt
        system_prompt = """You are a helpful AI assistant helping users learn from YouTube videos.

You have access to the video's transcript and can answer questions about:
- The content and main topics covered
- Specific details or explanations
- Clarifications on concepts
- Connections between ideas
- Practical applications

Provide clear, accurate, and helpful responses based on the transcript content.

VIDEO TRANSCRIPT:
---
{transcript}
---
"""

        # Create LangChain components
        llm = ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=self.api_key,
            temperature=0.3,
            max_output_tokens=512,
        )

        # Get recent message history
        history_messages = self.get_messages_as_langchain(user_id, video_id)

        # Build prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        # Create chain
        chain = prompt | llm | StrOutputParser()

        # Invoke chain
        response = chain.invoke(
            {
                "transcript": stored_transcript[:15000],  # Limit context size
                "history": history_messages[-self.max_history :],
                "input": message,
            }
        )

        # Save messages
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
    # Simple test
    manager = ConversationManager()

    # Test conversation
    user_id = "test_user"
    video_id = "test_video"

    # Set transcript
    manager.set_transcript(
        user_id, video_id, "This is a test transcript about Python programming."
    )

    # Send messages
    response1 = manager.chat(user_id, video_id, "What is this video about?")
    print(f"Q: What is this video about?")
    print(f"A: {response1}\n")

    response2 = manager.chat(user_id, video_id, "Can you elaborate?")
    print(f"Q: Can you elaborate?")
    print(f"A: {response2}\n")

    # List conversations
    convs = manager.list_conversations(user_id)
    print(f"Conversations: {len(convs)}")

    # Cleanup
    manager.clear_conversation(user_id, video_id)
    print("Conversation cleared")
