import chromadb 
import os
import tempfile
import shutil

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
ACCOUNT_NAME = "juridicai"
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_KEY", "").strip()
FILESYSTEM = "data"
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

def download_directory(file_system_client, remote_path, local_path):
    """Télécharge récursivement un dossier depuis ADLS"""
    os.makedirs(local_path, exist_ok=True)
    try:
        paths = file_system_client.get_paths(path=remote_path)
        for p in paths:
            if p.is_directory:
                continue
            
            # Reconstruire le chemin local
            relative_path = os.path.relpath(p.name, remote_path)
            local_file_path = os.path.join(local_path, relative_path)
            
            # Créer les dossiers parents locaux
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            # Télécharger
            file_client = file_system_client.get_file_client(p.name)
            with open(local_file_path, "wb") as f:
                if hasattr(file_client, "read_file"):
                    download = file_client.read_file()
                else:
                    download = file_client.download_file()
                download.readinto(f)
        print(f"Dossier téléchargé depuis ADLS: {remote_path} -> {local_path}")
    except Exception as e:
        print(f"Info: Impossible de télécharger le dossier (il n'existe peut-être pas encore): {e}")

class RetrievalPipeline:
    """
    Version simplifiée pour le serveur API - LECTURE SEULE
    Pas d'embedding, pas d'indexation, juste la connexion à ChromaDB
    """
    def __init__(self):
        # Initialiser le client Azure Data Lake Storage
        self.dls_client = get_dls_client()
        self.file_system = self.dls_client.get_file_system_client(FILESYSTEM)
        
        # --- GESTION CHROMADB SUR ADLS (SYNC - READ ONLY) ---
        # Utilisation d'un dossier temporaire système
        self.local_db_path = tempfile.mkdtemp(prefix="chroma_db_")
        self.remote_db_path = "chromadb"
        
        print(f"[SERVER] Initialisation: Dossier temporaire créé à {self.local_db_path}")
        print("[SERVER] Initialisation: Téléchargement de la base Chroma depuis ADLS...")
        download_directory(self.file_system, self.remote_db_path, self.local_db_path)
        
        # Connecte à la base de données Chroma (lecture seule)
        self.chroma_client = chromadb.PersistentClient(path=self.local_db_path)
        # Récupère la collection existante
        self.collection = self.chroma_client.get_or_create_collection(name="law_text")
        print(f"[SERVER] Collection chargée avec {self.collection.count()} documents")

    def cleanup(self):
        """Nettoie le dossier temporaire"""
        try:
            print(f"[SERVER] Nettoyage: Suppression du dossier temporaire {self.local_db_path}")
            shutil.rmtree(self.local_db_path)
        except Exception as e:
            print(f"[SERVER] Erreur lors du nettoyage: {e}")