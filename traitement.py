import chromadb 
from sentence_transformers import SentenceTransformer
import os
import sys
import json
import re

class RetrievalPipeline:
    def __init__(self, db_path="project/chroma_db"):
        # Initialise le modèle SentenceTransformer pour les embeddings de texte
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Crée ou connecte une base de données Chroma persistante au chemin donné
        self.chroma_client = chromadb.PersistentClient(db_path)
        # Récupère ou crée une collection dans la base appelée "law_text"
        self.collection = self.chroma_client.get_or_create_collection(name="law_text")
    
    def find_category(self, text):
        # trouve la categorie aproximatif
        
        # recupere le dic dans base_dechets.json
        with open("project\\base_dechets.json", mode="r", encoding="utf-8") as f:
            category = json.load(f)
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
            chunks.append(text[start:end])
            # Déplace la fenêtre vers l’avant, en gardant un chevauchement pour préserver le contexte
            start += chunk_size - overlap
        # verifie si les chunk ne sont pas trop petit et donc sens context
        for i, chunk in enumerate(chunks):
            if len(chunk) > 300:
                chunks.pop(i)

        return chunks

    def index_text(self, file_path):
        # Lit le contenu du fichier texte en encodage UTF-8
        with open(file_path, "r", encoding='utf-8') as text:
            text_law = text.read()

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

        # Boucle sur tous les segments du fichier
        for i, chunk in enumerate(chunks):
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
                metadatas=[{"source": file_path, "categorie": category, "date": date}]
            )
            new_chunks += 1

        # Affiche combien de nouveaux segments ont été indexés
        if new_chunks > 0:
            print(f"{new_chunks} New chunk indexed from {file_path}")
    
    def query_search(self, query_text):
        # Vérifie que la requête n’est pas vide
        if not query_text or query_text.strip() == "":
            return None
        
        # Encode le texte de la requête en un vecteur d’embedding
        query_embedding = self.model.encode(query_text)
        # Recherche dans la collection Chroma les segments les plus similaires
        
        # Récupère la liste des documents dans le dossier
        clean_data_path_list = os.listdir("./project/clean_data")
        # La quantité de documents 
        n_result = len(clean_data_path_list)
        
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result
        )
        # Retourne les résultats de la recherche
        return result
    
    def display_results(self, query, results):
        """Affiche les résultats de recherche de manière claire et formatée"""
        # Vérifier si les résultats sont valides
        if results is None:
            print("\n" + "="*100)
            print(" ⚠️  ERREUR ".center(100))
            print("="*100)
            print("\n❌ La requête est vide ! Veuillez saisir une question ou des mots-clés.\n")
            print("="*100 + "\n")
            return
        
        if not results['documents'][0]:
            print("\n" + "="*100)
            print(" 🔍  RECHERCHE SÉMANTIQUE - AUCUN RÉSULTAT ".center(100))
            print("="*100)
            print(f"\n💬 Requête : \"{query}\"")
            print(f"\n❌ Aucun résultat trouvé pour cette requête.\n")
            print("="*100 + "\n")
            return
        
        print("\n" + "="*100)
        print(" 🔍  RECHERCHE SÉMANTIQUE - RÉSULTATS ".center(100))
        print("="*100)
        print(f"\n💬 Requête : \"{query}\"")
        print(f"📊 Nombre de résultats trouvés : {len(results['documents'][0])}")
        print("\n" + "="*100 + "\n")
        
        # Parcourir tous les résultats
        for i in range(1, 4):
            doc = results["documents"][0]
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
            cleaned_doc = doc[i].replace('\\n', ' ').replace('\n', ' ')  # Remplace les retours à la ligne
            cleaned_doc = ' '.join(cleaned_doc.split())  # Enlève les espaces multiples
            
            print(f"╔═ 📄 RÉSULTAT #{i} {'═'*85}")
            print(f"║")
            print(f"║  📂 Source      : {metadata[i].get('source', 'N/A')}")
            print(f"║  {score_emoji} Pertinence  : {similarity_score:.1f}%")
            print(f"║")
            print(f"║  📝 Extrait :")
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
    
    print("🔄 Indexation des documents...")

    # Parcourt tous les fichiers texte dans le dossier 'clean_data' et les indexe
    file_list = os.listdir("project\clean_data")

    for file_path in file_list:
        file_path = os.path.join("project\clean_data", file_path)
        retrieval_pipeline.index_text(file_path)

    # Définit une requête de recherche (depuis la ligne de commande ou par défaut)
    if len(sys.argv) > 1:
        # Récupère la requête depuis les arguments de la ligne de commande
        query = " ".join(sys.argv[1:])
    else:
        # Demande à l’utilisateur de saisir une requête
        print("\n" + "="*100)
        print(" 💬  SAISISSEZ VOTRE REQUÊTE ".center(100))
        print("="*100)
        query = input("\n🔍 Votre question : ").strip()
    
    # Exécute la requête sur la collection Chroma
    result = retrieval_pipeline.query_search(query)
    # Affiche les résultats de recherche de manière claire
    retrieval_pipeline.display_results(query, result)