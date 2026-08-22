"""rescue-pets 構成図（AWS 公式アイコン）。mingrammer/diagrams で生成する。
実行: uv run --with diagrams python docs/diagrams/architecture.py（要 Graphviz。どのディレクトリから実行してもよい）
出力は同じディレクトリの architecture.svg / deploy-paths.svg。図を変えるときはこのファイルを直して再生成し、SVG を手で編集しない。
SVG にしているのは、GitHub 上でブラウザのズーム（⌘+）をかけても文字がぼやけないようにするため。

ノードは diagrams の既定（アイコンと文字が同じ固定サイズの箱）を使わず、Graphviz の HTML ラベルに
<IMG> を埋め込む。アイコンの大きさ（ICON_PX）と文字の大きさ（TITLE_PT / SUB_PT）を独立に決められ、
ノード幅は文字に合わせて自動で決まるため、文字を大きくしても隣と重ならない。
"""

import base64
import html
import re
from pathlib import Path

import diagrams
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
ICON_BASE = Path(diagrams.__file__).resolve().parent.parent  # diagrams 同梱アイコンの場所

FONT = "Hiragino Sans"
ICON_PX = 72  # アイコンの一辺（px、96dpi 基準）
TITLE_PT = 16  # ノード名の文字サイズ
SUB_PT = 13  # 補足行の文字サイズ
SUB_COLOR = "#5E6B64"
LATER_COLOR = "#8E9A94"
ACCENT = "#1F7A6E"  # LLM 呼び出し（課金される経路）

GRAPH = {"fontname": FONT, "fontsize": "15", "pad": "0.4", "nodesep": "0.35", "ranksep": "0.7", "splines": "spline"}
NODE = {"fontname": FONT}
EDGE = {"fontname": FONT, "fontsize": "13"}
CLUSTER = {"fontname": FONT, "fontsize": "15"}
LATER_CLUSTER = {**CLUSTER, "style": "dashed", "color": LATER_COLOR, "fontcolor": LATER_COLOR}
LATER_EDGE = {"style": "dashed", "color": LATER_COLOR, "fontcolor": LATER_COLOR}
# SVG の文字は閲覧側のフォントで描かれるので、Mac 以外でも日本語が出る候補を並べる
FONT_STACK = "Hiragino Sans, Noto Sans JP, Yu Gothic UI, Meiryo, sans-serif"


def svc(cls, title, *sub, color="#1C2420", sub_color=SUB_COLOR):
    """アイコン + タイトル + 補足行のノードを作る。幅は文字に合わせて自動で決まる。"""
    icon = ICON_BASE / cls._icon_dir / cls._icon
    rows = [
        f'<TR><TD FIXEDSIZE="TRUE" WIDTH="{ICON_PX}" HEIGHT="{ICON_PX}"><IMG SCALE="TRUE" SRC="{icon}"/></TD></TR>',
        f'<TR><TD><FONT POINT-SIZE="{TITLE_PT}" COLOR="{color}">{html.escape(title)}</FONT></TD></TR>',
    ]
    rows += [f'<TR><TD><FONT POINT-SIZE="{SUB_PT}" COLOR="{sub_color}">{html.escape(s)}</FONT></TD></TR>' for s in sub]
    label = '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="1">' + "".join(rows) + "</TABLE>>"
    return cls(label, image="", fixedsize="false", width="0", height="0", margin="0")


def later(cls, title, *sub):
    return svc(cls, title, *sub, color=LATER_COLOR, sub_color=LATER_COLOR)


def finalize_svg(path: Path) -> None:
    """Graphviz の SVG はアイコンをローカルパスで参照するので、base64 で埋め込んで単体で表示できる形にする。"""
    svg = path.read_text()

    def embed(m):
        icon = Path(m.group(1))
        data = base64.b64encode(icon.read_bytes()).decode()
        return f'xlink:href="data:image/png;base64,{data}"'

    svg = re.sub(r'xlink:href="(/[^"]+\.png)"', embed, svg)
    svg = svg.replace(f'font-family="{FONT}"', f'font-family="{FONT_STACK}"')
    svg = svg.replace('font-family="Sans-Serif"', f'font-family="{FONT_STACK}"')  # diagrams が図のタイトルに付ける既定
    path.write_text(svg)


