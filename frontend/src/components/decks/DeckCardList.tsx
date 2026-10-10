"use client";
import { useDeckCards, useRemoveCardFromDeck } from "@/hooks/useDeckCards";
import { useDeck } from "@/hooks/useDecks";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";

export function DeckCardList() {
  const { id } = useParams<{ id: string }>();
  const {
    data: deckCardData,
    isPending: isDeckCardPending,
    isError: isDeckCardError,
  } = useDeckCards(id);
  const {
    data: deckData,
    isPending: isDeckPending,
    isError: isDeckError,
    error: deckError,
  } = useDeck(id);
  const {
    mutate,
    isPending: isRemoving,
    isError: isRemoveError,
    error: removeError,
  } = useRemoveCardFromDeck(id);
  const router = useRouter();
  let errorRemoveMessage;

  function handleDeleteButton(cardId: string) {
    mutate(cardId);
  }

  // 処理中
  if (isDeckCardPending || isDeckPending) {
    return <div>読み込み中</div>;
  }

  // デッキ取得に関するエラー処理
  if (isDeckError) {
    if (
      deckError instanceof ApiError &&
      (deckError.status === 404 || deckError.status === 403)
    ) {
      return (
        <div>
          <div>デッキが見つかりません </div>
          <Button onClick={() => router.push("/decks")}>
            デッキ一覧に戻る
          </Button>
        </div>
      );
    } else {
      return (
        <div>
          <div>
            デッキの取得に失敗しました。時間をおいて再度お試しください。
          </div>
          <Button onClick={() => router.push("/decks")}>
            デッキ一覧に戻る
          </Button>
        </div>
      );
    }
  }

  // カードの取得に関するエラー処理
  if (isDeckCardError) {
    return (
      <div className="text-red-600">
        お題の取得に失敗しました。時間をおいて再度お試しください
      </div>
    );
  }

  // お題削除に関するのエラー処理
  if (removeError instanceof ApiError && removeError.status === 404) {
    errorRemoveMessage = "お題が見つかりません";
  } else if (removeError instanceof ApiError && removeError.status === 403) {
    errorRemoveMessage = "お題を外す権限がありません";
  } else {
    errorRemoveMessage = "お題を外せませんでした";
  }

  return (
    <div>
      <h1 className="text-4xl py-2">{deckData.deck_name}</h1>
      {deckCardData.length === 0 ? (
        <div>お題がまだありません。追加してみましょう。</div>
      ) : (
        <ul>
          {deckCardData.map((card) => {
            return (
              <li key={card.id}>
                {card.content}
                {card.description && "説明:" + card.description}
                <Button
                  onClick={() => handleDeleteButton(card.id)}
                  disabled={isRemoving}
                >
                  お題を外す
                </Button>
              </li>
            );
          })}
        </ul>
      )}
      {isRemoveError && errorRemoveMessage}
      <Button onClick={() => router.push("/decks")}>デッキ一覧に戻る</Button>
    </div>
  );
}
