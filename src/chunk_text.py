"""
Chunking intelligent orienté sémantique métier.
Objectif : produire des chunks autonomes, cohérents et exploitables par section FAD,
en utilisant un LLM léger pour guider la segmentation quand nécessaire.
"""

import os
import re
import json
import hashlib
from typing import List
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# ----------------------------
# Configuration
# ----------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "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"

# ==============================================================================
# 🧹 NETTOYAGE DU TEXTE BRUT
# ==============================================================================
NOISE_PATTERNS = [
    r"^\s*(Almatech|Client|Consultant|Intervenant|Réunion|Pause|Merci|OK|D'accord|Bonjour|Salut|Au revoir|Merci beaucoup)\s*:?",
    r"^\s*\d{1,2}:\d{2}(:\d{2})?\s*$",  # timestamps
    r"^\s*(Page \d+|Confidentiel|Almatech Consulting)\s*$",
    r"^\s*$",
]
NOISE_RE = re.compile('|'.join(f'({p})' for p in NOISE_PATTERNS), re.IGNORECASE)

def clean_lines(text: str) -> List[str]:
    """Nettoie le texte ligne par ligne, supprime le bruit."""
    lines = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped or NOISE_RE.search(stripped):
            continue
        if len(stripped) >= 4:
            lines.append(stripped)
    return lines

def hash_text(text: str) -> str:
    """Génère un identifiant stable pour un chunk."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# ==============================================================================
# 🧠 CHUNKING SÉMANTIQUE AVEC LLM (GUIDED SPLITTING)
# ==============================================================================
def semantic_split_with_llm(paragraph: str, max_words: int = 35) -> List[str]:
    """
    Utilise un LLM pour diviser un paragraphe long en unités sémantiques autonomes.
    Chaque unité = une seule idée métier complète (règle, volume, écart, besoin, etc.).
    """
    if len(paragraph.split()) <= max_words:
        return [paragraph.strip()]

    prompt = f"""Tu es un expert Dynamics 365 analysant des notes d’atelier.
Découpe ce texte en blocs sémantiquement autonomes. Chaque bloc doit :
- Être compréhensible seul,
- Décrire UNE SEULE idée métier (ex: règle de gestion, volume, problème, document, écart),
- Conserver les termes exacts (ex: "BL", "ordre fabrication", "workflow validation").
Ne modifie pas, ne résume pas, ne traduis pas.
Renvoie UNIQUEMENT les blocs, séparés par '===BLOCK==='.

Texte :
{paragraph}

Réponse :"""

    try:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.0, groq_api_key=GROQ_API_KEY)
        response = llm.invoke(prompt).content.strip()
        blocks = [b.strip() for b in response.split("===BLOCK===") if b.strip()]
        return blocks if blocks else [paragraph.strip()]
    except Exception as e:
        print(f"⚠️ Erreur LLM chunking (fallback sur découpage par phrases) : {e}")
        # Fallback robuste
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        chunks = []
        current = []
        for sent in sentences:
            if len(" ".join(current + [sent]).split()) > max_words:
                if current:
                    chunks.append(" ".join(current))
                current = [sent]
            else:
                current.append(sent)
        if current:
            chunks.append(" ".join(current))
        return [c.strip() for c in chunks if len(c.split()) >= 5]

# ==============================================================================
# 📑 RECONSTRUCTION DE BLOCS LOGIQUES (STRUCTURE PRÉSERVÉE)
# ==============================================================================
def reconstruct_logical_blocks(lines: List[str]) -> List[str]:
    """
    Étape 1 : regroupe en paragraphes logiques (sauts de ligne, listes).
    Étape 2 : applique un chunking sémantique intelligent.
    """
    # Regroupement en paragraphes grossiers
    paragraphs = []
    current = []

    for line in lines:
        is_list_item = line.lstrip().startswith(('-', '•', '*')) or re.match(r'^\d+\.', line.lstrip())
        if is_list_item:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append(line)  # Liste = chunk autonome
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    # Chunking sémantique
    smart_chunks = []
    for para in paragraphs:
        if len(para.split()) < 6:
            smart_chunks.append(para)
        else:
            chunks = semantic_split_with_llm(para, max_words=35)
            smart_chunks.extend(chunks)

    # Filtrage final
    return [c.strip() for c in smart_chunks if len(c.split()) >= 5]

# ==============================================================================
# 🚀 FONCTION PRINCIPALE
# ==============================================================================
def main():
    """Génère des chunks sémantiquement intelligents, prêts pour l’embedding."""
    input_dir = os.path.join(".", "data", "output", "extracted")
    output_dir = os.path.join(".", "data", "output", "chunks")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isdir(input_dir):
        print(f"❌ Dossier introuvable : {os.path.abspath(input_dir)}")
        return

    for filename in os.listdir(input_dir):
        if not filename.endswith(".txt"):
            continue

        src_path = os.path.join(input_dir, filename)
        with open(src_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        if not raw_text.strip():
            print(f"⚠️ {filename} est vide.")
            continue

        lines = clean_lines(raw_text)
        blocks = reconstruct_logical_blocks(lines)

        output_data = []
        for i, block in enumerate(blocks):
            output_data.append({
                "text": block,
                "chunk_id": hash_text(block),
                "metadata": {
                    "source_file": filename,
                    "chunk_index": i,
                    "total_chunks": len(blocks)
                }
            })

        out_filename = filename.replace(".txt", "_chunks.json")
        out_path = os.path.join(output_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ {filename} → {len(blocks)} chunks sémantiques")

if __name__ == "__main__":
    main()
