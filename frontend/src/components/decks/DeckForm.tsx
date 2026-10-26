"use client";
import { useCreateDeck } from "@/hooks/useDecks";
import { Button } from "@/components/ui/button";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { CardCategory } from "@/types/api";

export function DeckForm() {
  const { mutate, isPending, isError, error } = useCreateDeck();
  const router = useRouter();
  const [deckName, setDeckName] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<CardCategory | "">(
    "interview",
  );

  // error は失敗すると自動で更新されるので、表示のたびにここで文言を決める
  const errorMessage =
    error instanceof ApiError && error.status === 409
      ? "デッキの上限（20個）に達しています。不要なデッキを削除してください"
      : "作成できませんでした。もう一度お試しください。";

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();

    mutate(
      {
        deck_name: deckName,
        official_category:
          selectedCategory === "" ? undefined : selectedCategory,
      },
      { onSuccess: (newDeck) => router.push(`/decks/${newDeck.id}`) },
    );
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Label className="flex flex-row gap-2">
          <span className="w-18 shrink-0">デッキ名</span>
          <Input
            name="deck_name"
            value={deckName}
            onChange={(e) => setDeckName(e.target.value)}
            className="flex-1"
          ></Input>
        </Label>
        <Label>
          <span className="w-18 shrink-0">公式のお題</span>
          <select
            value={selectedCategory}
            onChange={(e) =>
              setSelectedCategory(e.target.value as CardCategory | "")
            }
            className="h-8 flex-1 rounded-lg border border-input bg-transparent px-2.5"
          >
            <option value="interview">面接の定番</option>
            <option value="reverse_question">逆質問</option>
            <option value="small_talk">懇親会の話題</option>
            <option value="">入れない</option>
          </select>
        </Label>

        <Button
          type="submit"
          disabled={isPending || deckName.trim() === ""}
          className="w-full"
        >
          {isPending ? "作成中" : "作成する"}
        </Button>
      </form>
      {isError && errorMessage}
    </div>
  );
}
