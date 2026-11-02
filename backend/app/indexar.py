"""Etapa 2: cria o banco vetorial com os pedaços dos PDFs.

Rode uma vez (e de novo sempre que mudar os PDFs ou o jeito de cortar):
    python -m app.indexar

Cache de embeddings:
  Cada embedding gerado fica salvo em cache/embeddings.json.
  Na próxima vez, só os pedaços NOVOS ou ALTERADOS vão para o Gemini.
  Isso economiza a cota diária do plano grátis (1000 por dia) e faz o
  Docker e o site publicado ligarem sem gastar nenhuma chamada.
"""

import hashlib
import json
import time

import chromadb

from app.config import DIMENSOES, MODELO_EMBEDDING, NOME_COLECAO, PASTA_BACKEND, PASTA_CHROMA
from app.documentos import carregar_pdfs, dividir_em_pedacos

ARQUIVO_CACHE = PASTA_BACKEND / "cache" / "embeddings.json"
LOTE = 50  # quantos pedaços mandamos ao Gemini por vez


def chave(texto: str) -> str:
    """Uma "impressão digital" do texto. Se o texto (ou o modelo) mudar, a chave muda."""
    return hashlib.sha256(f"{MODELO_EMBEDDING}|{DIMENSOES}|{texto}".encode("utf-8")).hexdigest()


def carregar_cache() -> dict:
    if ARQUIVO_CACHE.exists():
        return json.loads(ARQUIVO_CACHE.read_text(encoding="utf-8"))
    return {}


def salvar_cache(cache: dict) -> None:
    ARQUIVO_CACHE.parent.mkdir(exist_ok=True)
    # números com 6 casas decimais: arquivo menor, sem diferença na busca
    enxuto = {k: [round(x, 6) for x in v] for k, v in cache.items()}
    ARQUIVO_CACHE.write_text(json.dumps(enxuto), encoding="utf-8")


def indexar() -> None:
    pedacos = dividir_em_pedacos(carregar_pdfs())
    cache = carregar_cache()
    faltando = [p for p in pedacos if chave(p["texto"]) not in cache]
    print(f"{len(pedacos)} pedaços. {len(pedacos) - len(faltando)} já estão no cache, {len(faltando)} para gerar.")

    # 1) Gera só os embeddings que faltam, salvando o cache a cada lote.
    #    Se a cota acabar no meio, o que já foi feito não se perde.
    if faltando:
        from app.embeddings import gerar_embeddings  # só precisa da chave do Gemini se faltar algo

        for i in range(0, len(faltando), LOTE):
            lote = faltando[i : i + LOTE]
            vetores = gerar_embeddings([p["texto"] for p in lote], "RETRIEVAL_DOCUMENT")
            for p, v in zip(lote, vetores):
                cache[chave(p["texto"])] = v
            salvar_cache(cache)
            print(f"  {min(i + LOTE, len(faltando))}/{len(faltando)} gerados")
            time.sleep(1)  # pausa curta para respeitar o limite do plano grátis

    # 2) Só agora, com tudo pronto, troca o banco antigo pelo novo.
    #    Assim nunca fica um banco pela metade.
    banco = chromadb.PersistentClient(path=str(PASTA_CHROMA))
    try:
        banco.delete_collection(NOME_COLECAO)
    except Exception:
        pass
    # "cosine" = mede a semelhança pelo ângulo entre os vetores
    colecao = banco.create_collection(NOME_COLECAO, metadata={"hnsw:space": "cosine"})
    for i in range(0, len(pedacos), 500):
        lote = pedacos[i : i + 500]
        colecao.add(
            ids=[p["id"] for p in lote],
            embeddings=[cache[chave(p["texto"])] for p in lote],
            documents=[p["texto"] for p in lote],
            metadatas=[{"documento": p["documento"], "pagina": p["pagina"]} for p in lote],
        )

    # Tira do cache o que não é mais usado (ex.: pedaços do jeito antigo de cortar)
    usados = {chave(p["texto"]) for p in pedacos}
    if set(cache) - usados:
        salvar_cache({k: v for k, v in cache.items() if k in usados})

    print(f"Pronto! {len(pedacos)} pedaços no banco ({PASTA_CHROMA})")


if __name__ == "__main__":
    indexar()
