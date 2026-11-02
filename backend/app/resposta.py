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
from app.config import MODELO_LLM, MODELO_RESERVA, MODELOS_EXTRAS, nome_do_documento
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
    config = types.GenerateContentConfig(temperature=0.1)  # baixa = respostas mais fiéis
    if modelo.startswith("gemma"):
        # O Gemma não aceita "instruções de sistema" nem controle de pensamento.
        # As regras vão junto com a pergunta (ver montar_conteudo).
        return config
    config.system_instruction = INSTRUCOES
    # Diminui o "pensamento" do modelo: responde mais rápido e gasta menos cota
    if modelo.startswith("gemini-2.5"):
        config.thinking_config = types.ThinkingConfig(thinking_budget=0)
    else:
        config.thinking_config = types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
    return config


def montar_conteudo(modelo: str, prompt: str) -> str:
    if modelo.startswith("gemma"):
        return f"{INSTRUCOES}\n\n{prompt}"
    return prompt


def chamar_gemini(prompt: str) -> str:
    """Tenta cada modelo da lista (até 2 vezes cada) até um responder.

    Ordem: principal → reserva → extras. Se um modelo estiver lotado ou não existir,
    passa para o próximo. Assim, um pico de uso num modelo não derruba o assistente.
    """
    modelos = list(dict.fromkeys([MODELO_LLM, MODELO_RESERVA, *MODELOS_EXTRAS]))  # sem repetir
    ultimo_erro = None
    for n, modelo in enumerate(modelos):
        if n > 0:
            print(f"  Tentando outro modelo: {modelo}...")
        for tentativa in range(2):
            try:
                resposta = cliente.models.generate_content(
                    model=modelo, contents=montar_conteudo(modelo, prompt), config=montar_config(modelo)
                )
                return (resposta.text or "").strip()
            except errors.APIError as erro:
                ultimo_erro = erro
                if erro.code in ERROS_TEMPORARIOS and tentativa == 0:
                    print(f"  {modelo} respondeu erro {erro.code}. Esperando 8s...")
                    time.sleep(8)
                    continue
                # 404 (não existe), 400 (não aceita alguma opção) ou lotado de novo: próximo modelo
                print(f"  {modelo} falhou (erro {erro.code}), pulando.")
                break
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
