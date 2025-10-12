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

### Méthodes de recherche :

**1. Mode interactif (par défaut)**
```bash
make run
# Le système vous demandera de saisir votre question
```

**2. Avec une requête en ligne de commande**
```bash
python traitement.py "quelle autorité est responsable de la gestion des déchets ?"
```

**3. Avec le Makefile**
```bash
make query QUERY="votre question ici"
```

### Validation automatique :
- ✅ Le système vérifie que la requête n'est pas vide
- ✅ Affiche un message d'erreur clair si la requête est invalide
- ✅ Affiche les 3 meilleurs résultats avec un score de pertinence

## 🔧 Commandes Make disponibles

- `make install` - Installation complète avec environnement virtuel
- `make run` - Exécution du script en mode interactif
- `make query QUERY="..."` - Recherche avec une requête spécifique
- `make clean` - Nettoyage de l'environnement et fichiers temporaires
- `make reset-db` - Réinitialisation de la base de données
- `make help` - Affiche l'aide

## 📦 Dépendances principales

- **chromadb** : Base de données vectorielle
- **sentence-transformers** : Génération d'embeddings
- **numpy** : Calculs numériques

## 🎯 Exemples de recherche

**Exemple 1 : Mode interactif**
```bash
make run
# Puis saisir : "quelle autorité est responsable de la gestion des déchets ?"
```

**Exemple 2 : Ligne de commande**
```bash
make query QUERY="qui est responsable de l'application des sanctions ?"
```

**Exemple 3 : Directement avec Python**
```bash
python traitement.py "quelles sont les obligations des États membres ?"
```

Les résultats affichent :
- 🟢 Score vert (≥70%) : Très pertinent
- 🟡 Score jaune (40-69%) : Moyennement pertinent
- 🔴 Score rouge (<40%) : Faiblement pertinent

## 🔄 Réinitialiser la base de données

```bash
make reset-db
```

Puis relancez le script pour réindexer les documents.

