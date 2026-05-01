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


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalize line breaks."""
    text = re.sub(r"\s+", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def fetch_page(url: str) -> str:
    """Fetch a web page and extract plain text."""
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    raw_text = soup.get_text("\n")
    return clean_text(raw_text)


def extract_policy_section(text: str) -> str:
    """Extract the childcare support section from the page text."""
    start_keyword = "子育てに関する援助"

    if start_keyword in text:
        return text.split(start_keyword, 1)[1]

    return text


def split_services(text: str) -> list[dict]:
    """Split page text into service-level records."""
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
                services.append(
                    {
                        "title": current_title,
                        "description": " ".join(current_desc),
                    }
                )
                current_desc = []

            current_title = line
        else:
            if current_title:
                current_desc.append(line)

    if current_title:
        services.append(
            {
                "title": current_title,
                "description": " ".join(current_desc),
            }
        )

    return services


def is_valid_service(service: dict) -> bool:
    """Filter out obvious noise records."""
    description = service.get("description", "")

    if len(description) < 30:
        return False

    noise_words = ["フッター", "分類", "サイトマップ", "Copyright"]
    if any(word in description for word in noise_words):
        return False

    return True


def add_metadata(services: list[dict]) -> list[dict]:
    """Add metadata to each service record."""
    records = []

    for i, service in enumerate(services, start=1):
        records.append(
            {
                "id": f"saitama_childcare_{i:03d}",
                "municipality": "さいたま市",
                "domain": "子育て",
                "source_url": URL,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
                "title": service["title"],
                "description": service["description"],
                "ai_analysis": None,
            }
        )

    return records


def extract_json(content: str) -> dict:
    """Parse JSON from model output."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in AI response.")
        return json.loads(json_match.group())


def analyze_service(client: OpenAI, service: dict) -> dict:
    """Analyze one childcare support service with OpenAI API."""
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
        temperature=0,
    )

    content = response.choices[0].message.content
    return extract_json(content)


def main() -> None:
    print("Fetching page...")
    cleaned_text = fetch_page(URL)

    print("Extracting policy section...")
    policy_text = extract_policy_section(cleaned_text)

    print("Splitting into service records...")
    services = split_services(policy_text)
    services = [service for service in services if is_valid_service(service)]

    print(f"Extracted records: {len(services)}")
    records = add_metadata(services)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    print("Running AI analysis...")
    for record in records:
        print(f"Analyzing: {record['id']} {record['title']}")
        record["ai_analysis"] = analyze_service(client, record)
        time.sleep(1)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    print(f"Done: saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
