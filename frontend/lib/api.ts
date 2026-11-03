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
  let resposta: Response;
  try {
    resposta = await fetch(`${API_URL}/perguntar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta }),
    });
  } catch {
    // Nem chegou na API: ela está desligada, sem internet, ou bloqueada pelo CORS
    throw new Error("Não consegui falar com o servidor agora. Confira sua internet e tente de novo em alguns segundos.");
  }

  if (!resposta.ok) {
    const erro = await resposta.json().catch(() => null);
    const detalhe = typeof erro?.detail === "string" ? erro.detail : null;
    throw new Error(detalhe ?? "Não consegui falar com o assistente. Tente de novo.");
  }

  return resposta.json();
}

// Manda um "oi" pra API assim que o site abre.
// No plano grátis do Render a API dorme; assim ela já vai acordando
// enquanto a pessoa lê a tela e digita a pergunta.
export function acordarServidor(): void {
  fetch(`${API_URL}/saude`).catch(() => {
    // se falhar, tudo bem: a pergunta tenta de novo
  });
}
