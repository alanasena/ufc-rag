import type { Metadata } from "next";
import { Bricolage_Grotesque, Shrikhand } from "next/font/google";
import "./globals.css";

// Shrikhand: fonte retrô e "gordinha" para títulos. Bricolage: divertida, mas fácil de ler.
const retro = Shrikhand({ variable: "--font-retro", weight: "400", subsets: ["latin"] });
const corpo = Bricolage_Grotesque({ variable: "--font-corpo", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Tira-Dúvidas UFC",
  description: "Tire dúvidas sobre as regras da UFC com respostas baseadas nos documentos oficiais.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${retro.variable} ${corpo.variable} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
