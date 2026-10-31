-- お題ごとに、自分の想定回答をメモできるようにする。
-- メモは「お題 × ユーザー」で1つ。同じお題をまた引いたら、前のメモを見直せる。
-- room_drawn_cards には入れない(あのテーブルは「誰が引いたか」を持たないため)

create table public.card_notes (
    user_id uuid not null references public.users(id) on delete cascade,
    card_id uuid not null references public.cards(id) on delete cascade,
    note text not null,
    updated_at timestamptz not null default now(),
    primary key (user_id, card_id)
);

-- 0001と同じく、フロントのanon keyから直接読み書きできないようにする
alter table public.card_notes enable row level security;
