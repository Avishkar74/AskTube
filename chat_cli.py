#!/usr/bin/env python3
"""
AskTube Chat CLI - Interactive chat about YouTube videos.

Usage:
    python chat_cli.py <video_id_or_url> [--user-id USER_ID]
    python chat_cli.py --transcript transcript.txt [--video-id ID]
"""
import argparse
import sys
from pathlib import Path

from conversation_manager import ConversationManager
from config import settings
from rag_indexer import index_transcript
from transcript_extractor import extract_video_id, get_transcript


def chat_session(
    manager: ConversationManager,
    user_id: str,
    video_id: str,
    transcript: str,
):
    """Run interactive chat session.

    Args:
        manager: Conversation manager instance
        user_id: User identifier
        video_id: Video identifier
        transcript: Video transcript text
    """
    print(f"\n{'='*60}")
    print(f"AskTube Chat - Video: {video_id}")
    print(f"{'='*60}\n")
    print("Ask questions about the video. Type 'quit' or 'exit' to end.\n")

    # Set transcript
    manager.set_transcript(user_id, video_id, transcript)

    # Load existing conversation
    conversation = manager.load_conversation(user_id, video_id)
    message_count = len(conversation.get("messages", []))

    if message_count > 0:
        print(f"[Loaded {message_count} previous messages]\n")

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if user_input.lower() in ["clear", "reset"]:
                manager.clear_conversation(user_id, video_id)
                print("\n[Conversation cleared]\n")
                continue

            if user_input.lower() == "history":
                conversation = manager.load_conversation(user_id, video_id)
                messages = conversation.get("messages", [])
                print(f"\n[Conversation has {len(messages)} messages]\n")
                continue

            # Get response
            print("Assistant: ", end="", flush=True)
            response = manager.chat(user_id, video_id, user_input)
            print(response + "\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            continue


def main():
    parser = argparse.ArgumentParser(
        description="AskTube Chat - Interactive Q&A about YouTube videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Chat about a YouTube video
  python chat_cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

  # Chat about a transcript file
  python chat_cli.py --transcript transcript.txt --video-id my_video

  # Use custom user ID
  python chat_cli.py VIDEO_URL --user-id john
        """,
    )

    parser.add_argument(
        "input", nargs="?", help="YouTube URL or video ID (if not using --transcript)"
    )
    parser.add_argument(
        "--transcript", "-t", help="Path to transcript file"
    )
    parser.add_argument(
        "--video-id", help="Video ID (required when using --transcript)"
    )
    parser.add_argument(
        "--user-id", "-u", default="default_user", help="User ID (default: default_user)"
    )
    parser.add_argument(
        "--backend", "-b", default="ollama", choices=["ollama", "gemini"], help="Chat LLM backend (default: ollama)"
    )
    parser.add_argument(
        "--model", "-m", default=None, help="Model name (optional, uses backend defaults)"
    )
    rag_group = parser.add_mutually_exclusive_group()
    rag_group.add_argument(
        "--use-rag", action="store_true", help="Enable retrieval-augmented generation for chat"
    )
    rag_group.add_argument(
        "--no-rag", action="store_true", help="Disable retrieval-augmented generation for chat"
    )
    parser.add_argument(
        "--force-reindex", action="store_true", help="Force re-indexing of transcript before chat when RAG is enabled"
    )

    args = parser.parse_args()

    # Validate input
    if not args.input and not args.transcript:
        parser.error("Provide either a YouTube URL/video ID or --transcript")

    if args.transcript and not args.video_id:
        parser.error("--video-id required when using --transcript")

    try:
        # Initialize manager with selected backend
        # Determine RAG usage
        use_rag = settings.USE_RAG
        if args.use_rag:
            use_rag = True
        if args.no_rag:
            use_rag = False

        manager = ConversationManager(backend_type=args.backend, model=args.model, use_rag=use_rag)

        # Get transcript and video ID
        if args.transcript:
            # Load from file
            transcript_text = Path(args.transcript).read_text(encoding="utf-8")
            video_id = args.video_id
        else:
            # Extract from YouTube
            video_id = extract_video_id(args.input)
            if not video_id:
                video_id = args.input  # Assume it's already a video ID

            print(f"Fetching transcript for video: {video_id}...")
            transcript_items = get_transcript(f"https://youtube.com/watch?v={video_id}")
            transcript_text = " ".join([item["text"] for item in transcript_items])
            print(f"Transcript loaded: {len(transcript_text)} characters\n")

        # Auto-index for RAG (so chat works immediately with retrieval)
        if use_rag:
            try:
                print("Indexing transcript for retrieval (RAG)...")
                idx_res = index_transcript(video_id, transcript_text, force_reindex=args.force_reindex)
                if idx_res.get("indexed"):
                    print(f"[OK] Indexed {idx_res['chunks']} chunks (hash {idx_res['hash'][:8]}...)\n")
                else:
                    print(f"[OK] Index step: {idx_res.get('reason', 'skipped')}\n")
            except Exception as e:
                print(f"[WARN] RAG indexing failed: {e}. Proceeding without RAG.")

        # Start chat session
        chat_session(manager, args.user_id, video_id, transcript_text)

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
