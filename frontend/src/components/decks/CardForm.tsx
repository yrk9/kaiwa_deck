"use client";
import { useCreateCard } from "@/hooks/useCards";
import { useAddCardToDeck } from "@/hooks/useDeckCards";
import React, { useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";

export function CardForm() {
  const { id } = useParams<{ id: string }>();
  const [content, setContent] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const { mutate, isPending, isError, isSuccess, error } = useCreateCard();
  const {
    mutate: addToDeck,
    isPending: isAdding,
    isSuccess: isAddSuccess,
    error: addError,
    reset: resetAdd,
  } = useAddCardToDeck(id);
  let errorMessage;
  let addErrorMessage;

  if (error instanceof ApiError && error.status === 409) {
    errorMessage = "作れるお題の上限(200件)に達しました";
  } else if (error instanceof ApiError && error.status === 422) {
    errorMessage = "入力の内容が正しくありません";
  } else {
    errorMessage = "お題を作成できませんでした";
  }

  // お題は作れているので、「お題を追加」から入れ直せる
  if (addError instanceof ApiError && addError.status === 409) {
    addErrorMessage =
      "お題は作成しましたが、デッキの上限のため追加できませんでした";
  } else if (addError) {
    addErrorMessage =
      "お題は作成しましたが、デッキに追加できませんでした。「お題を追加」から追加してください";
  }

  function createCard(addAfterCreate: boolean) {
    resetAdd();
    mutate(
      { content, description: description === "" ? null : description },
      {
        onSuccess: (card) => {
          setContent("");
          setDescription("");
          if (addAfterCreate) addToDeck(card.id);
        },
      },
    );
  }

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    createCard(true);
  }

  const isBusy = isPending || isAdding;

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

        <div className="flex flex-col gap-2">
          <Button
            type="submit"
            disabled={isBusy || content.trim() === ""}
            className="w-full"
          >
            {isBusy ? "作成中" : "作成してデッキに追加"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => createCard(false)}
            disabled={isBusy || content.trim() === ""}
            className="w-full"
          >
            作成だけする
          </Button>
        </div>
      </form>
      {isError && errorMessage}
      {addErrorMessage && (
        <p className="pt-2 text-sm text-red-600">{addErrorMessage}</p>
      )}
      {/* 次のお題を入力し始めたら消す */}
      {isSuccess && !isAdding && !addErrorMessage && content === "" && (
        <p role="status" className="pt-2 text-sm text-muted-foreground">
          {isAddSuccess
            ? "お題を作成し、デッキに追加しました"
            : "お題を作成しました"}
        </p>
      )}
    </div>
  );
}
