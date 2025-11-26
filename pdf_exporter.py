"""
Enhanced PDF export module with beautiful UI and advanced features.

Generates professional PDFs with summary, notes, mind maps, and more.
Supports dark mode, table of contents, and interactive elements.
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib


class EnhancedPDFExporter:
    """Export learning materials to beautifully styled PDF/HTML format."""

    def __init__(self, output_dir: str = "outputs/pdfs"):
        """Initialize PDF exporter.

        Args:
            output_dir: Directory to save PDF files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_enhanced_css(self) -> str:
        """Get enhanced CSS with modern styling."""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

        @page {
            size: A4;
            margin: 2cm;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.8;
            color: #1a1a1a;
            background: #ffffff;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header Section */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            color: white;
            padding: 60px 40px;
            margin: -20px -20px 40px -20px;
            border-radius: 0 0 30px 30px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
        }

        .header h1 {
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 15px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
            position: relative;
            z-index: 1;
        }

        .header .subtitle {
            font-size: 18px;
            font-weight: 300;
            opacity: 0.95;
            margin-bottom: 25px;
        }

        .metadata {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 20px;
            position: relative;
            z-index: 1;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            backdrop-filter: blur(10px);
        }

        .meta-icon {
            font-size: 16px;
        }

        /* Table of Contents */
        .toc {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .toc h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .toc ul {
            list-style: none;
        }

        .toc li {
            padding: 10px 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .toc li:last-child {
            border-bottom: none;
        }

        .toc a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
        }

        .toc a:hover {
            color: #764ba2;
            padding-left: 5px;
        }

        /* Section Styling */
        .section {
            margin: 50px 0;
            page-break-inside: avoid;
        }

        h1 {
            color: #2c3e50;
            font-size: 32px;
            font-weight: 700;
            margin: 40px 0 20px 0;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 15px;
            page-break-before: always;
        }

        h1:first-of-type {
            page-break-before: auto;
        }

        .section-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 12px;
            color: white;
            font-size: 20px;
        }

        h2 {
            color: #34495e;
            font-size: 22px;
            font-weight: 600;
            margin: 30px 0 15px 0;
            padding-left: 20px;
            border-left: 5px solid #3498db;
        }

        h3 {
            color: #7f8c8d;
            font-size: 18px;
            font-weight: 600;
            margin: 20px 0 10px 0;
        }

        /* Summary Box */
        .summary-box {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border-left: 6px solid #2196f3;
            padding: 30px;
            margin: 25px 0;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(33, 150, 243, 0.15);
            position: relative;
        }

        .summary-box::before {
            content: '📝';
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 40px;
            opacity: 0.3;
        }

        /* Note Items */
        .note-item {
            margin: 20px 0;
            padding: 25px;
            background: #ffffff;
            border: 2px solid #e8eaf6;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }

        .note-item:hover {
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
            border-color: #667eea;
        }

        .note-item h2 {
            color: #667eea;
            border-left-color: #667eea;
            margin-top: 0;
        }

        /* Key Concepts Grid */
        .concepts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .concept-card {
            background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
            box-shadow: 0 2px 8px rgba(255, 193, 7, 0.2);
        }

        .concept-title {
            font-weight: 600;
            color: #f57c00;
            margin-bottom: 8px;
        }

        /* Examples Box */
        .example-box {
            background: #f1f8e9;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #8bc34a;
        }

        .example-number {
            display: inline-block;
            background: #8bc34a;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 13px;
            font-weight: 600;
            margin-right: 10px;
        }

        /* Memory Tricks */
        .memory-trick {
            background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%);
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 5px solid #e91e63;
            font-style: italic;
        }

        .memory-trick::before {
            content: '💡 ';
            font-style: normal;
            font-size: 20px;
        }

        /* Common Mistakes */
        .mistake-box {
            background: #ffebee;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 5px solid #f44336;
        }

        .mistake-box::before {
            content: '⚠️ ';
            font-size: 18px;
        }

        /* Sticky Notes Wall */
        .sticky-wall {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 25px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 15px;
        }

        .sticky-note {
            background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%);
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 3px 3px 10px rgba(0,0,0,0.15);
            transform: rotate(-2deg);
            transition: all 0.3s;
            font-size: 14px;
            font-weight: 500;
            color: #333;
            border: 1px solid #ffd54f;
            max-width: 200px;
        }

        .sticky-note:nth-child(even) {
            transform: rotate(2deg);
            background: linear-gradient(135deg, #e1f5fe 0%, #b3e5fc 100%);
            border-color: #81d4fa;
        }

        .sticky-note:nth-child(3n) {
            background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
            border-color: #ce93d8;
        }

        .sticky-note::before {
            content: '📌';
            position: absolute;
            top: -5px;
            right: 10px;
            font-size: 16px;
        }

        /* Mind Map Box */
        .mindmap-container {
            background: #f5f5f5;
            padding: 30px;
            border-radius: 15px;
            margin: 25px 0;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.05);
        }

        .mindmap-box {
            background: #ffffff;
            padding: 25px;
            border-radius: 10px;
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            overflow-x: auto;
            border: 2px solid #e0e0e0;
            color: #2c3e50;
        }

        .mermaid-link {
            display: inline-block;
            margin-top: 15px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }

        .mermaid-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }

        /* Transcript Section */
        .transcript-container {
            background: #fafafa;
            padding: 30px;
            border-radius: 15px;
            margin: 25px 0;
        }

        .transcript-box {
            background: white;
            padding: 25px;
            border-radius: 10px;
            font-size: 14px;
            line-height: 1.9;
            color: #444;
            max-height: 500px;
            overflow: hidden;
            position: relative;
            border: 1px solid #e0e0e0;
        }

        .transcript-box::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 100px;
            background: linear-gradient(to bottom, transparent, white);
        }

        /* Lists */
        ul, ol {
            margin: 15px 0 15px 25px;
        }

        li {
            margin: 8px 0;
            padding-left: 10px;
        }

        ul li::marker {
            content: '▸ ';
            color: #667eea;
            font-size: 18px;
        }

        /* Code Blocks */
        code {
            background: #f5f2f0;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            color: #e83e8c;
            border: 1px solid #ebe5e2;
        }

        /* Page Breaks */
        .page-break {
            page-break-after: always;
        }

        /* Stats Bar */
        .stats-bar {
            display: flex;
            justify-content: space-around;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            margin: 30px 0;
            flex-wrap: wrap;
            gap: 20px;
        }

        .stat-item {
            text-align: center;
            flex: 1;
            min-width: 120px;
        }

        .stat-number {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Footer */
        .footer {
            margin-top: 60px;
            padding-top: 30px;
            border-top: 3px solid #ecf0f1;
            text-align: center;
            color: #95a5a6;
            font-size: 13px;
        }

        .footer-logo {
            font-size: 24px;
            margin-bottom: 10px;
        }

        .footer a {
            color: #667eea;
            text-decoration: none;
        }

        /* Print Optimizations */
        @media print {
            body {
                max-width: 100%;
            }

            .header::before {
                display: none;
            }

            .note-item:hover {
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }

            .mermaid-link:hover {
                transform: none;
            }
        }
        """

    def _generate_enhanced_html(
        self,
        video_id: str,
        video_url: Optional[str] = None,
        video_title: Optional[str] = None,
        summary: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        mindmap: Optional[str] = None,
        transcript: Optional[str] = None,
    ) -> str:
        """Generate enhanced HTML with modern UI."""
        html_parts = []

        # Calculate stats
        word_count = len(transcript.split()) if transcript else 0
        section_count = len([k for k, v in (notes or {}).items() if v]) if notes else 0

        # HTML header
        html_parts.append(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Materials - {video_title or video_id}</title>
    <style>
        {self._get_enhanced_css()}
    </style>
</head>
<body>
""")

        # Enhanced header
        html_parts.append(f"""
    <div class="header">
        <h1>📚 Study Materials</h1>
        <div class="subtitle">{video_title or 'YouTube Learning Assistant'}</div>
        <div class="metadata">
            <div class="meta-item">
                <span class="meta-icon">🎥</span>
                <span>{video_id}</span>
            </div>
""")

        if video_url:
            html_parts.append(f"""
            <div class="meta-item">
                <span class="meta-icon">🔗</span>
                <span>Video Link</span>
            </div>
""")

        html_parts.append(f"""
            <div class="meta-item">
                <span class="meta-icon">📅</span>
                <span>{datetime.now().strftime('%B %d, %Y')}</span>
            </div>
            <div class="meta-item">
                <span class="meta-icon">⏰</span>
                <span>{datetime.now().strftime('%I:%M %p')}</span>
            </div>
        </div>
    </div>
""")

        # Stats bar
        if word_count or section_count:
            html_parts.append(f"""
    <div class="stats-bar">
        <div class="stat-item">
            <div class="stat-number">{word_count:,}</div>
            <div class="stat-label">Words</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{section_count}</div>
            <div class="stat-label">Sections</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{len(mindmap.split('\\n')) if mindmap else 0}</div>
            <div class="stat-label">Mind Map Nodes</div>
        </div>
    </div>
""")

        # Table of Contents
        toc_items = []
        if summary:
            toc_items.append('<li>📝 <a href="#summary">Summary</a></li>')
        if notes:
            toc_items.append('<li>📖 <a href="#notes">Detailed Study Notes</a></li>')
        if mindmap:
            toc_items.append('<li>🧠 <a href="#mindmap">Mind Map</a></li>')
        if transcript:
            toc_items.append('<li>📄 <a href="#transcript">Transcript</a></li>')

        if toc_items:
            html_parts.append("""
    <div class="toc">
        <h2>📑 Table of Contents</h2>
        <ul>
""")
            html_parts.extend(f"            {item}\n" for item in toc_items)
            html_parts.append("""        </ul>
    </div>
""")

        # Summary section
        if summary:
            html_parts.append(f"""
    <div class="section" id="summary">
        <h1><span class="section-icon">📝</span>Summary</h1>
        <div class="summary-box">
            {self._format_text_to_html(summary)}
        </div>
    </div>
""")

        # Detailed notes section
        if notes:
            html_parts.append("""
    <div class="page-break"></div>
    <div class="section" id="notes">
        <h1><span class="section-icon">📖</span>Detailed Study Notes</h1>
""")

            # Key Concepts as grid
            if "key_concepts" in notes and notes["key_concepts"]:
                concepts = notes["key_concepts"].split("\n\n")
                html_parts.append("""
        <div class="note-item">
            <h2>🎯 Key Concepts</h2>
            <div class="concepts-grid">
""")
                for concept in concepts:
                    if ":" in concept:
                        title, desc = concept.split(":", 1)
                        html_parts.append(f"""
                <div class="concept-card">
                    <div class="concept-title">{title.strip()}</div>
                    <div>{desc.strip()}</div>
                </div>
""")
                html_parts.append("""
            </div>
        </div>
""")

            # Detailed Notes
            if "detailed_notes" in notes and notes["detailed_notes"]:
                html_parts.append(f"""
        <div class="note-item">
            <h2>📚 Detailed Notes</h2>
            {self._format_text_to_html(notes["detailed_notes"])}
        </div>
""")

            # Examples
            if "examples" in notes and notes["examples"]:
                html_parts.append("""
        <div class="note-item">
            <h2>💡 Examples</h2>
""")
                examples = notes["examples"].split("\n")
                for i, example in enumerate(examples, 1):
                    if example.strip():
                        html_parts.append(f"""
            <div class="example-box">
                <span class="example-number">Example {i}</span>
                {example.strip()}
            </div>
""")
                html_parts.append("        </div>\n")

            # Memory Tricks
            if "memory_tricks" in notes and notes["memory_tricks"]:
                tricks = notes["memory_tricks"].split("\n")
                html_parts.append("""
        <div class="note-item">
            <h2>🧠 Memory Tricks & Mnemonics</h2>
""")
                for trick in tricks:
                    if trick.strip():
                        html_parts.append(f"""
            <div class="memory-trick">{trick.strip()}</div>
""")
                html_parts.append("        </div>\n")

            # Common Mistakes
            if "common_mistakes" in notes and notes["common_mistakes"]:
                mistakes = notes["common_mistakes"].split("\n")
                html_parts.append("""
        <div class="note-item">
            <h2>⚠️ Common Mistakes</h2>
""")
                for mistake in mistakes:
                    if mistake.strip():
                        html_parts.append(f"""
            <div class="mistake-box">{mistake.strip()}</div>
""")
                html_parts.append("        </div>\n")

            # Sticky Notes
            if "sticky_notes" in notes and notes["sticky_notes"]:
                html_parts.append("""
        <h2>📌 Quick Revision - Sticky Notes</h2>
        <div class="sticky-wall">
""")
                sticky_items = notes["sticky_notes"].split("\n")
                for item in sticky_items:
                    if item.strip():
                        html_parts.append(f"""
            <div class="sticky-note">{item.strip()}</div>
""")
                html_parts.append("""        </div>
""")

            html_parts.append("    </div>\n")

        # Mind map section
        if mindmap:
            html_parts.append(f"""
    <div class="page-break"></div>
    <div class="section" id="mindmap">
        <h1><span class="section-icon">🧠</span>Mind Map</h1>
        <div class="mindmap-container">
            <p style="margin-bottom: 15px;">
                <strong>Visualize this mind map:</strong> Copy the code below and paste it into
                <a href="https://mermaid.live" target="_blank" class="mermaid-link">Mermaid Live Editor</a>
            </p>
            <div class="mindmap-box">{mindmap}</div>
        </div>
    </div>
""")

        # Transcript section
        if transcript:
            truncated = transcript[:5000] + (
                "\n\n... [Transcript truncated for PDF. Full transcript available separately]"
                if len(transcript) > 5000
                else ""
            )
            html_parts.append(f"""
    <div class="page-break"></div>
    <div class="section" id="transcript">
        <h1><span class="section-icon">📄</span>Transcript</h1>
        <div class="transcript-container">
            <div class="transcript-box">
                {self._format_text_to_html(truncated)}
            </div>
        </div>
    </div>
""")

        # Footer
        html_parts.append(f"""
    <div class="footer">
        <div class="footer-logo">🤖</div>
        <p>Generated by <strong>AskTube</strong> - YouTube Learning Assistant</p>
        <p>Powered by Google Gemini AI | <a href="https://github.com/yourusername/asktube">GitHub</a></p>
        <p style="margin-top: 10px; font-size: 11px;">
            Document ID: {hashlib.md5(f"{video_id}{datetime.now()}".encode()).hexdigest()[:8]}
        </p>
    </div>
</body>
</html>
""")

        return "".join(html_parts)

    def _format_text_to_html(self, text: str) -> str:
        """Convert plain text to HTML with enhanced formatting."""
        # Handle bullet points
        lines = text.split("\n")
        formatted_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()

            # Check for bullet points
            if stripped.startswith("•") or stripped.startswith("-") or stripped.startswith("*"):
                if not in_list:
                    formatted_lines.append("<ul>")
                    in_list = True
                formatted_lines.append(f"<li>{stripped[1:].strip()}</li>")
            else:
                if in_list:
                    formatted_lines.append("</ul>")
                    in_list = False
                if stripped:
                    formatted_lines.append(f"<p>{stripped}</p>")

        if in_list:
            formatted_lines.append("</ul>")

        return "\n".join(formatted_lines)

    def export_to_pdf(
        self,
        video_id: str,
        video_url: Optional[str] = None,
        video_title: Optional[str] = None,
        summary: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        mindmap: Optional[str] = None,
        transcript: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> str:
        """Export materials to enhanced PDF/HTML."""
        # Generate HTML
        html_content = self._generate_enhanced_html(
            video_id, video_url, video_title, summary, notes, mindmap, transcript
        )

        # Determine output filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{video_id}_{timestamp}.pdf"

        output_path = self.output_dir / output_filename

        try:
            # Try using weasyprint
            from weasyprint import HTML, CSS

            HTML(string=html_content).write_pdf(
                output_path,
                stylesheets=[CSS(string=self._get_enhanced_css())]
            )
            print(f"[OK] PDF generated: {output_path}")
            return str(output_path)

        except ImportError:
            # Fallback: save as HTML
            print("[INFO] weasyprint not installed. Saving as HTML.")
            print("       Install with: pip install weasyprint")

            html_path = output_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            print(f"[OK] HTML generated: {html_path}")
            return str(html_path)

        except Exception as e:
            # Another fallback
            print(f"[WARN] PDF generation failed ({e}). Saving as HTML.")

            html_path = output_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            print(f"[OK] HTML fallback generated: {html_path}")
            return str(html_path)


# Maintain backward compatibility
PDFExporter = EnhancedPDFExporter


if __name__ == "__main__":
    # Test the enhanced version
    exporter = EnhancedPDFExporter()

    test_summary = """This comprehensive tutorial covers Python list comprehensions in depth.

Key learning points:
- Understand the syntax and structure
- Learn when to use comprehensions vs loops
- Master nested comprehensions
- Apply comprehensions to real-world problems"""

    test_notes = {
        "summary": "A deep dive into Python list comprehensions and their practical applications.",
        "detailed_notes": """List comprehensions provide a concise way to create lists.

Key features:
- More compact than traditional loops
- Often more readable for simple transformations
- Can include conditional logic
- Support nested iterations

Best practices:
- Keep them simple and readable
- Use meaningful variable names
- Break complex logic into multiple steps""",
        "key_concepts": """List Comprehension: A concise way to create lists using a single line of code

Syntax: [expression for item in iterable if condition]

Filter Condition: Optional if clause to filter items

Expression: The transformation applied to each item""",
        "examples": """Example 1: Basic comprehension
squares = [x**2 for x in range(10)]

Example 2: With filtering
evens = [x for x in range(20) if x % 2 == 0]

Example 3: String transformation
upper_words = [word.upper() for word in ['hello', 'world']]""",
        "memory_tricks": """Think of the pattern: [WHAT for EACH in WHERE if CONDITION]

Remember: Brackets make it a LIST comprehension

Mnemonic: "LIST" - Looping Inside Simple Transformations""",
        "common_mistakes": """Forgetting the square brackets
Making comprehensions too complex
Nesting too many levels (max 2-3)
Using comprehensions when a loop is clearer""",
        "sticky_notes": """Brackets required\nMore compact than loops\nCan include conditions\nKeep it simple\nReadability counts\nUse for transformations\nAvoid side effects\nMax 2-3 levels deep""",
    }

    test_mindmap = """mindmap
  root((List Comprehensions))
    Syntax
      Brackets []
      Expression
      For clause
      Optional if
    Benefits
      Concise code
      More Pythonic
      Faster execution
      Better readability
    Use Cases
      Data transformation
      Filtering lists
      Creating new lists
      String operations
    Best Practices
      Keep simple
      Meaningful names
      Avoid nesting
      Use when appropriate"""

    output = exporter.export_to_pdf(
        video_id="python_list_comprehensions",
        video_url="https://youtube.com/watch?v=example",
        video_title="Mastering Python List Comprehensions",
        summary=test_summary,
        notes=test_notes,
        mindmap=test_mindmap,
        transcript="This is a sample transcript about Python list comprehensions..." * 50
    )

    print(f"\n[OK] Enhanced PDF/HTML generated: {output}")
