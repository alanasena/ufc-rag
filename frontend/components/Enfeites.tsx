// Enfeites visuais: selos com borda serrilhada, estrelas e a fita rolando.

// Gera o contorno serrilhado de um selo (como os adesivos "Cluck feast!")
function contornoSerrilhado(dentes = 9, profundidade = 7): string {
  const pontos: string[] = [];
  const lado = (de: [number, number], para: [number, number], fora: [number, number]) => {
    for (let i = 0; i < dentes * 2; i++) {
      const t = i / (dentes * 2);
      const x = de[0] + (para[0] - de[0]) * t;
      const y = de[1] + (para[1] - de[1]) * t;
      const d = i % 2 === 0 ? 0 : profundidade;
      pontos.push(`${x + fora[0] * d}% ${y + fora[1] * d}%`);
    }
  };
  lado([0, 0], [100, 0], [0, 1]); // em cima
  lado([100, 0], [100, 100], [-1, 0]); // direita
  lado([100, 100], [0, 100], [0, -1]); // embaixo
  lado([0, 100], [0, 0], [1, 0]); // esquerda
  return `polygon(${pontos.join(", ")})`;
}

const SERRILHADO = contornoSerrilhado();

const CORES_SELO = {
  rosa: "bg-rosa text-tinta",
  amarelo: "bg-amarelo text-tinta",
  vermelho: "bg-vermelho text-creme",
  laranja: "bg-laranja text-tinta",
} as const;

export function Selo({
  children,
  cor = "rosa",
  girar = 0,
  className = "",
}: {
  children: React.ReactNode;
  cor?: keyof typeof CORES_SELO;
  girar?: number;
  className?: string;
}) {
  return (
    <span
      className={`inline-block px-5 py-3 font-titulo text-sm leading-none ${CORES_SELO[cor]} ${className}`}
      style={{ clipPath: SERRILHADO, transform: `rotate(${girar}deg)` }}
    >
      {children}
    </span>
  );
}

export function Estrela({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className}>
      <path
        d="M12 1.5l2.9 6.7 7.3.6-5.5 4.8 1.7 7.1L12 17l-6.4 3.7 1.7-7.1L1.8 8.8l7.3-.6z"
        fill="currentColor"
      />
    </svg>
  );
}

const ITENS_FITA = ["Regimento Geral", "Estatuto da UFC", "Prograd", "Cita a fonte", "Não inventa"];

export function Fita() {
  // A lista aparece duas vezes para a rolagem não ter "buraco"
  const itens = [...ITENS_FITA, ...ITENS_FITA, ...ITENS_FITA, ...ITENS_FITA];
  return (
    <div className="overflow-hidden border-y-2 border-tinta bg-vermelho py-1.5" aria-hidden="true">
      <div className="fita-trilho">
        {itens.map((item, i) => (
          <span key={i} className="flex items-center gap-3 px-3 font-titulo text-sm text-creme">
            {item}
            <Estrela className="size-3 text-amarelo" />
          </span>
        ))}
      </div>
    </div>
  );
}
