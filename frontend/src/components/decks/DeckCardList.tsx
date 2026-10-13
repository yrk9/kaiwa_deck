"use client";
import { useDeckCards, useRemoveCardFromDeck } from "@/hooks/useDeckCards";
import { useDeck } from "@/hooks/useDecks";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ApiError } from "@/lib/api";
import { CardPicker } from "@/components/decks/CardPicker";
import { CardForm } from "@/components/decks/CardForm";
import { useCreateRoom } from "@/hooks/useRooms";
import { TopicCard } from "@/components/TopicCard";

export function DeckCardList() {
  const { id } = useParams<{ id: string }>();
  const {
    mutate: mutateRoom,
    isPending: isRoomPending,
    isError: isRoomError,
  } = useCreateRoom();

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
      <div className="flex flex-row gap-2 pb-4">
        <Button
          onClick={() =>
            mutateRoom(
              { deck_id: id, room_name: "ひとりで引く" },
              { onSuccess: (newRoom) => router.push(`/room/${newRoom.id}`) },
            )
          }
          disabled={isRoomPending || deckCardData.length === 0}
        >
          ひとりで引く
        </Button>
        <Button>お題を追加</Button>

        <Dialog>
          {/* render で渡すと、ボタンの中にボタンが入らない */}
          <DialogTrigger render={<Button />}>お題を作る</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>お題を作る</DialogTitle>
              <DialogDescription>
                作ったお題は、「お題を追加」からデッキに入れられます
              </DialogDescription>
            </DialogHeader>
            <CardForm />
          </DialogContent>
        </Dialog>
      </div>

      {isRoomError &&
        "ルームを作成できませんでした。時間をおいて再度お試しください"}

      {deckCardData.length === 0 ? (
        <div>お題がまだありません。追加してみましょう。</div>
      ) : (
        <ul className="grid grid-cols-2 gap-2">
          {deckCardData.map((card) => {
            return (
              <li key={card.id} className="flex flex-row relative">
                <TopicCard
                  content={card.content}
                  description={card.description}
                  className="w-full"
                />
                <div className="absolute top-0 right-0 z-1">
                  <Button
                    onClick={() => handleDeleteButton(card.id)}
                    disabled={isRemoving}
                    variant="outline"
                    size={"sm"}
                  >
                    外す
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
      {isRemoveError && errorRemoveMessage}
      <h2>お題を追加</h2>
      <CardPicker></CardPicker>
      <Button onClick={() => router.push("/decks")}>デッキ一覧に戻る</Button>
    </div>
  );
}
