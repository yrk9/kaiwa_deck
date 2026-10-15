"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { decksQueryKey } from "@/hooks/useDecks";
import { api } from "@/lib/api";
import type { Card, DeckCard } from "@/types/api";

// デッキ内のお題を保存しておく名前(デッキごとに別)
const deckCardsQueryKey = (deckId: string | undefined) =>
  ["deck-cards", deckId] as const;

// デッキの中のお題の一覧。deckId が undefined の間は、取得しない
export function useDeckCards(deckId: string | undefined) {
  return useQuery({
    queryKey: deckCardsQueryKey(deckId),
    queryFn: () => api<Card[]>(`/deck/${deckId}/cards/`),
    enabled: Boolean(deckId),
  });
}

// 追加・削除のあとに、デッキ内の一覧と、デッキ一覧の card_count を最新にする
function useRefreshAfterChange(deckId: string) {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: deckCardsQueryKey(deckId) }),
      queryClient.invalidateQueries({ queryKey: decksQueryKey }),
    ]);
}

// お題をデッキに追加する。mutate(cardId) で呼ぶ
// 403: 他人のお題 / 404: お題が無い / 409: すでに入っている、またはデッキがいっぱい
export function useAddCardToDeck(deckId: string) {
  const refresh = useRefreshAfterChange(deckId);
  return useMutation({
    mutationFn: (cardId: string) =>
      api<DeckCard>(`/deck/${deckId}/cards/`, {
        method: "POST",
        body: { card_id: cardId },
      }),
    onSuccess: refresh,
  });
}

// お題をデッキから外す(お題そのものは消えない)。mutate(cardId) で呼ぶ
export function useRemoveCardFromDeck(deckId: string) {
  const refresh = useRefreshAfterChange(deckId);
  return useMutation({
    mutationFn: (cardId: string) =>
      api<void>(`/deck/${deckId}/cards/${cardId}/`, { method: "DELETE" }),
    onSuccess: refresh,
  });
}
