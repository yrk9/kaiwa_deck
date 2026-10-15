"use client";

import { useCards } from "@/hooks/useCards";
import { useAddCardToDeck, useDeckCards } from "@/hooks/useDeckCards";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

export function CardPicker() {
  const { id } = useParams<{ id: string }>();
  const {
    data: cardData,
    isPending: isCardPending,
    isError: isCardError,
  } = useCards();
  const {
    mutate,
    isPending: isAddCardPending,
    isError: isAddCardError,
    error: addCardError,
  } = useAddCardToDeck(id);
  const {
    data: deckCardData,
    isPending: isDeckCardPending,
    isError: isDeckCardError,
  } = useDeckCards(id);
  let errorAddMessage;

  function handleAddButton(cardId: string) {
    mutate(cardId);
  }

  //処理中
  if (isCardPending || isDeckCardPending) {
    return <div>読み込み中</div>;
  }

  //お題一覧取得に関するエラー処理
  if (isCardError) {
    return (
      <div className="text-red-600">
        お題の取得に失敗しました。時間をおいて再度お試しください
      </div>
    );
  }

  // デッキ内のお題の取得に関するエラー処理
  if (isDeckCardError) {
    return (
      <div className="text-red-600">
        お題の取得に失敗しました。時間をおいて再度お試しください
      </div>
    );
  }

  // お題追加に関するのエラー処理
  if (addCardError instanceof ApiError && addCardError.status === 404) {
    errorAddMessage = "お題が見つかりません";
  } else if (addCardError instanceof ApiError && addCardError.status === 403) {
    errorAddMessage = "他人のお題のため追加できませんでした";
  } else if (addCardError instanceof ApiError && addCardError.status === 409) {
    errorAddMessage = "お題が既に入っているかお題の枚数がデッキの上限です";
  } else {
    errorAddMessage = "お題を追加できませんでした";
  }

  // すでにデッキにあるお題を除外
  const addableCards = cardData.filter(
    (card) => !deckCardData.some((deckCard) => deckCard.id === card.id),
  );

  return (
    <div>
      {addableCards.length === 0 ? (
        <div>追加できるお題がありません。</div>
      ) : (
        <ul>
          {addableCards.map((card) => {
            return (
              <li key={card.id}>
                {card.content}
                {card.description && "説明:" + card.description}
                <Button
                  onClick={() => handleAddButton(card.id)}
                  disabled={isAddCardPending}
                >
                  お題をデッキに追加
                </Button>
              </li>
            );
          })}
        </ul>
      )}
      {isAddCardError && errorAddMessage}
    </div>
  );
}
