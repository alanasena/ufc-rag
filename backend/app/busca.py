"""Busca os pedaços mais parecidos com uma pergunta.

Teste:
    python -m app.busca "quantas faltas posso ter?"
"""

import sys

import chromadb

from app.config import NOME_COLECAO, PASTA_CHROMA
from app.embeddings import gerar_embeddings


def abrir_colecao():
    banco = chromadb.PersistentClient(path=str(PASTA_CHROMA))
    return banco.get_collection(NOME_COLECAO)


def buscar(pergunta: str, quantidade: int = 5) -> list[dict]:
    """Devolve os `quantidade` pedaços mais parecidos com a pergunta."""
    colecao = abrir_colecao()
    vetor = gerar_embeddings([pergunta], "RETRIEVAL_QUERY")[0]
    resultado = colecao.query(query_embeddings=[vetor], n_results=quantidade)

    trechos = []
    for texto, meta, distancia in zip(
        resultado["documents"][0], resultado["metadatas"][0], resultado["distances"][0]
    ):
        trechos.append({
            "texto": texto,
            "documento": meta["documento"],
            "pagina": meta["pagina"],
            "semelhanca": round(1 - distancia, 3),  # quanto mais perto de 1, mais parecido
        })
    return trechos


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "quantas faltas posso ter?"
    print(f"Pergunta: {pergunta}\n")
    for i, t in enumerate(buscar(pergunta), start=1):
        print(f"{i}. {t['documento']}, página {t['pagina']} (semelhança {t['semelhanca']})")
        print(f"   {t['texto'][:200]}...\n")