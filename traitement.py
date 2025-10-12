import chromadb 
from sentence_transformers import SentenceTransformer
import glob
import os

class RetrievalPipeline:
    def __init__(self, db_path="chroma_db"):
        # Initialize the SentenceTransformer model for text embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Create or connect to a persistent Chroma database at the given path
        self.chroma_client = chromadb.PersistentClient(db_path)
        # Get or create a collection inside the database called "law_text"
        self.collection = self.chroma_client.get_or_create_collection(name="law_text")

    def chunking(self, text, chunk_size=500, overlap=50):
        # Split long text into smaller overlapping chunks for better embedding quality
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            # Move the window forward, keeping some overlap to preserve context
            start += chunk_size - overlap
        return chunks

    def index_text(self, file_path):
        # Read the text file content in UTF-8 encoding
        with open(file_path, "r", encoding='utf-8') as text:
            text_law = text.read()

        # Split the text into chunks
        chunks = self.chunking(text_law)
        # Get the filename (without extension) to use as a unique file identifier
        file_id = os.path.splitext(os.path.basename(file_path))[0]

        # Retrieve existing document IDs from the Chroma collection to avoid duplicates
        existing_ids = set(self.collection.get()["ids"])
        new_chunks = 0

        # Loop through all chunks in the file
        for i, chunk in enumerate(chunks):
            # Create a unique ID for each chunk based on file name and index
            chunk_id = f"{file_id}_chunk_{i}"
            # Skip if this chunk is already indexed
            if chunk_id in existing_ids:
                continue

            # Generate an embedding for the chunk using the model
            embedding = self.model.encode(chunk, convert_to_numpy=True)
            # Add the chunk, its embedding, and metadata (file path) to the collection
            self.collection.add(
                ids=[chunk_id],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": file_path}]
            )
            new_chunks += 1

        # Print how many new chunks were indexed
        print(f"{new_chunks} New chunk indexed from {file_path}")
    
    def query_search(self, query_text, n_result=1):
        # Encode the query text into an embedding vector
        query_embedding = self.model.encode(query_text)
        # Search the Chroma collection for the most similar chunks
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_result
        )
        # Return the query results
        return result
    
    def display_results(self, query, results):
        """Affiche les résultats de recherche de manière claire et formatée"""
        print("\n" + "="*100)
        print(" 🔍  RECHERCHE SÉMANTIQUE - RÉSULTATS ".center(100))
        print("="*100)
        print(f"\n💬 Requête : \"{query}\"")
        print(f"📊 Nombre de résultats trouvés : {len(results['documents'][0])}")
        print("\n" + "="*100 + "\n")
        
        # Parcourir tous les résultats
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            # Calculer le score de similarité (plus c'est proche de 100%, mieux c'est)
            similarity_score = max(0, (2 - distance) / 2 * 100)
            
            # Déterminer l'emoji en fonction du score
            if similarity_score >= 70:
                score_emoji = "🟢"
            elif similarity_score >= 40:
                score_emoji = "🟡"
            else:
                score_emoji = "🔴"
            
            # Nettoyer le texte pour un meilleur affichage
            cleaned_doc = doc.replace('\\n', ' ').replace('\n', ' ')  # Remplace les retours à la ligne
            cleaned_doc = ' '.join(cleaned_doc.split())  # Enlève les espaces multiples
            
            print(f"╔═ 📄 RÉSULTAT #{i} {'═'*85}")
            print(f"║")
            print(f"║  📂 Source      : {metadata.get('source', 'N/A')}")
            print(f"║  {score_emoji} Pertinence  : {similarity_score:.1f}%")
            print(f"║")
            print(f"║  📝 Extrait :")
            print(f"║  {'-'*96}")
            # Wrapper le texte pour un affichage propre (75 caractères par ligne)
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
    # Initialize the retrieval pipeline
    retrieval_pipeline = RetrievalPipeline()
    
    print("🔄 Indexation des documents...")
    # Loop over all text files in the 'clean_data' directory and index them
    for file_path in glob.glob("clean_data/*.txt"):
        retrieval_pipeline.index_text(file_path)

    # Define a search query
    query = "quelle autorité est responsable de la gestion des déchets dangereux ?"
    # Run the query against the Chroma collection (récupérer top 3 résultats)
    result = retrieval_pipeline.query_search(query, n_result=3)
    # Display the search results in a clear format
    retrieval_pipeline.display_results(query, result)