import requests
import json
from traitement import RetrievalPipeline

# envoye et retourne une reponse du model mistral a la question pose par l utilisateur
# en moyenne 2 a 3min pour chaque réponse
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
        #question et model utiliser
        data = {
            "model":"mistral",
            "prompt": prompt
        }
        # récupere la reponse du serveur
        with requests.post(self.url, json=data, stream=True) as r:
            output = ""
            # la reponse du serveur est 'casse' en plusieru ligne json
            # parcour chaque ligne pour récuprer le texte
            for line in r.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    if "response" in chunk:
                        output += chunk["response"]
                    if chunk.get("done", False):
                        break
        # la reponse

        return output, results

if __name__ == "__main__":
    # question de l utilisateur
    query_text = input("Question: ")
    # function pour envoyer et recupere la reponse
    generation = Generation()
    output, result = generation.prompt_augmentation(query_text=query_text)
    # reponse
    print(f"\n Réponse: {output}")