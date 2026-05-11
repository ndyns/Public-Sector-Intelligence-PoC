import csv
import html
import json
from pathlib import Path
from collections import Counter

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Preformatted,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


# =========================
# File settings
# =========================

INPUT_JSON = "data/saitama_childcare_services_with_ai.json"
OUTPUT_CSV = "output/saitama_childcare_services_summary.csv"
OUTPUT_PDF = "output/Public_Sector_Intelligence_PoC_Report.pdf"


# =========================
# Utility functions
# =========================

def load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def join_list(value) -> str:
    if isinstance(value, list):
        return " / ".join(str(v) for v in value)
    if isinstance(value, str):
        return value
    return ""


def safe_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def get_ai(record: dict) -> dict:
    return record.get("ai_analysis", {}) or {}


def count_ai_field(records: list[dict], field_name: str) -> Counter:
    counter = Counter()

    for record in records:
        ai = get_ai(record)
        value = ai.get(field_name, "未分類")
        if not value:
            value = "未分類"
        counter[value] += 1

    return counter


def get_top_priority_records(records: list[dict], n: int = 5) -> list[dict]:
    def score(record: dict) -> int:
        ai = get_ai(record)
        value = ai.get("priority_score", 0)
        try:
            return int(value)
        except Exception:
            return 0

    return sorted(records, key=score, reverse=True)[:n]


# =========================
# CSV generation
# =========================

def create_csv(records: list[dict], output_path: str) -> None:
    rows = []

    for record in records:
        ai = get_ai(record)

        rows.append({
            "id": record.get("id", ""),
            "municipality": record.get("municipality", ""),
            "domain": record.get("domain", ""),
            "title": record.get("title", ""),
            "description": record.get("description", ""),
            "summary": ai.get("summary", ""),
            "policy_category": ai.get("policy_category", ""),
            "service_type": ai.get("service_type", ""),
            "target_user": ai.get("target_user", ""),
            "resident_touchpoint": ai.get("resident_touchpoint", ""),
            "related_department": ai.get("related_department", ""),
            "assumed_issue": ai.get("assumed_issue", ""),
            "operational_pain_point": ai.get("operational_pain_point", ""),
            "managed_data_objects": join_list(ai.get("managed_data_objects", "")),
            "crm_use_case": ai.get("crm_use_case", ""),
            "salesforce_relevance": ai.get("salesforce_relevance", ""),
            "sales_opportunity_hypothesis": ai.get("sales_opportunity_hypothesis", ""),
            "priority_score": ai.get("priority_score", ""),
            "priority_reason": ai.get("priority_reason", ""),
            "first_meeting_questions": join_list(ai.get("first_meeting_questions", "")),
            "data_quality_flag": ai.get("data_quality_flag", ""),
            "source_url": record.get("source_url", ""),
        })

    if not rows:
        print("CSV出力対象データがありません。")
        return

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV saved: {output_path}")


# =========================
# PDF helper
# =========================

