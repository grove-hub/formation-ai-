# uvicorn bridge:app --reload --host 127.0.0.1 --port 8000     <--pour lancer en back end sur local
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from reponse import Generation
from datetime import date

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model = Generation()

class Query(BaseModel):
    query: str

# class DemoRequest(BaseModel):
#     name: str
#     email: EmailStr
#     company: str
#     phone: str | None = None
#     role: str
#     message: str

@app.post("/search")

def search(data: Query):
    print("Requete recue : ", data.query)
    model_response, results  = model.prompt_augmentation(data.query)
    distance = results["distances"][0]
    relevance = max(0, (2 - distance[0]) / 2 * 100)
    
    payload = {
        "results" : [
            {
            "id": 1,
            "title": f"Résultat pour '{data.query}'",
            "excerpt": model_response,
            "source": "En manutention",
            "date": date.today().isoformat(),
            "type": "Réponse IA",
            "relevance": round(relevance),
            "link": "#"  
            }
        ]
    }
    
    print("Réponse envoyée au front :", payload)
    
    return payload

# @app.post("/demo-request")
# def demo_request(data: DemoRequest):
#     # pour l’instant on log
#     print("Nouvelle demande de démo :")
#     print(f"- Nom: {data.name}")
#     print(f"- Email: {data.email}")
#     print(f"- Société: {data.company}")
#     print(f"- Téléphone: {data.phone}")
#     print(f"- Rôle: {data.role}")
#     print(f"- Message: {data.message}")

#     # ici tu pourrais :
#     # - enregistrer en base
#     # - envoyer un email
#     # - créer un ticket
#     # - appeler un autre service

#     return {"status": "ok", "message": "Demande reçue"}
