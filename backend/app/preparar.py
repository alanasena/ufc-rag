"""Roda antes de ligar a API: monta o banco vetorial a partir dos PDFs.

Com o cache de embeddings (cache/embeddings.json), isso leva poucos segundos
e não gasta nenhuma chamada do Gemini. Só pedaços novos vão para a API.
Como roda toda vez, o banco nunca fica desatualizado em relação aos PDFs e ao código.
"""

from app.indexar import indexar

if __name__ == "__main__":
    indexar()