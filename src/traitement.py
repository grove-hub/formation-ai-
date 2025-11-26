import chromadb 
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
import json
import re
import tempfile
import atexit
import shutil
import sys
from typing import Optional

# Azure File Share
try:
    from azure.storage.fileshare import ShareServiceClient, ShareClient, ShareDirectoryClient
    from azure.core.exceptions import ResourceNotFoundError, AzureError
    AZURE_FILE_SHARE_AVAILABLE = True
except ImportError:
    AZURE_FILE_SHARE_AVAILABLE = False
    print("WARNING: azure-storage-file-share non installe. Installez-le avec: pip install azure-storage-file-share")

# Azure Blob Storage
try:
    from azure.storage.blob import BlobServiceClient
    from azure.core.exceptions import AzureError as BlobAzureError
    AZURE_BLOB_AVAILABLE = True
except ImportError:
    AZURE_BLOB_AVAILABLE = False
    print("WARNING: azure-storage-blob non installe. Installez-le avec: pip install azure-storage-blob")

# Azure Data Lake Storage Gen2
try:
    from azure.identity import ClientSecretCredential, DefaultAzureCredential
    from azure.storage.filedatalake import DataLakeServiceClient
    AZURE_ADLS_AVAILABLE = True
except ImportError:
    AZURE_ADLS_AVAILABLE = False
    print("WARNING: azure-storage-file-datalake non installe. Installez-le avec: pip install azure-storage-file-datalake")

# Charger les variables d'environnement depuis .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration: chemin vers base_dechets.json dans Azure Blob Storage (container 'data')
BASE_DECHETS_JSON_PATH = "base_dechets.json"

class AzureConfig:
    """Classe utilitaire pour gérer la configuration Azure de manière centralisée"""
    
    @staticmethod
    def get_azure_config():
        """
        Récupère la configuration Azure depuis les variables d'environnement.
        Utilise les valeurs par défaut comme dans le code original.
        
        Returns:
            Dict avec 'account', 'key', 'file_share_name', 'container_name'
        """
        # Valeurs par défaut comme dans traitement_azure2.py
        account = os.getenv("AZURE_STORAGE_ACCOUNT", "juridicai").strip()
        key = os.getenv("AZURE_STORAGE_KEY", "").strip()
        file_share_name = os.getenv("AZURE_FILE_SHARE_NAME", "chromadb").strip().lower()
        container_name = os.getenv("AZURE_CONTAINER_NAME", "data").strip()
        
        return {
            'account': account,
            'key': key,
            'file_share_name': file_share_name,
            'container_name': container_name
        }
    
    @staticmethod
    def build_connection_string(account: str, key: str) -> str:
        """Construit la chaîne de connexion Azure"""
        return f"DefaultEndpointsProtocol=https;AccountName={account};AccountKey={key};EndpointSuffix=core.windows.net"

