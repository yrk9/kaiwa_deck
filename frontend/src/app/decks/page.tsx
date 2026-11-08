"use client";
import { useState } from "react";
import { DeckList } from "@/components/decks/DeckList";
import { DeckForm } from "@/components/decks/DeckForm";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function DeckPage() {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="flex flex-col gap-4 max-w-xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">デッキリスト</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? "完了" : "編集"}
          </Button>
          <Dialog>
            <DialogTrigger render={<Button />}>デッキを追加</DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>デッキを作る</DialogTitle>
              </DialogHeader>
              <DeckForm></DeckForm>
            </DialogContent>
          </Dialog>
        </div>
      </div>
      <DeckList isEditing={isEditing}></DeckList>
    </div>
  );
}
