import { StartButton } from "@/components/StartButton";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-6 sm:px-16 bg-white dark:bg-black sm:items-start">
        {/* コンセプトの説明 */}
        <div className="flex flex-col gap-4">
          <h1 className="text-4xl">会話の一歩をカードから</h1>
          <p className="text-xl">
            話題をカードに見立てて、アイスブレークをゲーム感覚で楽しめる
          </p>
        </div>

        <div className="flex flex-col">
          <h2 className="text-3xl py-4">遊び方</h2>

          <ol>
            <li>
              デッキを作る(公式お題もあってシチュエーションに合わせてすぐに使える)
            </li>
            <li>カードを引く(ひとりでも、ルームで複数人でも)</li>
          </ol>
        </div>

        {/* はじめる */}
        <div className="flex flex-row gap-2">
          <StartButton buttonName="すぐにはじめる"></StartButton>
        </div>
      </main>
    </div>
  );
}
