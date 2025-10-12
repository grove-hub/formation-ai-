# 🔍 Système de Recherche Sémantique pour Textes Juridiques

Ce projet implémente un pipeline de recherche sémantique (RAG) utilisant ChromaDB et SentenceTransformers pour indexer et interroger des documents juridiques.

> 🚀 **Nouveau ?** Consultez le [Guide de démarrage rapide](QUICKSTART.md)

## 🎯 Fonctionnalités

✅ **Conversion PDF → TXT** : Extrait automatiquement le texte de vos PDFs  
✅ **Indexation intelligente** : Découpe et indexe vos documents avec des embeddings  
✅ **Recherche sémantique** : Trouve les passages pertinents même sans mots-clés exacts  
✅ **Affichage élégant** : Résultats formatés avec scores de pertinence  
✅ **Évite les doublons** : N'indexe pas deux fois le même contenu  
✅ **Multiple modes** : Interactif ou ligne de commande

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
├── traitement.py          # Script principal de recherche
├── pdf_to_txt.py         # Script de conversion PDF → TXT
├── requirements.txt       # Dépendances Python
├── Makefile              # Commandes d'automatisation
├── README.md             # Documentation
├── raw_pdfs/             # Dossier pour les PDFs sources (à créer)
├── clean_data/           # Dossier contenant les fichiers texte indexés
│   └── law_text2.txt
├── chroma_db/            # Base de données vectorielle (créée automatiquement)
└── venv/                 # Environnement virtuel Python
```

## 💡 Utilisation

### Étape 1 : Convertir les PDFs en TXT (optionnel)

Si vous avez des fichiers PDF à indexer :

1. Placez vos fichiers PDF dans le dossier `raw_pdfs/`
2. Lancez la conversion :

```bash
make convert-pdf
```

Le script `pdf_to_txt.py` :
- ✅ Lit tous les PDFs du dossier `raw_pdfs/`
- ✅ Extrait le texte de chaque page
- ✅ Crée des fichiers TXT dans `clean_data/`
- ✅ Affiche des statistiques détaillées

### Étape 2 : Recherche sémantique

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
- `make convert-pdf` - Convertit les PDFs en TXT (dossier raw_pdfs/)
- `make run` - Exécution du script en mode interactif
- `make query QUERY="..."` - Recherche avec une requête spécifique
- `make clean` - Nettoyage de l'environnement et fichiers temporaires
- `make reset-db` - Réinitialisation de la base de données
- `make help` - Affiche l'aide

## 📦 Dépendances principales

- **chromadb** : Base de données vectorielle
- **sentence-transformers** : Génération d'embeddings
- **numpy** : Calculs numériques
- **pypdf** : Extraction de texte depuis des PDFs

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

## 🔄 Workflow complet

### Scénario : Indexer et rechercher dans des documents PDF

```bash
# 1. Installation
make install

# 2. Placer vos PDFs dans le dossier raw_pdfs/
# (Glissez-déposez vos fichiers PDF dans raw_pdfs/)

# 3. Convertir les PDFs en TXT
make convert-pdf

# 4. Rechercher dans vos documents
make run
# Ou avec une requête directe :
make query QUERY="votre question ici"

# 5. (Optionnel) Réinitialiser la base de données
make reset-db
```

### Workflow de mise à jour

Quand vous ajoutez de nouveaux documents :

```bash
# Ajouter nouveaux PDFs dans raw_pdfs/
make convert-pdf  # Convertir les nouveaux PDFs
make run          # Les nouveaux TXT seront automatiquement indexés
```

Le système évite les doublons automatiquement !

---

## 📚 Documentation supplémentaire

Pour des exemples détaillés et des cas d'usage, consultez [EXEMPLES.md](EXEMPLES.md).

