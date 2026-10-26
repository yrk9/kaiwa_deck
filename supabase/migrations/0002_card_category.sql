-- 公式のお題に、種類(どの公式デッキに入るか)を持たせる。
-- 経緯は docs/課題とペルソナ.md の「コンセプトの見直し」を参照。
-- 列を足すだけなので、古いバックエンドもそのまま動く。

alter table public.cards add column category text;

-- 値は3種類だけ(NULLは「種類なし」)
alter table public.cards add constraint cards_category_check
    check (category in ('interview', 'reverse_question', 'small_talk'));

-- 種類を持てるのは、公式のお題(作成者なし)だけ
alter table public.cards add constraint cards_category_official_only
    check (category is null or create_user_id is null);
