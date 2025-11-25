# 📚 Exemples d'utilisation

Ce document contient des exemples pratiques pour utiliser le système de recherche sémantique.

## 🚀 Démarrage rapide

### 1️⃣ Installation initiale

```bash
make install
```

Cette commande :
- Crée un environnement virtuel Python
- Installe toutes les dépendances nécessaires
- Configure le projet

---

## 📄 Conversion de PDFs

### Exemple 1 : Convertir un seul PDF

```bash
# 1. Placer votre PDF
cp mon_document.pdf raw_pdfs/

# 2. Convertir
make convert-pdf
```

**Résultat attendu :**
```
📄 Conversion des PDFs en TXT...

================================================================================
                           📄  CONVERSION PDF → TXT
================================================================================

📂 Dossier source : raw_pdfs/
📂 Dossier destination : clean_data/
📊 Nombre de PDFs trouvés : 1

================================================================================

[1/1] 🔄 Conversion de : mon_document.pdf
   ✅ Converti avec succès : mon_document.txt
   📄 Pages : 42 | Caractères : 125,456
```

### Exemple 2 : Convertir plusieurs PDFs

```bash
# Placer plusieurs PDFs
cp *.pdf raw_pdfs/

# Convertir tous les PDFs en une fois
make convert-pdf
```

---

## 🔍 Recherche sémantique

### Exemple 1 : Mode interactif

```bash
make run
```

Le système vous demande votre question :
```
🔍 Votre question : quelle autorité est responsable ?
```

### Exemple 2 : Ligne de commande directe

```bash
make query QUERY="qui est responsable de la gestion des déchets ?"
```

### Exemple 3 : Avec Python directement

```bash
python traitement.py "quelles sont les obligations des États membres ?"
```

---

## 📊 Interprétation des résultats

### Exemple de résultat

```
====================================================================================================
                                🔍  RECHERCHE SÉMANTIQUE - RÉSULTATS
====================================================================================================

💬 Requête : "qui est responsable de la gestion des déchets ?"
📊 Nombre de résultats trouvés : 3

====================================================================================================

╔═ 📄 RÉSULTAT #1 ═════════════════════════════════════════════════════════
║
║  📂 Source      : clean_data/law_text2.txt
║  🟢 Pertinence  : 75.2%    ← Score élevé = Très pertinent
║
║  📝 Extrait :
║  ────────────────────────────────────────────────────────────────────────
║  collection, transport or treatment of waste, supervision of such 
║  operations and after-care of disposal sites, including action taken 
║  as a dealer or a broker...
║
╚══════════════════════════════════════════════════════════════════════════
```

### Comprendre les scores de pertinence

- **🟢 70-100%** : Très pertinent - La réponse est très probablement dans ce passage
- **🟡 40-69%** : Moyennement pertinent - Contient des informations liées
- **🔴 0-39%** : Faiblement pertinent - Peu de rapport avec la question

---

## 🎯 Exemples de questions

### Questions juridiques générales

```bash
make query QUERY="quelles sont les sanctions prévues ?"
make query QUERY="qui peut prendre une décision ?"
make query QUERY="quelle est la procédure à suivre ?"
```

### Questions spécifiques

```bash
make query QUERY="délai de prescription des infractions environnementales"
make query QUERY="responsabilité des États membres en matière de déchets"
make query QUERY="autorités compétentes pour les sanctions"
```

### Questions sur des concepts

```bash
make query QUERY="qu'est-ce qu'un déchet dangereux ?"
make query QUERY="définition d'une infraction environnementale"
make query QUERY="obligations de reporting des États"
```

---

## 🔄 Workflow type

### Scénario : Analyser une nouvelle directive européenne

```bash
# 1. Télécharger la directive (PDF)
# 2. La placer dans raw_pdfs/
cp directive_2024_xyz.pdf raw_pdfs/

# 3. Convertir en texte
make convert-pdf

# 4. Rechercher des informations spécifiques
make query QUERY="obligations des États membres"
make query QUERY="sanctions applicables"
make query QUERY="date d'entrée en vigueur"

# 5. Recherche approfondie en mode interactif
make run
```

---

## 🛠️ Maintenance

### Ajouter de nouveaux documents

```bash
# Ajouter de nouveaux PDFs
cp nouveaux_docs/*.pdf raw_pdfs/

# Convertir
make convert-pdf

# Rechercher (les nouveaux docs sont automatiquement indexés)
make run
```

### Réinitialiser la base de données

Si vous voulez tout réindexer depuis zéro :

```bash
# Supprimer l'index
make reset-db

# Réindexer
make run
```

### Nettoyer le projet

```bash
# Supprimer l'environnement virtuel et fichiers temporaires
make clean

# Réinstaller si nécessaire
make install
```

---

## 💡 Conseils d'utilisation

### Pour de meilleurs résultats

1. **Formulez des questions complètes**
   - ✅ "Quelle autorité est responsable de la gestion des déchets dangereux ?"
   - ❌ "autorité déchets"

2. **Utilisez un langage naturel**
   - Le système comprend le sens, pas seulement les mots-clés

3. **Soyez spécifique**
   - Plus votre question est précise, meilleurs sont les résultats

4. **Essayez différentes formulations**
   - Si les résultats ne sont pas satisfaisants, reformulez votre question

### Limitations

- ⚠️ Les PDFs scannés (images) ne peuvent pas être convertis
- ⚠️ Les PDFs protégés par mot de passe sont inaccessibles
- ⚠️ La qualité de l'extraction dépend de la qualité du PDF source

---

## 🆘 Problèmes courants

### "Aucun fichier PDF trouvé"

**Solution :** Vérifiez que vos PDFs sont bien dans `raw_pdfs/` et ont l'extension `.pdf`

### "La requête est vide"

**Solution :** Assurez-vous de saisir une question avant de valider

### "Aucun résultat trouvé"

**Solutions :**
- Vérifiez que des fichiers TXT existent dans `clean_data/`
- Essayez une formulation différente de votre question
- Assurez-vous que l'indexation s'est bien déroulée (relancez `make run`)

---

## 📞 Support

Pour plus d'informations, consultez le [README.md](README.md) principal.

