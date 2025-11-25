.PHONY: install run clean help convert-pdf

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin

help:
	@echo "📋 Commandes disponibles :"
	@echo "  make install           - Crée un environnement virtuel et installe les dépendances"
	@echo "  make convert-pdf       - Convertit les PDFs en TXT (dossier raw_pdfs/)"
	@echo "  make run               - Execute le script en mode interactif"
	@echo "  make query QUERY=\"...\" - Execute une recherche avec une requête spécifique"
	@echo "  make clean             - Supprime l'environnement virtuel et les fichiers temporaires"
	@echo "  make reset-db          - Supprime la base de données ChromaDB"

install:
	@echo "🔧 Création de l'environnement virtuel..."
	$(PYTHON) -m venv $(VENV)
	@echo "📦 Installation des dépendances..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@echo "✅ Installation terminée !"
	@echo "💡 Pour activer l'environnement : source $(VENV_BIN)/activate"

run:
	@echo "🚀 Exécution du script en mode interactif..."
	$(VENV_BIN)/python -m src.traitement

query:
	@echo "🚀 Exécution de la recherche..."
	$(VENV_BIN)/python -m src.traitement $(QUERY)

convert-pdf:
	@echo "📄 Conversion des PDFs en TXT..."
	$(VENV_BIN)/python -m src.pdf_to_txt

clean:
	@echo "🧹 Nettoyage..."
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Nettoyage terminé !"

reset-db:
	@echo "🗑️  Suppression de la base de données..."
	rm -rf data/chroma_db/
	@echo "✅ Base de données supprimée !"

