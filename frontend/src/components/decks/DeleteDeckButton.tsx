"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useDeleteDeck } from "@/hooks/useDecks";
import { ApiError } from "@/lib/api";

type Props = {
  deckId: string;
  deckName: string;
};

export function DeleteDeckButton({ deckId, deckName }: Props) {
  const [open, setOpen] = useState(false);
  const { mutate, isPending, error, reset } = useDeleteDeck();
  let errorMessage;

  // ひとりで引いたときのルームが残っていると、409になる
  if (error instanceof ApiError && error.status === 409) {
    errorMessage = "このデッキは使用中のため削除できません";
  } else if (error) {
    errorMessage = "削除できませんでした";
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen);
        if (!nextOpen) reset();
      }}
    >
      <DialogTrigger render={<Button variant="outline" size="sm" />}>
        削除
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>本当に削除しますか?</DialogTitle>
          <DialogDescription>
            「{deckName}」を削除します。元に戻せません
          </DialogDescription>
        </DialogHeader>
        {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
        <DialogFooter>
          <DialogClose
            render={<Button variant="outline" />}
            disabled={isPending}
          >
            やめる
          </DialogClose>
          <Button
            variant="destructive"
            disabled={isPending}
            onClick={() =>
              mutate(deckId, { onSuccess: () => setOpen(false) })
            }
          >
            削除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
