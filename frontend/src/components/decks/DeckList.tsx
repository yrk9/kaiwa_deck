"use client";
import { useDecks } from "@/hooks/useDecks";
import Link from "next/link";

export function DeckList() {
  const { data, isPending, isError } = useDecks();

  if (isPending) {
    return <div>読み込み中</div>;
  }

  if (isError) {
    return (
      <div className="text-red-600">
        デッキの取得に失敗しました。時間をおいて再度お試しください
      </div>
    );
  }

  if (data.length === 0) {
    return <div>デッキは0件です。まずはデッキを作成してください。</div>;
  }

  return (
    <ul>
      {data.map((deck) => {
        return (
          <li key={deck.id}>
            <Link href={`/decks/${deck.id}`}>
              {deck.deck_name} {deck.card_count}枚
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
