import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from scrap import TextScrapper
from traitement import RetrievalPipeline, list_files_in_adls, ACCOUNT_NAME, FILESYSTEM

def run_pipeline():
    """Main pipeline orchestrator: scraping -> indexing"""
    print("="*80)
    print("   DÉMARRAGE DU PIPELINE AUTOMATISÉ (SCRAP -> INDEX) ".center(80))
    print("="*80 + "\n")

    print("--- ÉTAPE 1: SCRAPING & CONVERSION ---")
    
    urls = [
        "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/parcours-dechets-professionnels-reduire-trier-et-gerer-vos-dechets-bruxelles"
    ]
    
    total_new_files = 0
    
    for u in urls:
        print(f"\nTraitement de l'URL: {u}")
        scrap = TextScrapper(u)
        
        scrap.download_text()
        scrap.pdf_to_txt()
        scrap.clean_text()
        scrap.clone_verifie()
        
        total_new_files += scrap.new_files_count

    print(f"\nTotal nouveaux fichiers détectés et convertis : {total_new_files}")

    print("\n" + "="*80)
    if total_new_files > 0:
        print("   NOUVEAUX FICHIERS DÉTECTÉS -> LANCEMENT DE L'INDEXATION ".center(80))
        print("="*80 + "\n")
        
        try:
            retrieval_pipeline = RetrievalPipeline()
            
            file_list = list_files_in_adls(retrieval_pipeline.file_system, retrieval_pipeline.clean_data_dir)
            
            if not file_list:
                print("Attention: Aucun fichier trouvé dans clean_data malgré la détection de nouveaux fichiers.")
            else:
                print(f"Indexation de {len(file_list)} fichiers...")
                for file_name in file_list:
                    retrieval_pipeline.index_text(file_name)
            
            retrieval_pipeline.save_to_adls()
            retrieval_pipeline.cleanup()
            
            print("\n" + "="*80)
            print("   PIPELINE TERMINÉ AVEC SUCCÈS ".center(80))
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\nERREUR CRITIQUE LORS DE L'INDEXATION: {e}")
            try:
                if 'retrieval_pipeline' in locals():
                    retrieval_pipeline.cleanup()
            except:
                pass
            sys.exit(1)
            
    else:
        print("   AUCUN NOUVEAU FICHIER -> INDEXATION IGNORÉE ".center(80))
        print("="*80 + "\n")
        print("Le pipeline s'est terminé normalement sans mise à jour de la base de données.")

if __name__ == "__main__":
    run_pipeline()
