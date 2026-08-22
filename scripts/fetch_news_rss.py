"""
Lấy tin tức kinh tế qua RSS — MIỄN PHÍ, không cần API key
pip install feedparser
"""
import os
import json
from datetime import datetime

import feedparser

FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "CafeF": "https://cafef.vn/thi-truong-chung-khoan.rss",
    "VnEconomy": "https://vneconomy.vn/tai-chinh.rss",
    "Vietstock": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "Investing.com Economy": "https://www.investing.com/rss/news_14.rss",
}


def fetch_feed(name, url, limit=6):
    try:
        parsed = feedparser.parse(url)
        items = []
        for entry in parsed.entries[:limit]:
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", entry.get("updated", "")),
            })
        return items
    except Exception as e:
        return [{"error": str(e)}]


def main():
    result = {"fetched_at": datetime.utcnow().isoformat(), "feeds": {}}
    for name, url in FEEDS.items():
        result["feeds"][name] = fetch_feed(name, url)

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Đã ghi data/news.json")


if __name__ == "__main__":
    main()
