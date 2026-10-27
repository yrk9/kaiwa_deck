"use client";
import { useLeaveRoom } from "@/hooks/useRooms";
import { useDrawCard, useResetDrawn, useRoomState } from "@/hooks/useRoomState";
import { useParams, useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { TopicCard, TopicCardBack } from "@/components/TopicCard";

export function DrawRoom() {
  const { id } = useParams<{ id: string }>();
  const { data, isPending, isError, error } = useRoomState(id);
  const {
    mutate: mutateDraw,
    isPending: isDrawPending,
    isError: isDrawError,
  } = useDrawCard(id);
  const {
    mutate: mutateReset,
    isPending: isResetPending,
    isError: isResetError,
  } = useResetDrawn(id);
  const {
    mutate: mutateLeave,
    isPending: isLeavePending,
    isError: isLeaveError,
    isSuccess: isLeaveSuccess,
  } = useLeaveRoom(id);
  const router = useRouter();

  function handleEndButton() {
    mutateLeave(undefined, {
      onSuccess: () => {
        router.push("/decks");
      },
    });
  }

  // stateが読み込み中
  if (isPending) {
    return <div>読み込み中</div>;
  }

  // stateがエラー
  if (isError) {
    if (
      error instanceof ApiError &&
      (error.status === 404 || error.status === 403)
    ) {
      return (
        <div>
          <div>ルームが見つかりません</div>
          <Button onClick={() => router.push("/decks")}>
            デッキ一覧に戻る
          </Button>
        </div>
      );
    } else {
      return (
        <div>
          <div>
            ルームを取得できませんでした。お時間をおいてもう一度お試しください
          </div>
          <Button onClick={() => router.push("/decks")}>
            デッキ一覧に戻る
          </Button>
        </div>
      );
    }
  }
  const latestCard = data.drawn.at(-1);

  return (
    <div className="flex flex-col items-center mx-auto w-full gap-4 max-w-xl">
      <div className="grid w-full grid-cols-[1fr_auto_1fr] items-center">
        <div></div>
        <h1 className="text-xl font-bold">{data.room.room_name}</h1>

        <Button
          onClick={handleEndButton}
          disabled={isLeavePending || isLeaveSuccess}
          variant="outline"
          className="justify-self-end"
          size="sm"
        >
          終わる
        </Button>
      </div>
      {isLeaveError && (
        <div className="text-sm text-destructive">
          ルームを退出できませんでした。時間をおいてもう一度お試しください
        </div>
      )}
      {/* 残り枚数 */}
      <div>残り枚数: {data.remaining_card_count}枚</div>

      {data.remaining_card_count === 0 && (
        <div> 山札がなくなりました。リセットすると、もう一度引けます</div>
      )}

      {/* 引いたお題 */}
      <div className="flex flex-col gap-2">
        {latestCard !== undefined ? (
          <TopicCard
            content={latestCard.content}
            description={latestCard.description}
            showDescription={true}
          />
        ) : (
          <TopicCardBack />
        )}
      </div>

      <div className="flex flex-col gap-2 w-full max-w-2xs">
        <Button
          onClick={() => {
            mutateDraw();
          }}
          disabled={isDrawPending || data.remaining_card_count === 0}
          size="lg"
        >
          引く
        </Button>
        <Button
          onClick={() => {
            mutateReset();
          }}
          disabled={isResetPending || data.drawn.length === 0}
          variant="outline"
          size="sm"
        >
          リセット
        </Button>
      </div>
      {isDrawError && (
        <div className="text-sm text-destructive">
          ドローに失敗しました。時間をおいてもう一度お試しください
        </div>
      )}
      {isResetError && (
        <div className="text-sm text-destructive">
          デッキのリセットに失敗しました。時間をおいてもう一度お試しください
        </div>
      )}

      {/* 引いたお題の一覧 */}
      <h2 className="text-sm font-bold">これまでに引いたお題</h2>
      <ul>
        {data.drawn.map((card) => {
          return (
            <li key={card.card_id} className="py-2 text-base">
              <p>{card.content}</p>
              <p>{card.description && "説明:" + card.description}</p>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
