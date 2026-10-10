"use client";

// 一時的な動作確認用のページ。確認が終わったら削除する(コミットしない)
import { useAuth } from "@/hooks/useAuth";
import { useCreateDeck, useDecks, useDeleteDeck } from "@/hooks/useDecks";

export default function HooksCheck() {
  const auth = useAuth();
  const decks = useDecks();
  const create = useCreateDeck();
  const remove = useDeleteDeck();

  const error =
    decks.error?.message ?? create.error?.message ?? remove.error?.message;

  return (
    <main style={{ padding: 16 }}>
      <p id="auth">
        {auth.status} {auth.status === "ready" ? auth.userId : ""}
      </p>
      <p id="list-status">{decks.status}</p>
      <pre id="list">
        {JSON.stringify(
          decks.data?.map((d) => ({ name: d.deck_name, n: d.card_count })),
        )}
      </pre>
      <p id="error">{error ?? ""}</p>
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
      <button id="create-bad" onClick={() => create.mutate({ deck_name: "" })}>
        create bad
      </button>
      <button
        id="delete-first"
        onClick={() => {
          const first = decks.data?.[0];
          if (first) remove.mutate(first.id);
        }}
      >
        delete first
      </button>
    </main>
  );
}
