# 🔍 Système de Recherche Sémantique pour Textes Juridiques

Ce projet implémente un pipeline de recherche sémantique (RAG) utilisant ChromaDB et SentenceTransformers pour indexer et interroger des documents juridiques.

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip

## 🚀 Installation rapide

### Avec Make (recommandé)

```bash
# Installer toutes les dépendances
make install

# Activer l'environnement virtuel
source venv/bin/activate

# Exécuter le script
make run
```

### Installation manuelle

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Exécuter le script
python traitement.py
```

## 📁 Structure du projet

```
formation-ai-/
├── traitement.py          # Script principal
├── requirements.txt       # Dépendances Python
├── Makefile              # Commandes d'automatisation
├── README.md             # Documentation
├── clean_data/           # Dossier contenant les fichiers texte à indexer
│   └── law_text2.txt
├── chroma_db/            # Base de données vectorielle (créée automatiquement)
└── venv/                 # Environnement virtuel Python
```

## 💡 Utilisation

Le script `traitement.py` :
1. Indexe automatiquement tous les fichiers `.txt` du dossier `clean_data/`
2. Découpe les textes en chunks de 500 caractères avec 50 caractères de chevauchement
3. Génère des embeddings pour chaque chunk
4. Permet de faire des recherches sémantiques

## 🔧 Commandes Make disponibles

- `make install` - Installation complète avec environnement virtuel
- `make run` - Exécution du script
- `make clean` - Nettoyage de l'environnement et fichiers temporaires
- `make reset-db` - Réinitialisation de la base de données
- `make help` - Affiche l'aide

## 📦 Dépendances principales

- **chromadb** : Base de données vectorielle
- **sentence-transformers** : Génération d'embeddings
- **numpy** : Calculs numériques

## 🎯 Exemple de recherche

Le script effectue une recherche exemple :
```python
query = "a competent authority can take a decision"
result = retrieval_pipeline.query_search(query)
print(result)
```

## 🔄 Réinitialiser la base de données

```bash
make reset-db
```

Puis relancez le script pour réindexer les documents.

