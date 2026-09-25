# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 作業上のルール

- **コミットは人間が手動で行う。** Claude自身がコミットを作成してはならない。変更を終えたら、内容を説明して人間の判断に委ねること
- **git追跡外のファイルを削除・追加・編集する場合は、必ず事前に確認を取る。** リポジトリの追跡対象外のファイル・ディレクトリに対する変更(生成物の削除、無関係な場所へのファイル作成、想定外のファイルの書き換えなど)は、実行前に必ずユーザーに確認すること

- **ドキュメントは網羅的に書きすぎない。** 読み手は大学生〜ジュニアエンジニアレベルを想定し、要点を絞って平易に書くこと。全パターンの列挙や過剰な詳細は避ける

- **コードは1コミット分の粒度ずつ出力する。** 1回の作業で複数の関心事(例: 依存追加・機能実装・ドキュメント更新)を一度に進めず、1コミットにまとめられる単位で区切り、人間が確認・コミットしてから次に進むこと

- **Pythonのコードは PEP 8 に則って書く。** 出力前に準拠しているか確認すること(命名規則、1行の長さ、import順など)

## プロジェクトの状態

**実装初期。** 設計は`docs/`に揃っており、開発環境(Docker Compose)・Supabaseスキーマ・JWT検証まで完成している。お題/デッキ/ルーム等の業務ロジック(CRUD・drawn・WebSocket)とフロントの画面はこれから。順序は末尾の「実装順序」を参照。

## コマンド

すべてリポジトリルートで実行する(ホストにNode.js/Pythonは不要)。

```bash
docker compose up -d --build    # frontend(:3000)とbackend(:8000)を起動
docker compose down

# backendテスト(テスト用依存はrequirements-dev.txtでイメージには含めない)
docker compose exec backend sh -c "pip install -q -r requirements-dev.txt && python -m pytest -q"
docker compose exec backend python -m pytest tests/test_security.py::test_valid_token_returns_user_id   # 単一テスト

# backendのPEP 8チェック
docker compose exec backend sh -c "pip install -q -r requirements-dev.txt && python -m pycodestyle app tests"

docker compose exec frontend npm run lint
```

`backend/.env`・`frontend/.env.local`は`.gitignore`対象で、雛形は`*.example`。環境構築で詰まりやすい点(Git Bash/WSL/Docker Desktopのパス・統合の問題、Supabase接続文字列のIPv6問題など)は`docs/苦労話.md`にまとめてある。

## プロジェクト概要

「kaiwa_deck(会話デッキ)」は、TCG(トレーディングカードゲーム)の「デッキから1枚引く」というメタファーを応用したアイスブレイク用Webアプリ。よく知らない相手(就活・懇親会での相手、顔見知りだが話したことのない人、オンライン初対面)との会話のきっかけを、「お題カードを引く」というゲーム的な行為で作る。想定用途は2つ: ①事前に一人でデッキを準備する、②その場で複数人が同じ「ルーム」でリアルタイムに同期して引く。背景と検証の詳細は`docs/課題とペルソナ.md`を参照。

## アーキテクチャ(設計済み、未実装)

各判断の詳しい理由は`docs/技術選定.md`を参照。将来のセッションが尊重すべき要点:

- **フロントエンド**: Next.js(App Router) + TypeScript + Tailwind + shadcn/ui + Framer Motion、`frontend/`に配置
- **バックエンド**: FastAPI(Python)、`backend/`に配置。このアプリに真の並列処理の必要性はほぼ無いにもかかわらず、Go等ではなくFastAPIを意図的に選んでいる — CRUD/API設計を学ぶことが目的の1つだったため。BaaS完結構成に「簡略化」しないこと
  - REST CRUDは同期SQLAlchemy、WebSocketのルーム進行ロジック(`backend/app/ws/room_manager.py`、未作成)はasyncio + ルーム単位の`asyncio.Lock`で排他制御する、という意図的な使い分け。バックエンド全体を非同期ORMに統一しないこと
