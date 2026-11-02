"""Etapa 1 (versão 2): ler os PDFs e dividir o texto em pedaços (chunks).

Versão 1: cortava a cada 1000 caracteres. Os parágrafos de artigos grandes
ficavam em pedaços sem o "Art. X" escrito, e aí a resposta saía sem o artigo.

Versão 2 (chunking estrutural): corta onde começa cada artigo.
- Artigo pequeno = 1 pedaço, que já começa com "Art. 113. ..."
- Artigo grande = vários pedaços, e cada continuação leva o nome na frente:
  "[Art. 110, continuação] § 3º ..."
- Documento sem artigos (como o FAQ da Prograd) = cortado por frases.
"""

import re
from pathlib import Path

from pypdf import PdfReader

# Pasta onde ficam os PDFs (backend/docs)
PASTA_DOCS = Path(__file__).resolve().parent.parent / "docs"

TAMANHO_MAXIMO = 1200  # tamanho máximo de um pedaço, em caracteres
JUNTAR_ATE = 600  # artigos bem curtos vizinhos são juntados até esse tamanho

# "Art. 101-A", "Art. 5º", "Art 24"
PADRAO_ARTIGO = re.compile(r"Art\.?\s*(\d+)\s*[ºo°]?\s*(?:-\s*([A-Z])\b)?")
# Fim de frase: ponto ou ponto e vírgula, seguido de letra maiúscula ou §.
# Assim "Art. 113" e "Prov. 02/2018" não são cortados no meio.
PADRAO_FIM_FRASE = re.compile(r"(?<=[.;])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ§])")


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


def juntar_paginas(paginas: list[dict]) -> tuple[str, list[tuple[int, int]]]:
    """Junta as páginas de um documento num texto só, lembrando onde cada página começa.

    Isso deixa um artigo que começa numa página e termina na outra ficar inteiro.
    """
    partes, inicios, posicao = [], [], 0
    for pag in paginas:
        inicios.append((posicao, pag["pagina"]))
        partes.append(pag["texto"])
        posicao += len(pag["texto"]) + 1
    return " ".join(partes), inicios


def pagina_da_posicao(inicios: list[tuple[int, int]], posicao: int) -> int:
    pagina = inicios[0][1]
    for inicio, numero in inicios:
        if inicio > posicao:
            break
        pagina = numero
    return pagina


def achar_artigos(texto: str) -> list[tuple[int, str]]:
    """Acha onde começa cada artigo. Só conta quando "Art." abre uma frase,
    para não confundir com citações tipo "conforme o Art. 54 do Estatuto"."""
    artigos = []
    for m in PADRAO_ARTIGO.finditer(texto):
        antes = texto[max(0, m.start() - 2) : m.start()]
        if m.start() == 0 or re.fullmatch(r"[.;:)\]] ", antes):
            rotulo = f"Art. {m.group(1)}" + (f"-{m.group(2)}" if m.group(2) else "")
            artigos.append((m.start(), rotulo))
    return artigos


def dividir_em_frases(texto: str, inicio: int) -> list[tuple[int, str]]:
    """Divide em frases, guardando a posição de cada uma no documento."""
    frases, pos = [], 0
    for m in PADRAO_FIM_FRASE.finditer(texto):
        frases.append((inicio + pos, texto[pos : m.start()]))
        pos = m.end()
    frases.append((inicio + pos, texto[pos:]))
    return [(p, f) for p, f in frases if f.strip()]


