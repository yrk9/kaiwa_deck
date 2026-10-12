"use client";
import { useCreateCard } from "@/hooks/useCards";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

export function CardForm() {
  const [content, setContent] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const { mutate, isPending, isError, error } = useCreateCard();
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
      <form onSubmit={handleSubmit} className="flex flex-col">
        <label>
          お題の内容
          <input
            name="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            maxLength={200}
            className="border border-gray-600"
          ></input>
        </label>
        <label>
          説明
          <input
            name="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={500}
            className="border border-gray-600"
          ></input>
        </label>

        <Button
          type="submit"
          disabled={isPending || content.trim() === ""}
          className="mx-auto"
        >
          {isPending ? "作成中" : "作成する"}
        </Button>
      </form>
      {isError && errorMessage}
    </div>
  );
}
