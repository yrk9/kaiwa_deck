"use client";
import { useCreateCard } from "@/hooks/useCards";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";

export function CardForm() {
  const [content, setContent] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const { mutate, isPending, isError, isSuccess, error } = useCreateCard();
  let errorMessage;

  if (error instanceof ApiError && error.status === 409) {
    errorMessage = "作れるお題の上限(200件)に達しました";
  } else if (error instanceof ApiError && error.status === 422) {
    errorMessage = "入力の内容が正しくありません";
  } else {
    errorMessage = "お題を作成できませんでした";
  }

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    mutate(
      { content, description: description === "" ? null : description },
      {
        onSuccess: () => {
          setContent("");
          setDescription("");
        },
      },
    );
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Label>
          <span className="w-18 shrink-0">内容</span>
          <Input
            name="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            maxLength={200}
            placeholder="最近ハマってることは?"
            className="flex-1"
          />
        </Label>
        {/* 入力欄が複数行なので、文字は上に揃える */}
        <Label className="items-start">
          <span className="w-18 shrink-0 pt-2">説明(任意)</span>
          <Textarea
            name="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={500}
            placeholder="補足事項"
            className="max-h-40 flex-1"
          />
        </Label>

        <Button
          type="submit"
          disabled={isPending || content.trim() === ""}
          className="w-full"
        >
          {isPending ? "作成中" : "作成する"}
        </Button>
      </form>
      {isError && errorMessage}
      {/* 次のお題を入力し始めたら消す */}
      {isSuccess && content === "" && (
        <p role="status" className="pt-2 text-sm text-muted-foreground">
          お題を作成しました
        </p>
      )}
    </div>
  );
}
