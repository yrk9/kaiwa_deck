"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { ensureSession } from "@/lib/auth";
import type { Room, RoomInput, RoomMember, RoomUser } from "@/types/api";

// ルームのデータを保存しておく名前(ルームごとに別)
// ["rooms", id] を取り直すと、ルーム・参加者・state のすべてが最新になる
export const roomQueryKey = (roomId: string) => ["rooms", roomId] as const;

// ルームは他の人の操作でも変わるので、画面を離れたら保存したデータを捨てる
export const roomGcTime = 0;

// ルーム1件(ルーム名など)。参加していなくても見られる
// 404: ルームが無い(解散した)
export function useRoom(roomId: string) {
  return useQuery({
    queryKey: roomQueryKey(roomId),
    queryFn: () => api<Room>(`/room/${roomId}/`),
    gcTime: roomGcTime,
  });
}

// 参加者の一覧(参加した順)。参加していなくても見られる
export function useRoomMembers(roomId: string) {
  return useQuery({
    queryKey: [...roomQueryKey(roomId), "members"],
    queryFn: () => api<RoomMember[]>(`/room/${roomId}/user/`),
    gcTime: roomGcTime,
  });
}

// ルームを作る。作った人は、最初から参加者になっている
// 上限(4件)のときは、自分のいちばん古いルームが消える
// 403: 自分のデッキではない / 404: デッキが無い
export function useCreateRoom() {
  return useMutation({
    mutationFn: (input: RoomInput) =>
      api<Room>("/room/", { method: "POST", body: input }),
  });
}

// ルーム名とデッキを変える(作成者だけ)。デッキを変えると、引いた記録は消える
// 403: 作成者ではない、または参加者のデッキではない
export function useUpdateRoom(roomId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RoomInput) =>
      api<Room>(`/room/${roomId}/`, { method: "PUT", body: input }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: roomQueryKey(roomId) }),
  });
}

// ルームに参加する。mutate() で呼ぶ。成功すると、state が取れるようになる
// 404: ルームが無い / 409: 満員
export function useJoinRoom(roomId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api<RoomUser>(`/room/${roomId}/user/`, { method: "POST" }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: roomQueryKey(roomId) }),
  });
}

// ルームから退出する。mutate() で呼ぶ。作成者が退出すると、ルームは解散する
// 成功したら、画面側で /decks へ移動する
export function useLeaveRoom(roomId: string) {
  return useMutation({
    mutationFn: async () => {
      // 自分のidは、画面から受け取らずにログイン情報から取る
      const { user } = await ensureSession();
      return api<void>(`/room/${roomId}/user/${user.id}/`, {
        method: "DELETE",
      });
    },
  });
}

// ルームを解散する(作成者だけ)。mutate() で呼ぶ
// 成功したら、画面側で /decks へ移動する
export function useDeleteRoom(roomId: string) {
  return useMutation({
    mutationFn: () => api<void>(`/room/${roomId}/`, { method: "DELETE" }),
  });
}