def build_styles():
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleJP",
        parent=styles["Title"],
        fontName="HeiseiKakuGo-W5",
        fontSize=20,
        leading=26,
        spaceAfter=12,
        textColor=colors.HexColor("#111827"),
    )

    subtitle_style = ParagraphStyle(
        "SubtitleJP",
        parent=styles["Normal"],
        fontName="HeiseiKakuGo-W5",
        fontSize=12,
        leading=18,
        spaceAfter=14,
        textColor=colors.HexColor("#374151"),
    )

    h2_style = ParagraphStyle(
        "H2JP",
        parent=styles["Heading2"],
        fontName="HeiseiKakuGo-W5",
        fontSize=13,
        leading=18,
        spaceBefore=8,
        spaceAfter=8,
        textColor=colors.HexColor("#111827"),
    )

    body_style = ParagraphStyle(
        "BodyJP",
        parent=styles["Normal"],
        fontName="HeiseiMin-W3",
        fontSize=9.5,
        leading=15,
        spaceAfter=6,
        textColor=colors.HexColor("#111827"),
    )

    small_style = ParagraphStyle(
        "SmallJP",
        parent=styles["Normal"],
        fontName="HeiseiMin-W3",
        fontSize=7.5,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )

    code_style = ParagraphStyle(
        "CodeJP",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.2,
        leading=9.2,
        leftIndent=6,
        spaceAfter=8,
    )

    callout_style = ParagraphStyle(
        "CalloutJP",
        parent=styles["Normal"],
        fontName="HeiseiKakuGo-W5",
        fontSize=9,
        leading=14,
        backColor=colors.HexColor("#F3F4F6"),
        borderColor=colors.HexColor("#E5E7EB"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "h2": h2_style,
        "body": body_style,
        "small": small_style,
        "code": code_style,
        "callout": callout_style,
    }


def P(text, style):
    escaped = html.escape(safe_text(text)).replace("\n", "<br/>")
    return Paragraph(escaped, style)


def bullet_items(items: list[str], style) -> list:
    return [P("・" + item, style) for item in items]


def create_simple_table(rows, col_widths):
    table = Table(rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


# =========================
# PDF generation
# =========================

def create_pdf(records: list[dict], output_path: str) -> None:
    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    story = []

    # -------------------------
    # Page 1: Summary
    # -------------------------

    story.append(P("Public Sector Intelligence PoC", styles["title"]))
    story.append(P("さいたま市 子育て支援情報の構造化とAIによる営業・戦略情報抽出", styles["subtitle"]))

    story.append(P("1. 結論", styles["h2"]))
    story.append(P(
        "さいたま市の子育て支援制度情報を制度単位に構造化し、AI分析により、"
        "住民接点管理・申請/相談履歴管理・支援ニーズ可視化に関する活用余地を抽出した。",
        styles["callout"],
    ))

    story.append(P("2. 目的", styles["h2"]))
    story += bullet_items([
        "自治体Webページに分散する非構造情報を収集し、制度単位の構造化データへ変換する。",
        "AIにより、要約・分類・対象者・業務課題・営業仮説を抽出する。",
        "公共ビジネスにおける顧客理解、仮説構築、提案準備に使えるデータを生成する。",
    ], styles["body"])

    story.append(P("3. 対象データ", styles["h2"]))
    story += bullet_items([
        "対象自治体：さいたま市",
        "対象領域：子育て支援政策",
        "取得対象：さいたま市Webサイト内「子育てに関する援助」ページ",
        f"抽出件数：{len(records)}件",
    ], styles["body"])

    story.append(P("4. 求人要件との対応", styles["h2"]))
    rows = [
        [P("求人要件", styles["small"]), P("本PoCでの対応", styles["small"])],
        [P("政策・施策情報の収集自動化", styles["small"]), P("Pythonで自治体Web情報を取得", styles["small"])],
        [P("クレンジングと分析", styles["small"]), P("HTML本文を整形し、制度単位に分割", styles["small"])],
        [P("AIへの接続", styles["small"]), P("OpenAI APIで制度ごとに分析", styles["small"])],
        [P("戦略情報の抽出", styles["small"]), P("CRM活用仮説・営業質問・優先度を生成", styles["small"])],
    ]
    story.append(create_simple_table(rows, [62 * mm, 100 * mm]))

    story.append(P("5. 処理フロー", styles["h2"]))
    story.append(P(
        "Webページ → スクレイピング → テキストクレンジング → 制度単位に分割 → "
        "JSON構造化 → AI分析 → CSV/PDF出力",
        styles["callout"],
    ))

    story.append(PageBreak())

    # -------------------------
    # Page 2: Analysis Summary
    # -------------------------

    story.append(P("分析結果サマリー", styles["title"]))

    policy_counts = count_ai_field(records, "policy_category")
    service_type_counts = count_ai_field(records, "service_type")
    crm_counts = count_ai_field(records, "crm_use_case")
    quality_counts = count_ai_field(records, "data_quality_flag")

    story.append(P("1. 政策カテゴリ別件数", styles["h2"]))
    rows = [[P("政策カテゴリ", styles["small"]), P("件数", styles["small"])]]
    for key, value in policy_counts.items():
        rows.append([P(key, styles["small"]), P(value, styles["small"])])
    story.append(create_simple_table(rows, [115 * mm, 30 * mm]))

    story.append(Spacer(1, 8))

    story.append(P("2. 業務タイプ別件数", styles["h2"]))
    rows = [[P("業務タイプ", styles["small"]), P("件数", styles["small"])]]
    for key, value in service_type_counts.items():
        rows.append([P(key, styles["small"]), P(value, styles["small"])])
    story.append(create_simple_table(rows, [115 * mm, 30 * mm]))

    story.append(Spacer(1, 8))

    story.append(P("3. CRMユースケース別件数", styles["h2"]))
    rows = [[P("CRMユースケース", styles["small"]), P("件数", styles["small"])]]
    for key, value in crm_counts.items():
        rows.append([P(key, styles["small"]), P(value, styles["small"])])
    story.append(create_simple_table(rows, [115 * mm, 30 * mm]))

    story.append(Spacer(1, 8))

    story.append(P("4. データ品質", styles["h2"]))
    rows = [[P("品質フラグ", styles["small"]), P("件数", styles["small"])]]
    for key, value in quality_counts.items():
        rows.append([P(key, styles["small"]), P(value, styles["small"])])
    story.append(create_simple_table(rows, [115 * mm, 30 * mm]))

    story.append(PageBreak())

    # -------------------------
    # Page 3: Insights
    # -------------------------

    story.append(P("主要インサイト", styles["title"]))

    story.append(P("Insight 1：申請・助成型制度は、申請履歴と対象者属性の管理が重要", styles["h2"]))
    story.append(P(
        "医療費助成や進学支援金などは、対象者属性、申請状況、助成実績、利用率を継続的に管理することで、"
        "支援が必要な層に届いているかを把握できる。CRMや住民ポータルとの接続余地がある。",
        styles["body"],
    ))

    story.append(P("Insight 2：相談支援型制度は、ケース管理と相談履歴の蓄積と相性が高い", styles["h2"]))
    story.append(P(
        "相談窓口系の制度では、相談内容、相談者属性、対応履歴、地域別相談傾向を管理することで、"
        "個別対応の質向上と政策課題の把握に活用できる。",
        styles["body"],
    ))

    story.append(P("Insight 3：訪問・預かり支援は、支援員・施設リソースの需給可視化が重要", styles["h2"]))
    story.append(P(
        "多胎児支援、ヘルパー派遣、ショートステイなどは、利用者ニーズと支援員・施設側の供給状況を"
        "同時に把握する必要がある。リソース配分やサービス拡充判断にデータ活用余地がある。",
        styles["body"],
    ))

    story.append(P("Salesforce活用仮説", styles["h2"]))
    rows = [
        [P("業務課題", styles["small"]), P("CRMユースケース", styles["small"]), P("活用仮説", styles["small"])],
        [P("相談内容が分散", styles["small"]), P("ケース管理", styles["small"]), P("Service Cloud等による相談・対応履歴管理", styles["small"])],
        [P("申請・助成履歴の把握", styles["small"]), P("申請管理", styles["small"]), P("住民ポータルやCRMによる申請状況管理", styles["small"])],
        [P("地域別ニーズ把握", styles["small"]), P("ダッシュボード分析", styles["small"]), P("Tableau等による地域別・制度別の可視化", styles["small"])],
        [P("複数制度の横断管理", styles["small"]), P("データ統合", styles["small"]), P("Data Cloud等による住民接点情報の統合", styles["small"])],
    ]
    story.append(create_simple_table(rows, [45 * mm, 45 * mm, 70 * mm]))

    story.append(PageBreak())

    # -------------------------
    # Page 4: Output examples
    # -------------------------

    story.append(P("出力例：営業判断表", styles["title"]))

    top_records = get_top_priority_records(records, n=5)

    rows = [[
        P("制度名", styles["small"]),
        P("CRM用途", styles["small"]),
        P("優先度", styles["small"]),
        P("営業仮説", styles["small"]),
    ]]

    for record in top_records:
        ai = get_ai(record)
        rows.append([
            P(record.get("title", ""), styles["small"]),
            P(ai.get("crm_use_case", ""), styles["small"]),
            P(ai.get("priority_score", ""), styles["small"]),
            P(ai.get("sales_opportunity_hypothesis", ""), styles["small"]),
        ])

    story.append(create_simple_table(rows, [42 * mm, 38 * mm, 18 * mm, 65 * mm]))

    story.append(P("初回ヒアリングで確認すべき論点例", styles["h2"]))

    question_rows = [[
        P("制度名", styles["small"]),
        P("質問例", styles["small"]),
    ]]

    for record in top_records[:3]:
        ai = get_ai(record)
        questions = join_list(ai.get("first_meeting_questions", ""))
        question_rows.append([
            P(record.get("title", ""), styles["small"]),
            P(questions, styles["small"]),
        ])

    story.append(create_simple_table(question_rows, [52 * mm, 110 * mm]))

    story.append(P("成果物", styles["h2"]))
    story += bullet_items([
        "構造化済みJSON：saitama_childcare_services_with_ai.json",
        "営業判断用CSV：saitama_childcare_services_summary.csv",
        "概要レポートPDF：Public_Sector_Intelligence_PoC_Report.pdf",
    ], styles["body"])

    story.append(P("本質", styles["h2"]))
    story.append(P(
        "本PoCの主眼は、AIを使うこと自体ではなく、公共領域の非構造情報をAIが処理しやすい形に変換し、"
        "営業・戦略判断に使える情報として出力することにある。",
        styles["callout"],
    ))

    doc.build(story)

    print(f"PDF saved: {output_path}")


# =========================
# Main
# =========================

def main() -> None:
    input_path = Path(INPUT_JSON)

    if not input_path.exists():
        raise FileNotFoundError(
            f"{INPUT_JSON} が見つかりません。main.py を先に実行してJSONを作成してください。"
        )

    records = load_json(INPUT_JSON)

    create_csv(records, OUTPUT_CSV)
    create_pdf(records, OUTPUT_PDF)


if __name__ == "__main__":
    main()
