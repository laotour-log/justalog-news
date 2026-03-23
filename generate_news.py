import os
import re
import anthropic
import feedparser
from datetime import datetime

# ── 設定 ──────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
COUNT = 3  # 各カテゴリの記事数

FEEDS = {
    "ai": [
        "https://feeds.feedburner.com/venturebeat/SZYF",   # VentureBeat AI
        "https://techcrunch.com/feed/",                    # TechCrunch
    ],
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ],
    "gadget": [
        "https://feeds.feedburner.com/engadget",
        "https://www.theverge.com/rss/index.xml",
    ],
}

AI_KEYWORDS    = ["ai", "artificial intelligence", "llm", "gpt", "claude", "gemini", "openai", "machine learning", "chatgpt", "generative"]
TECH_KEYWORDS  = ["software", "app", "developer", "code", "tech", "google", "apple", "microsoft", "startup", "cloud"]
GADGET_KEYWORDS= ["gadget", "device", "smartphone", "iphone", "laptop", "camera", "headphone", "review", "hardware", "product"]

CATEGORY_KEYWORDS = {
    "ai": AI_KEYWORDS,
    "tech": TECH_KEYWORDS,
    "gadget": GADGET_KEYWORDS,
}

# ── RSS取得 ────────────────────────────────────────
def fetch_items(category):
    keywords = CATEGORY_KEYWORDS[category]
    items = []
    seen = set()
    for url in FEEDS[category]:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "")
                link  = entry.get("link", "")
                summary = entry.get("summary", entry.get("description", ""))
                if link in seen:
                    continue
                text = (title + " " + summary).lower()
                if any(k in text for k in keywords):
                    seen.add(link)
                    items.append({
                        "title": title,
                        "link": link,
                        "summary": summary[:500],
                        "date": entry.get("published", ""),
                    })
                if len(items) >= COUNT * 3:
                    break
        except Exception as e:
            print(f"RSS fetch error ({url}): {e}")
    return items[:COUNT]

# ── Claude API で日本語要約 ────────────────────────
def summarize(client, item):
    prompt = f"""以下の英語ニュース記事を日本語で要約してください。

タイトル: {item['title']}
内容: {item['summary']}

以下のJSON形式のみで返してください（前置き・説明不要）:
{{
  "title_ja": "日本語タイトル（40文字以内）",
  "summary_ja": "日本語要約（100文字以内）"
}}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text.strip()
        import json
        data = json.loads(text)
        return data.get("title_ja", item["title"]), data.get("summary_ja", "")
    except Exception as e:
        print(f"Claude API error: {e}")
        return item["title"], ""

# ── HTML生成 ───────────────────────────────────────
def make_featured(item, title_ja, summary_ja, date_str):
    return f"""<a class="featured-card" href="{item['link']}" target="_blank" rel="noopener noreferrer">
  <div class="featured-badge">Latest</div>
  <div class="featured-title">{title_ja}</div>
  <div class="featured-summary">{summary_ja}</div>
  <div class="featured-meta">
    <span class="featured-meta-tag">AI</span>
    <span>{date_str}</span>
  </div>
</a>"""

def make_article_item(index, item, title_ja, date_str):
    return f"""<a class="article-item" href="{item['link']}" target="_blank" rel="noopener noreferrer">
  <div class="article-num">0{index}</div>
  <div class="article-body">
    <div class="article-title">{title_ja}</div>
    <div class="article-meta">{date_str}</div>
  </div>
</a>"""

# ── HTMLファイル更新 ───────────────────────────────
def update_html(category, articles):
    path = f"{category}/index.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    today = datetime.now().strftime("%Y-%m-%d")

    # Featured（最新1件）
    featured_html = make_featured(
        articles[0]["item"],
        articles[0]["title_ja"],
        articles[0]["summary_ja"],
        today
    )
    html = re.sub(
        r'<!-- FEATURED_START -->.*?<!-- FEATURED_END -->',
        f'<!-- FEATURED_START -->\n  {featured_html}\n  <!-- FEATURED_END -->',
        html, flags=re.DOTALL
    )

    # 記事一覧（全件）
    items_html = "\n".join([
        make_article_item(i + 1, a["item"], a["title_ja"], today)
        for i, a in enumerate(articles)
    ])

    # 既存の記事リストを読み込んで先頭に追加
    existing_match = re.search(
        r'<!-- ARTICLES_START -->(.*?)<!-- ARTICLES_END -->',
        html, re.DOTALL
    )
    existing = existing_match.group(1).strip() if existing_match else ""

    # 記事リストを更新（新しいものを上に、最大30件まで保持）
    all_items = f'<div class="article-list">\n{items_html}\n</div>'
    html = re.sub(
        r'<!-- ARTICLES_START -->.*?<!-- ARTICLES_END -->',
        f'<!-- ARTICLES_START -->\n  {all_items}\n  <!-- ARTICLES_END -->',
        html, flags=re.DOTALL
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Updated: {path}")

# ── メイン ────────────────────────────────────────
def main():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    for category in ["ai", "tech", "gadget"]:
        print(f"\n=== {category.upper()} ===")
        items = fetch_items(category)
        if not items:
            print("記事が取得できませんでした")
            continue

        articles = []
        for item in items:
            print(f"処理中: {item['title'][:50]}...")
            title_ja, summary_ja = summarize(client, item)
            articles.append({
                "item": item,
                "title_ja": title_ja,
                "summary_ja": summary_ja,
            })

        update_html(category, articles)

if __name__ == "__main__":
    main()
