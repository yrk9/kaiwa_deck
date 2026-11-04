"use client";
import { Textarea } from "@/components/ui/textarea";
import { useDeleteCardNote, useSaveCardNote } from "@/hooks/useCardNotes";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

type Props = {
  id: string;
  initialNote: string | null;
};

export function CardNoteForm({ id, initialNote }: Props) {
  const [text, setText] = useState(initialNote ?? "");
  const {
    mutate: saveNote,
    isPending: isSaving,
    reset,
    error: saveError,
    isSuccess: isSaveSuccess,
  } = useSaveCardNote();
  const {
    mutate: deleteNote,
    isPending: isDeleting,
    reset: resetDelete,
    error: deleteError,
  } = useDeleteCardNote();
  let errorMessage;

  if (saveError instanceof ApiError && saveError.status === 422) {
    errorMessage = "2000文字以内で書いてください";
  } else if (saveError) {
    errorMessage = "保存できませんでした";
  } else if (deleteError) {
    errorMessage = "削除できませんでした";
  }

  return (
    <div className="flex flex-col gap-2">
      <label>想定回答</label>
      <Textarea
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          reset();
        }}
        className="max-h-60"
      ></Textarea>
      {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
      {isSaveSuccess && <p className="text-sm">保存しました</p>}
      <div className="flex gap-2">
        <Button
          disabled={isSaving || text.trim() === ""}
          onClick={() => saveNote({ cardId: id, note: text })}
        >
          保存
        </Button>
        {initialNote && (
          <Button
            onClick={() => {
              deleteNote(id, {
                onSuccess: () => {
                  setText("");
                  reset();
                  resetDelete();
                },
              });
            }}
            disabled={isDeleting}
          >
            削除
          </Button>
        )}
      </div>
    </div>
  );
}
