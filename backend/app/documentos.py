"""Etapa 1: ler os PDFs e dividir o texto em pedaços (chunks)."""

import re
from pathlib import Path

from pypdf import PdfReader

# Pasta onde ficam os PDFs (backend/docs)
PASTA_DOCS = Path(__file__).resolve().parent.parent / "docs"


def limpar_texto(texto: str) -> str:
    """Arruma o texto que sai do PDF, que costuma vir bagunçado."""
    texto = texto.replace("\x00", "")
    texto = re.sub(r"-\n(\w)", r"\1", texto)  # junta palavras quebradas com hífen no fim da linha
    texto = re.sub(r"\s+", " ", texto)  # troca quebras de linha e espaços repetidos por um espaço
    return texto.strip()


def carregar_pdfs(pasta: Path = PASTA_DOCS) -> list[dict]:
    """Lê cada página de cada PDF e guarda o texto junto com o nome do documento e o número da página."""
    paginas = []
    for arquivo in sorted(pasta.glob("*.pdf")):
        leitor = PdfReader(arquivo)
        for numero, pagina in enumerate(leitor.pages, start=1):
            texto = limpar_texto(pagina.extract_text() or "")
            if texto:
                paginas.append({"documento": arquivo.name, "pagina": numero, "texto": texto})
    return paginas


def dividir_em_pedacos(paginas: list[dict], tamanho: int = 1000, sobreposicao: int = 200) -> list[dict]:
    """Corta o texto de cada página em pedaços de até `tamanho` caracteres.

    - Tenta cortar no fim de uma frase, para não partir uma regra no meio.
    - Cada pedaço repete os últimos `sobreposicao` caracteres do anterior,
      assim uma regra que caiu na divisa aparece inteira em pelo menos um pedaço.
    """
    pedacos = []
    for pag in paginas:
        texto = pag["texto"]
        inicio = 0
        while inicio < len(texto):
            fim = min(inicio + tamanho, len(texto))
            if fim < len(texto):
                ponto = texto.rfind(". ", inicio + tamanho // 2, fim)
                if ponto != -1:
                    fim = ponto + 1
            trecho = texto[inicio:fim].strip()
            if trecho:
                pedacos.append({
                    "id": f"{pag['documento']}-p{pag['pagina']}-{len(pedacos)}",
                    "documento": pag["documento"],
                    "pagina": pag["pagina"],
                    "texto": trecho,
                })
            if fim >= len(texto):
                break
            inicio = max(fim - sobreposicao, inicio + 1)
    return pedacos


if __name__ == "__main__":
    paginas = carregar_pdfs()
    pedacos = dividir_em_pedacos(paginas)

    print(f"Páginas lidas: {len(paginas)}")
    for doc in sorted({p["documento"] for p in paginas}):
        qtd = sum(1 for p in paginas if p["documento"] == doc)
        print(f"  - {doc}: {qtd} páginas")
    print(f"Pedaços criados: {len(pedacos)}")

    exemplo = pedacos[len(pedacos) // 2]
    print("\nExemplo de pedaço:")
    print(f"  {exemplo['documento']}, página {exemplo['pagina']}")
    print(f"  {exemplo['texto'][:400]}...")