import { DeckList } from "@/components/decks/DeckList";
import { DeckForm } from "@/components/decks/DeckForm";

export default function DeckPage() {
  return (
    <div>
      <h1>デッキリスト</h1>
      <DeckList></DeckList>
      <DeckForm></DeckForm>
    </div>
  );
}
