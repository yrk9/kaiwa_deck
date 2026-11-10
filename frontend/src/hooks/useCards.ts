"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { allDeckCardsQueryKey } from "@/hooks/useDeckCards";
import { allRoomsQueryKey } from "@/hooks/useRooms";
import { api } from "@/lib/api";
import type { Card, CardInput } from "@/types/api";

// お題の一覧を保存しておく名前
const cardsQueryKey = ["cards"] as const;

// 公式のお題と、自分のお題の一覧(他人のお題は出ない)。デッキにお題を追加するときの選択肢に使う
export function useCards() {
  return useQuery({
    queryKey: cardsQueryKey,
    queryFn: () => api<Card[]>("/card/"),
  });
}

// 自分のお題を作る。成功すると、一覧が自動で最新になる
// 作ったお題をそのままデッキに入れるには、mutateAsync の結果の id を useAddCardToDeck に渡す
// 409: 作れるお題の上限(200件)に達した / 422: 文字数オーバー(内容200字、補足500字)
export function useCreateCard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CardInput) =>
      api<Card>("/card/", { method: "POST", body: input }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: cardsQueryKey }),
  });
}

// 自分のお題の内容を書き換える。mutate({ cardId, input }) で呼ぶ
// description を省くと、補足は消える(上書きなので、残すなら今の値を渡す)
// 403: 公式のお題、または他人のお題 / 404: お題が無い / 422: 文字数オーバー
export function useUpdateCard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ cardId, input }: { cardId: string; input: CardInput }) =>
      api<Card>(`/card/${cardId}/`, { method: "PUT", body: input }),
    // お題の内容は、お題一覧・デッキのお題一覧・ルームの state に入っている
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: cardsQueryKey }),
        queryClient.invalidateQueries({ queryKey: allDeckCardsQueryKey }),
        queryClient.invalidateQueries({ queryKey: allRoomsQueryKey }),
      ]),
  });
}
