# 🚀 Démarrage rapide

## En 4 étapes simples

### 1️⃣ Installation (une seule fois)

```bash
make install
```

⏱️ Durée : ~2-3 minutes

---

### 2️⃣ Convertir vos PDFs (optionnel)

```bash
# Placer vos PDFs dans raw_pdfs/
make convert-pdf
```

💡 Si vous avez déjà des fichiers TXT, passez à l'étape 3

---

### 3️⃣ Lancer une recherche

**Mode interactif :**
```bash
make run
```

**Avec une question directe :**
```bash
make query QUERY="votre question ici"
```

---

### 4️⃣ Profiter des résultats ! 🎉

Les résultats s'affichent avec :
- 📄 Les extraits les plus pertinents
- 🎯 Un score de pertinence
- 📂 La source du document

---

## ⚡ Commandes essentielles

| Commande | Description |
|----------|-------------|
| `make help` | Voir toutes les commandes |
| `make convert-pdf` | Convertir PDFs → TXT |
| `make run` | Recherche interactive |
| `make query QUERY="..."` | Recherche directe |
| `make reset-db` | Réinitialiser l'index |

---

## 📖 Plus d'infos

- **README complet** : [README.md](README.md)
- **Exemples détaillés** : [EXEMPLES.md](EXEMPLES.md)
- **Instructions PDFs** : [raw_pdfs/README.md](raw_pdfs/README.md)

---

## 🆘 Besoin d'aide ?

**Problème :** Aucun résultat trouvé  
**Solution :** Vérifiez que des fichiers TXT sont dans `clean_data/`

**Problème :** Erreur d'importation  
**Solution :** Relancez `make install`

**Problème :** PDF non converti  
**Solution :** Vérifiez que le PDF n'est pas une image scannée

