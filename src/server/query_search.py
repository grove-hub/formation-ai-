from sentence_transformers import SentenceTransformer
from traitement import RetrievalPipeline

class QuerySearch:
    def __init__(self):

        # Initialise le modèle SentenceTransformer pour les embeddings de texte
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # collection de chromadb avec tout les documents indexé
        self.collection = RetrievalPipeline().collection
        
    def query_search_db(self, query):
        # Vérifie que la requête n’est pas vide
        if not query or query.strip() == "":
            return None
        
        # Encode le texte de la requête en un vecteur d’embedding
        query_embedding = self.model.encode(query)
        # Recherche dans la collection Chroma les segments les plus similaires
        n_result = 3
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results= n_result
        )
        
        # list pour mettre les retour finaux des document
        final_result = []
        # reprend les metadata
        metadatas_dic = result["metadatas"][0]
        # parcour au nombre de resultat demander
        for i in range(n_result):
            # recupere les id des chunk
            metadata = metadatas_dic[i]
            idx = metadata["chunk_id"]
            # fait une recherche des chunk voisin 
            neighbors = self.collection.get(
                where={
                    "chunk_id":{"$in": [idx-1, idx, idx+1]}
                }
            )
            # ajoute les document trouver 
            doc_str = ""
            for doc in neighbors["documents"]:
                doc_str += str(doc)
            final_result.append(doc_str)
        # Retourne les résultats de la recherche
        return final_result, result
        