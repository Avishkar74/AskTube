#!/usr/bin/env python3
"""
Test script for M3 features (chat and PDF export).
"""
import sys
from pathlib import Path

# Test data
TEST_TRANSCRIPT = """
This tutorial covers Python list comprehensions.
List comprehensions provide a concise way to create lists.
They consist of brackets containing an expression followed by a for clause.
For example: squares = [x**2 for x in range(10)]
List comprehensions are more compact and faster than loops.
""".strip()

TEST_VIDEO_ID = "test_python_lists"
TEST_USER_ID = "test_user_123"

def test_pdf_export():
    """Test PDF export functionality."""
    print("\n" + "="*60)
    print("Testing PDF Export")
    print("="*60 + "\n")

    try:
        from pdf_exporter import PDFExporter

        # Create exporter
        exporter = PDFExporter(output_dir="outputs/test_pdfs")

        # Test data
        test_notes = {
            "summary": "Overview of Python list comprehensions",
            "detailed_notes": "List comprehensions offer concise syntax\nThey are more Pythonic than loops",
            "key_concepts": "List Comprehension: Concise syntax for lists\nSyntax: [expression for item in iterable]",
            "examples": "Example 1: [x*2 for x in [1,2,3]]\nExample 2: [x for x in range(10) if x % 2 == 0]",
            "memory_tricks": "Think: [WHAT for EACH in WHERE]",
            "common_mistakes": "Forgetting the brackets\nUsing them when a loop is clearer",
            "sticky_notes": "Brackets required\nMore compact than loops\nCan include conditions",
        }

        test_mindmap = """mindmap
  root((List Comprehensions))
    Syntax
      Brackets
      Expression
      For clause
    Benefits
      Concise
      Readable
      Fast"""

        # Generate PDF/HTML
        output_path = exporter.export_to_pdf(
            video_id=TEST_VIDEO_ID,
            video_url=f"https://youtube.com/watch?v={TEST_VIDEO_ID}",
            summary="Quick introduction to Python list comprehensions.",
            notes=test_notes,
            mindmap=test_mindmap,
            transcript=TEST_TRANSCRIPT
        )

        print(f"[OK] PDF/HTML generated: {output_path}")

        # Verify file exists
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            print(f"[OK] File exists ({file_size} bytes)")
            return True
        else:
            print("[FAIL] File not created")
            return False

    except Exception as e:
        print(f"[FAIL] PDF export error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_manager():
    """Test conversation manager functionality."""
    print("\n" + "="*60)
    print("Testing Conversation Manager")
    print("="*60 + "\n")

    try:
        from conversation_manager import ConversationManager

        # Create manager
        manager = ConversationManager(storage_dir="conversations/test")

        # Set transcript
        print("Setting transcript...")
        manager.set_transcript(TEST_USER_ID, TEST_VIDEO_ID, TEST_TRANSCRIPT)
        print("[OK] Transcript set")

        # Load conversation
        print("\nLoading conversation...")
        conv = manager.load_conversation(TEST_USER_ID, TEST_VIDEO_ID)
        print(f"[OK] Conversation loaded (has transcript: {conv.get('transcript') is not None})")

        # Add messages manually (skip chat to avoid API calls)
        print("\nAdding test messages...")
        manager.add_message(TEST_USER_ID, TEST_VIDEO_ID, "user", "What are list comprehensions?")
        manager.add_message(TEST_USER_ID, TEST_VIDEO_ID, "assistant", "They are a concise way to create lists in Python.")
        print("[OK] Messages added")

        # Check message history
        print("\nChecking message history...")
        messages = manager.get_messages_as_langchain(TEST_USER_ID, TEST_VIDEO_ID)
        print(f"[OK] Found {len(messages)} messages")

        # List conversations
        print("\nListing conversations...")
        convs = manager.list_conversations(TEST_USER_ID)
        print(f"[OK] Found {len(convs)} conversations for user")

        # Clear conversation
        print("\nClearing conversation...")
        cleared = manager.clear_conversation(TEST_USER_ID, TEST_VIDEO_ID)
        print(f"[OK] Conversation cleared: {cleared}")

        return True

    except Exception as e:
        print(f"[FAIL] Conversation manager error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AskTube M3 Features Test Suite")
    print("="*60)

    results = {}

    # Test PDF export
    results["PDF Export"] = test_pdf_export()

    # Test conversation manager
    results["Conversation Manager"] = test_conversation_manager()

    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60 + "\n")

    all_passed = True
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