class RetrievalPipeline:
    def __init__(self):
        # Initialise le modèle SentenceTransformer pour les embeddings de texte
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        #base du projet ou ce fichier ce trouve
        self.base_dir = Path(__file__).resolve().parent
        self.project_root = self.base_dir.parent
        
        # Configuration Azure centralisée
        azure_config = AzureConfig.get_azure_config()
        self.azure_storage_account = azure_config['account']
        self.azure_storage_key = azure_config['key']
        self.azure_file_share_name = azure_config['file_share_name']
        self.azure_container_name = azure_config['container_name']
        
        # Dossier temporaire pour Azure File Share (sera nettoyé à la fin)
        self.temp_mount = None
        self._register_cleanup()
        
        # Configuration Azure File Share pour ChromaDB
        self.use_azure_file_share = False
        self.share_service_client = None
        
        if AZURE_FILE_SHARE_AVAILABLE and self.azure_storage_account and self.azure_storage_key:
            try:
                # Créer un point de montage temporaire local qui sera synchronisé avec Azure File Share
                self.temp_mount = tempfile.mkdtemp(prefix="chroma_azure_")
                self.db_path = Path(self.temp_mount) / "chroma_db"
                self.db_path.mkdir(parents=True, exist_ok=True)
                
                # Se connecter à Azure File Share et synchroniser
                connection_string = AzureConfig.build_connection_string(
                    self.azure_storage_account, 
                    self.azure_storage_key
                )
                self.share_service_client = ShareServiceClient.from_connection_string(connection_string)
                
                # Créer le share s'il n'existe pas
                self._ensure_azure_file_share_exists()
                
                # Synchroniser les fichiers depuis Azure File Share vers le dossier local temporaire
                self._sync_from_azure_file_share(
                    self.share_service_client, 
                    self.azure_file_share_name, 
                    str(self.db_path)
                )
                
                print(f"OK: ChromaDB configure avec Azure File Share: {self.azure_file_share_name}")
                self.use_azure_file_share = True
            except (AzureError, Exception) as e:
                print(f"WARNING: Erreur de connexion a Azure File Share: {e}")
                print("   Utilisation du stockage local")
                self._cleanup_temp_mount()
                self.db_path = (self.project_root / "data" / "chroma_db").resolve()
                self.db_path.mkdir(parents=True, exist_ok=True)
                self.use_azure_file_share = False
        else:
            # Utiliser le stockage local
            self.db_path = (self.project_root / "data" / "chroma_db").resolve()
            self.db_path.mkdir(parents=True, exist_ok=True)
            self.use_azure_file_share = False
            
            if not AZURE_FILE_SHARE_AVAILABLE:
                print("WARNING: azure-storage-file-share non installe")
            elif not self.azure_storage_account:
                print("INFO: Mode local active (AZURE_STORAGE_ACCOUNT non defini)")
            elif not self.azure_storage_key:
                print("INFO: Mode local active (AZURE_STORAGE_KEY non defini)")
        
        # Crée ou connecte une base de données Chroma persistante au chemin donné
        self.chroma_client = chromadb.PersistentClient(path=str(self.db_path))
        # Récupère ou crée une collection dans la base appelée "law_text"
        self.collection = self.chroma_client.get_or_create_collection(name="law_text")
        
        # Configuration Azure Data Lake Storage Gen2 pour lire clean_data et base_dechets.json
        self.use_azure_adls = False
        self.adls_client = None
        self.adls_file_system = None
        self.adls_filesystem_name = self.azure_container_name  # Utilise le même nom que le container
        
        if AZURE_ADLS_AVAILABLE and self.azure_storage_account and self.azure_storage_key:
            try:
                account_url = f"https://{self.azure_storage_account}.dfs.core.windows.net"
                self.adls_client = DataLakeServiceClient(account_url=account_url, credential=self.azure_storage_key)
                self.adls_file_system = self.adls_client.get_file_system_client(self.adls_filesystem_name)
                # Tester la connexion
                self.adls_file_system.get_file_system_properties()
                self.use_azure_adls = True
                print(f"OK: Lecture depuis Azure Data Lake Storage Gen2: {self.azure_storage_account}/{self.adls_filesystem_name}")
            except Exception as e:
                print(f"WARNING: Impossible de se connecter a Azure Data Lake Storage: {e}")
                self.use_azure_adls = False
        
        # Configuration Azure Blob Storage pour lire clean_data depuis le container 'data' (fallback)
        self.use_azure_blob_for_data = False
        self.blob_service_client = None
        if not self.use_azure_adls and AZURE_BLOB_AVAILABLE and self.azure_storage_account and self.azure_storage_key:
            try:
                connection_string = AzureConfig.build_connection_string(
                    self.azure_storage_account, 
                    self.azure_storage_key
                )
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                # Tester la connexion au container 'data'
                container_client = self.blob_service_client.get_container_client(self.azure_container_name)
                container_client.get_container_properties()  # Test de connexion
                self.use_azure_blob_for_data = True
                print(f"OK: Lecture de clean_data depuis Azure Blob Storage: {self.azure_container_name}/clean_data")
            except (BlobAzureError, Exception) as e:
                print(f"WARNING: Impossible de se connecter a Azure Blob Storage pour clean_data: {e}")
                self.use_azure_blob_for_data = False
        
        if not self.use_azure_adls and not self.use_azure_blob_for_data:
            # Chemin vers clean_data local
            self.data_dir = (self.project_root / "data" / "clean_data").resolve()
        else:
            self.data_dir = None  # Pas utilisé si on utilise Azure
        
        # Compteur pour la synchronisation batch
        self._pending_sync = False
    
    def _register_cleanup(self):
        """Enregistre une fonction de nettoyage à l'arrêt du programme"""
        def cleanup():
            self._cleanup_temp_mount()
            self._sync_to_azure_file_share()
        atexit.register(cleanup)
    
    def close(self):
        """Ferme proprement les connexions ChromaDB avant le nettoyage"""
        try:
            if hasattr(self, 'chroma_client') and self.chroma_client:
                if hasattr(self, 'collection'):
                    self.collection = None
                self.chroma_client = None
        except Exception:
            pass
    
    def _cleanup_temp_mount(self):
        """Nettoie le dossier temporaire si il existe"""
        if not self.temp_mount or not os.path.exists(self.temp_mount):
            return
        
        self.close()
        
        import time
        import gc
        gc.collect()
        time.sleep(0.5)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.rmtree(self.temp_mount)
                return
            except (PermissionError, OSError):
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                    gc.collect()
            except Exception:
                pass
    
    def _ensure_azure_file_share_exists(self):
        """Crée le File Share Azure s'il n'existe pas"""
        try:
            share_client = self.share_service_client.get_share_client(self.azure_file_share_name)
            try:
                share_client.get_share_properties()
            except ResourceNotFoundError:
                share_client.create_share(quota=5120)
                print(f"OK: Azure File Share '{self.azure_file_share_name}' cree")
        except AzureError as e:
            print(f"WARNING: Erreur lors de la creation/verification du File Share: {e}")
            raise
    
    def _sync_from_azure_file_share(self, share_service_client, share_name, local_path):
        """Synchronise les fichiers depuis Azure File Share vers le système local"""
        try:
            share_client = share_service_client.get_share_client(share_name)
            directory_client = share_client.get_directory_client("chroma_db")
            os.makedirs(local_path, exist_ok=True)
            
            try:
                for item in directory_client.list_directories_and_files():
                    if item.is_directory:
                        sub_dir = os.path.join(local_path, item.name)
                        os.makedirs(sub_dir, exist_ok=True)
                        sub_dir_client = directory_client.get_subdirectory_client(item.name)
                        self._download_directory(sub_dir_client, sub_dir)
                    else:
                        file_client = directory_client.get_file_client(item.name)
                        file_path = os.path.join(local_path, item.name)
                        with open(file_path, "wb") as f:
                            data = file_client.download_file()
                            f.write(data.readall())
            except ResourceNotFoundError:
                pass
        except (AzureError, Exception) as e:
            print(f"WARNING: Erreur lors de la synchronisation depuis Azure File Share: {e}")
    
    def _download_directory(self, directory_client, local_path):
        """Télécharge récursivement un répertoire depuis Azure File Share"""
        try:
            for item in directory_client.list_directories_and_files():
                if item.is_directory:
                    sub_dir = os.path.join(local_path, item.name)
                    os.makedirs(sub_dir, exist_ok=True)
                    sub_dir_client = directory_client.get_subdirectory_client(item.name)
                    self._download_directory(sub_dir_client, sub_dir)
                else:
                    file_client = directory_client.get_file_client(item.name)
                    file_path = os.path.join(local_path, item.name)
                    with open(file_path, "wb") as f:
                        data = file_client.download_file()
                        f.write(data.readall())
        except ResourceNotFoundError:
            pass
    
    def _sync_to_azure_file_share(self):
        """Synchronise les fichiers locaux vers Azure File Share"""
        if not self.use_azure_file_share:
            return
        
        try:
            share_client = self.share_service_client.get_share_client(self.azure_file_share_name)
            directory_client = share_client.get_directory_client("chroma_db")
            
            try:
                directory_client.create_directory()
            except AzureError:
                pass
            
            for root, dirs, files in os.walk(self.db_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file_path, self.db_path)
                    azure_path = relative_path.replace("\\", "/")
                    
                    try:
                        file_client = directory_client.get_file_client(azure_path)
                        with open(local_file_path, "rb") as f:
                            file_content = f.read()
                            try:
                                file_client.get_file_properties()
                                file_client.delete_file()
                            except ResourceNotFoundError:
                                pass
                            file_client.upload_file(file_content)
                    except (AzureError, Exception) as upload_error:
                        print(f"WARNING: Erreur lors de l'upload de {azure_path}: {upload_error}")
        except (AzureError, Exception) as e:
            print(f"WARNING: Erreur lors de la synchronisation vers Azure File Share: {e}")
    
    def sync_to_azure(self):
        """Méthode publique pour forcer la synchronisation vers Azure"""
        if self._pending_sync:
            self._sync_to_azure_file_share()
            self._pending_sync = False
    
    def _list_files_from_azure_blob(self, folder: str = "clean_data"):
        """Liste les fichiers depuis Azure (ADLS ou Blob Storage) dans un dossier spécifique"""
        # Essayer ADLS d'abord
        if self.use_azure_adls and self.adls_file_system:
            try:
                paths_iter = self.adls_file_system.get_paths(path=folder)
                files = []
                for p in paths_iter:
                    if not p.is_directory and p.name.startswith(folder + "/"):
                        file_name = os.path.basename(p.name)
                        if file_name and file_name.endswith('.txt'):
                            files.append(file_name)
                return files
            except Exception as e:
                print(f"WARNING: Erreur lors de la liste des fichiers depuis Azure ADLS: {e}")
        
        # Fallback vers Blob Storage
        if self.use_azure_blob_for_data and self.blob_service_client:
            try:
                container_client = self.blob_service_client.get_container_client(self.azure_container_name)
                prefix = f"{folder}/" if folder else ""
                files = []
                for blob in container_client.list_blobs(name_starts_with=prefix):
                    file_name = blob.name.replace(prefix, "")
                    if file_name and not file_name.endswith('/') and file_name.endswith('.txt'):
                        files.append(file_name)
                return files
            except (BlobAzureError, Exception) as e:
                print(f"WARNING: Erreur lors de la liste des fichiers depuis Azure Blob Storage: {e}")
        
        return []
    
    def _read_file_from_azure_blob(self, file_path: str) -> Optional[str]:
        """Lit un fichier depuis Azure (ADLS ou Blob Storage)"""
        # Essayer ADLS d'abord
        if self.use_azure_adls and self.adls_file_system:
            try:
                file_client = self.adls_file_system.get_file_client(file_path)
                if hasattr(file_client, "read_file"):
                    downloader = file_client.read_file()
                else:
                    downloader = file_client.download_file()
                return downloader.readall().decode("utf-8")
            except Exception as e:
                print(f"WARNING: Erreur lors de la lecture de {file_path} depuis Azure ADLS: {e}")
        
        # Fallback vers Blob Storage
        if self.use_azure_blob_for_data and self.blob_service_client:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.azure_container_name,
                    blob=file_path
                )
                return blob_client.download_blob().readall().decode('utf-8')
            except (BlobAzureError, Exception) as e:
                print(f"WARNING: Erreur lors de la lecture de {file_path} depuis Azure Blob Storage: {e}")
        
        return None
    
    def _read_json_from_azure_adls(self, file_path: str) -> Optional[dict]:
        """Lit un fichier JSON depuis Azure Data Lake Storage Gen2"""
        if not self.use_azure_adls or not self.adls_file_system:
            return None
        
        try:
            file_client = self.adls_file_system.get_file_client(file_path)
            if hasattr(file_client, "read_file"):
                downloader = file_client.read_file()
            else:
                downloader = file_client.download_file()
            json_content = downloader.readall().decode("utf-8")
            return json.loads(json_content)
        except Exception as e:
            print(f"WARNING: Erreur lors de la lecture de {file_path} depuis Azure ADLS: {e}")
            return None
    
    def find_category(self, text):
        # trouve la categorie aproximatif
        
        category = None
        
        # Essayer de lire depuis Azure Data Lake Storage Gen2 d'abord (comme scrap.py)
        if self.use_azure_adls and self.adls_file_system:
            category = self._read_json_from_azure_adls(BASE_DECHETS_JSON_PATH)
        
        # Fallback vers Azure Blob Storage si ADLS n'est pas disponible
        if category is None and self.use_azure_blob_for_data and self.blob_service_client:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.azure_container_name, 
                    blob=BASE_DECHETS_JSON_PATH
                )
                json_content = blob_client.download_blob().readall().decode('utf-8')
                category = json.loads(json_content)
            except (BlobAzureError, json.JSONDecodeError, Exception) as e:
                print(f"WARNING: Impossible de lire {BASE_DECHETS_JSON_PATH} depuis Azure Blob Storage: {e}")
        
        # Fallback vers le fichier local
        if category is None:
            json_path = (self.project_root / "data" / "base_dechets.json").resolve()
            try:
                with open(json_path, mode="r", encoding="utf-8") as f:
                    category = json.load(f)
            except FileNotFoundError:
                azure_path = f"{self.azure_storage_account}/{self.adls_filesystem_name}/{BASE_DECHETS_JSON_PATH}" if self.use_azure_adls else f"{self.azure_container_name}/{BASE_DECHETS_JSON_PATH}"
                print(f"ERREUR: base_dechets.json introuvable (local: {json_path}, Azure: {azure_path})")
                return "unknown"
            except json.JSONDecodeError as e:
                print(f"ERREUR: base_dechets.json est invalide: {e}")
                return "unknown"
        
        if not isinstance(category, dict):
            print("ERREUR: base_dechets.json doit contenir un dictionnaire")
            return "unknown"
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

    def index_text(self, file_path):
        
        # Lit le contenu du fichier texte en encodage UTF-8
        if self.use_azure_adls or self.use_azure_blob_for_data:
            # Lire depuis Azure (ADLS ou Blob Storage)
            text_law = self._read_file_from_azure_blob(file_path)
            if text_law is None:
                azure_type = "Azure ADLS" if self.use_azure_adls else "Azure Blob Storage"
                print(f"ERREUR: Impossible de lire {file_path} depuis {azure_type}")
                return
        else:
            # Lire depuis le système de fichiers local
            try:
                with open(file_path, "r", encoding='utf-8') as text:
                    text_law = text.read()
            except (FileNotFoundError, UnicodeDecodeError, Exception) as e:
                print(f"ERREUR: Impossible de lire {file_path}: {e}")
                return

        # Divise le texte en segments
        chunks = self.chunking(text_law)
        # Récupère le nom du fichier (sans extension) pour l’utiliser comme identifiant unique
        file_id = os.path.splitext(os.path.basename(file_path))[0]
        
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

        # Affiche combien de nouveaux segments ont été indexés
        if new_chunks > 0:
            print(f"{new_chunks} New chunk indexed from {file_path}")
            # Marquer pour synchronisation batch
            self._pending_sync = True
    
    def query_search(self, query_text):
        # Vérifie que la requête n’est pas vide
        if not query_text or query_text.strip() == "":
            return None
        
        # Encode le texte de la requête en un vecteur d’embedding
        query_embedding = self.model.encode(query_text)
        # Recherche dans la collection Chroma les segments les plus similaires
        n_result = 3
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results= n_result
        )
        
        # list pour mettre les retour finaux des document
        final_result = []
        # reprend les metadata
        metadatas_dic = result["metadatas"][0]
        # parcour au nombre de resultat demander
        for i in range(n_result):
            # recupere les id des chunk
            metadata = metadatas_dic[i]
            idx = metadata["chunk_id"]
            # fait une recherche des chunk voisin 
            neighbors = self.collection.get(
                where={
                    "chunk_id":{"$in": [idx-1, idx, idx+1]}
                }
            )
            # ajoute les document trouver 
            doc_str = ""
            for doc in neighbors["documents"]:
                doc_str += str(doc)
            final_result.append(doc_str)
        # Retourne les résultats de la recherche
        return final_result, result
    
    def display_results(self, query, response, results):
        """Affiche les résultats de recherche de manière claire et formatée"""
        # Vérifier si les résultats sont valides
        if response is None:
            print("\n" + "="*100)
            print("   ERREUR ".center(100))
            print("="*100)
            print("\n La requête est vide ! Veuillez saisir une question ou des mots-clés.\n")
            print("="*100 + "\n")
            return
        
        if not response:
            print("\n" + "="*100)
            print("   RECHERCHE SÉMANTIQUE - AUCUN RÉSULTAT ".center(100))
            print("="*100)
            print(f"\n Requête : \"{query}\"")
            print(f"\n Aucun résultat trouvé pour cette requête.\n")
            print("="*100 + "\n")
            return
        
        print("\n" + "="*100)
        print("   RECHERCHE SÉMANTIQUE - RÉSULTATS ".center(100))
        print("="*100)
        print(f"\n Requête : \"{query}\"")
        print(f" Nombre de résultats trouvés : {len(response)}")
        print("\n" + "="*100 + "\n")
        
        # Parcourir tous les résultats
        for i in range(0, 3):
            metadata = results["metadatas"][0]
            distance = results["distances"][0]
            # Calculer le score de similarité (plus c’est proche de 100 %, mieux c’est)
            similarity_score = max(0, (2 - distance[i]) / 2 * 100)
            
            # Déterminer l’emoji en fonction du score
            if similarity_score >= 70:
                score_emoji = "🟢"
            elif similarity_score >= 40:
                score_emoji = "🟡"
            else:
                score_emoji = "🔴"
            
            # Nettoyer le texte pour un meilleur affichage
            cleaned_doc = response[i].replace('\\n', ' ').replace('\n', ' ')  # Remplace les retours à la ligne
            cleaned_doc = ' '.join(cleaned_doc.split())  # Enlève les espaces multiples
            
            print(f"╔═  RÉSULTAT #{i} {'═'*85}")
            print(f"║")
            print(f"║   Source      : {metadata[i].get('source', 'N/A')}")
            print(f"║  {score_emoji} Pertinence  : {similarity_score:.1f}%")
            print(f"║")
            print(f"║   Extrait :")
            print(f"║  {'-'*96}")
            # Coupe le texte pour un affichage propre (75 caractères par ligne)
            words = cleaned_doc.split()
            line = "║  "
            for word in words:
                if len(line) + len(word) + 1 > 98:
                    print(line)
                    line = "║  " + word + " "
                else:
                    line += word + " "
            if line.strip() != "║":
                print(line)
            print(f"║")
            print(f"╚{'═'*98}\n")

