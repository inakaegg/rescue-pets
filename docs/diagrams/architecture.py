"""rescue-pets 構成図（AWS 公式アイコン）。mingrammer/diagrams で生成する。
実行: uv run --with diagrams python docs/diagrams/architecture.py（要 Graphviz。どのディレクトリから実行してもよい）
出力は同じディレクトリの architecture.png / deploy-paths.png。図を変えるときはこのファイルを直して再生成し、PNG を手で編集しない。
"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import SQS
from diagrams.aws.management import Cloudformation, Cloudwatch
from diagrams.aws.mobile import Amplify
from diagrams.aws.network import APIGateway, CloudFront
from diagrams.aws.security import Cognito
from diagrams.aws.storage import S3
from diagrams.onprem.client import Client, User, Users
from diagrams.onprem.vcs import Git, Github
from diagrams.programming.flowchart import Document

try:
    from diagrams.aws.ml import Bedrock
except ImportError:  # 古い diagrams には Bedrock アイコンが無い
    from diagrams.aws.ml import Sagemaker as Bedrock

try:
    from diagrams.saas.chat import Line
except ImportError:
    Line = Client

HERE = Path(__file__).resolve().parent  # 出力先をスクリプトの場所に固定する
FONT = "Hiragino Sans"
GRAPH = {"fontname": FONT, "fontsize": "13", "pad": "0.4", "nodesep": "0.5", "ranksep": "0.9", "splines": "spline"}
NODE = {"fontname": FONT, "fontsize": "11"}
EDGE = {"fontname": FONT, "fontsize": "10"}
LATER = {"style": "dashed", "color": "#8E9A94", "fontcolor": "#8E9A94"}

with Diagram(
    "rescue-pets 目標構成（番号は実装の順序）",
    filename=str(HERE / "architecture"), outformat="png", show=False, direction="TB",
    graph_attr={**GRAPH, "ranksep": "1.1", "nodesep": "0.7"}, node_attr=NODE, edge_attr=EDGE,
):
    with Cluster("手元（AWS の外）"):
        user = Users("利用者\nブラウザ")
        org = User("団体の担当者\nブラウザ")
        cli = Client("開発者の CLI ①\npets seed / pets search")
        mem = Document("メモリ内ストア\n自動テスト専用")

    with Cluster("AWS  ap-northeast-1"):
        hosting = Amplify("Amplify Hosting ③\nCloudFront + S3")
        api = APIGateway("API Gateway ②\nHTTP API\nルート別 throttle / JWT authorizer")
        cognito = Cognito("Cognito ④\nユーザープール")
        fn = Lambda("Lambda（Hono）②\nreserved concurrency 2〜5")
        logs = Cloudwatch("CloudWatch Logs ②\n保持 7 日")
        ddb = Dynamodb("DynamoDB ②\n1 テーブル + 日次カウンタ")
        bedrock = Bedrock("Bedrock ②\nGPT-5.6 Luna\nglobal 推論プロファイル")

    with Cluster("後回し（初版に含めない）", graph_attr={"style": "dashed", "color": "#8E9A94", "fontcolor": "#8E9A94"}):
        s3 = S3("S3（写真）")
        sqs = SQS("SQS（非同期化）")
        crawler = Lambda("クローラ（収集）")
        line = Line("LINE 通知")

    user >> Edge(label="SPA 取得") >> hosting
    user >> Edge(label="検索・詳細・一覧") >> api
    org >> Edge(label="ログイン → JWT") >> cognito
    org >> Edge(label="登録・編集・削除 + JWT") >> api
    api >> Edge(label="JWKS で検証", style="dashed") >> cognito
    api >> fn
    fn >> Edge(label="ログ") >> logs
    fn >> Edge(label="Query / Put / Delete") >> ddb
    fn >> Edge(label="Converse API\n条件抽出・並べ替え・構造化", color="#1F7A6E", fontcolor="#1F7A6E", penwidth="2") >> bedrock
    cli >> Edge(label="テスト") >> mem
    cli >> Edge(label="seed 投入 / 検索（sandbox のテーブル）") >> ddb
    cli >> Edge(label="search 時の LLM 呼び出し", color="#1F7A6E", fontcolor="#1F7A6E", style="dashed") >> bedrock
    # 後回しの群を最下段に置くための見えない辺
    ddb >> Edge(style="invis") >> s3
    ddb >> Edge(style="invis") >> sqs
    bedrock >> Edge(style="invis") >> crawler
    bedrock >> Edge(style="invis") >> line

with Diagram(
    "動かす経路 — A: sandbox（開発・検証）  B: 公開（push が前提）",
    filename=str(HERE / "deploy-paths"), outformat="png", show=False, direction="LR",
    graph_attr=GRAPH, node_attr=NODE, edge_attr=EDGE,
):
    repo = Git("リポジトリ（ローカル）\namplify/ + src/ + cli/")

    with Cluster("A. 開発・検証 — npx ampx sandbox（いつでも作って消せる）"):
        with Cluster("個人用スタック（CloudFormation）"):
            cfn = Cloudformation("amplify-rescue-pets-\n<user>-sandbox")
            a_api = APIGateway("API Gateway")
            a_fn = Lambda("Lambda（Hono）")
            a_ddb = Dynamodb("DynamoDB")
            a_cog = Cognito("Cognito")
        outputs = Document("amplify_outputs.json\n接続先が書かれる")
        dev = Client("npm run dev\n手元のフロント")
        cli = Client("pets seed / search")

    with Cluster("B. 公開 — git push（ターンごとの明示許可）"):
        gh = Github("GitHub（private）")
        app = Amplify("Amplify アプリ\nブランチ接続")
        host = CloudFront("Hosting\nCloudFront + S3")
        b_stack = Cloudformation("ブランチ用\nバックエンドスタック")

    repo >> Edge(label="CDK deploy・変更を監視") >> cfn
    cfn >> Edge(style="dotted") >> [a_api, a_fn, a_ddb, a_cog]
    cfn >> Edge(label="出力") >> outputs >> dev
    dev >> Edge(label="API を呼ぶ（Bedrock も本物）") >> a_api
    cli >> Edge(label="seed 投入 / 検索") >> a_ddb
    repo >> Edge(label="git push") >> gh >> app
    app >> Edge(label="フロントをビルド") >> host
    app >> Edge(label="バックエンドを deploy") >> b_stack
    host >> Edge(label="API を呼ぶ") >> b_stack