def dividir_secao(texto: str, inicio: int, rotulo: str | None) -> list[tuple[int, str]]:
    """Divide uma seção (um artigo, ou um documento sem artigos) em pedaços de até TAMANHO_MAXIMO.

    Cada pedaço novo repete a última frase do anterior (sobreposição),
    e se for continuação de um artigo, leva o nome dele na frente.
    """
    if len(texto) <= TAMANHO_MAXIMO:
        return [(inicio, texto)]

    pedacos, atual, atual_inicio = [], [], inicio
    for pos, frase in dividir_em_frases(texto, inicio):
        # frase gigante: corta no espaço mais próximo
        while len(frase) > TAMANHO_MAXIMO:
            corte = frase.rfind(" ", 0, TAMANHO_MAXIMO)
            corte = corte if corte > 0 else TAMANHO_MAXIMO
            if atual:
                pedacos.append((atual_inicio, " ".join(atual)))
                atual = []
            pedacos.append((pos, frase[:corte]))
            pos, frase = pos + corte + 1, frase[corte + 1 :]
        tamanho_atual = sum(len(f) + 1 for f in atual)
        if atual and tamanho_atual + len(frase) > TAMANHO_MAXIMO:
            pedacos.append((atual_inicio, " ".join(atual)))
            atual, atual_inicio = [atual[-1]], pos  # repete a última frase
        if not atual:
            atual_inicio = pos
        atual.append(frase)
    if atual:
        pedacos.append((atual_inicio, " ".join(atual)))

    if rotulo:
        pedacos = [(p, t) if i == 0 else (p, f"[{rotulo}, continuação] {t}") for i, (p, t) in enumerate(pedacos)]
    return pedacos


def dividir_documento(paginas: list[dict]) -> list[tuple[int, str]]:
    texto, inicios = juntar_paginas(paginas)
    artigos = achar_artigos(texto)

    # Seções: o que vem antes do 1º artigo, e depois um artigo por seção
    secoes = []
    limites = [p for p, _ in artigos] + [len(texto)]
    if not artigos or limites[0] > 0:
        secoes.append((0, texto[: limites[0]].strip(), None))
    for (pos, rotulo), fim in zip(artigos, limites[1:]):
        secoes.append((pos, texto[pos:fim].strip(), rotulo))

    # Junta artigos bem curtos que estão um do lado do outro
    juntas = []
    for pos, trecho, rotulo in secoes:
        if not trecho:
            continue
        if juntas and len(juntas[-1][1]) + len(trecho) < JUNTAR_ATE:
            p, t, r = juntas[-1]
            juntas[-1] = (p, f"{t} {trecho}", r or rotulo)
        else:
            juntas.append((pos, trecho, rotulo))

    pedacos = []
    for pos, trecho, rotulo in juntas:
        for p, t in dividir_secao(trecho, pos, rotulo):
            pedacos.append((pagina_da_posicao(inicios, p), t.strip()))
    return pedacos


def dividir_em_pedacos(paginas: list[dict]) -> list[dict]:
    """Divide todos os documentos em pedaços, guardando documento e página de cada um."""
    pedacos = []
    for documento in sorted({p["documento"] for p in paginas}):
        paginas_doc = [p for p in paginas if p["documento"] == documento]
        for i, (pagina, texto) in enumerate(dividir_documento(paginas_doc)):
            pedacos.append({
                "id": f"{documento}-{i}",
                "documento": documento,
                "pagina": pagina,
                "texto": texto,
            })
    return pedacos


if __name__ == "__main__":
    paginas = carregar_pdfs()
    pedacos = dividir_em_pedacos(paginas)

    print(f"Páginas lidas: {len(paginas)}")
    for doc in sorted({p["documento"] for p in paginas}):
        qtd_pag = sum(1 for p in paginas if p["documento"] == doc)
        qtd_ped = sum(1 for p in pedacos if p["documento"] == doc)
        print(f"  - {doc}: {qtd_pag} páginas, {qtd_ped} pedaços")
    print(f"Pedaços criados: {len(pedacos)}")
    print(f"Maior pedaço: {max(len(p['texto']) for p in pedacos)} caracteres")

    # Mostra exemplos de artigos, para conferir se o corte ficou bom
    for busca in ["Art. 110", "[Art. 110, continuação]", "Art. 113"]:
        exemplo = next((p for p in pedacos if p["texto"].startswith(busca)), None)
        if exemplo:
            print(f"\nExemplo ({exemplo['documento']}, página {exemplo['pagina']}):")
            print(f"  {exemplo['texto'][:300]}...")
