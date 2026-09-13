import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Lumina AI",
  description: "A premium AI assistant for all your needs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased bg-gray-50 dark:bg-zinc-950 text-gray-900 dark:text-gray-100`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
