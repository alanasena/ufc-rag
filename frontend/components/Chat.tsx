"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { perguntar } from "@/lib/api";
import { Mensagem, type MensagemChat } from "./Mensagem";

const SUGESTOES = [
  "Quantas faltas posso ter?",
  "Como trancar uma disciplina?",
  "Qual a média para passar direto?",
  "Supressão afeta o IRA?",
];

export function Chat() {
  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  const fimRef = useRef<HTMLDivElement>(null);
  const proximoId = useRef(0);

  // Rola a tela para a última mensagem
  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens, carregando]);

  async function enviar(pergunta: string) {
    const limpa = pergunta.trim();
    if (limpa.length < 3 || carregando) return;

    setMensagens((m) => [...m, { id: proximoId.current++, autor: "usuario", texto: limpa }]);
    setTexto("");
    setCarregando(true);

    try {
      const dados = await perguntar(limpa);
      setMensagens((m) => [
        ...m,
        { id: proximoId.current++, autor: "assistente", texto: dados.resposta, fontes: dados.fontes },
      ]);
    } catch (erro) {
      const texto = erro instanceof Error ? erro.message : "Algo deu errado. Tente de novo.";
      setMensagens((m) => [...m, { id: proximoId.current++, autor: "assistente", texto, erro: true }]);
    } finally {
      setCarregando(false);
    }
  }

  function aoEnviar(e: FormEvent) {
    e.preventDefault();
    enviar(texto);
  }

  const vazio = mensagens.length === 0;

  return (
    <div className="mx-auto flex h-dvh w-full max-w-3xl flex-col px-4">
      <header className="flex items-center justify-between border-b border-tinta/10 py-4">
        <div>
          <h1 className="font-serif text-xl font-semibold text-tinta">Assistente Acadêmico UFC</h1>
          <p className="text-sm text-tinta/60">Respostas com base nos documentos oficiais</p>
        </div>
        {!vazio && (
          <button
            type="button"
            onClick={() => setMensagens([])}
            className="whitespace-nowrap rounded-full px-3 py-1.5 text-sm text-tinta/60 hover:bg-tinta/5 hover:text-tinta"
          >
            Nova conversa
          </button>
        )}
      </header>

      <main className="flex-1 overflow-y-auto py-6">
        {vazio ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <p className="font-serif text-3xl leading-tight text-tinta sm:text-4xl">
              Tire suas dúvidas sobre <br />
              as <span className="destaque">regras da UFC</span>
            </p>
            <p className="mt-4 max-w-md text-tinta/60">
              Consulto o Regimento Geral, o Estatuto e as orientações da Prograd e mostro de onde veio
              cada resposta. Se não estiver nos documentos, eu aviso.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-2">
              {SUGESTOES.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => enviar(s)}
                  className="rounded-full border border-tinta/15 bg-white px-4 py-2 text-sm text-tinta transition hover:border-tinta/40 hover:shadow-sm"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {mensagens.map((m) => (
              <Mensagem key={m.id} mensagem={m} />
            ))}
            {carregando && (
              <div className="flex items-center gap-3 text-sm text-tinta/60">
                <div className="grid size-8 place-items-center rounded-full bg-sol font-serif text-sm font-semibold text-tinta">
                  U
                </div>
                <span className="pontinhos">Procurando nos documentos</span>
              </div>
            )}
            <div ref={fimRef} />
          </div>
        )}
      </main>

      <form onSubmit={aoEnviar} className="pb-5 pt-2">
        <div className="flex items-end gap-2 rounded-2xl border border-tinta/15 bg-white p-2 shadow-sm focus-within:border-tinta/40">
          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              // Enter envia, Shift + Enter pula linha
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                enviar(texto);
              }
            }}
            placeholder="Pergunte sobre faltas, trancamento, notas..."
            rows={1}
            maxLength={500}
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-tinta outline-none placeholder:text-tinta/40"
            aria-label="Sua pergunta"
          />
          <button
            type="submit"
            disabled={carregando || texto.trim().length < 3}
            className="rounded-xl bg-tinta px-4 py-2 text-sm font-medium text-papel transition hover:bg-tinta/90 disabled:opacity-30"
          >
            Enviar
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-tinta/40">
          Projeto de estudo, não é um canal oficial da UFC. Confirme informações importantes com a coordenação.
        </p>
      </form>
    </div>
  );
}
