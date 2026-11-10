"use client";
import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateCard } from "@/hooks/useCards";
import { ApiError } from "@/lib/api";
import type { DeckCardItem } from "@/types/api";

type Props = {
  card: DeckCardItem;
  // 保存できたとき、または「やめる」を押したときに呼ぶ
  onDone: () => void;
  onDirtyChange?: (isDirty: boolean) => void;
};

export function CardEditForm({ card, onDone, onDirtyChange }: Props) {
  const [content, setContent] = useState(card.content);
  const [description, setDescription] = useState(card.description ?? "");
  const { mutate, isPending, error, reset } = useUpdateCard();
  // 保存するときに前後の空白が消えるので、空白を除いて比べる
  const isDirty =
    content.trim() !== card.content ||
    description.trim() !== (card.description ?? "");
  // このデッキの分を除いた数
  const otherDeckCount = card.deck_count - 1;
  let errorMessage;

  if (error instanceof ApiError && error.status === 403) {
    errorMessage = "このお題は編集できません";
  } else if (error instanceof ApiError && error.status === 422) {
    errorMessage = "入力の内容が正しくありません";
  } else if (error) {
    errorMessage = "保存できませんでした";
  }

  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    if (
      otherDeckCount > 0 &&
      !window.confirm(
        `ほかの${otherDeckCount}つのデッキでも内容が変わります。保存しますか?`,
      )
    ) {
      return;
    }
    mutate(
      {
        cardId: card.id,
        input: {
          content,
          description: description.trim() === "" ? null : description,
        },
      },
      { onSuccess: onDone },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Label className="items-start">
        <span className="w-18 shrink-0 pt-2">内容</span>
        <Textarea
          name="content"
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            reset();
          }}
          maxLength={200}
          className="flex-1"
        />
      </Label>
      <Label className="items-start">
        <span className="w-18 shrink-0 pt-2">説明(任意)</span>
        <Textarea
          name="description"
          value={description}
          onChange={(e) => {
            setDescription(e.target.value);
            reset();
          }}
          maxLength={500}
          className="max-h-40 flex-1"
        />
      </Label>
      {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
      <div className="flex gap-2">
        <Button
          type="submit"
          disabled={isPending || !isDirty || content.trim() === ""}
        >
          {isPending ? "保存中" : "保存"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onDone}
          disabled={isPending}
        >
          やめる
        </Button>
      </div>
    </form>
  );
}
