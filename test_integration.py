#!/usr/bin/env python3
"""
Quick integration test for PDF export in asktube.py
Tests without making API calls by mocking the components.
"""
from pathlib import Path
from pdf_exporter import PDFExporter

def test_pdf_integration():
    """Test PDF export integration."""
    print("Testing PDF export integration...")

    # Test data (simulating what asktube.py would generate)
    test_video_id = "test_integration"
    test_url = "https://youtube.com/watch?v=test"
    test_title = "Integration Test Video"

    test_summary = "This is a test summary for the integration test."

    test_notes = {
        "summary": "Brief summary of the video",
        "detailed_notes": "Detailed notes about the content",
        "key_concepts": "Concept 1: Definition\nConcept 2: Another definition",
        "examples": "Example 1: Code sample\nExample 2: Another sample",
        "memory_tricks": "Remember: TEST - Thorough Example System Test",
        "common_mistakes": "Don't forget to test\nAlways verify outputs",
        "sticky_notes": "Test everything\nVerify outputs\nCheck edge cases",
    }

    test_mindmap = """mindmap
  root((Integration Test))
    Setup
      Initialize
      Configure
    Execute
      Run tests
      Collect results
    Verify
      Check outputs
      Validate"""

    test_transcript = "This is a test transcript for the integration test. " * 20

    # Create PDF exporter
    exporter = PDFExporter(output_dir="outputs/pdfs")

    # Generate PDF
    pdf_path = exporter.export_to_pdf(
        video_id=test_video_id,
        video_url=test_url,
        video_title=test_title,
        summary=test_summary,
        notes=test_notes,
        mindmap=test_mindmap,
        transcript=test_transcript
    )

    print(f"[OK] PDF generated: {pdf_path}")

    # Verify file exists
    if Path(pdf_path).exists():
        file_size = Path(pdf_path).stat().st_size
        print(f"[OK] File exists ({file_size} bytes)")
        print("[PASS] Integration test passed!")
        return True
    else:
        print("[FAIL] File not created")
        return False

if __name__ == "__main__":
    import sys
    success = test_pdf_integration()
    sys.exit(0 if success else 1)
