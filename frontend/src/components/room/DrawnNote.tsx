"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";

type Props = {
  note: string | null;
};

// 引いたお題の想定回答。答える前に目に入らないよう、押すまで閉じておく
export function DrawnNote({ note }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  if (!note) {
    return (
      <p className="text-sm text-muted-foreground">
        想定回答は、デッキの編集画面でお題を開くと書けます
      </p>
    );
  }

  return (
    <div className="flex w-full max-w-md flex-col items-center gap-2">
      <Button variant="outline" size="sm" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? "想定回答を閉じる" : "想定回答を見る"}
      </Button>
      {isOpen && (
        <p className="max-h-60 w-full overflow-y-auto rounded-lg border bg-card p-3 text-sm break-words whitespace-pre-wrap">
          {note}
        </p>
      )}
    </div>
  );
}
