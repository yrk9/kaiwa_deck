"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Deck, DeckInput, DeckListItem } from "@/types/api";

// デッキのデータを保存しておく名前。作成・削除のあとに、この名前のデータを取り直す
// ["decks"] を取り直すと、一覧 ["decks"] と、詳細 ["decks", id] の両方が最新になる
export const decksQueryKey = ["decks"] as const;

// 自分のデッキ一覧(お題の枚数 card_count つき)
export function useDecks() {
  return useQuery({
    queryKey: decksQueryKey,
    queryFn: () => api<DeckListItem[]>("/deck/"),
  });
}

// デッキ1件(デッキ名など)。お題の一覧は useDeckCards で取る
export function useDeck(deckId: string) {
  return useQuery({
    queryKey: [...decksQueryKey, deckId],
    queryFn: () => api<Deck>(`/deck/${deckId}/`),
  });
}

// デッキを作る。成功すると、一覧が自動で最新になる
export function useCreateDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: DeckInput) =>
      api<Deck>("/deck/", { method: "POST", body: input }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: decksQueryKey }),
  });
}

// デッキを消す。ルームが使っているデッキは、409になる
export function useDeleteDeck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deckId: string) =>
      api<void>(`/deck/${deckId}/`, { method: "DELETE" }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: decksQueryKey }),
  });
}
