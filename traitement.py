import chromadb 
from sentence_transformers import SentenceTransformer
import glob
import os

class RetrievalPipeline:
    def __init__(self, db_path="project/chroma_db"):
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

if __name__ == "__main__":
    # Initialize the retrieval pipeline
    retrieval_pipeline = RetrievalPipeline()
    
    # Loop over all text files in the 'clean_data' directory and index them
    for file_path in glob.glob("project/clean_data/*.txt"):
        retrieval_pipeline.index_text(file_path)

    # Define a search query
    query = "a competent authority can take a decision"
    # Run the query against the Chroma collection
    result = retrieval_pipeline.query_search(query)
    # Print the search results
    print(result)