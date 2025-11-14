"""
PDF export module for combining all learning materials.

Generates a comprehensive PDF with summary, notes, mind map, and more.
Uses weasyprint for HTML to PDF conversion (no Node.js required).
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class PDFExporter:
    """Export learning materials to PDF format."""

    def __init__(self, output_dir: str = "outputs/pdfs"):
        """Initialize PDF exporter.

        Args:
            output_dir: Directory to save PDF files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_html(
        self,
        video_id: str,
        video_url: Optional[str] = None,
        summary: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        mindmap: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> str:
        """Generate HTML content for PDF.

        Args:
            video_id: Video identifier
            video_url: Optional YouTube URL
            summary: Summary text
            notes: Detailed notes dictionary
            mindmap: Mermaid mindmap code
            transcript: Video transcript

        Returns:
            HTML string
        """
        html_parts = []

        # HTML header with styling
        html_parts.append(
            """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Study Materials - {video_id}</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
        }}

        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            page-break-before: always;
        }}

        h1:first-of-type {{
            page-break-before: auto;
        }}

        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}

        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}

        .header {{
            text-align: center;
            padding: 20px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: -20px -20px 30px -20px;
            padding: 40px 20px;
        }}

        .header h1 {{
            color: white;
            border: none;
            margin: 0;
            page-break-before: auto;
        }}

        .metadata {{
            color: rgba(255,255,255,0.9);
            font-size: 14px;
            margin-top: 10px;
        }}

        .section {{
            margin: 30px 0;
            page-break-inside: avoid;
        }}

        .summary-box {{
            background: #f8f9fa;
            border-left: 5px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .note-item {{
            margin: 15px 0;
            padding: 15px;
            background: #fff;
            border: 1px solid #e1e8ed;
            border-radius: 5px;
        }}

        .sticky-note {{
            display: inline-block;
            background: #fff9c4;
            padding: 10px 15px;
            margin: 5px;
            border-radius: 3px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 14px;
        }}

        .mindmap-box {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            overflow-x: auto;
        }}

        .transcript-box {{
            background: #fafafa;
            padding: 15px;
            border-radius: 5px;
            font-size: 13px;
            line-height: 1.8;
            max-height: 400px;
            overflow: hidden;
        }}

        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #95a5a6;
            font-size: 12px;
        }}

        ul {{
            list-style-type: none;
            padding-left: 0;
        }}

        li:before {{
            content: "→ ";
            color: #3498db;
            font-weight: bold;
            margin-right: 8px;
        }}

        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}

        .page-break {{
            page-break-after: always;
        }}
    </style>
</head>
<body>
""".format(
                video_id=video_id
            )
        )

        # Header section
        html_parts.append(
            f"""
    <div class="header">
        <h1>Study Materials</h1>
        <div class="metadata">
            Video ID: {video_id}<br>
"""
        )

        if video_url:
            html_parts.append(f"            URL: {video_url}<br>\n")

        html_parts.append(
            f"""            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
"""
        )

        # Summary section
        if summary:
            html_parts.append(
                f"""
    <div class="section">
        <h1>Summary</h1>
        <div class="summary-box">
            {self._format_text_to_html(summary)}
        </div>
    </div>
"""
            )

        # Detailed notes section
        if notes:
            html_parts.append(
                """
    <div class="page-break"></div>
    <div class="section">
        <h1>Detailed Study Notes</h1>
"""
            )

            for field_name, field_label in [
                ("summary", "Overview"),
                ("detailed_notes", "Detailed Notes"),
                ("key_concepts", "Key Concepts"),
                ("examples", "Examples"),
                ("memory_tricks", "Memory Tricks & Mnemonics"),
                ("common_mistakes", "Common Mistakes"),
            ]:
                if field_name in notes and notes[field_name]:
                    html_parts.append(
                        f"""
        <div class="note-item">
            <h2>{field_label}</h2>
            {self._format_text_to_html(notes[field_name])}
        </div>
"""
                    )

            # Sticky notes
            if "sticky_notes" in notes and notes["sticky_notes"]:
                html_parts.append(
                    """
        <h2>Quick Revision - Sticky Notes</h2>
        <div style="margin: 20px 0;">
"""
                )

                sticky_items = notes["sticky_notes"].split("\n")
                for item in sticky_items:
                    if item.strip():
                        html_parts.append(
                            f'            <span class="sticky-note">{item.strip()}</span>\n'
                        )

                html_parts.append("        </div>\n")

            html_parts.append("    </div>\n")

        # Mind map section
        if mindmap:
            html_parts.append(
                f"""
    <div class="page-break"></div>
    <div class="section">
        <h1>Mind Map</h1>
        <p>Mermaid diagram code (paste into <a href="https://mermaid.live">mermaid.live</a> to visualize):</p>
        <div class="mindmap-box">{mindmap}</div>
    </div>
"""
            )

        # Transcript section (truncated)
        if transcript:
            truncated = transcript[:3000] + (
                "...\n\n[Transcript truncated for PDF]"
                if len(transcript) > 3000
                else ""
            )
            html_parts.append(
                f"""
    <div class="page-break"></div>
    <div class="section">
        <h1>Transcript</h1>
        <div class="transcript-box">
            {self._format_text_to_html(truncated)}
        </div>
    </div>
"""
            )

        # Footer
        html_parts.append(
            """
    <div class="footer">
        Generated by AskTube - YouTube Learning Assistant<br>
        Powered by Google Gemini AI
    </div>
</body>
</html>
"""
        )

        return "".join(html_parts)

    def _format_text_to_html(self, text: str) -> str:
        """Convert plain text to HTML with basic formatting.

        Args:
            text: Plain text

        Returns:
            HTML formatted text
        """
        # Replace newlines with <br>
        html = text.replace("\n\n", "</p><p>").replace("\n", "<br>")

        # Wrap in paragraphs
        html = f"<p>{html}</p>"

        return html

    def export_to_pdf(
        self,
        video_id: str,
        video_url: Optional[str] = None,
        summary: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        mindmap: Optional[str] = None,
        transcript: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> str:
        """Export materials to PDF.

        Args:
            video_id: Video identifier
            video_url: Optional YouTube URL
            summary: Summary text
            notes: Detailed notes dictionary
            mindmap: Mermaid mindmap code
            transcript: Video transcript
            output_filename: Optional custom filename

        Returns:
            Path to generated PDF file
        """
        # Generate HTML
        html_content = self._generate_html(
            video_id, video_url, summary, notes, mindmap, transcript
        )

        # Determine output filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{video_id}_{timestamp}.pdf"

        output_path = self.output_dir / output_filename

        try:
            # Try using weasyprint
            from weasyprint import HTML

            HTML(string=html_content).write_pdf(output_path)
            return str(output_path)

        except ImportError:
            # Fallback: save as HTML if weasyprint not available
            print("Warning: weasyprint not installed. Saving as HTML instead.")
            print("Install with: pip install weasyprint")

            html_path = output_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            return str(html_path)

        except Exception as e:
            # Another fallback: save as HTML
            print(f"Warning: PDF generation failed ({e}). Saving as HTML instead.")

            html_path = output_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            return str(html_path)


if __name__ == "__main__":
    # Simple test
    exporter = PDFExporter()

    # Test data
    test_summary = """This video covers Python programming basics.

Key points:
- Variables and data types
- Control flow
- Functions"""

    test_notes = {
        "summary": "A comprehensive introduction to Python programming.",
        "detailed_notes": "Variables store data\nFunctions encapsulate logic\nControl flow directs execution",
        "key_concepts": "Variable: Named storage location\nFunction: Reusable code block",
        "examples": "Example 1: x = 5\nExample 2: def greet(): print('Hello')",
        "memory_tricks": "Remember: Variables Vary, Functions Function",
        "common_mistakes": "Forgetting colons after function definitions",
        "sticky_notes": "Variables store data\nFunctions are reusable\nIndentation matters",
    }

    test_mindmap = """mindmap
  root((Python Basics))
    Variables
      Types
      Assignment
    Functions
      Definition
      Calling"""

    # Generate PDF
    output = exporter.export_to_pdf(
        video_id="test_video",
        video_url="https://youtube.com/watch?v=test",
        summary=test_summary,
        notes=test_notes,
        mindmap=test_mindmap,
    )

    print(f"Generated: {output}")
