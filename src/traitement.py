import chromadb 
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import json
import re

try:
    from azure.identity import ClientSecretCredential, DefaultAzureCredential
    from azure.storage.filedatalake import DataLakeServiceClient
except ModuleNotFoundError:
    raise SystemExit(
        "SDK Azure manquant: installez 'azure-identity' et 'azure-storage-file-datalake'.\n"
        "Exemples:\n"
        "  - pip:    python -m pip install azure-identity azure-storage-file-datalake\n"
        "  - conda:  conda install -c conda-forge azure-identity azure-storage-file-datalake"
    )

# ---------- CONFIGURATION ADLS ----------
# Variables d'environnement attendues:
# - AZURE_STORAGE_ACCOUNT: nom du compte (sans suffixe .dfs.core.windows.net)
# - AZURE_STORAGE_KEY: clé de compte (option 1 d'authentification)
# - STORAGE_FILESYSTEM: nom du file system (ex: 'data')
# - Option service principal (si pas de STORAGE_KEY):
#   AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
ACCOUNT_NAME = "juridicai"
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_KEY", "").strip()
FILESYSTEM = "data"

CLEAN_DIR = "clean_data"
JSON_FILE = "base_dechets.json"
# ---------------------------------------

def get_dls_client():
    """Crée et retourne un client Azure Data Lake Storage"""
    if not ACCOUNT_NAME or not FILESYSTEM:
        raise SystemExit("Veuillez définir AZURE_STORAGE_ACCOUNT et STORAGE_FILESYSTEM.")
    account_url = f"https://{ACCOUNT_NAME}.dfs.core.windows.net"

    if ACCOUNT_KEY:
        return DataLakeServiceClient(account_url=account_url, credential=ACCOUNT_KEY)

    # Essayer DefaultAzureCredential (Managed Identity / dev env), sinon service principal
    try:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        return DataLakeServiceClient(account_url=account_url, credential=credential)
    except Exception:
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        if not (tenant_id and client_id and client_secret):
            raise SystemExit(
                "Aucun mode d'authentification disponible. Fournissez AZURE_STORAGE_KEY "
                "ou un service principal (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)."
            )
        credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
        return DataLakeServiceClient(account_url=account_url, credential=credential)

def list_files_in_adls(file_system_client, directory_path):
    """Liste tous les fichiers dans un répertoire ADLS"""
    try:
        paths_iter = file_system_client.get_paths(path=directory_path)
        files = []
        for p in paths_iter:
            if not p.is_directory and p.name.startswith(directory_path + "/"):
                files.append(os.path.basename(p.name))
        return files
    except Exception:
        return []

def read_text_from_adls(file_system_client, file_path):
    """Lit un fichier texte depuis ADLS et retourne son contenu"""
    try:
        file_client = file_system_client.get_file_client(file_path)
        if hasattr(file_client, "read_file"):
            downloader = file_client.read_file()
        else:
            downloader = file_client.download_file()
        return downloader.readall().decode("utf-8")
    except Exception as e:
        print(f"Erreur lors de la lecture: {e}")
        return None

