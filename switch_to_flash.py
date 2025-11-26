#!/usr/bin/env python3
"""
Switch all models from gemini-2.5-pro to gemini-1.5-flash-latest
"""
from pathlib import Path

def update_model_in_file(file_path):
    """Update model default in a single file."""
    content = file_path.read_text(encoding='utf-8')
    original = content

    # Replace the model string
    content = content.replace('gemini-2.5-pro', 'gemini-1.5-flash-latest')

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    """Update all Python files in the project."""
    project_dir = Path('.')
    updated_files = []

    # Find all .py files
    for py_file in project_dir.glob('*.py'):
        if py_file.name == 'switch_to_flash.py':
            continue

        if update_model_in_file(py_file):
            updated_files.append(py_file.name)
            print(f"[OK] Updated: {py_file.name}")

    print(f"\n[OK] Updated {len(updated_files)} files to gemini-1.5-flash-latest")
    print("\nFiles updated:")
    for f in updated_files:
        print(f"  - {f}")

if __name__ == '__main__':
    main()
