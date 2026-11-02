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

# Modelo que escreve a resposta. Dá pra trocar no .env sem mexer no código
MODELO_LLM = os.getenv("MODELO_LLM", "gemini-3.8-flash")
# Modelo reserva: usado quando o principal está ocupado ou lento
MODELO_RESERVA = os.getenv("MODELO_RESERVA", "gemini-3.8-flash")
# Mais opções, separadas por vírgula, para quando o Gemini estiver lotado.
# O Gemma é um modelo aberto do Google, também grátis na mesma chave e com fila separada.
MODELOS_EXTRAS = [
    m.strip()
    for m in os.getenv("MODELOS_EXTRAS", "gemini-3.5-flash-lite,gemma-4-31b-it").split(",")
    if m.strip()
]

# Nomes bonitos para mostrar nas fontes
NOMES_DOCUMENTOS = {
    "regimento-geral.pdf": "Regimento Geral da UFC",
    "estatuto-ufc.pdf": "Estatuto da UFC",
    "prograd-supressao.pdf": "Prograd: Perguntas sobre supressão e trancamento",
}


def nome_do_documento(arquivo: str) -> str:
    return NOMES_DOCUMENTOS.get(arquivo, arquivo)


# Onde o ChromaDB salva o banco vetorial
PASTA_CHROMA = PASTA_BACKEND / "chroma_db"
NOME_COLECAO = "documentos_ufc"
