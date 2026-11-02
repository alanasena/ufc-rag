"""Etapa 7: mede se o assistente acerta.

Para cada pergunta de avaliacao/perguntas.json, confere 3 coisas:
  1. Busca:    o trecho certo (documento + artigo) veio entre os encontrados?
  2. Resposta: a resposta tem as informações esperadas? Ou, se a pergunta
               não está nos documentos, ele disse que não sabe?
  3. Citação:  as fontes citadas são do documento/artigo certo?

Rodar:
    python -m app.avaliar
"""

import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from app.config import MODELO_LLM, PASTA_BACKEND
from app.resposta import QUANTIDADE_TRECHOS, RESPOSTA_SEM_INFO, responder

PASTA_AVALIACAO = PASTA_BACKEND / "avaliacao"
PAUSA_ENTRE_PERGUNTAS = 5  # segundos, para respeitar o limite do plano grátis


def normalizar(texto: str) -> str:
    """Deixa tudo minúsculo e sem acento, para comparar com mais justiça."""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def tem_artigo(texto: str, artigo: str) -> bool:
    """Procura 'Art. 113' (e não confunde com 'Art. 1130')."""
    padrao = rf"art\.?\s*{re.escape(artigo.lower())}(?![\d])"
    return re.search(padrao, normalizar(texto)) is not None


def trecho_bate(arquivo: str, texto: str, caso: dict) -> bool:
    """O trecho é do documento esperado e (se tiver) menciona o artigo esperado?"""
    if arquivo != caso["documento"]:
        return False
    return caso["artigo"] is None or tem_artigo(texto, caso["artigo"])


def tem_palavras(resposta: str, palavras_chave: list[str]) -> bool:
    """Cada item precisa aparecer. 'a|b' quer dizer 'a' OU 'b'."""
    texto = normalizar(resposta)
    for grupo in palavras_chave:
        opcoes = [normalizar(p) for p in grupo.split("|")]
        if not any(re.search(rf"\b{re.escape(o)}\b", texto) for o in opcoes):
            return False
    return True


def avaliar_caso(caso: dict) -> dict:
    resultado = responder(caso["pergunta"])
    resposta, fontes, trechos = resultado["resposta"], resultado["fontes"], resultado["trechos"]
    recusou = RESPOSTA_SEM_INFO in resposta

    if caso["deve_responder"]:
        busca_ok = any(trecho_bate(t["documento"], t["texto"], caso) for t in trechos)
        resposta_ok = not recusou and tem_palavras(resposta, caso["palavras_chave"])
        citacao_ok = any(trecho_bate(f["arquivo"], f["trecho"], caso) for f in fontes)
    else:
        busca_ok = None  # não existe trecho certo para achar
        resposta_ok = recusou and not fontes
        citacao_ok = None

    return {
        "id": caso["id"],
        "pergunta": caso["pergunta"],
        "deve_responder": caso["deve_responder"],
        "busca_ok": busca_ok,
        "resposta_ok": resposta_ok,
        "citacao_ok": citacao_ok,
        "resposta": resposta,
        "fontes": [f"{f['arquivo']} p.{f['pagina']}" for f in fontes],
    }


def porcentagem(valores: list) -> str:
    validos = [v for v in valores if v is not None]
    if not validos:
        return "-"
    return f"{100 * sum(validos) / len(validos):.0f}% ({sum(validos)}/{len(validos)})"


def marca(valor) -> str:
    return "-" if valor is None else ("✅" if valor else "❌")


def main() -> None:
    casos = json.loads((PASTA_AVALIACAO / "perguntas.json").read_text(encoding="utf-8"))
    print(f"Avaliando {len(casos)} perguntas com {MODELO_LLM}...\n")

    resultados = []
    for i, caso in enumerate(casos, start=1):
        try:
            r = avaliar_caso(caso)
        except Exception as erro:
            # Gemini fora do ar por um tempo: espera 1 minuto e tenta essa pergunta de novo
            print(f"  Erro na pergunta {caso['id']} ({erro.__class__.__name__}). Tentando de novo em 60s...")
            time.sleep(60)
            try:
                r = avaliar_caso(caso)
            except Exception:
                r = {"id": caso["id"], "pergunta": caso["pergunta"], "deve_responder": caso["deve_responder"],
                     "busca_ok": None, "resposta_ok": None, "citacao_ok": None, "erro": True,
                     "resposta": "", "fontes": []}
                print(f"[{i:02d}/{len(casos)}] ⚠️  não deu pra avaliar (Gemini indisponível)  {caso['pergunta']}")
                resultados.append(r)
                continue
        resultados.append(r)
        print(f"[{i:02d}/{len(casos)}] busca {marca(r['busca_ok'])}  resposta {marca(r['resposta_ok'])}  "
              f"citação {marca(r['citacao_ok'])}  {caso['pergunta']}")
        if i < len(casos):
            time.sleep(PAUSA_ENTRE_PERGUNTAS)

    dentro = [r for r in resultados if r["deve_responder"]]
    fora = [r for r in resultados if not r["deve_responder"]]

    resumo = {
        "Busca encontrou o trecho certo (top " + str(QUANTIDADE_TRECHOS) + ")": porcentagem([r["busca_ok"] for r in dentro]),
        "Resposta correta (perguntas dos documentos)": porcentagem([r["resposta_ok"] for r in dentro]),
        "Citou a fonte certa": porcentagem([r["citacao_ok"] for r in dentro]),
        "Disse que não sabe (perguntas fora dos documentos)": porcentagem([r["resposta_ok"] for r in fora]),
        "Acerto geral": porcentagem([r["resposta_ok"] for r in resultados]),
    }

    com_erro = sum(1 for r in resultados if r.get("erro"))
    if com_erro:
        resumo["Perguntas não avaliadas (Gemini indisponível)"] = str(com_erro)

    print("\n===== RESULTADO =====")
    for nome, valor in resumo.items():
        print(f"{nome}: {valor}")

    # Salva tudo, para comparar depois de cada melhoria
    data = datetime.now().strftime("%Y-%m-%d %H:%M")
    (PASTA_AVALIACAO / "resultados.json").write_text(
        json.dumps({"data": data, "modelo": MODELO_LLM, "resumo": resumo, "detalhes": resultados},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    linhas = [
        f"# Resultado da avaliação\n",
        f"Data: {data} · Modelo: `{MODELO_LLM}` · {len(casos)} perguntas\n",
        "| Métrica | Resultado |",
        "|---|---|",
        *[f"| {nome} | {valor} |" for nome, valor in resumo.items()],
        "\n## Por pergunta\n",
        "| # | Pergunta | Busca | Resposta | Citação |",
        "|---|---|---|---|---|",
        *[f"| {r['id']} | {r['pergunta']} | {marca(r['busca_ok'])} | {marca(r['resposta_ok'])} | {marca(r['citacao_ok'])} |"
          for r in resultados],
    ]
    (PASTA_AVALIACAO / "RESULTADOS.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\nDetalhes salvos em avaliacao/resultados.json e avaliacao/RESULTADOS.md")


if __name__ == "__main__":
    main()