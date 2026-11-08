"use client";
import { useDecks } from "@/hooks/useDecks";
import Link from "next/link";
import { DeleteDeckButton } from "@/components/decks/DeleteDeckButton";

export function DeckList() {
  const { data, isPending, isError } = useDecks();

  if (isPending) {
    return <div>読み込み中</div>;
  }

  if (isError) {
    return (
      <div className="text-destructive">
        デッキの取得に失敗しました。時間をおいて再度お試しください
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 py-12 text-center">
        デッキは0件です。まずはデッキを作成してください。
      </div>
    );
  }

  return (
    <ul className="grid grid-cols-1 gap-4">
      {data.map((deck) => {
        return (
          <li key={deck.id} className="flex items-center gap-2">
            <Link
              href={`/decks/${deck.id}`}
              className="flex flex-1 min-w-0 items-center justify-between gap-2 rounded-xl border bg-card p-4 transition hover:shadow-md"
            >
              <span className="font-bold truncate min-w-0">
                {deck.deck_name}
              </span>
              <span className="rounded-full bg-secondary px-2 py-0.5 text-sm">
                {deck.card_count}枚
              </span>
            </Link>
            <DeleteDeckButton deckId={deck.id} deckName={deck.deck_name} />
          </li>
        );
      })}
    </ul>
  );
}
