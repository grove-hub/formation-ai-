.PHONY: install run clean help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
VENV := venv
VENV_BIN := $(VENV)/bin

help:
	@echo "📋 Commandes disponibles :"
	@echo "  make install    - Crée un environnement virtuel et installe les dépendances"
	@echo "  make run        - Execute le script traitement.py"
	@echo "  make clean      - Supprime l'environnement virtuel et les fichiers temporaires"
	@echo "  make reset-db   - Supprime la base de données ChromaDB"

install:
	@echo "🔧 Création de l'environnement virtuel..."
	$(PYTHON) -m venv $(VENV)
	@echo "📦 Installation des dépendances..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@echo "✅ Installation terminée !"
	@echo "💡 Pour activer l'environnement : source $(VENV_BIN)/activate"

run:
	@echo "🚀 Exécution du script..."
	$(VENV_BIN)/python traitement.py

clean:
	@echo "🧹 Nettoyage..."
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Nettoyage terminé !"

reset-db:
	@echo "🗑️  Suppression de la base de données..."
	rm -rf chroma_db/
	@echo "✅ Base de données supprimée !"

