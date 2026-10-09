// APIのレスポンスと送る内容の形。docs/API設計.md と backend/app/schemas に対応する

export type Card = {
  id: string;
  // 公式のお題は null
  create_user_id: string | null;
  content: string;
  description: string | null;
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
  // true なら、公式のお題を全部入れた状態で作る
  include_official_cards?: boolean;
};

export type DeckCard = {
  deck_id: string;
  card_id: string;
};
