import { StartButton } from "@/components/StartButton";

export default function Home() {
  return (
    <div className="flex w-full flex-col items-center py-8 gap-12">
      {/* コンセプトの説明 */}
      <div className="flex flex-col gap-4">
        <h1 className="text-4xl">会話の一歩をカードから</h1>
        <p className="text-xl">
          話題をカードに見立てて、アイスブレークをゲーム感覚で楽しめる
        </p>
      </div>

      <div className="flex flex-col">
        <h2 className="text-3xl py-4">遊び方</h2>
        <ol className="list-decimal pl-5">
          <li className="pb-2">
            デッキを作る(公式お題もあってシチュエーションに合わせてすぐに使える)
          </li>
          <li>カードを引く</li>
        </ol>
      </div>

      {/* はじめる */}
      <div className="flex flex-row gap-2">
        <StartButton buttonName="すぐにはじめる"></StartButton>
      </div>
    </div>
  );
}
