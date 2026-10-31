// Conversa com a API em Python (FastAPI).
// O endereço vem de uma variável de ambiente, para trocar fácil quando publicar.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Fonte = {
  numero: number;
  documento: string;
  arquivo: string;
  pagina: number;
  trecho: string;
};

export type RespostaApi = {
  resposta: string;
  fontes: Fonte[];
};

export async function perguntar(pergunta: string): Promise<RespostaApi> {
  const resposta = await fetch(`${API_URL}/perguntar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pergunta }),
  });

  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => null);
    const detalhe = typeof erro?.detail === "string" ? erro.detail : null;
    throw new Error(detalhe ?? "Não consegui falar com o assistente. Tente de novo.");
  }

  return resposta.json();
}
