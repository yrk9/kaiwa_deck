import { cn } from "@/lib/utils";

// カードの大きさと形。表と裏で同じにする(めくったときにずれないように)
const cardShape = "aspect-[7/5] w-64 rounded-2xl shadow-lg";

// 文字が多いお題でもカードに収まるよう、長さで文字の大きさを変える
function contentSize(content: string) {
  if (content.length <= 30) return "text-sm";
  if (content.length <= 80) return "text-xs";
  return "text-xs";
}

type TopicCardProps = {
  content: string;
  description?: string | null;
  // 大きさなどを、使う側で変えるためのクラス(例: "w-40")
  className?: string;
  showDescription?: boolean;
  // w-40くらいの小さいカード用に、余白と文字を小さくする
  small?: boolean;
};

// お題カードの表
export function TopicCard({
  content,
  description,
  className,
  showDescription = true,
  small = false,
}: TopicCardProps) {
  return (
    <div
      className={cn(
        cardShape,
        "border bg-card p-3 text-card-foreground",
        small && "p-1.5",
        className,
      )}
    >
      <div
        className={cn(
          "flex h-full flex-col gap-2 rounded-xl border-2 border-foreground/80 p-4",
          small && "gap-1 p-2",
        )}
      >
        <p
          className={cn(
            "text-xs tracking-widest text-muted-foreground",
            small && "text-[10px]",
          )}
        >
          お題
        </p>

        {/* 短いときは中央に、収まらないときはスクロールする */}
        <div className="flex min-h-0 flex-1 overflow-y-auto">
          <p
            className={cn(
              "m-auto text-center font-bold break-words",
              small ? "text-xs" : contentSize(content),
            )}
          >
            {content}
          </p>
        </div>

        {showDescription && description && (
          <p className="max-h-20 overflow-y-auto border-t pt-2 text-xs break-words text-muted-foreground">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

// お題カードの裏。山札や、めくる前の面に使う
export function TopicCardBack({
  className,
  small = false,
}: {
  className?: string;
  small?: boolean;
}) {
  return (
    <div
      className={cn(
        cardShape,
        "bg-primary p-3 text-primary-foreground",
        small && "p-1.5",
        className,
      )}
    >
      <div className="flex h-full items-center justify-center rounded-xl border-2 border-primary-foreground/60">
        <span
          className={cn(
            "text-sm font-bold tracking-[0.3em]",
            small && "text-[10px] tracking-[0.2em]",
          )}
        >
          KAIWA DECK
        </span>
      </div>
    </div>
  );
}
