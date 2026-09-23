-- kaiwa_deck 初期スキーマ
-- テーブル/カラムの英語名は docs/API設計.md のレスポンスフィールド名にそのまま対応させている。
-- 設計の背景・多対多解消の経緯は docs/テーブル設計.md を参照。

create extension if not exists "pgcrypto";

-- =========================================================
-- users(ユーザ): Supabase Auth(auth.users)を拡張するプロフィール
-- =========================================================
create table public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    user_name text not null,
    mail text,
    is_anonymous boolean not null default false,
    created_at timestamptz not null default now()
);

-- auth.usersに新規ユーザーが作られたら(匿名サインイン含む)、public.usersにも自動で行を作る
create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.users (id, user_name, mail, is_anonymous)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'user_name', 'ゲスト'),
    new.email,
    coalesce(new.is_anonymous, false)
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();

-- =========================================================
-- decks(デッキ)
-- =========================================================
create table public.decks (
    id uuid primary key default gen_random_uuid(),
    create_user_id uuid not null references public.users(id) on delete cascade,
    deck_name text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- =========================================================
-- cards(お題)
-- =========================================================
create table public.cards (
    id uuid primary key default gen_random_uuid(),
    create_user_id uuid references public.users(id) on delete set null,
    content text not null,
    description text
);

-- =========================================================
-- deck_cards(デッキとお題の中間テーブル)
-- 並び順は管理しない、重複登録は不可(複合PK)
-- =========================================================
create table public.deck_cards (
    deck_id uuid not null references public.decks(id) on delete cascade,
    card_id uuid not null references public.cards(id) on delete cascade,
    primary key (deck_id, card_id)
);

-- =========================================================
-- rooms(ルーム): 1ルームにつき使用デッキは1つだけ
-- =========================================================
create table public.rooms (
    id uuid primary key default gen_random_uuid(),
    room_create_user uuid not null references public.users(id) on delete cascade,
    deck_id uuid not null references public.decks(id) on delete restrict,
    room_name text not null,
    created_at timestamptz not null default now()
);

-- =========================================================
-- room_users(ルームとユーザーの中間テーブル)
-- 再入室は新規行を増やさずUPSERT(last_seen_at更新)で対応する想定
-- =========================================================
create table public.room_users (
    room_id uuid not null references public.rooms(id) on delete cascade,
    user_id uuid not null references public.users(id) on delete cascade,
    joined_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    primary key (room_id, user_id)
);

-- =========================================================
-- room_drawn_cards(ルームで引かれたお題の記録)
-- drawn_byは持たない(個人がルームをまたいだ履歴はPhase2)。
-- 同一ルームで同じお題は1回しか引けない(複合PK)。
-- Cloud Run(min-instance=0)でインスタンスがスケールダウンしても
-- 進行状態を復元できるようDBに永続化する。
-- =========================================================
create table public.room_drawn_cards (
    room_id uuid not null references public.rooms(id) on delete cascade,
    card_id uuid not null references public.cards(id) on delete cascade,
    drawn_at timestamptz not null default now(),
    primary key (room_id, card_id)
);

-- =========================================================
-- RLS: 全テーブルで有効化し、ポリシーは追加しない。
-- FastAPIはテーブル所有者(postgres)権限の直接接続で読み書きするためRLSの影響を受けない。
-- 一方、SupabaseがデフォルトでPostgREST経由に公開するanon/authenticatedロールからは
-- ポリシー無し=全拒否となり、フロントのanon keyでテーブルを直接読み書きできなくなる。
-- =========================================================
alter table public.users enable row level security;
alter table public.decks enable row level security;
alter table public.cards enable row level security;
alter table public.deck_cards enable row level security;
alter table public.rooms enable row level security;
alter table public.room_users enable row level security;
alter table public.room_drawn_cards enable row level security;
