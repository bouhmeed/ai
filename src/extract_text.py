# src/extract_text.py
import os
from docx import Document
import fitz  # PyMuPDF

def extract_file(filepath):
    """Extract text from .pdf, .docx, or .txt files."""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower().strip()

    try:
        if ext == ".pdf":
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text

        elif ext == ".docx":
            doc = Document(filepath)
            return "\n".join(para.text for para in doc.paragraphs)

        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()

        else:
            return None  # Unsupported format

    except Exception as e:
        print(f"❌ Erreur lors du traitement de {filepath}: {e}")
        return ""

def main():
    notes_dir = os.path.join(".", "data", "notes_raw")
    output_dir = os.path.join(".", "data", "output", "extracted")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isdir(notes_dir):
        print(f"❌ Dossier source introuvable : {os.path.abspath(notes_dir)}")
        return

    for filename in os.listdir(notes_dir):
        src_path = os.path.join(notes_dir, filename)

        if not os.path.isfile(src_path):
            continue  # skip directories

        text = extract_file(src_path)

        if text is None:
            print(f"⚠️ Format non supporté : {src_path}")
            continue

        # Save as .txt regardless of input format
        out_filename = os.path.splitext(filename)[0] + ".txt"
        out_path = os.path.join(output_dir, out_filename)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Logging
        preview = text[:200].replace('\n', ' ').strip()
        if text.strip():
            print(f"✅ {filename} -> {preview}...")
        else:
            print(f"⚠️ {filename} est vide")

if __name__ == "__main__":
    main()