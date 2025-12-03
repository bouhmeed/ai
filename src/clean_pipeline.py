# src/clean_pipeline.py
"""
Nettoie les dossiers intermédiaires du pipeline RAG et les caches Python.
Ne supprime PAS 'notes_raw' ni 'templates'.
"""

import os
import shutil

def empty_folder(folder_path):
    """Supprime tout le contenu d'un dossier sans supprimer le dossier lui-même."""
    if not os.path.exists(folder_path):
        return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"  ⚠️ Erreur lors de la suppression de {file_path}: {e}")

def main():
    print("🧹 Nettoyage du pipeline RAG...")

    # --- 1. Nettoyer data/output/ ---
    output_dir = os.path.join(".", "data", "output")
    if os.path.exists(output_dir):
        folders_to_clean = ["extracted", "chunks", "embeddings", "index", "fad_generated"]
        for folder in folders_to_clean:
            folder_path = os.path.join(output_dir, folder)
            empty_folder(folder_path)
            print(f"  ✅ Vidé : {folder_path}")

        # Supprimer fichier de cache
        cache_file = os.path.join(output_dir, "pipeline_cache.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"  ✅ Supprimé : {cache_file}")
    else:
        print("  ℹ️ Dossier 'data/output/' absent → ignoré.")

    # --- 2. Nettoyer __pycache__ au niveau racine et dans src/ ---
    for pycache_dir in ["__pycache__", os.path.join("src", "__pycache__")]:
        if os.path.exists(pycache_dir):
            try:
                shutil.rmtree(pycache_dir)
                print(f"  ✅ Supprimé : {pycache_dir}")
            except Exception as e:
                print(f"  ⚠️ Erreur suppression {pycache_dir}: {e}")
        else:
            print(f"  ℹ️ Absent : {pycache_dir}")

    print("\n✨ Pipeline nettoyé ! Prêt pour une nouvelle génération.")
    return "✅ Pipeline nettoyé avec succès !"

if __name__ == "__main__":
    main()