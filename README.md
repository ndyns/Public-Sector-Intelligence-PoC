# Public Sector Intelligence PoC

## 概要
本プロジェクトは、自治体の公開Web情報（非構造データ）を収集し、制度単位に構造化した上で、AIにより営業・戦略判断に活用可能なデータへ変換するPoCです。

---

## 背景・課題

公共領域では以下の課題が存在します：

- 政策・施策情報がWeb上に分散
- HTML・PDFなど非構造データが中心
- 手動収集による属人的なリサーチ

その結果、データ活用が進まず、戦略立案の高度化が難しい状況にあります。

---

## 目的

- 公共情報の収集・構造化の自動化
- AIによる戦略情報の抽出
- CRM（例：Salesforce）連携を前提としたデータ設計

---

## 対象

- 自治体：さいたま市  
- 分野：子育て支援政策  

---

## 処理フロー

```
Webページ
↓
スクレイピング（requests / BeautifulSoup）
↓
テキストクレンジング
↓
制度単位に分割
↓
JSON構造化
↓
AI分析（OpenAI API）
↓
戦略情報抽出
```

---

## 技術構成

- Python
- requests / BeautifulSoup
- OpenAI API
- JSON

---

## データ構造

```json
{
  "id": "",
  "municipality": "",
  "domain": "",
  "title": "",
  "description": "",
  "ai_analysis": {
    "summary": "",
    "policy_category": "",
    "target_user": "",
    "assumed_issue": "",
    "strategic_insight": {
      "data_management": [],
      "visualization_and_utilization": [],
      "business_decision": []
    }
  }
}
```

---

## 出力例

```json
{
  "title": "多胎児家庭サポート事業",
  "summary": "1歳未満の多胎児家庭に対する育児支援サービス",
  "target_user": "多胎児を養育する家庭",
  "assumed_issue": "育児負担の増大と外出困難",
  "strategic_insight": {
    "data_management": [
      "対象世帯情報",
      "支援利用履歴",
      "満足度データ"
    ],
    "visualization_and_utilization": [
      "地域別ニーズの可視化",
      "利用傾向分析"
    ],
    "business_decision": [
      "リソース配分最適化",
      "新規施策検討"
    ]
  }
}
```

---

## 成果

- 約12件の子育て支援制度を構造化
- AIにより以下を自動生成：
  - 要約
  - 政策分類
  - 対象ユーザー
  - 背景課題
  - 戦略示唆（データ管理・可視化・意思決定）

---

## ビジネス価値

- 政策情報の横断的可視化
- 顧客理解の深化
- データドリブンな公共営業
- CRM導入余地の特定

---

## 本プロジェクトの特徴

- 非構造 → 構造化 → 意味付け → 戦略化まで一貫
- AIを「要約」ではなく「意思決定支援」に活用
- 実務を想定したデータ設計

---

## 強み

- 非構造データを制度単位に分解
- AIで意味付けし戦略情報へ変換
- データ → 業務 → 意思決定まで接続

→ 単なる分析ではなく、事業開発に直結するアウトプット

---

## 実行方法

### 1. 環境構築

```bash
pip install requests beautifulsoup4 openai
```

---

### 2. APIキー設定

```bash
export OPENAI_API_KEY="your-api-key"
```

---

### 3. 実行

```bash
python main.py
```

---

## 今後の展望

- 他自治体への横展開
- 時系列データの蓄積
- BIツールとの連携
- Salesforceとの接続

---

## 一言まとめ

公共機関の非構造情報を収集し、制度単位に構造化した上で、AIにより営業・戦略判断に活用可能なデータへ変換するPoCを構築しました。

---

## 本プロジェクトの本質

本取り組みは単なるAI活用ではなく、

**「AIが使える形に情報を変換する仕組みの構築」**

に主眼を置いています。
