"""Roda antes de ligar a API: se o banco vetorial ainda não existe, cria ele.

Assim o container funciona sozinho, sem precisar rodar `python -m app.indexar` na mão.
"""

import chromadb

from app.config import NOME_COLECAO, PASTA_CHROMA
from app.indexar import indexar


def banco_pronto() -> bool:
    try:
        banco = chromadb.PersistentClient(path=str(PASTA_CHROMA))
        return banco.get_collection(NOME_COLECAO).count() > 0
    except Exception:
        return False


if __name__ == "__main__":
    if banco_pronto():
        print("Banco vetorial já existe. Pulando a indexação.")
    else:
        print("Banco vetorial não encontrado. Criando agora (leva alguns minutos)...")
        indexar()
