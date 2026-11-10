"use client";
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { TopicCard } from "@/components/TopicCard";
import { CardNoteForm } from "@/components/decks/CardNoteForm";
import type { DeckCardItem } from "@/types/api";

type Props = {
  card: DeckCardItem;
};

export function CardNoteDialog({ card }: Props) {
  const [isDirty, setIsDirty] = useState(false);

  return (
    <Dialog
      onOpenChange={(open, eventDetails) => {
        if (open || !isDirty) return;
        if (!window.confirm("保存していない変更があります。閉じますか?")) {
          eventDetails.cancel();
          return;
        }
        // 閉じるとフォームが消えるので、ここで戻しておく
        setIsDirty(false);
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
        <DialogHeader>
          <DialogTitle className="pr-8 leading-snug">{card.content}</DialogTitle>
          <DialogDescription>
            {card.description ?? "このお題には補足がありません"}
          </DialogDescription>
        </DialogHeader>
        <CardNoteForm
          id={card.id}
          initialNote={card.note}
          onDirtyChange={setIsDirty}
        />
      </DialogContent>
    </Dialog>
  );
}
