import json
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from openai import OpenAI


URL = "https://www.city.saitama.lg.jp/003/001/011/index.html"
OUTPUT_FILE = "saitama_childcare_services_with_ai.json"
os.environ["OPENAI_API_KEY"] = "sk-****"

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def fetch_page(url: str) -> str:
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    raw_text = soup.get_text("\n")
    return clean_text(raw_text)


def extract_policy_section(text: str) -> str:
    start_keyword = "子育てに関する援助"

    if start_keyword in text:
        return text.split(start_keyword, 1)[1]

    return text


def split_services(text: str) -> list[dict]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    services = []
    current_title = None
    current_desc = []

    for line in lines:
        is_title = (
            len(line) < 45
            and any(k in line for k in ["事業", "制度", "センター", "支援", "相談"])
        )

        if is_title:
            if current_title:
                services.append({
                    "title": current_title,
                    "description": " ".join(current_desc)
                })
                current_desc = []

            current_title = line
        else:
            if current_title:
                current_desc.append(line)

    if current_title:
        services.append({
            "title": current_title,
            "description": " ".join(current_desc)
        })

    return services


def is_valid_service(service: dict) -> bool:
    desc = service.get("description", "")

    if len(desc) < 30:
        return False

    noise_words = ["フッター", "分類", "サイトマップ", "Copyright"]
    if any(word in desc for word in noise_words):
        return False

    return True


def add_metadata(services: list[dict]) -> list[dict]:
    records = []

    for i, service in enumerate(services, start=1):
        record = {
            "id": f"saitama_childcare_{i:03d}",
            "municipality": "さいたま市",
            "domain": "子育て",
            "source_url": URL,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "title": service["title"],
            "description": service["description"],
            "ai_analysis": None
        }
        records.append(record)

    return records


def extract_json(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_str = re.search(r"\{.*\}", content, re.DOTALL).group()
        return json.loads(json_str)


def analyze_service(client: OpenAI, service: dict) -> dict:
    prompt = f"""
あなたは公共領域の事業開発担当者です。
以下の子育て支援制度の説明文を読み、営業・戦略判断に使える情報へ変換してください。

【タイトル】
{service["title"]}

【説明】
{service["description"]}

【出力形式】
必ずJSONのみで出力してください。

{{
  "summary": "",
  "policy_category": "",
  "target_user": "",
  "assumed_issue": "",
  "strategic_insight": {{
    "data_management": [],
    "visualization_and_utilization": [],
    "business_decision": []
  }}
}}

【ルール】
- summaryは1文で簡潔に書く
- policy_categoryは「子育て支援」「医療」「教育」「福祉」「相談支援」のいずれかに近い分類にする
- target_userは具体的に書く
- assumed_issueは背景にある行政課題・社会課題を書く
- strategic_insightでは以下を必ず書く
  - どのデータを管理すべきか
  - どう可視化・活用できるか
  - 業務判断や政策判断にどうつながるか
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content
    return extract_json(content)


def main():
    print("ページ取得中...")
    cleaned_text = fetch_page(URL)

    print("本文抽出中...")
    policy_text = extract_policy_section(cleaned_text)

    print("制度単位に分割中...")
    services = split_services(policy_text)
    services = [s for s in services if is_valid_service(s)]

    print(f"抽出件数: {len(services)}")

    records = add_metadata(services)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY が設定されていません。")

    client = OpenAI(api_key=api_key)

    print("AI分析中...")
    for record in records:
        print(f"分析中: {record['id']} {record['title']}")
        record["ai_analysis"] = analyze_service(client, record)
        time.sleep(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"完了: {OUTPUT_FILE} に保存しました。")


if __name__ == "__main__":
    main()