- **認証**: Supabase Auth(匿名認証+アカウント昇格)。バックエンドは認証情報を発行・保存せず、Supabase発行のJWTを検証して`user_id`を取得するだけ(`backend/app/core/security.py`の`get_current_user_id`依存関係)。このプロジェクトのトークンは**ES256(非対称鍵)署名**なので、旧来のHS256共有シークレットではなくJWKS(`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`)の公開鍵で検証する。JWKSの取得先はトークン内の`iss`ではなく設定値`SUPABASE_URL`に固定すること(トークンを信用して取得先を決めない)。**`user_id`や作成者idをリクエスト引数として受け取ってはならない** — 全エンドポイントで検証済みJWTから取得すること。これはAPI設計時に何度も指摘された規約で、ハンドラをコピペする際に混入しやすい退行なので特に注意
- **DB**: Supabase Postgres。スキーマは`supabase/migrations/`(未作成)配下の生SQLを唯一の正とする — **Alembicは導入しない**。`backend/app/models/`のSQLAlchemyモデルはこのスキーマに追従する手書きの写像であり、スキーマの発生源ではない
- **ホスティング方針**: Vercel(フロント) + Google Cloud Run(`min-instance=0`、バックエンド) + Supabase(DB/Auth)。無料/低コスト運用を狙った構成で、これには実装上の重要な帰結がある: Cloud Runインスタンスはリクエスト間でゼロにスケールダウンしうるため、**ゲーム/ルームの状態はバックエンドのプロセスメモリではなくDBに永続化する**こと
- **ローカル開発**: Docker Compose(ローカルへのNode.js/Python個別インストールは前提としない)。`frontend`・`backend`の2サービスのみで、ローカルPostgresコンテナは無い(DBはクラウドのSupabaseプロジェクト)。frontendのベースイメージはNode 22 — `@supabase/supabase-js`がNode 20ではネイティブWebSocket未対応で`createClient()`時にクラッシュするため、下げないこと。backendのDB接続はSupabaseの**Shared pooler**を使う(Direct connectionはIPv6専用でコンテナから届かない)

## データモデル

完全なスキーマと各中間テーブルの設計理由は`docs/テーブル設計.md`を参照。テーブルを追加・変更する前に必ず読むこと。将来のセッションが安易に「修正」すべきでない点:

- 全ての主キーは連番intではなく`uuid` — ルーム/デッキのidはURLで共有されるため、推測可能な連番だとIDOR(不正な直接オブジェクト参照)のリスクがあるという意図的な判断
- `room_drawn_cards`(room_id, card_id, drawn_at)には意図的に**`drawn_by`カラムが無い** — 個人がルームをまたいで引いた履歴はMVPスコープ外でPhase 2送りにした。`docs/API設計.md`の「ルームの進行」節を確認せずに追加し直さないこと
- 多対多の関係(デッキ⇔お題、ルーム⇔ユーザー)は配列ではなく明示的な中間テーブル(`deck_cards`, `room_users`)でモデル化している — 設計レビューで意図的に修正した経緯がある
- 匿名ユーザーも`ユーザ`テーブルに実際の行を持つ(`is_anonymous`フラグ)。認証を素通りさせる実装ではなく、後からゲスト利用を本アカウントに昇格できるようにするための設計

## API設計の規約

エンドポイント一覧は`docs/API設計.md`参照。新しいエンドポイントを追加する際に共通して適用すべき規約:

- リソースIDはURLパスに含める。そのリソース自身のbodyフィールドとしては渡さない
- `POST`/`PUT`は作成・更新後のリソース本体を返す。`DELETE`は204でボディ無し
- 一覧系エンドポイントは関連する表示用データをJOINして含める(例: ルーム参加者一覧は`user_id`だけでなく`user_name`も含む)。フロント側でN+1回のリクエストを発生させない
- 複数テーブルのデータを同時に必要とする画面には、専用の集約エンドポイントを用意する(例: `GET /room/{room_id}/state`)。フロントに複数リクエストを乱発させない
- 山札の残り枚数は公開するが、まだ引かれていないお題の中身を事前に見せてはならない — これはスタイルの好みではなく、ゲーム性(ネタバレ防止)に関わる制約

## 実装順序

`docs/開発計画.md`にフェーズ分けされたMVPの内訳がある。想定している実装順序(直前の計画セッションより): DBスキーマ → JWT検証ミドルウェア → お題CRUD → デッキCRUD/deck_cards → ルーム/room_users → drawn・state系エンドポイント → フロント結合 → ソロドロー体験 → WebSocketリアルタイム層(引くロジックのバグと同期のバグを同時にデバッグしないよう、意図的に最後に回す)。
