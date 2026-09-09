import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "RUEXIS AI — Multi-Tier Desktop Intelligence & Agentic Ingestion Platform",
  description: "Deterministic 6-Division architecture featuring 10 autonomous LangGraph agents, native Win32 C-FFI docking, dual-tier intelligent model routing, and 13-state mascot FSM.",
  icons: {
    icon: "/ruexis_logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable} dark scroll-smooth`}
    >
      <body className="min-h-screen bg-[#18181B] text-[#F4F3EE] font-sans antialiased selection:bg-[#DA7756]/30 selection:text-[#F4F3EE]">
        {children}
      </body>
    </html>
  );
}
