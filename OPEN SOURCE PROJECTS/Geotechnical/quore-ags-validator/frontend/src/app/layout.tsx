import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Quore Geotechnical | AGS Validator",
  description: "Ultra-modern, cross-platform AGS data file validation engine.",
  manifest: "/manifest.json",
  themeColor: "#000000",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} bg-black text-white antialiased selection:bg-white/20 font-sans`}>
        {children}
      </body>
    </html>
  );
}
