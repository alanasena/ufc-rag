"use client";

import { useState } from "react";
import type { Fonte } from "@/lib/api";
import { Estrela } from "./Enfeites";

export type MensagemChat = {
  id: number;
  autor: "usuario" | "assistente";
  texto: string;
  fontes?: Fonte[];
  erro?: boolean;
};

// Cada número de fonte ganha uma cor, igual adesivos diferentes
const CORES_CITACAO = [
  "bg-rosa text-tinta",
  "bg-amarelo text-tinta",
  "bg-laranja text-tinta",
  "bg-vermelho text-creme",
];

function corDaCitacao(numero: number) {
  return CORES_CITACAO[(numero - 1) % CORES_CITACAO.length];
}

function Citacao({ numero, grande = false }: { numero: number; grande?: boolean }) {
  return (
    <span
      className={`inline-grid place-items-center rounded-full border-2 border-tinta font-bold leading-none ${corDaCitacao(numero)} ${
        grande ? "size-7 text-xs" : "mx-0.5 size-5 align-[2px] text-[0.65rem]"
      }`}
      aria-label={`fonte ${numero}`}
    >
      {numero}
    </span>
  );
}

// Troca os [1], [2]... do texto por bolinhas coloridas
function TextoComCitacoes({ texto }: { texto: string }) {
  const partes = texto.split(/(\[\d+\])/g);
  return (
    <>
      {partes.map((parte, i) => {
        const numero = parte.match(/^\[(\d+)\]$/)?.[1];
        if (numero) return <Citacao key={i} numero={Number(numero)} />;
        return <span key={i}>{parte.replace(/\*\*/g, "")}</span>;
      })}
    </>
  );
}

// O Gemini às vezes responde em lista ("* item"). Aqui a gente transforma em <ul>
function TextoFormatado({ texto }: { texto: string }) {
  const linhas = texto.split("\n").filter((l) => l.trim() !== "");
  const blocos: { tipo: "p" | "ul"; linhas: string[] }[] = [];

  for (const linha of linhas) {
    const item = linha.match(/^\s*[*-]\s+(.*)/);
    if (item) {
      const ultimo = blocos[blocos.length - 1];
      if (ultimo?.tipo === "ul") ultimo.linhas.push(item[1]);
      else blocos.push({ tipo: "ul", linhas: [item[1]] });
    } else {
      blocos.push({ tipo: "p", linhas: [linha] });
    }
  }

  return (
    <div className="space-y-3">
      {blocos.map((bloco, i) =>
        bloco.tipo === "ul" ? (
          <ul key={i} className="space-y-1.5">
            {bloco.linhas.map((l, j) => (
              <li key={j} className="flex gap-2">
                <Estrela className="mt-1 size-3.5 shrink-0 text-laranja" />
                <span>
                  <TextoComCitacoes texto={l} />
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p key={i}>
            <TextoComCitacoes texto={bloco.linhas[0]} />
          </p>
        ),
      )}
    </div>
  );
}

function CartaoFonte({ fonte }: { fonte: Fonte }) {
  const [aberto, setAberto] = useState(false);
  return (
    <li className="overflow-hidden rounded-xl border-2 border-tinta bg-white">
      <button
        type="button"
        onClick={() => setAberto(!aberto)}
        className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm hover:bg-creme"
        aria-expanded={aberto}
      >
        <Citacao numero={fonte.numero} grande />
        <span className="flex-1">
          <span className="font-semibold">{fonte.documento}</span>
          <span className="text-tinta/60"> · página {fonte.pagina}</span>
        </span>
        <span className="whitespace-nowrap rounded-full border-2 border-tinta px-2.5 py-0.5 text-xs font-semibold">
          {aberto ? "fechar" : "ver trecho"}
        </span>
      </button>
      {aberto && (
        <blockquote className="border-t-2 border-dashed border-tinta/30 bg-creme/60 px-4 py-3 text-sm leading-relaxed text-tinta/80">
          “{fonte.trecho}”
        </blockquote>
      )}
    </li>
  );
}

export function Avatar() {
  return (
    <div className="grid size-10 shrink-0 place-items-center rounded-full border-2 border-tinta bg-amarelo sombra-dura-sm">
      <Estrela className="size-5 text-vermelho" />
    </div>
  );
}

export function Mensagem({ mensagem }: { mensagem: MensagemChat }) {
  if (mensagem.autor === "usuario") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm border-2 border-tinta bg-vermelho px-4 py-2.5 font-medium text-creme sombra-dura-sm">
          {mensagem.texto}
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <Avatar />
      <div className="min-w-0 flex-1 space-y-3">
        <div
          className={`rounded-2xl rounded-tl-sm border-2 border-tinta px-4 py-3 leading-relaxed sombra-dura ${
            mensagem.erro ? "bg-rosa" : "bg-white"
          }`}
        >
          <TextoFormatado texto={mensagem.texto} />
        </div>

        {mensagem.fontes && mensagem.fontes.length > 0 && (
          <div>
            <p className="mb-2 font-titulo text-sm text-vermelho">De onde veio isso:</p>
            <ul className="space-y-2">
              {mensagem.fontes.map((f) => (
                <CartaoFonte key={f.numero} fonte={f} />
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
