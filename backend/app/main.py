"""Etapa 4: a API que o front-end vai chamar.

Rodar:
    uvicorn app.main:app --reload
Testar no navegador:
    http://localhost:8000/docs
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.resposta import responder

app = FastAPI(
    title="Assistente UFC",
    description="Responde dúvidas sobre documentos oficiais da UFC usando RAG",
    version="1.0.0",
)

# CORS: diz quais sites podem chamar esta API.
# Em casa é o front-end local (porta 3000). Online, colocamos o endereço da Vercel no .env
origens = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origens],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Formato do que chega e do que sai. O FastAPI valida tudo sozinho.
class Pergunta(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500, examples=["quantas faltas posso ter?"])


class Fonte(BaseModel):
    numero: int
    documento: str
    arquivo: str
    pagina: int
    trecho: str


class Resposta(BaseModel):
    resposta: str
    fontes: list[Fonte]


@app.get("/saude")
def saude():
    """Só confirma que a API está no ar."""
    return {"status": "ok"}


@app.post("/perguntar", response_model=Resposta)
def perguntar(dados: Pergunta):
    try:
        return responder(dados.pergunta.strip())
    except Exception as erro:
        print(f"Erro ao responder: {erro}")
        raise HTTPException(
            status_code=503,
            detail="O assistente está sobrecarregado agora. Tente de novo em alguns segundos.",
        )