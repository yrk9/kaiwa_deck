// APIのレスポンスと送る内容の形。docs/API設計.md と backend/app/schemas に対応する

// 公式デッキの種類(面接の定番、逆質問、懇親会の話題)。backend/app/schemas/card.py と同じ値
export const cardCategories = [
  "interview",
  "reverse_question",
  "small_talk",
] as const;
export type CardCategory = (typeof cardCategories)[number];

export type Card = {
  id: string;
  // 公式のお題は null
  create_user_id: string | null;
  content: string;
  description: string | null;
  // 公式のお題だけが持つ。自分で作ったお題は null
  category: CardCategory | null;
};

export type CardInput = {
  content: string;
  description?: string | null;
};

export type Deck = {
  id: string;
  create_user_id: string;
  deck_name: string;
  created_at: string;
  updated_at: string;
};

// デッキ一覧の1件。お題の枚数つき
export type DeckListItem = Deck & {
  card_count: number;
};

export type DeckInput = {
  deck_name: string;
  // 指定すると、その種類の公式のお題を入れた状態で作る
  official_category?: CardCategory;
  // true なら、公式のお題を全部入れて作る(古い使い方。official_category と同時には使えない)
  include_official_cards?: boolean;
};

export type DeckCard = {
  deck_id: string;
  card_id: string;
};

export type Room = {
  id: string;
  room_create_user: string;
  deck_id: string;
  room_name: string;
  created_at: string;
};

export type RoomInput = {
  deck_id: string;
  room_name: string;
};

// 参加したときに返ってくる、自分の参加の記録
export type RoomUser = {
  room_id: string;
  user_id: string;
  joined_at: string;
  last_seen_at: string;
};

// 参加者一覧の1件。表示用の user_name つき
export type RoomMember = RoomUser & {
  user_name: string;
};

// 引いたお題
export type DrawnCard = {
  room_id: string;
  card_id: string;
  drawn_at: string;
  content: string;
  description: string | null;
};

// ルーム画面に必要な情報をまとめたもの
export type RoomState = {
  room: Room;
  participants: {
    user_id: string;
    user_name: string;
    joined_at: string;
    last_seen_at: string;
  }[];
  // 山札の中身は来ない。残りの枚数だけ
  remaining_card_count: number;
  // 引いた順
  drawn: {
    card_id: string;
    content: string;
    description: string | null;
    drawn_at: string;
  }[];
};
