"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { roomGcTime, roomQueryKey } from "@/hooks/useRooms";
import { api } from "@/lib/api";
import type { DrawnCard, RoomState } from "@/types/api";

const roomStateQueryKey = (roomId: string) =>
  [...roomQueryKey(roomId), "state"] as const;

// ルーム画面に必要な情報(ルーム・参加者・残り枚数・引いたお題)を、1回で取る
// 403: 参加していない(「参加する」を出す) / 404: ルームが無い(解散した)
export function useRoomState(roomId: string) {
  return useQuery({
    queryKey: roomStateQueryKey(roomId),
    queryFn: () => api<RoomState>(`/room/${roomId}/state/`),
    gcTime: roomGcTime,
  });
}

// お題を1枚引く。mutate() で呼ぶ。引いたお題は onSuccess の引数で受け取れる
// 409: 山札が空
export function useDrawCard(roomId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api<DrawnCard>(`/room/${roomId}/drawn/`, { method: "POST" }),
    onSuccess: () => {
      // めくる演出をすぐ始められるよう、取り直しの完了は待たない
      void queryClient.invalidateQueries({
        queryKey: roomStateQueryKey(roomId),
      });
    },
  });
}

// 山札をリセットする(引いた記録を消す)。mutate() で呼ぶ
export function useResetDrawn(roomId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api<void>(`/room/${roomId}/drawn/`, { method: "DELETE" }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: roomStateQueryKey(roomId) }),
  });
}
