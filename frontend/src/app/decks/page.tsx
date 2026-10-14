import { DeckList } from "@/components/decks/DeckList";
import { DeckForm } from "@/components/decks/DeckForm";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export default function DeckPage() {
  return (
    <div className="flex flex-col gap-4 max-w-xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">デッキリスト</h1>
        <Dialog>
          <DialogTrigger render={<Button />}>デッキを追加</DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>デッキを作る</DialogTitle>
            </DialogHeader>
            <DeckForm></DeckForm>
          </DialogContent>
        </Dialog>
      </div>
      <DeckList></DeckList>
    </div>
  );
}
