# API設計

テーブル設計は [テーブル設計.md](./テーブル設計.md) を参照。一旦FastAPI(REST)のみを対象とし、WebSocketによるリアルタイム同期は別途検討する。

## 設計方針

対話しながら固めた設計原則。

- 認証はSupabase Auth(JWT)。**自分自身のuser_idや作成者idはリクエスト引数として渡さず、JWT検証の結果から取得する**(クライアントが他人のidを騙って送れないようにするため)
- リソースのIDはURLパスに含める(例: `DELETE /deck/{id}/`)。中間テーブルの操作も含め、パスの親子構造を統一する
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
| デッキ作成 | `POST /deck/` | `デッキ名`、(任意)`include_official_cards` | `{id, create_user_id, deck_name, created_at, updated_at}` |
| デッキ削除 | `DELETE /deck/{id}/` | なし | 204 |
| デッキ参照 | `GET /deck/{id}/` | なし | `{id, create_user_id, deck_name, created_at, updated_at}` |

- 参照・更新・削除は作成者本人だけ(デッキには公開の仕組みが無いため、参照も含めて本人限定。他人のは403)
- 使用中(ルームで使われている)のデッキは削除できず、409を返す
- `include_official_cards`を`true`にすると、公式のお題をすべて入れた状態でデッキが作られる(初めての人が、1回のリクエストで最初のデッキを用意できるように)。省略時は`false`

## deck_cards(デッキとお題の中間テーブル)

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| デッキ内のお題一覧 | `GET /deck/{deck_id}/cards/` | なし | `[{id, create_user_id, content, description}, ...]` |
| お題を追加 | `POST /deck/{deck_id}/cards/` | `card_id` | `{deck_id, card_id}` |
| お題を削除 | `DELETE /deck/{deck_id}/cards/{card_id}/` | なし | 204 |

- どれもデッキの持ち主だけ(他人のデッキは403、存在しないデッキは404)。一覧は、内容(`content`)の順
- 追加できるお題は、**公式のお題と自分で作ったお題だけ**。他人のお題は403(作成者があとから編集・削除しても、他人のデッキに影響しないようにするため)
- 同じお題を同じデッキに2回追加すると409

## ルーム

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| ルーム作成 | `POST /room/` | `deck_id`, `ルーム名` | `{id, room_create_user, deck_id, room_name, created_at}` |
| ルーム削除 | `DELETE /room/{id}/` | なし | 204 |
| ルーム参照 | `GET /room/{id}/` | なし | `{id, room_create_user, deck_id, room_name, created_at}` |
| デッキ/ルーム名の変更 | `PUT /room/{id}/` | `ルーム名`, `デッキid` | `{id, room_create_user, deck_id, room_name, created_at}` |

- 参照は、ログインしていれば誰でもできる(リンクで人を誘う前提のため)
- 更新・削除は作成者本人だけ。他人のルームは403、存在しないidは404
- `deck_id`には、**ルームの参加者のデッキのみ**指定できる(作成時点では参加者は作成者のみなので、実質「自分のデッキのみ」)。参加者以外のデッキを指定すると403、存在しないデッキは404
- デッキを別のデッキに変更すると、引いた記録はリセットされる(ルーム名だけの変更では、リセットされない)

### room_users(ルームとユーザーの中間テーブル)

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| ルーム参加 | `POST /room/{room_id}/user/` | なし(JWTから自分のuser_id) | `{room_id, user_id, joined_at, last_seen_at}` |
| 参加者一覧 | `GET /room/{room_id}/user/` | なし | `[{room_id, user_id, user_name, joined_at, last_seen_at}, ...]` |
| ルーム退出 | `DELETE /room/{room_id}/user/{user_id}/` | なし | 204 |

- 参加は、初めてなら201、再入室なら200(新しい行は作らず、`last_seen_at`だけ更新する)
- 参加者一覧は、ルーム参照と同じく、ログインしていれば誰でも見られる(`joined_at`が早い順)
- 退出は本人だけ。他の参加者を外すのは、作成者でも403。参加していない人の退出は404
- 作成者が退出すると、ルームは解散(削除)される。作成者がいなくなるとオーナーを引き継げないため
- ルームが使っているデッキの持ち主が退出しても、デッキはそのまま

