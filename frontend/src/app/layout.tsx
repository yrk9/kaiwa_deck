import type { Metadata } from "next";
import { Noto_Sans_JP } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Header } from "@/components/Header";

const notoSans = Noto_Sans_JP({
  variable: "--font-noto-sans-jp",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Kaiwa Deck",
  description: "会話の一歩をカードから",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" className={`${notoSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <Providers>
          <Header></Header>
          <main className="mx-auto w-full max-w-2xl px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
