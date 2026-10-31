"use client";

import { useState } from "react";
import type { Fonte } from "@/lib/api";

export type MensagemChat = {
  id: number;
  autor: "usuario" | "assistente";
  texto: string;
  fontes?: Fonte[];
  erro?: boolean;
};

// Troca os [1], [2]... do texto por bolinhas numeradas
function TextoComCitacoes({ texto }: { texto: string }) {
  const partes = texto.split(/(\[\d+\])/g);
  return (
    <>
      {partes.map((parte, i) => {
        const numero = parte.match(/^\[(\d+)\]$/)?.[1];
        if (numero) {
          return (
            <sup key={i} className="citacao" aria-label={`fonte ${numero}`}>
              {numero}
            </sup>
          );
        }
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
          <ul key={i} className="list-disc space-y-1.5 pl-5 marker:text-tinta/40">
            {bloco.linhas.map((l, j) => (
              <li key={j}>
                <TextoComCitacoes texto={l} />
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
    <li className="rounded-lg border border-tinta/10 bg-papel">
      <button
        type="button"
        onClick={() => setAberto(!aberto)}
        className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm"
        aria-expanded={aberto}
      >
        <span className="citacao citacao-grande">{fonte.numero}</span>
        <span className="flex-1">
          <span className="font-medium text-tinta">{fonte.documento}</span>
          <span className="text-tinta/60"> · página {fonte.pagina}</span>
        </span>
        <span className="text-xs text-tinta/50">{aberto ? "fechar" : "ver trecho"}</span>
      </button>
      {aberto && (
        <blockquote className="border-t border-tinta/10 px-4 py-3 text-sm leading-relaxed text-tinta/75">
          “{fonte.trecho}”
        </blockquote>
      )}
    </li>
  );
}

export function Mensagem({ mensagem }: { mensagem: MensagemChat }) {
  if (mensagem.autor === "usuario") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-tinta px-4 py-2.5 text-papel">
          {mensagem.texto}
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-sol font-serif text-sm font-semibold text-tinta">
        U
      </div>
      <div className="min-w-0 flex-1 space-y-3">
        <div
          className={`rounded-2xl rounded-tl-md px-4 py-3 leading-relaxed ${
            mensagem.erro ? "bg-red-50 text-red-800" : "bg-white text-tinta shadow-sm ring-1 ring-tinta/5"
          }`}
        >
          <TextoFormatado texto={mensagem.texto} />
        </div>

        {mensagem.fontes && mensagem.fontes.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-tinta/50">Fontes</p>
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
