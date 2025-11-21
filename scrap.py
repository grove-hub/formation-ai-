import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os 
from pathlib import Path
import re 
from pypdf import PdfReader 
from docx import Document
# Recupere les document des url passe et les transforme en texte netoyer et pret pour le pipeline

class TextScraper():
    def __init__(self, url):
        
        try:
            self.headers = {
                # Utilisez un User-Agent commun pour Chrome, Firefox, ou autre
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
            }
            self.url = url
            self.response = requests.get(self.url, self.headers)
            self.response.raise_for_status()

            self.html = self.response.text

            self.soup = BeautifulSoup(self.html, "html.parser")
        except:
            self.soup = ""

        self.pdf_urls = []    

        #base du projet ou ce fichier ce trouve et du fichier de sortie
        self.base_dir = Path(__file__).resolve().parent
        self.project_root = self.base_dir
        # fichier des pdf
        self.raw_pdf = os.path.join(self.project_root, "raw_pdf_test")
        # fichier sortie
        self.output_folder = os.path.join(self.project_root, "before_clean_data")
        # fichier pour les entierement pret
        self.final_folder = os.path.join(self.project_root, "clean_data_test")
        
        # cree les fichier si il n existe pas
        os.makedirs(self.raw_pdf, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.final_folder, exist_ok=True)

    def get_text(self):
        
        try:
            for a in self.soup.find_all("a", href=True, target="_blank"):
                href = a["href"]

                if href.lower() and "document" in str(href):
                    pdf_url = urljoin(self.url, href)
                    self.pdf_urls.append(pdf_url)
        except Exception as e:
            print("Erreur de l'url: ", e)
        
    
    def download_text(self):
        self.get_text()

        file_list = os.listdir(self.raw_pdf)

        for pdf_url in self.pdf_urls:
            print("Has recovered :", pdf_url)
            try:
                request = requests.get(pdf_url, stream=True)
                request.raise_for_status()
            except:
                continue

            # nom du fichier = dernière partie de l'URL
            if ".docx" in pdf_url or "doc_num.php" in pdf_url:

                # essayer de récupérer le vrai nom dans l'en-tête HTTP
                cd = request.headers.get("Content-Disposition")

                if cd:
                    # extraire le nom du fichier depuis l'en-tête
                    filename = re.findall('filename="?(.+)"?', cd)[0]
                else:
                    # fallback si pas d'en-tête → créer un nom propre
                    filename = pdf_url.split("/")[-1]
                    filename = filename.replace("?", "_").replace("=", "_")  # retirer caractères interdits
                    if not filename.lower().endswith(".docx"):
                        filename += ".docx"
            else:
                filename = pdf_url.split("/")[-1]
            
            filename = filename.strip().strip('"').strip("'")
            filename = re.sub(r'[<>:"/\\|?*]', '_',filename)
            filepath = os.path.join(self.raw_pdf, filename)

            try:
                if not filename in file_list:
                    with open(filepath, "wb") as f:
                        for chunk in request.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print("→ Sauvegardé dans", filepath)
                else:
                    print(f"Text: {filename}, already here.")
            except Exception as e:
                print("can't save:", e)

    def pdf_to_txt(self):
        """
        Convertit tous les PDFs d'un dossier en fichiers TXT
        
        Args:
            pdf_folder: Dossier contenant les PDFs à convertir
            output_folder: Dossier de destination pour les fichiers TXT
        """
        
        # Récupérer tous les fichiers PDF
        pdf_files = os.listdir(self.raw_pdf)
        
        if not pdf_files:
            print(f"  Aucun fichier PDF trouvé dans le dossier '{self.raw_pdf}/'")
            print(f" Placez vos fichiers PDF dans le dossier '{self.raw_pdf}/' et relancez le script.")
            return
        
        print(f"\n{'='*80}")
        print(f"   CONVERSION PDF → TXT ".center(80))
        print(f"{'='*80}\n")
        print(f" Dossier source : {self.raw_pdf}/")
        print(f" Dossier destination : {self.output_folder}/")
        print(f" Nombre de PDFs trouvés : {len(pdf_files)}\n")
        print(f"{'='*80}\n")
        
        success_count = 0
        error_count = 0
        
        # liste avec tout les nom des fichier texte de clean_data
        text_list = os.listdir(self.output_folder)

        # Convertir chaque PDF
        for i, pdf_path in enumerate(pdf_files, 1):

            pdf_path = os.path.join(self.raw_pdf, pdf_path)
            pdf_name = os.path.basename(pdf_path)
            
            try:
                try:
                    txt_name = pdf_name.replace('.pdf', '.txt')
                    output_path = os.path.join(self.output_folder, txt_name)
                    
                    if not txt_name in  text_list:
                        print(f"[{i}/{len(pdf_files)}]  Conversion de : {pdf_name}")
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
                        print(f"    Converti avec succès : {txt_name}")
                        print(f"    Pages : {pages_count} | Caractères : {chars_count:,}\n")
                        
                        success_count += 1
                
                except:
                    txt_name = pdf_name.replace('.docx', '.txt')
                    output_path = os.path.join(self.output_folder, txt_name)
                    
                    if not txt_name in text_list:
                        print(f"[{i}/{len(pdf_files)}]  Conversion de : {pdf_name}")
                        # Lire le PDF
                        doc = Document(pdf_path)
                        
                        # Extraire le texte de toutes les pages
                        text = ""
                        for paragraph in doc.paragraphs:
                            page_text = page.extract_text() or ""
                            text += paragraph.text
                        
                        # Écrire le texte dans un fichier TXT
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(text)
                        
                        # Afficher les statistiques
                        pages_count = len(reader.pages)
                        chars_count = len(text)
                        print(f"    Converti avec succès : {txt_name}")
                        print(f"    Pages : {pages_count} | Caractères : {chars_count:,}\n")
                        
                        success_count += 1
                
            except Exception as e:
                print(f"  Erreur lors de la conversion : {str(e)}\n")
                error_count += 1
        
        # Résumé final
        print(f"{'='*80}")
        print(f"   RÉSUMÉ DE LA CONVERSION ".center(80))
        print(f"{'='*80}\n")
        print(f" Conversions réussies : {success_count}")
        print(f" Conversions échouées : {error_count}")
        print(f" Fichiers TXT disponibles dans : {self.output_folder}/\n")
        print(f"{'='*80}\n")


    def clean_text(self):
        text_path = os.listdir(self.output_folder)

        for text_name in text_path:
            text_directory = os.path.join(self.output_folder, text_name)

            with open(text_directory, mode="r", encoding="utf-8") as r:
                text = r.read()

            # enleve les espace
            text_to_clean = re.sub(r'\s+', ' ', text)
            #enleve les espace devant la ponctuation double
            text_to_clean = re.sub(r'\s([:;?!])', r'\1', text_to_clean)
            # un espace apre ponctuation double
            text_to_clean = re.sub(r'([:;?!])([a-zA-Z0-9])', r'\1 \2', text_to_clean)
            # retire l espace devant la virgule et le point
            text_to_clean = re.sub(r'\s([,\.])', r'\1', text_to_clean)
            # reduit les espace autour des parenthese
            text_to_clean = re.sub(r'\s(\(|\))', r'\1', text_to_clean) # avent ( ou )
            text_to_clean = re.sub(r'(\()\s', r'\1', text_to_clean) # apre ( 
            text_to_clean = re.sub(r'\s(\))', r'\1', text_to_clean) # avant )
            # supprime les espace multiple 
            text_to_clean = re.sub(r'\s{2,}', ' ', text_to_clean)
            # suprime les /
            text_to_clean = text_to_clean.replace("/", "")
            # transmorme tout en minuscule
            text_to_clean = text_to_clean.lower()
            #
            text_to_clean = text_to_clean.strip()

            clean_text_directory = os.path.join(self.final_folder, text_name)

            with open(clean_text_directory, "w", encoding="utf-8") as t:
                t.write(text_to_clean)

if __name__ == "__main__":
    # tout les site qu on veut scraper
    num = int(input("Combien de site a scraper?: "))
    urls = [
        "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/la-gestion-et-la-prevention-des-dechets-de-chantier",
        "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/comment-gerer-vos-dechets-professionnels-de-la-prevention-levacuation",
        "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/que-faire-de-vos-dechets-demballage",
        "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/horeca-et-commerces-alimentaires-conseils-zero-dechet-et-gestion-des-dechets"
    ]
    for n in range(num):
        url = str(input("Votre url: "))
        urls.append(url)
    for u in urls:
        scrap = TextScraper(u)
        # telecharge tout les texte
        scrap.download_text()
        scrap.pdf_to_txt()
        scrap.clean_text()