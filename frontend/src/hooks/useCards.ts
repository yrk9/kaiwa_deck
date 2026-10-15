"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

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
