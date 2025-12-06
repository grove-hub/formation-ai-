from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

@app.post("/search")
def search(data: Query):
    # Search endpoint that returns AI-generated answers based on document retrieval
    print("Requete recue : ", data.query)
    model_response, results = model.prompt_augmentation(data.query)
    
    distance = results["distances"][0]
    relevance = max(0, (2 - distance[0]) / 2 * 100)
    
    metadatas = results["metadatas"][0]
    metadatas_topics = metadatas[0]
    
    payload = {
        "results": [
            {
                "id": 1,
                "title": f"Résultat pour '{data.query}'",
                "excerpt": model_response,
                "source": metadatas_topics['source'],
                "date": date.today().isoformat(),
                "type": "Réponse IA",
                "relevance": round(relevance),
                "link": "#"  
            }
        ]
    }
    
    print("Réponse envoyée au front :", payload)
    
    return payload

@app.post("/admin/restart")
def trigger_restart():
    """Admin endpoint to restart the API container (called by pipeline after updates)"""
    import os
    import signal
    print("[ADMIN] Restart requested - shutting down to reload data...")
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "restarting"}
