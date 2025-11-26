#!/usr/bin/env python3
"""
Test asktube.py PDF generation using cached data.
"""
import json
from pathlib import Path
from asktube import AskTube

def setup_cache():
    """Setup cache with test data to avoid API calls."""
    from cache_manager import CacheManager

    cache = CacheManager(cache_dir="cache", default_ttl=86400)

    test_video_id = "test_asktube_pdf"
    test_model = "gemini-1.5-flash"

    # Cache transcript
    transcript_text = "This is a test transcript about Python programming. " * 50
    cache.set(
        f"transcript_{test_video_id}",
        {
            "text": transcript_text,
            "data": {"items": [], "text": transcript_text}
        },
        namespace="transcripts"
    )

    # Cache summary
    summary = "This video covers Python programming fundamentals including variables, functions, and data structures."
    cache.set(
        f"summary_{test_video_id}_{test_model}",
        summary,
        namespace="outputs"
    )

    # Cache notes
    notes = {
        "summary": "Overview of Python programming basics",
        "detailed_notes": "Python is a high-level programming language.\nIt supports multiple programming paradigms.\nIt has extensive standard library.",
        "key_concepts": "Variable: A named storage location\nFunction: Reusable block of code\nData Structure: Organization of data",
        "examples": "Example 1: x = 10\nExample 2: def greet(): print('Hello')",
        "memory_tricks": "Remember: Python is named after Monty Python",
        "common_mistakes": "Forgetting colons after function definitions\nIncorrect indentation",
        "sticky_notes": "Use meaningful names\nKeep functions small\nWrite docstrings",
    }
    cache.set(
        f"notes_{test_video_id}_{test_model}",
        notes,
        namespace="outputs"
    )

    # Cache mindmap
    mindmap = """mindmap
  root((Python Programming))
    Basics
      Variables
      Data Types
      Operations
    Functions
      Definition
      Parameters
      Return values
    Data Structures
      Lists
      Dictionaries
      Sets"""
    cache.set(
        f"mindmap_{test_video_id}_{test_model}",
        mindmap,
        namespace="outputs"
    )

    return test_video_id, transcript_text

def test_asktube_with_pdf():
    """Test asktube with PDF generation."""
    print("\n" + "="*60)
    print("Testing AskTube with PDF Generation")
    print("="*60 + "\n")

    # Setup cache
    test_video_id, transcript_text = setup_cache()
    print(f"[OK] Cache setup complete for video: {test_video_id}\n")

    # Create transcript file
    transcript_file = Path("outputs") / "test_asktube_transcript.txt"
    transcript_file.write_text(transcript_text, encoding="utf-8")
    print(f"[OK] Test transcript file created: {transcript_file}\n")

    # Initialize AskTube
    asktube = AskTube(
        output_dir="outputs",
        use_cache=True,
        cache_ttl=86400
    )

    # Test 1: Process transcript file WITH PDF generation
    print("\nTest 1: Processing transcript file WITH --generate-pdf")
    print("-" * 60)

    try:
        results = asktube.process_transcript_file(
            transcript_path=str(transcript_file),
            output_prefix="test_asktube_pdf",
            model="gemini-1.5-flash",
            skip_summary=False,
            skip_notes=False,
            skip_mindmap=False,
            generate_pdf=True,
        )

        print("\n[OK] Processing completed!")
        print("\nGenerated files:")
        for key, value in results.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for subkey, subvalue in value.items():
                    print(f"    - {subkey}: {subvalue}")
            else:
                print(f"  - {key}: {value}")

        # Verify PDF was generated
        if "pdf" in results:
            pdf_path = Path(results["pdf"])
            if pdf_path.exists():
                file_size = pdf_path.stat().st_size
                print(f"\n[PASS] PDF generated successfully ({file_size} bytes)")
                return True
            else:
                print("\n[FAIL] PDF file not found")
                return False
        else:
            print("\n[FAIL] PDF not in results")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_asktube_without_pdf():
    """Test that PDF is NOT generated when flag is False."""
    print("\n\nTest 2: Processing WITHOUT --generate-pdf")
    print("-" * 60)

    transcript_file = Path("outputs") / "test_asktube_transcript.txt"

    asktube = AskTube(
        output_dir="outputs",
        use_cache=True,
        cache_ttl=86400
    )

    try:
        results = asktube.process_transcript_file(
            transcript_path=str(transcript_file),
            output_prefix="test_no_pdf",
            model="gemini-1.5-flash",
            skip_summary=False,
            skip_notes=False,
            skip_mindmap=False,
            generate_pdf=False,  # No PDF
        )

        # Verify PDF was NOT generated
        if "pdf" not in results:
            print("\n[PASS] Correctly did not generate PDF when flag is False")
            return True
        else:
            print("\n[FAIL] PDF was generated when it shouldn't be")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False

def test_asktube_pdf_with_skip():
    """Test that PDF generation warns when summary/notes are skipped."""
    print("\n\nTest 3: Testing PDF generation with --skip-summary")
    print("-" * 60)

    transcript_file = Path("outputs") / "test_asktube_transcript.txt"

    asktube = AskTube(
        output_dir="outputs",
        use_cache=True,
        cache_ttl=86400
    )

    try:
        results = asktube.process_transcript_file(
            transcript_path=str(transcript_file),
            output_prefix="test_skip_warning",
            model="gemini-1.5-flash",
            skip_summary=True,  # Skip summary
            skip_notes=False,
            skip_mindmap=False,
            generate_pdf=True,  # Try to generate PDF
        )

        # Should not have PDF since summary is skipped
        if "pdf" not in results:
            print("\n[PASS] Correctly prevented PDF generation when summary is skipped")
            return True
        else:
            print("\n[FAIL] PDF was generated despite skipped summary")
            return False

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("AskTube PDF Integration Test Suite")
    print("="*60)

    results = {}

    # Run tests
    results["PDF Generation"] = test_asktube_with_pdf()
    results["No PDF when disabled"] = test_asktube_without_pdf()
    results["Skip validation"] = test_asktube_pdf_with_skip()

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
    import sys
    sys.exit(main())
