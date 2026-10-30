-- ユーザーを消したときに、そのユーザーのものが正しく消えるようにする。
--
-- 1. お題: 作成者が消えると、作成者なし(=公式のお題)として全員に見えていた。
--    作成者と一緒に消す。他の人のお題はデッキに入れられないので、他の人のデッキには影響しない
-- 2. ルームが使うデッキ: restrict だと、ユーザーを消すときに、ルームより先にデッキを消そうとして
--    止まることがある。no action にすると、削除の最後に確かめるので、ルームとデッキを一緒に消せる
--    (デッキだけを消そうとしたときは、これまでどおりDBが止める)

begin;

alter table public.cards drop constraint cards_create_user_id_fkey;
alter table public.cards add constraint cards_create_user_id_fkey
    foreign key (create_user_id) references public.users(id) on delete cascade;

alter table public.rooms drop constraint rooms_deck_id_fkey;
alter table public.rooms add constraint rooms_deck_id_fkey
    foreign key (deck_id) references public.decks(id);

commit;
