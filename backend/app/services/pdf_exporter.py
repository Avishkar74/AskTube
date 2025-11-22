import os
from ..core.logging import logger

class EnhancedPDFExporter:
    def export_to_pdf(self, video_id: str, video_url: str, video_title: str, summary: str, notes: str, mindmap: str, transcript: str) -> str:
        """Generate HTML and PDF reports."""
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; padding: 20px; }}
                h1 {{ color: #333; }}
                .section {{ margin-bottom: 20px; }}
                .mermaid {{ border: 1px solid #ddd; padding: 10px; }}
            </style>
        </head>
        <body>
            <h1>{video_title or video_id}</h1>
            <p><a href="{video_url}">{video_url}</a></p>
            
            <div class="section">
                <h2>Summary</h2>
                <div>{summary}</div>
            </div>
            
            <div class="section">
                <h2>Study Notes</h2>
                <div>{notes}</div>
            </div>
            
            <div class="section">
                <h2>Mind Map</h2>
                <pre class="mermaid">{mindmap}</pre>
            </div>
        </body>
        </html>
        """
        
        # Save HTML
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        html_path = os.path.join(output_dir, f"{video_id}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        # Generate PDF (Optional)
        try:
            from weasyprint import HTML
            pdf_path = os.path.join(output_dir, f"{video_id}.pdf")
            HTML(string=html_content).write_pdf(pdf_path)
            return pdf_path
        except Exception as e:
            logger.warning(f"PDF export failed (returning HTML): {e}")
            return html_path
