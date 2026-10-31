import { StartButton } from "@/components/StartButton";
import { HeroCards } from "@/components/HeroCards";

export default function Home() {
  return (
    <div className="flex w-full flex-col items-center py-8 gap-12">
      {/* コンセプトの説明 */}
      <div className="flex flex-col gap-4">
        <h1 className="text-4xl">1枚引いて練習しよう</h1>
        <p className="text-xl">
          面接の質問をランダムに1枚引いて、声に出して答えてみましょう
        </p>
      </div>
      <HeroCards />
      <div className="flex flex-col">
        <h2 className="text-3xl py-4">使い方</h2>
        <ol className="list-decimal pl-5">
          <li className="pb-2">
            デッキを選ぶ：面接の定番・逆質問・懇親会の話題から選ぶ
          </li>
          <li className="pb-2">1枚引く</li>
          <li>声に出して答える</li>
        </ol>
      </div>

      {/* はじめる */}
      <div className="flex flex-row gap-2">
        <StartButton buttonName="すぐにはじめる"></StartButton>
      </div>
    </div>
  );
}
