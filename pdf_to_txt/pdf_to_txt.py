import os
from io import BytesIO

try:
    from pypdf import PdfReader
except ModuleNotFoundError:
    try:
        from PyPDF2 import PdfReader
    except ModuleNotFoundError:
        raise SystemExit(
            "Dépendances manquantes: installez 'pypdf' (ou 'PyPDF2') et les SDK Azure.\n"
            "Exemples:\n"
            "  - pip:    python -m pip install pypdf azure-identity azure-storage-file-datalake\n"
            "  - conda:  conda install -c conda-forge pypdf azure-identity azure-storage-file-datalake"
        )

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


ACCOUNT_NAME = "juridicai"
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_KEY", "").strip()
FILESYSTEM = "data"

RAW_DIR = "raw_pdfs"
CLEAN_DIR = "clean_data"
# ---------------------------------------

def get_dls_client():
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

def list_pdf_paths(file_system_client, directory_path):
    paths_iter = file_system_client.get_paths(path=directory_path)
    pdf_paths = []
    for p in paths_iter:
        if p.is_directory:
            continue
        if p.name.lower().endswith(".pdf"):
            pdf_paths.append(p.name)
    return pdf_paths

def download_pdf_bytes(file_client):
    # Compatibilité selon version du SDK:
    # - nouvelles versions: read_file()
    # - anciennes versions: download_file()
    if hasattr(file_client, "read_file"):
        downloader = file_client.read_file()
    else:
        downloader = file_client.download_file()
    return downloader.readall()

def upload_text(file_client, text):
    data = text.encode("utf-8")
    # Créer ou écraser le fichier, puis append/flush
    try:
        file_client.create_file()
    except Exception:
        # Si existe déjà, on supprime puis on recrée
        try:
            file_client.delete_file()
        except Exception:
            pass
        file_client.create_file()
    file_client.append_data(data=data, offset=0, length=len(data))
    file_client.flush_data(len(data))

def convert_pdfs_in_adls():
    dls = get_dls_client()
    fs = dls.get_file_system_client(FILESYSTEM)

    # Vérifier/Créer le dossier clean_data si nécessaire
    try:
        fs.create_directory(CLEAN_DIR)
    except Exception:
        # existe déjà
        pass

    pdf_paths = list_pdf_paths(fs, RAW_DIR)

    if not pdf_paths:
        print(f"⚠️  Aucun PDF trouvé dans '{FILESYSTEM}/{RAW_DIR}'.")
        print("💡 Déposez des fichiers et relancez.")
        return

    print(f"\n{'='*80}")
    print(f" 📄  CONVERSION PDF → TXT (ADLS) ".center(80))
    print(f"{'='*80}\n")
    print(f"📂 Source      : {ACCOUNT_NAME}/{FILESYSTEM}/{RAW_DIR}")
    print(f"📂 Destination : {ACCOUNT_NAME}/{FILESYSTEM}/{CLEAN_DIR}")
    print(f"📊 PDFs trouvés: {len(pdf_paths)}\n")
    print(f"{'='*80}\n")

    success_count = 0
    error_count = 0

    for idx, pdf_adls_path in enumerate(pdf_paths, 1):
        pdf_name = os.path.basename(pdf_adls_path)
        base_name, _ = os.path.splitext(pdf_name)
        txt_adls_path = f"{CLEAN_DIR}/{base_name}.txt"

        print(f"[{idx}/{len(pdf_paths)}] 🔄 Conversion de : {pdf_name}")
        try:
            pdf_file_client = fs.get_file_client(pdf_adls_path)
            pdf_bytes = download_pdf_bytes(pdf_file_client)

            # Lecture PDF depuis mémoire
            reader = PdfReader(BytesIO(pdf_bytes))
            text_chunks = []
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                if page_num < len(reader.pages):
                    text_chunks.append(page_text + "\n\n")
                else:
                    text_chunks.append(page_text)
            text = "".join(text_chunks)

            txt_file_client = fs.get_file_client(txt_adls_path)
            upload_text(txt_file_client, text)

            print(f"   ✅ Converti avec succès : {txt_adls_path}")
            print(f"   📄 Pages : {len(reader.pages)} | Caractères : {len(text):,}\n")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Erreur : {e}\n")
            error_count += 1

    print(f"{'='*80}")
    print(f" 📊  RÉSUMÉ DE LA CONVERSION ".center(80))
    print(f"{'='*80}\n")
    print(f"✅ Conversions réussies : {success_count}")
    print(f"❌ Conversions échouées : {error_count}")
    print(f"📁 Fichiers TXT dans : {ACCOUNT_NAME}/{FILESYSTEM}/{CLEAN_DIR}\n")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    convert_pdfs_in_adls()