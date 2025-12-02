import requests
import json
import os
from query_search import QuerySearch

class Generation:
    """Handles LLM response generation using Ollama/Mistral"""
    
    def __init__(self):
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.url = f"{base_url}/api/generate"
        self.pipeline = QuerySearch()

    def question_subject(self, query):

        prompt = f"""
            Tu es un assistant qui génère UN SEUL sujet très concis pour une question donnée.

            Objectif :
            - Tu dois capturer l'idée principale de la question en quelques mots.
            - Le sujet doit être court, clair et en français.
            - Ce doit être un seul sujet central, pas une phrase, pas plusieurs idées.

            Exemples de comportement attendu :

            Question : "Donne-moi trois exemples de comment bien trier."
            --> Sujet attendu : "Méthodes de tri efficaces"

            Question : "Comment organiser mes fichiers sur l'ordinateur ?"
            --> Sujet attendu : "Organisation des fichiers sur ordinateur"

            Question : "Quelles sont les bonnes pratiques pour apprendre le Python ?"
            --> Sujet attendu : "Bonnes pratiques pour apprendre Python"

            Règles STRICTES de format :
            - Réponds par UN SEUL sujet, 3 à 8 mots maximum.
            - Pas de phrase complète.
            - Pas de deux-points (:) dans la réponse.
            - Pas de guillemets.
            - Pas d'explication.
            - Pas de texte avant ou après le sujet.
            - Pas de préfixe du type "Sujet :" ou "Ligne de sujet :".

            Question :
            {query}

            Réponds uniquement par le sujet, rien d'autre.
            """

        data = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
        }

        try:
            r = requests.post(self.url, json=data)
            r.raise_for_status()

            response_json = r.json()
            subject_line = response_json.get("response", "").strip()

            # Petit filet de sécurité : si jamais le modèle renvoie "Sujet : XXX"
            for prefix in ["Sujet :", "Sujet:", "Ligne de sujet :", "Ligne de sujet:"]:
                if subject_line.lower().startswith(prefix.lower()):
                    subject_line = subject_line[len(prefix):].strip()
            
            subject_line = subject_line.replace('"', '').replace("'", "")   

            return subject_line or "Sujet indisponible"

        except Exception as e:
            print(f"Erreur lors de l'appel à Ollama ({self.url}): {e}")
            return "Sujet indisponible"
        
    def prompt_augmentation(self, query):
        # Generate an answer based on retrieved documents

        # appele la fonction pour filtrer le sujet de la question
        query_subject = self.question_subject(query)
        response, results = self.pipeline.query_search_db(query_subject)

        prompt = f"""
                Tu es un assistant qui répond uniquement à partir des documents suivants.
                N'ajoute aucune information, supposition ou connaissance extérieure.
                Si les documents ne contiennent pas suffisamment d'information pour répondre complètement,
                répond exactement : "Aucune information pertinente trouvée dans les documents."

                Règles à suivre :
                1. Utilise exclusivement les faits présents dans les documents ci-dessous, sans dire :"selon les documents fournis"
                2. Si une idée ou phrase ne provient pas clairement des documents, NE L'ÉCRIS PAS.
                3. Si la réponse ne peut pas être déduite directement des documents, réponds exactement :
                "Aucune information pertinente trouvée dans les documents."
                4. Ne fais aucun raisonnement ou hypothèse non soutenu par les documents.

                Ta tâche :
                - Lis attentivement les documents suivants :
                {response[0]}
                {response[1]}
                {response[2]}

                - Puis, réponds strictement à la question ci-dessous.
                - Si la réponse n'est pas clairement présente ou déductible des documents, réponds uniquement :
                "Aucune information pertinente trouvée dans les documents."

                Question : {query}

                Ta réponse finale :
        """
        
        data = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
        
        try:
            r = requests.post(self.url, json=data)
            r.raise_for_status()
            
            response_json = r.json()
            output = response_json.get("response", "")
            
            return output, results, query_subject
            
        except Exception as e:
            print(f"Erreur lors de l'appel à Ollama ({self.url}): {e}")
            return "Désolé, le service de génération de réponse est indisponible pour le moment.", results

if __name__ == "__main__":
    query = input("Question: ")
    generation = Generation()
    output, result, query_subject = generation.prompt_augmentation(query)
    print(f"\n Réponse: {output}")
    print(f"\n Sujets de la question: {query_subject}")