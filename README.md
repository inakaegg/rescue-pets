# rescue-pets — 保護犬猫ポータル

更新日: 2026-08-22

全国の保護犬猫の譲渡情報を1か所で検索できるようにする Web サービスの PoC です。掲載データはすべて架空です。仕様は [SPEC.md](SPEC.md) にあります。

現在は雛形の段階で、機能の実装はまだありません。自動テストも未整備です。最初に作るのは「架空ページの収集 → AI 構造化 → 検索」を通す CLI で、テストはそこで導入します。

## 技術構成

- フロントエンド: React + Vite + TypeScript
- API: Hono（Lambda では aws-lambda アダプタ、ローカルでは Node サーバー）
- インフラ: AWS Amplify Gen2 + AWS CDK（Amplify Data は使いません）
- データベース: Amazon DynamoDB の1テーブル（ローカルと CLI は JSON ファイル）
- AI: Amazon Bedrock 上の GPT-5.6 Luna（CLI とテストは LLM を呼ばないスタブで動きます）

AWS 以外の外部サービスは使いません。

## コマンド

| 目的 | コマンド |
|---|---|
| 依存のインストール | `npm install` |
| フロントエンド開発サーバー | `npm run dev` |
| API ローカル実行（port 3001） | `npm run dev:api` |
| ビルド | `npm run build` |
| ビルド結果のプレビュー | `npm run preview` |
| lint | `npm run lint` |
| バックエンドの型検査 | `npm run typecheck:backend` |
| AWS サンドボックス起動（要 AWS 認証。クラウド操作のため [AGENTS.md](AGENTS.md) の明示許可ルールの対象） | `npx ampx sandbox` |
