"use client";
import { useLeaveRoom } from "@/hooks/useRooms";
import { useDrawCard, useResetDrawn, useRoomState } from "@/hooks/useRoomState";
import { useParams, useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";

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
    <div>
      <h1>{data.room.room_name}</h1>

      {/* 残り枚数 */}
      <div>残り枚数: {data.remaining_card_count}枚</div>

      {data.remaining_card_count === 0 && (
        <div> 山札がなくなりました。リセットすると、もう一度引けます</div>
      )}

      {/* 引いたお題の一覧 */}
      <h2>これまでに引いたお題</h2>
      <ul>
        {data.drawn.map((card) => {
          return (
            <li key={card.card_id}>
              {card.content}
              {card.description && "説明:" + card.description}
            </li>
          );
        })}
      </ul>

      {/* 引いたお題 */}
      <div>
        引いたお題
        {latestCard !== undefined ? (
          <div>
            <div>タイトル: {latestCard.content}</div>
            <div>説明: {latestCard.description && latestCard.description}</div>
          </div>
        ) : (
          <div>まだお題が引かれていません</div>
        )}
      </div>

      <div className="flex flex-row">
        <Button
          onClick={() => {
            mutateDraw();
          }}
          disabled={isDrawPending || data.remaining_card_count === 0}
        >
          引く
        </Button>
        <Button
          onClick={() => {
            mutateReset();
          }}
          disabled={isResetPending || data.drawn.length === 0}
        >
          リセット
        </Button>
        <Button
          onClick={handleEndButton}
          disabled={isLeavePending || isLeaveSuccess}
        >
          終わる
        </Button>
      </div>
      {isDrawError &&
        "ドローに失敗しました。時間をおいてもう一度お試しください"}
      {isResetError &&
        "デッキのリセットに失敗しました。時間をおいてもう一度お試しください"}
      {isLeaveError &&
        "ルームを退出できませんでした。時間をおいてもう一度お試しください"}
    </div>
  );
}
