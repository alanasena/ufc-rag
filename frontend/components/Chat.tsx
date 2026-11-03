"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { acordarServidor, perguntar } from "@/lib/api";
import { Estrela, Fita, Selo } from "./Enfeites";
import { Avatar, Mensagem, type MensagemChat } from "./Mensagem";

// Cada sugestão tem uma cor e uma inclinação diferente, como adesivos colados
const SUGESTOES = [
  { texto: "Quantas faltas posso ter?", cor: "bg-amarelo", girar: "-rotate-2" },
  { texto: "Como trancar uma disciplina?", cor: "bg-rosa", girar: "rotate-1" },
  { texto: "Qual a média pra passar direto?", cor: "bg-laranja", girar: "-rotate-1" },
  { texto: "Supressão afeta o IRA?", cor: "bg-white", girar: "rotate-2" },
];

// Depois desse tempo carregando, avisa que o servidor grátis pode estar "acordando"
const AVISO_SERVIDOR_MS = 8000;

export function Chat() {
  const [mensagens, setMensagens] = useState<MensagemChat[]>([]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [demorando, setDemorando] = useState(false);
  const fimRef = useRef<HTMLDivElement>(null);
  const proximoId = useRef(0);

  // Assim que o site abre, já acorda o servidor
  useEffect(() => {
    acordarServidor();
  }, []);

  // Rola a tela para a última mensagem
  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens, carregando, demorando]);

  async function enviar(pergunta: string) {
    const limpa = pergunta.trim();
    if (limpa.length < 3 || carregando) return;

    setMensagens((m) => [...m, { id: proximoId.current++, autor: "usuario", texto: limpa }]);
    setTexto("");
    setCarregando(true);
    const relogio = setTimeout(() => setDemorando(true), AVISO_SERVIDOR_MS);

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
      clearTimeout(relogio);
      setCarregando(false);
      setDemorando(false);
    }
  }

  function aoEnviar(e: FormEvent) {
    e.preventDefault();
    enviar(texto);
  }

  const vazio = mensagens.length === 0;

  return (
    <div className="flex h-dvh flex-col">
      <div className="listras h-3 shrink-0 border-b-2 border-tinta" />

      <header className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-2">
          <h1 className="font-titulo text-2xl text-vermelho sm:text-3xl">Tira-Dúvidas UFC</h1>
          <span className="hidden sm:inline-block">
            <Selo cor="amarelo" girar={-6} className="px-3 py-2 text-xs">
              com IA!
            </Selo>
          </span>
        </div>
        {!vazio && (
          <button
            type="button"
            onClick={() => setMensagens([])}
            className="whitespace-nowrap rounded-full border-2 border-tinta bg-white px-3 py-1.5 text-sm font-semibold sombra-dura-sm transition hover:-translate-y-0.5"
          >
            Nova conversa
          </button>
        )}
      </header>

      <Fita />

      <main className="mx-auto w-full max-w-3xl flex-1 overflow-y-auto px-4 py-6">
        {vazio ? (
          <div className="relative flex min-h-full flex-col items-center justify-center py-10 text-center">
            {/* estrelinhas espalhadas */}
            <Estrela className="absolute left-[8%] top-[12%] size-6 rotate-12 text-amarelo" />
            <Estrela className="absolute right-[10%] top-[20%] size-4 text-rosa" />
            <Estrela className="absolute bottom-[18%] left-[14%] size-4 text-laranja" />
            <Estrela className="absolute bottom-[10%] right-[16%] size-7 -rotate-12 text-vermelho" />

            <div className="relative">
              <Selo cor="rosa" girar={-8} className="absolute -top-12 left-0 sm:-left-12 sm:-top-8">
                Cita a fonte!
              </Selo>
              <p className="letreiro text-[2.7rem] leading-[1.05] text-vermelho sm:text-7xl">
                Tira-dúvidas
                <br />
                <span className="text-laranja">da UFC</span>
              </p>
              <Selo cor="amarelo" girar={6} className="absolute -bottom-12 right-0 sm:-bottom-6 sm:-right-10">
                Não inventa!
              </Selo>
            </div>

            <p className="mt-14 max-w-md text-lg sm:mt-10">
              Pergunte sobre faltas, trancamento e notas. Eu procuro no <b>Regimento</b>, no <b>Estatuto</b> e
              nas orientações da <b>Prograd</b> e mostro de onde veio cada resposta.
            </p>

            <div className="mt-8 flex flex-wrap justify-center gap-3">
              {SUGESTOES.map((s) => (
                <button
                  key={s.texto}
                  type="button"
                  onClick={() => enviar(s.texto)}
                  className={`${s.cor} ${s.girar} rounded-full border-2 border-tinta px-4 py-2 text-sm font-semibold sombra-dura-sm transition hover:-translate-y-0.5 hover:rotate-0`}
                >
                  {s.texto}
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
              <div className="flex items-center gap-3">
                <Avatar />
                <div className="rounded-2xl border-2 border-dashed border-tinta/40 bg-white/60 px-4 py-2.5 text-sm">
                  <span className="font-semibold">Procurando nos documentos </span>
                  <span className="text-laranja">
                    <span className="pulando">★</span>
                    <span className="pulando">★</span>
                    <span className="pulando">★</span>
                  </span>
                  {demorando && (
                    <p className="mt-1 text-tinta/70">
                      O servidor grátis estava dormindo e está acordando. Pode levar cerca de 1 minuto. 😴
                    </p>
                  )}
                </div>
              </div>
            )}
            <div ref={fimRef} />
          </div>
        )}
      </main>

      <form onSubmit={aoEnviar} className="mx-auto w-full max-w-3xl px-4 pb-4 pt-2">
        <div className="flex items-end gap-2 rounded-2xl border-2 border-tinta bg-white p-2 sombra-dura">
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
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 outline-none placeholder:text-tinta/45"
            aria-label="Sua pergunta"
          />
          <button
            type="submit"
            disabled={carregando || texto.trim().length < 3}
            className="rounded-xl border-2 border-tinta bg-vermelho px-5 py-2 font-titulo text-creme transition hover:-translate-y-0.5 disabled:translate-y-0 disabled:opacity-40"
          >
            Enviar!
          </button>
        </div>
        <p className="mt-3 text-center text-xs text-tinta/60">
          Projeto de estudo, não é um canal oficial da UFC. Confirme informações importantes com a coordenação.
        </p>
      </form>
    </div>
  );
}