## お題

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| お題一覧 | `GET /card/` | なし | `[{id, create_user_id, content, description}, ...]` |
| お題作成 | `POST /card/` | `内容`, `補足` | `{id, create_user_id, content, description}` |
| お題削除 | `DELETE /card/{id}/` | なし | 204 |
| お題参照 | `GET /card/{id}/` | なし | `{id, create_user_id, content, description}` |
| お題編集 | `PUT /card/{id}/` | `内容`, `補足` | `{id, create_user_id, content, description}` |

- どのルートもログイン必須(トークンが無いと401)。作成は201を返す
- 参照は、ログインしていれば誰でもできる
- 更新・削除は**作成者本人だけ**。他人のお題や公式のお題(作成者なし)は403、存在しないidは404
- 入力の上限は`content`が1〜200文字、`description`が500文字まで(超えると422)
- 一覧に出るのは、公式のお題と自分のお題だけ(他人のお題は出ない)。公式が先、その中は内容(`content`)の順

## ルームの進行(引いたお題の記録)

`テーブル.txt`の当初の方針(引いた記録は不要、フロントで管理)から転換。Cloud Run(min-instance=0)構成ではインスタンスがスケールダウンしうるため、進行状態をDBに永続化する。

| 操作 | メソッド/パス | 引数 | レスポンス |
|---|---|---|---|
| お題を引く | `POST /room/{room_id}/drawn/` | なし(サーバー側が未使用のお題からランダムに選ぶ) | `{room_id, card_id, drawn_at, content, description}` |
| 引かれたお題一覧 | `GET /room/{room_id}/drawn/` | なし | `[{room_id, card_id, drawn_at, content, description}, ...]` |
| 山札をリセット | `DELETE /room/{room_id}/drawn/` | なし | 204 |

- 引く・一覧・リセットは、ルームの参加者だけ(参加者以外は403、存在しないルームは404)
- 引くときは、まだ引かれていないお題の中から、サーバーがランダムに選ぶ。同時に引いても、同じお題は2回出ない
- 引けるお題が残っていないとき(山札が空のとき)に引こうとすると、409
- リセットは、参加者なら誰でもできる

## ルーム入室時の集約API

ルーム画面(`/room/[code]`)の初期表示に必要な情報(ルーム情報・参加者・山札の残り枚数・引かれたお題)を1回のリクエストにまとめる。山札の中身は返さず、残り枚数のみ返してネタバレを防ぐ。`remaining_card_count`は、デッキのお題のうち、まだ引かれていない枚数。見られるのは参加者だけ(参加者以外は403)。

```
GET /room/{room_id}/state/
引数: なし
レスポンス: 成功→200 {
    room: {id, room_create_user, deck_id, room_name, created_at},
    participants: [{user_id, user_name, joined_at, last_seen_at}, ...],
    remaining_card_count: 0,
    drawn: [{card_id, content, description, drawn_at}, ...]
}
```

## 上限

匿名ログインは誰でもできるため、DBの容量(無料プランは500MB)を守るための目安。超えると409を返す。数字はコードの1か所にまとめ、あとから変えやすくする。同時に操作したときに、1〜2個超えることは許容する。

| 対象 | 上限 | 超えたときの操作 |
|---|---|---|
| 1人が作るデッキ | 20 | `POST /deck/` |
| 1デッキに入るお題 | 300 | `POST /deck/{deck_id}/cards/` |
| 1人が作るお題 | 200 | `POST /card/` |
| 1人が作るルーム | 4 | `POST /room/` |
| 1ルームの参加者 | 50 | `POST /room/{room_id}/user/`(参加済みの人の再入室は対象外) |

- 1デッキに入るお題の300は、公式お題をすべて入れても、自分のお題と合わせて収まる大きさにしている
- アカウントの量産や大量リクエストへの対策は、バックエンドの外(SupabaseのCAPTCHA、デプロイ時のレート制限)で扱う

## 画面構成

`drawn`はroom単位でのみ記録し「誰が引いたか」を持たない設計にしたため、個人がルームをまたいで引いた履歴を表示する`/history`はPhase 2(`drawn_by`追加時)に送る。MVPでは`GET /room/{room_id}/drawn/`をルーム画面内の表示に留める。

また、「一人で使う」体験も内部的には自分1人だけが参加するルームを自動作成して`drawn`を叩く実装になる(確定APIが`drawn`・`state`とも`room_id`必須のため)。

作るページの一覧と遷移図は、[画面遷移図.md](./画面遷移図.md)を参照。
