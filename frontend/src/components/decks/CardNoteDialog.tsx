"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { TopicCard } from "@/components/TopicCard";
import { CardEditForm } from "@/components/decks/CardEditForm";
import { CardNoteForm } from "@/components/decks/CardNoteForm";
import type { DeckCardItem } from "@/types/api";

type Props = {
  card: DeckCardItem;
};

export function CardNoteDialog({ card }: Props) {
  const [isNoteDirty, setIsNoteDirty] = useState(false);
  const [isCardDirty, setIsCardDirty] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  // デッキに入れられるのは公式か自分のお題だけなので、作成者がいれば自分のお題
  const isOwnCard = card.create_user_id !== null;

  function finishEditing() {
    // 編集欄が消えるので、ここで戻しておく
    setIsCardDirty(false);
    setIsEditing(false);
  }

  return (
    <Dialog
      onOpenChange={(open, eventDetails) => {
        if (open) return;
        if (
          (isNoteDirty || isCardDirty) &&
          !window.confirm("保存していない変更があります。閉じますか?")
        ) {
          eventDetails.cancel();
          return;
        }
        // 閉じるとフォームが消えるので、ここで戻しておく
        setIsNoteDirty(false);
        finishEditing();
      }}
    >
      <DialogTrigger
        render={
          <button type="button" className="w-full text-left cursor-pointer" />
        }
      >
        <TopicCard
          content={card.content}
          className="w-full"
          showDescription={false}
        />
      </DialogTrigger>
      <DialogContent>
        {isEditing ? (
          <>
            <DialogHeader>
              <DialogTitle>お題を編集</DialogTitle>
            </DialogHeader>
            <CardEditForm
              card={card}
              onDone={finishEditing}
              onDirtyChange={setIsCardDirty}
            />
          </>
        ) : (
          <DialogHeader>
            <DialogTitle className="pr-8 leading-snug">
              {card.content}
            </DialogTitle>
            <DialogDescription>
              {card.description ?? "このお題には補足がありません"}
            </DialogDescription>
            {isOwnCard && (
              <Button
                variant="outline"
                size="sm"
                className="self-start"
                onClick={() => setIsEditing(true)}
              >
                お題を編集
              </Button>
            )}
          </DialogHeader>
        )}
        <CardNoteForm
          id={card.id}
          initialNote={card.note}
          onDirtyChange={setIsNoteDirty}
        />
      </DialogContent>
    </Dialog>
  );
}
