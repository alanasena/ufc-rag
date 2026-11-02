"""Etapa 3: o "cérebro" do assistente.

1. Busca os trechos mais parecidos com a pergunta
2. Manda os trechos + a pergunta pro Gemini, com regras bem claras
3. Devolve a resposta e as fontes (documento + página) que ela usou

Teste:
    python -m app.resposta "quantas faltas posso ter?"
"""

import re
import sys
import time

from google.genai import errors, types

from app.busca import buscar
from app.config import MODELO_LLM, MODELO_RESERVA, nome_do_documento
from app.embeddings import cliente

QUANTIDADE_TRECHOS = 6

RESPOSTA_SEM_INFO = "Não encontrei essa informação nos documentos oficiais que eu tenho."

# As "regras do jogo" para o Gemini. É aqui que a gente impede que ele invente coisas.
INSTRUCOES = f"""Você é um assistente que tira dúvidas de estudantes da Universidade Federal do Ceará (UFC).

Regras:
1. Responda SOMENTE com base nos trechos fornecidos. Não use conhecimento próprio.
2. Se os trechos não tiverem a resposta, responda exatamente: "{RESPOSTA_SEM_INFO}"
3. Depois de cada informação, indique o trecho usado com o número entre colchetes, por exemplo [1] ou [2][3].
4. Responda em português, de forma curta, clara e direta.
5. Se a informação vier de um artigo, diga o número dele (ex.: "Art. 113")."""


def montar_contexto(trechos: list[dict]) -> str:
    """Junta os trechos numerados, para o Gemini poder citar [1], [2]..."""
    partes = []
    for i, t in enumerate(trechos, start=1):
        partes.append(f"[{i}] {nome_do_documento(t['documento'])}, página {t['pagina']}:\n{t['texto']}")
    return "\n\n".join(partes)


# Códigos de erro que valem uma nova tentativa:
# 429 = limite do plano grátis, 500/503 = servidor com problema ou ocupado, 504 = demorou demais
ERROS_TEMPORARIOS = (429, 500, 503, 504)


def montar_config(modelo: str) -> types.GenerateContentConfig:
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCOES,
        temperature=0.1,  # baixa = respostas mais fiéis e menos "criativas"
    )
    # Diminui o "pensamento" do modelo: responde mais rápido e gasta menos cota
    if modelo.startswith("gemini-2.5"):
        config.thinking_config = types.ThinkingConfig(thinking_budget=0)
    else:
        config.thinking_config = types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
    return config


def chamar_gemini(prompt: str) -> str:
    """Tenta o modelo principal 3 vezes. Se continuar falhando, tenta o modelo reserva."""
    modelos = list(dict.fromkeys([MODELO_LLM, MODELO_RESERVA]))  # sem repetir se forem iguais
    ultimo_erro = None
    for n, modelo in enumerate(modelos):
        if n > 0:
            print(f"  Trocando para o modelo reserva ({modelo})...")
        for tentativa in range(3):
            try:
                resposta = cliente.models.generate_content(
                    model=modelo, contents=prompt, config=montar_config(modelo)
                )
                return (resposta.text or "").strip()
            except errors.APIError as erro:
                ultimo_erro = erro
                if erro.code == 404:
                    print(f"  Modelo {modelo} não encontrado, pulando.")
                    break
                if erro.code not in ERROS_TEMPORARIOS:
                    raise
                if tentativa < 2:
                    espera = 10 * 2**tentativa  # 10s, 20s
                    print(f"  {modelo} respondeu erro {erro.code}. Esperando {espera}s...")
                    time.sleep(espera)
    raise ultimo_erro


def responder(pergunta: str) -> dict:
    trechos = buscar(pergunta, quantidade=QUANTIDADE_TRECHOS)
    prompt = f"Trechos dos documentos:\n\n{montar_contexto(trechos)}\n\nPergunta do estudante: {pergunta}"
    texto = chamar_gemini(prompt)

    # Descobre quais trechos o Gemini citou ([1], [2]...) para mostrar só essas fontes
    citados = sorted({int(n) for n in re.findall(r"\[(\d+)\]", texto)})
    fontes = [
        {
            "numero": n,
            "documento": nome_do_documento(trechos[n - 1]["documento"]),
            "arquivo": trechos[n - 1]["documento"],
            "pagina": trechos[n - 1]["pagina"],
            "trecho": trechos[n - 1]["texto"],
        }
        for n in citados
        if 1 <= n <= len(trechos)
    ]

    if RESPOSTA_SEM_INFO in texto:
        fontes = []

    # "trechos" = tudo que a busca trouxe. A API não manda isso pro site,
    # mas a avaliação usa para medir se a busca encontrou o trecho certo.
    return {"resposta": texto, "fontes": fontes, "trechos": trechos}


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "quantas faltas posso ter?"
    resultado = responder(pergunta)
    print(f"Pergunta: {pergunta}\n")
    print(f"Resposta: {resultado['resposta']}\n")
    print("Fontes:")
    if not resultado["fontes"]:
        print("  (nenhuma)")
    for f in resultado["fontes"]:
        print(f"  [{f['numero']}] {f['documento']}, página {f['pagina']}")