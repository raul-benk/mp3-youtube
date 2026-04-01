import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YouTube MP3 Downloader",
  description: "Coleta links e baixa MP3 em lote"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
