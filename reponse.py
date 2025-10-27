import requests
import json
from traitement import RetrievalPipeline

class Generation:
    def __init__(self):
        # url du serveur d'ollama sur docker
        self.url = "http://localhost:11434/api/generate"
        # classe des traitement de donne
        self.pipeline = RetrievalPipeline()

    def prompt_augmentation(self, query_text):
        # resulta des recherche
        results = self.pipeline.query_search(query_text=query_text)
        # document recupere de la recherche
        doc = results["documents"][0]
        # prompt detailer
        prompt =f"""
                Tu es un assistant qui répond uniquement à partir des documents suivants.
                N'ajoute aucune information, supposition ou connaissance extérieure.
                Si les documents ne contiennent pas suffisamment d'information pour répondre complètement,
                répond exactement : "Aucune information pertinente trouvée dans les documents."

                Règles à suivre :
                1. Utilise exclusivement les faits présents dans les documents ci-dessous.
                2. Si une idée ou phrase ne provient pas clairement des documents, NE L'ÉCRIS PAS.
                3. Si la réponse ne peut pas être déduite directement des documents, réponds exactement :
                "Aucune information pertinente trouvée dans les documents."
                4. Ne fais aucun raisonnement ou hypothèse non soutenu par les documents.

                Ta tâche :
                - Lis attentivement les documents suivants :
                {doc[0]}
                {doc[1]}
                {doc[2]}

                - Puis, réponds strictement à la question ci-dessous.
                - Si la réponse n'est pas clairement présente ou déductible des documents, réponds uniquement :
                "Aucune information pertinente trouvée dans les documents."

                Question : {query_text}

                Ta réponse finale :
        """
        
        data = {
            "model":"mistral",
            "prompt": prompt
        }

        with requests.post(self.url, json=data, stream=True) as r:
            output = ""

            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    if "response" in chunk:
                        output += chunk["response"]
                    if chunk.get("done", False):
                        break
        return output

if __name__ == "__main__":
    query_text = input("Question: ")

    generation = Generation()
    output = generation.prompt_augmentation(query_text=query_text)

    print(f"Réponse: {output}")