# Imagem base: Python 3.12 numa versão enxuta do Linux
FROM python:3.12-slim

# Não guardar cache do pip (imagem menor) e mostrar os prints na hora
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# O Hugging Face roda o container com o usuário de número 1000.
# Criamos esse usuário aqui para ele ter permissão de escrever o banco vetorial.
RUN useradd -m -u 1000 user

WORKDIR /app

# Primeiro só o requirements.txt: assim o Docker reaproveita essa camada
# quando você muda só o código, e o build fica bem mais rápido
COPY requirements.txt .
RUN pip install -r requirements.txt

# Depois o código, os PDFs e o cache de embeddings
# (com o cache, o container cria o banco sem gastar nenhuma chamada do Gemini)
COPY --chown=user app ./app
COPY --chown=user docs ./docs
COPY --chown=user cache ./cache
RUN chown -R user /app

USER user

# Monta o banco vetorial AGORA, na hora do build (usa o cache, sem chamar o Gemini).
# Assim, quando o servidor acorda, ele já liga pronto, sem ler os PDFs de novo.
RUN python -m app.preparar

EXPOSE 8000

# Liga a API. A porta vem da variável PORT (se o site de hospedagem definir) ou usa 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
