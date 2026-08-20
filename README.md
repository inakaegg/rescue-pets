# rescue-pets — 保護犬猫ポータル

更新日: 2026-08-20

全国の保護犬猫の譲渡情報を1か所で検索できるようにする Web サービスの PoC です。掲載データはすべて架空です。仕様は [SPEC.md](SPEC.md) にあります。

現在は雛形の段階で、機能の実装はまだありません。

## 技術構成

- フロントエンド: React + Vite + TypeScript
- API: Hono（Lambda では aws-lambda アダプタ、ローカルでは Node サーバー）
- インフラ: AWS Amplify Gen2 + AWS CDK（Amplify Data は使いません）
- データベース: PostgreSQL（開発はローカル Docker。クラウドの置き場所は未定）

## コマンド

| 目的 | コマンド |
|---|---|
| 依存のインストール | `npm install` |
| フロントエンド開発サーバー | `npm run dev` |
| API ローカル実行（port 3001） | `npm run dev:api` |
| ビルド | `npm run build` |
| lint | `npm run lint` |
| バックエンドの型検査 | `npm run typecheck:backend` |
| AWS サンドボックス起動（要 AWS 認証） | `npx ampx sandbox` |
