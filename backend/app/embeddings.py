"""Transforma textos em embeddings (listas de números) usando o Gemini."""

import time

from google import genai
from google.genai import errors, types

from app.config import DIMENSOES, GEMINI_API_KEY, MODELO_EMBEDDING

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY não encontrada. Confira o arquivo backend/.env")

cliente = genai.Client(api_key=GEMINI_API_KEY)


def gerar_embeddings(textos: list[str], tipo: str) -> list[list[float]]:
    """Gera um embedding para cada texto.

    tipo:
      - "RETRIEVAL_DOCUMENT" para os pedaços dos PDFs
      - "RETRIEVAL_QUERY" para a pergunta do usuário
    O Gemini ajusta os números de acordo com o tipo, e isso melhora a busca.
    """
    for tentativa in range(5):
        try:
            resposta = cliente.models.embed_content(
                model=MODELO_EMBEDDING,
                contents=textos,
                config=types.EmbedContentConfig(task_type=tipo, output_dimensionality=DIMENSOES),
            )
            return [e.values for e in resposta.embeddings]
        except errors.APIError as erro:
            # 429 = limite do plano grátis. Espera um pouco e tenta de novo.
            if erro.code == 429 and tentativa < 4:
                espera = 30 * (tentativa + 1)
                print(f"  Limite do plano grátis atingido. Esperando {espera}s...")
                time.sleep(espera)
            else:
                raise
    return []