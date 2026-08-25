# 掲載データ

このサービスが扱う「掲載」（保護犬猫1件ぶんの情報）の決まりごとを説明します。

## データはすべて架空

- 掲載データは架空とする。団体、犬猫のプロフィール、掲載元ページのすべてを架空に作る。実在の団体・動物の情報は使わない。
- 実在サイトへはアクセスしない。
- 写真は権利上安全なものだけを使う（自前撮影、生成画像、CC0素材）。見本掲載の写真は生成画像を `public/pets/` へ置く。素材を作る道具は本サービスの範囲外とし、別リポジトリ（`pets-image`）で持つ。
- `pets-image` から受け取るのは、写真50枚（`public/pets/sample-<名前>.webp`）と、呼び名・種別・紹介文を持つ `data/sample-pets.json` の2つである。写真と紹介文は対で1件の掲載になるため、片方だけの差し替えを `npm run test:pet-assets` が弾く。

## 見本掲載50件

- 初期データは50件の**見本掲載**とする。ランダム生成はしない。全件が内容を固定した架空の掲載で、写真・呼び名・紹介文を `pets-image` 側で作る。idは `sample-` で始める。
- 紹介文から検索用の項目（年齢区分・体格・相性・要約など）を作る処理は、団体の登録と同じLLMによる構造化とする。ただし一度だけ実行し、結果を `data/listings.json` へ固定してリポジトリへ置く。掲載の内容が実行のたびに揺れると、検索の確認にならないためである。
- `pets seed` は `data/listings.json` を読んでDynamoDBへ投入する。同じidは上書きし、再実行しても件数が増えない。

## 掲載1件の項目

AIが構造化する項目と、収集・登録で決まる項目を分けて持ちます。

| 項目 | 内容 | 決まり方 |
|---|---|---|
| id | 掲載の識別子 | 生成 |
| species | `dog` / `cat` | AI |
| name | 呼び名（架空） | AI |
| sex | `male` / `female` / `unknown` | AI |
| ageCategory | `baby` / `young` / `adult` / `senior` / `unknown` | AI（推定） |
| size | `small` / `medium` / `large` / `unknown`（猫は `unknown` でよい） | AI（推定） |
| prefecture | 都道府県 | AIまたは団体の所在地 |
| traits | 性格を表す短い語句の配列 | AI |
| conditions | 譲渡条件の配列 | AI |
| suitability | 子ども・他の犬・猫・集合住宅との相性。各 `yes` / `no` / `unknown` | AI（推定） |
| summary | 検索結果に出す1〜2文の要約 | AI |
| description | 元の紹介文・メモ | 収集・登録 |
| organization | 団体のid・名前・サイトURL | 収集・登録 |
| photoUrl | 写真のURL | 収集・登録 |
| sourceUrl | 掲載元ページのURL | 収集・登録 |
| status | `available` / `adopted` / `closed` | 団体の操作 |
| source | `crawl` / `org` / `seed` | 収集・登録・seed |
| createdAt / updatedAt | ISO 8601の日時 | 生成 |

AIの推定項目は、元の文章に根拠がなければ `unknown` を入れます。推定で埋めて断定しないためです。

## データの置き場所

データベースはAmazon DynamoDBの1テーブルです。PostgreSQLや外部のマネージドDBは使いません。この選定の理由と検討した代替案は [decisions/001](decisions/001-DynamoDBを採用する.md) にあります。

- テーブルは `pk` / `sk` の単一テーブル設計とする。掲載は `pk = LISTING#<id>`、`sk = META`。団体ごとの一覧には `orgId` をキーにしたGSIを使う（GSIのQueryは実装の順序4で足す。順序は [ROADMAP](ROADMAP.md) を参照）。
- LLM呼び出しの日次カウンタも同じテーブルへ置く（`pk = COUNTER#llm`、`sk = <日付>`）。
- CLIとローカル開発はsandboxのDynamoDBを既定の保存先にする（`amplify_outputs.json` からテーブル名を読む）。自動テストだけ、同じ保存インターフェースのメモリ内実装を使う。
- 初版の保存操作は「全件読む・1件書く・1件消す」の3つに限定し、団体別の読み出しは順序4で加える。