class RetrievalPipeline:
    def __init__(self):
        # Initialise le modèle SentenceTransformer pour les embeddings de texte
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        #base du projet ou ce fichier ce trouve
        self.base_dir = Path(__file__).resolve().parent
        self.project_root = self.base_dir.parent

        # chemin pour le dossier chroma (local, pas dans ADLS)
        self.db_path = (self.project_root / "data" / "chroma_db").resolve()
        # Crée ou connecte une base de données Chroma persistante au chemin donné
        self.chroma_client = chromadb.PersistentClient(path=str(self.db_path))
        # Récupère ou crée une collection dans la base appelée "law_text"
        self.collection = self.chroma_client.get_or_create_collection(name="law_text")

        # Initialiser le client Azure Data Lake Storage
        self.dls_client = get_dls_client()
        self.file_system = self.dls_client.get_file_system_client(FILESYSTEM)
        
        # Chemins Azure pour les dossiers
        self.clean_data_dir = CLEAN_DIR
        self.json_file_path = JSON_FILE
        
    def find_category(self, text):
        # trouve la categorie aproximatif
        
        # recupere le dic dans base_dechets.json depuis ADLS
        json_content = read_text_from_adls(self.file_system, self.json_file_path)
        if json_content is None:
            raise SystemExit(f"Impossible de lire {self.json_file_path} depuis ADLS.")
        category = json.loads(json_content)
        # cree un dic avec les meme cle que l original
        dominent_category = {key:0 for key in category}
        # parcour chaque cle de category
        for key,data in category.items():
            # recupere les poid de chaque categorie
            weight = data["weight"]
            total = 0
            for word in data["keywords"]:
                #pour chaque partie de texte conte l'aparition des mot en ajoutent le poid
                pattern = r"\b" + word + r"\b"
                total += len(re.findall(pattern, text))
                dominent_category[key] = total * weight
        
        # la categorie qui apparait le plus
        dominent = max(dominent_category, key=dominent_category.get)
        # return la categorie
        return dominent

    def chunking(self, text, chunk_size=450, overlap=50):
        # Divise un texte long en petits segments qui se chevauchent pour une meilleure qualité d’embedding
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            # si le chunk est assez grand, on le garde
            if len(chunk) >= 250:
                chunks.append(chunk)

            # Déplace la fenêtre vers l’avant, en gardant un chevauchement pour préserver le contexte
            start += chunk_size - overlap

        return chunks

    def index_text(self, file_name):
        """
        Indexe un fichier texte depuis ADLS
        
        Args:
            file_name: Nom du fichier dans le dossier clean_data (ex: "document.txt")
        """
        # Construit le chemin complet dans ADLS
        adls_file_path = f"{self.clean_data_dir}/{file_name}"
        
        # Lit le contenu du fichier texte depuis ADLS
        text_law = read_text_from_adls(self.file_system, adls_file_path)
        if text_law is None:
            print(f"Erreur: Impossible de lire {file_name} depuis ADLS.")
            return

        # Divise le texte en segments
        chunks = self.chunking(text_law)
        # Récupère le nom du fichier (sans extension) pour l'utiliser comme identifiant unique
        file_id = os.path.splitext(file_name)[0]
        
        #essaye de recuperer la date
        pattern = r"(janv|fevr|mars|avr|mai|juin|juil|aout|sept|oct|nov|dec)[\s\-]+[0-9]{4}"
        # essaye de trouve une date au debut du texte
        match = re.search(pattern, text_law[:100], re.IGNORECASE)
        # si match = True return la date recupere
        if match:
            date = match.group(0)
        else:
            date="unknow"
        # Récupère les identifiants de documents existants dans la collection Chroma pour éviter les doublons
        existing_ids = set(self.collection.get()["ids"])
        new_chunks = 0
        
        idx = len(existing_ids)

        # Boucle sur tous les segments du fichier
        for i, chunk in enumerate(chunks):
            idx += 1
            # Crée un identifiant unique pour chaque segment basé sur le nom du fichier et son index
            chunk_id = f"{file_id}_chunk_{i}" 
            # recupere la categorie
            category = self.find_category(chunk)
            # Passe ce segment s’il est déjà indexé
            if chunk_id in existing_ids:
                continue
            
            # Génère un embedding pour le segment à l’aide du modèle
            embedding = self.model.encode(chunk, convert_to_numpy=True)
            # Ajoute le segment, son embedding et ses métadonnées (chemin du fichier) à la collection
            self.collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": file_id, "categorie": category, "date": date, "chunk_id":idx}]
            )
            new_chunks += 1

if __name__ == "__main__":
    # Initialise le pipeline de recherche
    retrieval_pipeline = RetrievalPipeline()
    
    # Parcourt tous les fichiers texte dans le dossier 'clean_data' depuis ADLS et les indexe
    file_list = list_files_in_adls(retrieval_pipeline.file_system, retrieval_pipeline.clean_data_dir)
    
    if not file_list:
        print(f"Aucun fichier trouvé dans {ACCOUNT_NAME}/{FILESYSTEM}/{retrieval_pipeline.clean_data_dir}/")
        print("Assurez-vous que les fichiers ont été traités par scrap.py et sont disponibles dans ADLS.")
    else:
        print(f"Trouvé {len(file_list)} fichier(s) à indexer dans {ACCOUNT_NAME}/{FILESYSTEM}/{retrieval_pipeline.clean_data_dir}/")
        for file_name in file_list:
            print(f"Indexation de: {file_name}")
            retrieval_pipeline.index_text(file_name)