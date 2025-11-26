import os
from pathlib import Path
from app.services.pdf_exporter import EnhancedPDFExporter

def main():
    video_id = "7eSQd7me6QI"
    upload_dir = Path("data/uploads") / video_id
    
    print(f"Checking {upload_dir.absolute()}")
    
    if not upload_dir.exists():
        print("Upload dir not found")
        return

    files = list(upload_dir.glob("*"))
    uploaded_files = []
    for file_path in files:
        if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            uploaded_files.append({
                "filename": file_path.name,
                "path": str(file_path)
            })
            
    print(f"Found {len(uploaded_files)} images")
    
    if not uploaded_files:
        return

    exporter = EnhancedPDFExporter()
    try:
        pdf_bytes = exporter.generate_uploaded_notes_pdf(
            video_id=video_id,
            video_title="Test Video",
            uploaded_files=uploaded_files
        )
        print(f"Success! PDF size: {len(pdf_bytes)} bytes")
        
        # Save it to check
        with open("test_output.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("Saved to test_output.pdf")
        
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
