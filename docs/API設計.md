# API設計

テーブル設計は [テーブル設計.md](./テーブル設計.md) を参照。一旦FastAPI(REST)のみを対象とし、WebSocketによるリアルタイム同期は別途検討する。

## 設計方針

対話しながら固めた設計原則。

- 認証はSupabase Auth(JWT)。**自分自身のuser_idや作成者idはリクエスト引数として渡さず、JWT検証の結果から取得する**(クライアントが他人のidを騙って送れないようにするため)
- リソースのIDはURLパスに含める(例: `DELETE /deck/{id}`)。中間テーブルの操作も含め、パスの親子構造を統一する
- **POST/PUTは作成・更新後の中身をレスポンスとして返す**(クライアントがサーバー生成値を知る必要があるため)。**DELETEは204でボディを返さない**
- 一覧系のAPIは、関連テーブルをJOINして表示に必要な情報を含める(N+1問題を避ける。例: 参加者一覧に`user_name`を含める)
- 画面の初期表示に複数テーブルの情報が必要な場合は、専用の集約エンドポイントを用意する(例: ルーム入室時の`state`)
- ゲーム性に関わる情報(山札の中身)はAPIレスポンスでネタバレさせない。残り枚数のみ返す

## ユーザー

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| 自分の情報参照 | `GET /user/{id}/` | なし | `{user_name, mail, is_anonymous}` |
| 他人の情報参照 | `GET /user/{id}/` | なし | `{user_name}` (mailは含めない) |
| ユーザ名変更 | `PUT /user/{id}/` | `user_name` | `{user_name, mail, is_anonymous}` |

## デッキ

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| 自分のデッキ一覧 | `GET /deck/` | なし(JWTから自分のuser_id) | `[{id, create_user_id, deck_name, card_count, created_at, updated_at}, ...]` |
| デッキ作成 | `POST /deck/` | `デッキ名` | `{id, create_user_id, deck_name, created_at, updated_at}` |
| デッキ削除 | `DELETE /deck/{id}` | なし | 204 |
| デッキ参照 | `GET /deck/{id}/` | なし | `{id, create_user_id, deck_name, created_at, updated_at}` |

## deck_cards(デッキとお題の中間テーブル)

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| お題を追加 | `POST /decks/{deck_id}/cards` | `card_id` | `{deck_id, card_id}` |
| お題を削除 | `DELETE /decks/{deck_id}/cards/{card_id}` | なし | 204 |

## ルーム

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| ルーム作成 | `POST /room/` | `deck_id`, `ルーム名` | `{id, room_create_user, deck_id, room_name, created_at}` |
| ルーム削除 | `DELETE /room/{id}/` | なし | 204 |
| ルーム参照 | `GET /room/{id}/` | なし | `{id, room_create_user, deck_id, room_name, created_at}` |
| デッキ/ルーム名の変更 | `PUT /room/{id}/` | `ルーム名`, `デッキid` | `{id, room_create_user, deck_id, room_name, created_at}` |

### room_users(ルームとユーザーの中間テーブル)

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| ルーム参加 | `POST /room/{room_id}/user/` | なし(JWTから自分のuser_id) | `{room_id, user_id, joined_at, last_seen_at}` |
| 参加者一覧 | `GET /room/{room_id}/user/` | なし | `[{room_id, user_id, user_name, joined_at, last_seen_at}, ...]` |
| ルーム退出 | `DELETE /room/{room_id}/user/{user_id}` | なし | 204 |

## お題

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| お題作成 | `POST /card/` | `内容`, `補足` | `{id, create_user_id, content, description}` |
| お題削除 | `DELETE /card/{id}/` | なし | 204 |
| お題参照 | `GET /card/{id}/` | なし | `{id, create_user_id, content, description}` |
| お題編集 | `PUT /card/{id}/` | `内容`, `補足` | `{id, create_user_id, content, description}` |

- どのルートもログイン必須(トークンが無いと401)。作成は201を返す
- 参照は、ログインしていれば誰でもできる
- 更新・削除は**作成者本人だけ**。他人のお題や公式のお題(作成者なし)は403、存在しないidは404
- 入力の上限は`content`が1〜200文字、`description`が500文字まで(超えると422)

## ルームの進行(引いたお題の記録)

`テーブル.txt`の当初の方針(引いた記録は不要、フロントで管理)から転換。Cloud Run(min-instance=0)構成ではインスタンスがスケールダウンしうるため、進行状態をDBに永続化する。

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| お題を引く | `POST /room/{room_id}/drawn` | なし(サーバー側が未使用のお題からランダムに選ぶ) | `{room_id, card_id, drawn_at, content, description}` |
| 引かれたお題一覧 | `GET /room/{room_id}/drawn` | なし | `[{room_id, card_id, drawn_at, content, description}, ...]` |
| 山札をリセット | `DELETE /room/{room_id}/drawn` | なし | 204 |

## ルーム入室時の集約API

ルーム画面(`/room/[code]`)の初期表示に必要な情報(ルーム情報・参加者・山札の残り枚数・引かれたお題)を1回のリクエストにまとめる。山札の中身は返さず、残り枚数のみ返してネタバレを防ぐ。

```
GET /room/{room_id}/state
引数: なし
レスポンス: 成功→200 {
    room: {id, room_create_user, deck_id, room_name, created_at},
    participants: [{user_id, user_name, joined_at, last_seen_at}, ...],
    remaining_card_count: 0,
    drawn: [{card_id, content, description, drawn_at}, ...]
}
```

## 画面構成

`drawn`はroom単位でのみ記録し「誰が引いたか」を持たない設計にしたため、個人がルームをまたいで引いた履歴を表示する`/history`はPhase 2(`drawn_by`追加時)に送る。MVPでは`GET /room/{room_id}/drawn`をルーム画面内の表示に留める。

また、「一人で使う」体験も内部的には自分1人だけが参加するルームを自動作成して`drawn`を叩く実装になる(確定APIが`drawn`・`state`とも`room_id`必須のため)。

```
/                LP(コンセプト説明・差別化・CTA)
/play            モード選択(一人で準備する / 誰かと今すぐ共有する)
/room/new        ルーム作成(デッキ選択→共有リンク/QR発行)
/room/[code]     共有ドロー画面(参加者一覧、山札、めくり演出、同期、引いた履歴表示) ← 最重要画面
/decks           自分のデッキ一覧+公式プリセット
/decks/[id]      デッキ編集(カード追加/削除/並べ替え)
/decks/[id]/cards カードライブラリ検索・追加
/account         ゲスト→アカウント昇格導線、プロフィール
```

**Phase 2**: `/history`(`drawn_by`追加後、個人がルームをまたいで引いた履歴+お気に入り/評価)
