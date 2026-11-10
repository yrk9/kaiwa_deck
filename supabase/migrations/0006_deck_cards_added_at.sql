-- デッキのお題一覧を、デッキに入れた順に並べるため、入れた日時を持たせる。
-- 列を足すだけなので、古いバックエンドもそのまま動く。
-- 今ある行はすべて同じ日時になり、並びは今まで通り(内容の順)のまま。

alter table public.deck_cards
    add column added_at timestamptz not null default now();
