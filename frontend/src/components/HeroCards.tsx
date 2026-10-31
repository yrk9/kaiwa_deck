import { TopicCard, TopicCardBack } from "@/components/TopicCard";

// LPの一番上に置く、山札と引いた1枚の絵
export function HeroCards() {
  return (
    <div className="flex items-center justify-center py-4">
      {/* 山札。中身をabsoluteで重ねるので、親に大きさを持たせる */}
      <div className="relative aspect-[7/5] w-40 shrink-0">
        <TopicCardBack
          small
          className="absolute top-3 left-3 w-40 opacity-60"
        />
        <TopicCardBack
          small
          className="absolute top-1.5 left-1.5 w-40 opacity-80"
        />
        <TopicCardBack small className="absolute top-0 left-0 w-40 -rotate-3" />
      </div>

      {/* 引いた1枚。山札に少し重ねて、手前に出す */}
      <TopicCard
        content="学生時代に力を入れたことは？"
        showDescription={false}
        small
        className="relative z-10 -ml-6 mt-8 w-40 shrink-0 rotate-6"
      />
    </div>
  );
}
