"""Etapa 2: cria o banco vetorial com os pedaços dos PDFs.

Rode uma vez (e de novo sempre que mudar os PDFs):
    python -m app.indexar
"""

import time

import chromadb

from app.config import NOME_COLECAO, PASTA_CHROMA
from app.documentos import carregar_pdfs, dividir_em_pedacos
from app.embeddings import gerar_embeddings

LOTE = 50  # quantos pedaços mandamos ao Gemini por vez


def indexar() -> None:
    pedacos = dividir_em_pedacos(carregar_pdfs())
    print(f"{len(pedacos)} pedaços para indexar.")

    banco = chromadb.PersistentClient(path=str(PASTA_CHROMA))

    # Apaga a coleção antiga (se existir) para não duplicar pedaços
    try:
        banco.delete_collection(NOME_COLECAO)
    except Exception:
        pass

    # "cosine" = mede a semelhança pelo ângulo entre os vetores
    colecao = banco.create_collection(NOME_COLECAO, metadata={"hnsw:space": "cosine"})

    for i in range(0, len(pedacos), LOTE):
        lote = pedacos[i : i + LOTE]
        vetores = gerar_embeddings([p["texto"] for p in lote], "RETRIEVAL_DOCUMENT")
        colecao.add(
            ids=[p["id"] for p in lote],
            embeddings=vetores,
            documents=[p["texto"] for p in lote],
            metadatas=[{"documento": p["documento"], "pagina": p["pagina"]} for p in lote],
        )
        print(f"  {min(i + LOTE, len(pedacos))}/{len(pedacos)} indexados")
        time.sleep(1)  # pausa curta para respeitar o limite do plano grátis

    print(f"Pronto! Banco salvo em {PASTA_CHROMA}")


if __name__ == "__main__":
    indexar()