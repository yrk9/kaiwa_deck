import Link from "next/link";

// 全ページ共通のヘッダー。幅は、layout.tsx の main と同じにして左端を揃える
export function Header() {
  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex w-full max-w-2xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-bold tracking-wide">
          Kaiwa Deck
        </Link>
        <nav>
          <Link
            href="/decks"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            デッキ一覧
          </Link>
        </nav>
      </div>
    </header>
  );
}
