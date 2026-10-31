# Imagem base: Python 3.12 numa versão enxuta do Linux
FROM python:3.12-slim

# Não guardar cache do pip (imagem menor) e mostrar os prints na hora
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primeiro só o requirements.txt: assim o Docker reaproveita essa camada
# quando você muda só o código, e o build fica bem mais rápido
COPY requirements.txt .
RUN pip install -r requirements.txt

# Depois o código e os PDFs
COPY app ./app
COPY docs ./docs

EXPOSE 8000

# 1) cria o banco vetorial se ainda não existir  2) liga a API
# A porta vem da variável PORT (os sites de hospedagem definem ela) ou usa 8000
CMD python -m app.preparar && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