with Diagram(
    "rescue-pets 目標構成（番号は実装の順序）",
    filename=str(HERE / "architecture"),
    outformat="svg",
    show=False,
    direction="TB",
    graph_attr={**GRAPH, "ranksep": "0.8"},
    node_attr=NODE,
    edge_attr=EDGE,
):
    with Cluster("手元（AWS の外）", graph_attr=CLUSTER):
        user = svc(Users, "利用者", "ブラウザ（スマホ / PC）")
        org = svc(User, "団体の担当者", "ブラウザ")
        cli = svc(Client, "開発者の CLI ①", "pets seed / pets search")
        mem = svc(Document, "メモリ内ストア", "自動テスト専用")

    with Cluster("AWS  ap-northeast-1", graph_attr=CLUSTER):
        hosting = svc(Amplify, "Amplify Hosting ③", "CloudFront + S3")
        api = svc(APIGateway, "API Gateway ②", "HTTP API", "ルート別 throttle / JWT authorizer")
        cognito = svc(Cognito, "Cognito ④", "ユーザープール")
        fn = svc(Lambda, "Lambda（Hono）②", "reserved concurrency 2〜5")
        logs = svc(Cloudwatch, "CloudWatch Logs ②", "保持 7 日")
        ddb = svc(Dynamodb, "DynamoDB ②", "1 テーブル + 日次カウンタ")
        bedrock = svc(Bedrock, "Bedrock ②", "GPT-5.6 Luna", "global 推論プロファイル")

    with Cluster("後回し（初版に含めない）", graph_attr=LATER_CLUSTER):
        s3 = later(S3, "S3（写真）")
        sqs = later(SQS, "SQS（非同期化）")
        crawler = later(Lambda, "クローラ（収集）")
        line = later(Line, "LINE 通知")

    user >> Edge(label="SPA 取得") >> hosting
    user >> Edge(label="検索・詳細・一覧") >> api
    org >> Edge(label="ログイン → JWT") >> cognito
    org >> Edge(label="登録・編集・削除 + JWT") >> api
    api >> Edge(label="JWKS で検証", style="dashed") >> cognito
    api >> fn
    fn >> Edge(label="ログ") >> logs
    fn >> Edge(label="Query / Put / Delete") >> ddb
    fn >> Edge(label="Converse API\n条件抽出・並べ替え・構造化", color=ACCENT, fontcolor=ACCENT, penwidth="2") >> bedrock
    cli >> Edge(label="テスト") >> mem
    cli >> Edge(label="seed 投入 / 検索") >> ddb
    cli >> Edge(label="LLM\n呼び出し", color=ACCENT, fontcolor=ACCENT, style="dashed") >> bedrock
    # 後回しの群を最下段に置くための見えない辺
    ddb >> Edge(style="invis") >> s3
    ddb >> Edge(style="invis") >> sqs
    bedrock >> Edge(style="invis") >> crawler
    bedrock >> Edge(style="invis") >> line

finalize_svg(HERE / "architecture.svg")


with Diagram(
    "動かす経路 — A: sandbox（開発・検証）  B: 公開（push が前提）",
    filename=str(HERE / "deploy-paths"),
    outformat="svg",
    show=False,
    direction="LR",
    graph_attr=GRAPH,
    node_attr=NODE,
    edge_attr=EDGE,
):
    repo = svc(Git, "リポジトリ（ローカル）", "amplify/ + src/ + cli/")

    with Cluster("A. 開発・検証 — npx ampx sandbox（いつでも作って消せる）", graph_attr=CLUSTER):
        with Cluster("個人用スタック（CloudFormation）", graph_attr=CLUSTER):
            cfn = svc(Cloudformation, "スタック", "amplify-rescue-pets-<user>-sandbox")
            a_api = svc(APIGateway, "API Gateway")
            a_fn = svc(Lambda, "Lambda（Hono）")
            a_ddb = svc(Dynamodb, "DynamoDB")
            a_cog = svc(Cognito, "Cognito")
        outputs = svc(Document, "amplify_outputs.json", "接続先が書かれる")
        dev = svc(Client, "npm run dev", "手元のフロント")
        cli = svc(Client, "pets seed / search")

    with Cluster("B. 公開 — git push（ターンごとの明示許可）", graph_attr=CLUSTER):
        gh = svc(Github, "GitHub（private）")
        app = svc(Amplify, "Amplify アプリ", "ブランチ接続")
        host = svc(CloudFront, "Hosting", "CloudFront + S3")
        b_stack = svc(Cloudformation, "ブランチ用バックエンドスタック")

    repo >> Edge(label="CDK deploy・変更を監視") >> cfn
    cfn >> Edge(style="dotted") >> [a_api, a_fn, a_ddb, a_cog]
    cfn >> Edge(label="出力") >> outputs >> dev
    dev >> Edge(label="API を呼ぶ（Bedrock も本物）") >> a_api
    cli >> Edge(label="seed 投入 / 検索") >> a_ddb
    repo >> Edge(label="git push") >> gh >> app
    app >> Edge(label="フロントをビルド") >> host
    app >> Edge(label="バックエンドを deploy") >> b_stack
    host >> Edge(label="API を呼ぶ") >> b_stack

finalize_svg(HERE / "deploy-paths.svg")
