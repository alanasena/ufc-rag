"""Configurações do projeto num lugar só."""

import os
from pathlib import Path

from dotenv import load_dotenv

PASTA_BACKEND = Path(__file__).resolve().parent.parent

# Lê o arquivo backend/.env (a chave fica lá, nunca no código)
load_dotenv(PASTA_BACKEND / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Modelo que transforma texto em números (embeddings)
MODELO_EMBEDDING = "gemini-embedding-001"
# Tamanho de cada vetor. 768 é bem menor que o padrão (3072) e funciona bem para textos curtos
DIMENSOES = 768

# Onde o ChromaDB salva o banco vetorial
PASTA_CHROMA = PASTA_BACKEND / "chroma_db"
NOME_COLECAO = "documentos_ufc"