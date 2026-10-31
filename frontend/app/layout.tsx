import type { Metadata } from "next";
import { Fraunces, Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ variable: "--font-geist", subsets: ["latin"] });
const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Assistente Acadêmico UFC",
  description: "Tire dúvidas sobre as regras da UFC com respostas baseadas nos documentos oficiais.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${geist.variable} ${fraunces.variable} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
