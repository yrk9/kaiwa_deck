"use client";

// 一時的な動作確認用のページ。確認が終わったら削除する
import { useAuth } from "@/hooks/useAuth";
import {
  useAddCardToDeck,
  useDeckCards,
  useRemoveCardFromDeck,
} from "@/hooks/useDeckCards";
import { useCreateDeck, useDecks, useDeleteDeck } from "@/hooks/useDecks";
import { ApiError } from "@/lib/api";

function describe(error: Error | null | undefined) {
  if (!error) return "";
  return error instanceof ApiError
    ? `${error.status}: ${error.message}`
    : error.message;
}

export default function HooksCheck() {
  const auth = useAuth();
  const decks = useDecks();
  const create = useCreateDeck();
  const remove = useDeleteDeck();

  const official = decks.data?.find((d) => d.deck_name === "official");
  const empty = decks.data?.find((d) => d.deck_name === "empty");
  const officialCards = useDeckCards(official?.id);
  const emptyCards = useDeckCards(empty?.id);
  const add = useAddCardToDeck(empty?.id ?? "");
  const removeCard = useRemoveCardFromDeck(empty?.id ?? "");

  const firstOfficialCard = officialCards.data?.[0];

  return (
    <main style={{ padding: 16 }}>
      <p id="auth">
        {auth.status} {auth.status === "ready" ? auth.userId : ""}
      </p>
      <pre id="list">
        {JSON.stringify(
          decks.data?.map((d) => ({ name: d.deck_name, n: d.card_count })),
        )}
      </pre>
      <p id="empty-cards">{emptyCards.data?.length ?? "none"}</p>
      <p id="official-cards">{officialCards.data?.length ?? "none"}</p>
      <p id="deck-error">
        {describe(create.error) || describe(remove.error)}
      </p>
      <p id="add-error">{describe(add.error)}</p>
      <p id="remove-error">{describe(removeCard.error)}</p>

      <button
        id="create-official"
        onClick={() =>
          create.mutate({ deck_name: "official", include_official_cards: true })
        }
      >
        create official
      </button>
      <button
        id="create-empty"
        onClick={() => create.mutate({ deck_name: "empty" })}
      >
        create empty
      </button>
      <button
        id="add-first"
        onClick={() => {
          if (firstOfficialCard) add.mutate(firstOfficialCard.id);
        }}
      >
        add first official card to empty
      </button>
      <button
        id="remove-first"
        onClick={() => {
          if (firstOfficialCard) removeCard.mutate(firstOfficialCard.id);
        }}
      >
        remove it from empty
      </button>
      <button
        id="delete-empty"
        onClick={() => {
          if (empty) remove.mutate(empty.id);
        }}
      >
        delete empty deck
      </button>
    </main>
  );
}
