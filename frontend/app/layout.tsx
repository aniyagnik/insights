import type { Metadata } from "next";
import Providers from "@/components/Providers";  // Imported
import "./globals.css";

export const metadata: Metadata = {
  title: "Real-Time Analytics Platform",
  description: "Production-grade multi-tenant analytics engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased min-h-screen">
        <Providers> 
          {children}
        </Providers>
      </body>
    </html>
  );
}