if __name__ == "__main__":
    # Initialise le pipeline de recherche
    retrieval_pipeline = RetrievalPipeline()
    
    print(" Indexation des documents...")
    
    # Parcourt tous les fichiers texte dans le dossier 'clean_data' et les indexe
    if retrieval_pipeline.use_azure_adls or retrieval_pipeline.use_azure_blob_for_data:
        # Lire depuis Azure (ADLS ou Blob Storage)
        try:
            file_list = retrieval_pipeline._list_files_from_azure_blob("clean_data")
            azure_type = "Azure ADLS" if retrieval_pipeline.use_azure_adls else "Azure Blob Storage"
            print(f"Fichiers trouves sur {azure_type}: {len(file_list)}")
            for file in file_list:
                azure_path = f"clean_data/{file}"
                retrieval_pipeline.index_text(azure_path)
        except Exception as e:
            azure_type = "Azure ADLS" if retrieval_pipeline.use_azure_adls else "Azure Blob Storage"
            print(f"ERREUR lors de la lecture depuis {azure_type}: {e}")
            sys.exit(1)
    else:
        # Lire depuis le système de fichiers local
        data_dir = retrieval_pipeline.data_dir
        if not data_dir.exists():
            print(f"ERREUR: Le dossier {data_dir} n'existe pas!")
            sys.exit(1)
        
        file_list = [f for f in os.listdir(data_dir) if os.path.isfile(data_dir / f) and f.endswith('.txt')]
        if not file_list:
            print(f"WARNING: Aucun fichier .txt trouve dans {data_dir}")
        
        print(f"Fichiers trouves localement: {len(file_list)}")
        for file in file_list:
            file_path = data_dir / file
            retrieval_pipeline.index_text(str(file_path))
    
    # Synchroniser vers Azure une seule fois à la fin
    retrieval_pipeline.sync_to_azure()
    print("Indexation terminee.")
    
    # Demande à l'utilisateur de saisir une requête
    print("\n" + "="*100)
    print("   SAISISSEZ VOTRE REQUÊTE ".center(100))
    print("="*100)
    query = input("\n Votre question : ").strip()
    
    # Exécute la requête sur la collection Chroma
    final_result, result_data = retrieval_pipeline.query_search(query)
    # Affiche les résultats de recherche de manière claire
    retrieval_pipeline.display_results(query, final_result, result_data)
    
    # Fermer proprement avant la fin du programme
    retrieval_pipeline.close()