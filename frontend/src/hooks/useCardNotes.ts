"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { roomStateQueryKey } from "@/hooks/useRoomState";
import { api } from "@/lib/api";
import type { CardNote } from "@/types/api";

// メモは state の引いたお題に入っているので、保存・削除のあとは state を取り直す
function useRefreshRoomState(roomId: string) {
  const queryClient = useQueryClient();
  return () =>
    queryClient.invalidateQueries({ queryKey: roomStateQueryKey(roomId) });
}

// 想定回答のメモを保存する(無ければ作り、あれば上書き)。mutate({ cardId, note }) で呼ぶ
// 404: お題が無い / 422: 空のメモ、または2000文字を超える
export function useSaveCardNote(roomId: string) {
  const refresh = useRefreshRoomState(roomId);
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
export function useDeleteCardNote(roomId: string) {
  const refresh = useRefreshRoomState(roomId);
  return useMutation({
    mutationFn: (cardId: string) =>
      api<void>(`/card/${cardId}/note/`, { method: "DELETE" }),
    onSuccess: refresh,
  });
}
