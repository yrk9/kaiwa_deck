"use client";
import { useCreateDeck } from "@/hooks/useDecks";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";

export function DeckForm() {
  const { mutate, isPending, isError, error } = useCreateDeck();
  const router = useRouter();
  const [deckName, setDeckName] = useState<string>("");
  const [isInclude, setIsInclude] = useState<boolean>(true);

  // error は失敗すると自動で更新されるので、表示のたびにここで文言を決める
  const errorMessage =
    error instanceof ApiError && error.status === 409
      ? "デッキの上限（20個）に達しています。不要なデッキを削除してください"
      : "作成できませんでした。もう一度お試しください。";

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();

    mutate(
      { deck_name: deckName, include_official_cards: isInclude },
      { onSuccess: (newDeck) => router.push(`/decks/${newDeck.id}`) },
    );
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col">
        <label>
          デッキ名
          <input
            name="deck_name"
            value={deckName}
            onChange={(e) => setDeckName(e.target.value)}
            className="border border-gray-600"
          ></input>
        </label>
        <label>
          公式お題を入れる
          <input
            name="include"
            type="checkbox"
            checked={isInclude}
            onChange={(e) => setIsInclude(e.target.checked)}
          ></input>
        </label>

        <Button
          type="submit"
          disabled={isPending || deckName === ""}
          className="mx-auto"
        >
          {isPending ? "作成中" : "作成する"}
        </Button>
      </form>
      {isError && errorMessage}
    </div>
  );
}
