"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { allDeckCardsQueryKey } from "@/hooks/useDeckCards";
import { allRoomsQueryKey } from "@/hooks/useRooms";
import { api } from "@/lib/api";
import type { CardNote } from "@/types/api";

// メモはデッキのお題一覧とルームの state に入っている。同じお題が複数のデッキに
// 入りうるので、デッキやルームを絞らずに両方を取り直す
function useRefreshNotes() {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: allDeckCardsQueryKey }),
      queryClient.invalidateQueries({ queryKey: allRoomsQueryKey }),
    ]);
}

// 想定回答のメモを保存する(無ければ作り、あれば上書き)。mutate({ cardId, note }) で呼ぶ
// 404: お題が無い / 422: 空のメモ、または2000文字を超える
export function useSaveCardNote() {
  const refresh = useRefreshNotes();
  return useMutation({
    mutationFn: ({ cardId, note }: { cardId: string; note: string }) =>
      api<CardNote>(`/card/${cardId}/note/`, {
        method: "PUT",
        body: { note },
      }),
    onSuccess: refresh,
  });
}

// メモを消す。mutate(cardId) で呼ぶ
// 404: メモが無い
export function useDeleteCardNote() {
  const refresh = useRefreshNotes();
  return useMutation({
    mutationFn: (cardId: string) =>
      api<void>(`/card/${cardId}/note/`, { method: "DELETE" }),
    onSuccess: refresh,
  });
}
