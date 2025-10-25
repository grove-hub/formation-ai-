"""
Script de conversion PDF vers TXT
Convertit tous les fichiers PDF du dossier raw_pdfs/ en fichiers TXT dans clean_data/
"""
from pypdf import PdfReader 
import os

def pdf_to_txt(pdf_folder="project\\raw_pdfs", output_folder="project\\clean_data"):
    """
    Convertit tous les PDFs d'un dossier en fichiers TXT
    
    Args:
        pdf_folder: Dossier contenant les PDFs à convertir
        output_folder: Dossier de destination pour les fichiers TXT
    """
    
    # Récupérer tous les fichiers PDF
    pdf_files = os.listdir(pdf_folder)
    
    if not pdf_files:
        print(f"⚠️  Aucun fichier PDF trouvé dans le dossier '{pdf_folder}/'")
        print(f"💡 Placez vos fichiers PDF dans le dossier '{pdf_folder}/' et relancez le script.")
        return
    
    print(f"\n{'='*80}")
    print(f" 📄  CONVERSION PDF → TXT ".center(80))
    print(f"{'='*80}\n")
    print(f"📂 Dossier source : {pdf_folder}/")
    print(f"📂 Dossier destination : {output_folder}/")
    print(f"📊 Nombre de PDFs trouvés : {len(pdf_files)}\n")
    print(f"{'='*80}\n")
    
    success_count = 0
    error_count = 0
    
    # Convertir chaque PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_folder, pdf_path)
        pdf_name = os.path.basename(pdf_path)
        txt_name = pdf_name.replace('.pdf', '.txt')
        output_path = os.path.join(output_folder, txt_name)
        
        try:
            print(f"[{i}/{len(pdf_files)}] 🔄 Conversion de : {pdf_name}")
            
            # Lire le PDF
            reader = PdfReader(pdf_path)
            
            # Extraire le texte de toutes les pages
            text = ""
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                text += page_text
            
            # Écrire le texte dans un fichier TXT
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            # Afficher les statistiques
            pages_count = len(reader.pages)
            chars_count = len(text)
            print(f"   ✅ Converti avec succès : {txt_name}")
            print(f"   📄 Pages : {pages_count} | Caractères : {chars_count:,}\n")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur lors de la conversion : {str(e)}\n")
            error_count += 1
    
    # Résumé final
    print(f"{'='*80}")
    print(f" 📊  RÉSUMÉ DE LA CONVERSION ".center(80))
    print(f"{'='*80}\n")
    print(f"✅ Conversions réussies : {success_count}")
    print(f"❌ Conversions échouées : {error_count}")
    print(f"📁 Fichiers TXT disponibles dans : {output_folder}/\n")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    # Créer le dossier raw_pdfs s'il n'existe pas
    # if not os.path.exists("/project/raw_pdfs"):
    #     os.makedirs("raw_pdfs")
    #     print("📁 Dossier 'raw_pdfs/' créé.")
    #     print("💡 Placez vos fichiers PDF dans ce dossier et relancez le script.\n")
    
    # Lancer la conversion
    pdf_to_txt()
