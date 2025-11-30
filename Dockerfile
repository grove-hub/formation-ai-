# Utiliser une image Python légère
FROM python:3.11-slim

# Éviter les fichiers .pyc et le buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installer les dépendances système (nécessaires pour certains packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier le fichier de dépendances
COPY requirements.txt .

# Installer les dépendances Python
# Astuce: Installer PyTorch CPU-only AVANT requirements.txt pour éviter de télécharger la version GPU énorme
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code source
COPY src/ ./src/

# Définir le dossier src comme module pour les imports
ENV PYTHONPATH=/app/src

# Pour le Job d'indexation (Pipeline complet): CMD ["python", "src/scrap/pipeline.py"]
# Pour l'API: CMD ["uvicorn", "src.bridge:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["python", "src/scrap/pipeline.py"]
