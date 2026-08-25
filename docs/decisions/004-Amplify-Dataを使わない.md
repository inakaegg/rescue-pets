# 004 — Amplify Dataを使わない

Amplify Data（AppSync/GraphQL + DynamoDB）は使わない。Amplify Gen2が受け持つのはAuth（Cognito構築）とHostingだけとし、DynamoDB・API・Bedrockの権限は自前のCDKスタックで定義する。

## 理由

- データ層をRESTに保つ。Amplify Dataを使うとGraphQL（AppSync）が前提になり、REST APIの設計が成果物として残らない。
- スキーマ・権限・課金の仕組みを自分で説明できる範囲に保つ。

## トレードオフ

- Amplify Dataなら自動生成されるCRUDやリアルタイム購読を、自前で書くことになる。初版のAPIは小さいので許容する。
