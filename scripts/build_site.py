"""
Đọc toàn bộ dữ liệu trong data/*.json và dựng thành trang HTML tĩnh
để publish qua GitHub Pages (thư mục /docs).
"""
import json
import os
from datetime import datetime, timezone, timedelta

DATA_DIR = "data"
OUTPUT_DIR = "docs"

VN_TZ = timezone(timedelta(hours=7))


def load_json(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return {"status": "missing"}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_news_html(news_data):
    rows = []
    for source, items in news_data.get("feeds", {}).items():
        for item in items[:4]:
            if "error" in item:
                continue
            title = item.get("title", "")
            link = item.get("link", "#")
            rows.append(f'''
            <div class="news-item">
              <div class="news-src">{source}</div>
              <a class="news-headline" href="{link}" target="_blank" rel="noopener">{title}</a>
            </div>''')
    return "\n".join(rows) if rows else '<div class="empty">Chưa có dữ liệu tin tức — kiểm tra lại nguồn RSS.</div>'


def render_equities_html(finnhub_data):
    rows = []
    for name, quote in finnhub_data.get("equities", {}).items():
        if not isinstance(quote, dict) or "c" not in quote:
            continue
        price = quote.get("c", "—")
        change_pct = quote.get("dp", 0)
        direction = "up" if isinstance(change_pct, (int, float)) and change_pct >= 0 else "down"
        arrow = "▲" if direction == "up" else "▼"
        rows.append(f'''
          <div class="tick">
            <div class="tick-label">{name.replace("_", " ").upper()}</div>
            <div class="tick-val">{price}</div>
            <div class="tick-chg {direction}">{arrow} {change_pct}%</div>
          </div>''')
    return "\n".join(rows) if rows else '<div class="empty">Chưa có dữ liệu chỉ số — kiểm tra FINNHUB_API_KEY.</div>'


def render_crypto_html(crypto_data):
    prices = crypto_data.get("prices", {})
    rows = []
    for coin, vals in prices.items():
        if not isinstance(vals, dict):
            continue
        usd = vals.get("usd", "—")
        chg = vals.get("usd_24h_change", 0)
        direction = "up" if isinstance(chg, (int, float)) and chg >= 0 else "down"
        arrow = "▲" if direction == "up" else "▼"
        rows.append(f'''
          <div class="tick">
            <div class="tick-label">{coin.upper()}</div>
            <div class="tick-val">${usd:,.0f}</div>
            <div class="tick-chg {direction}">{arrow} {chg:.2f}%</div>
          </div>''' if isinstance(usd, (int, float)) else "")
    return "\n".join(rows) if rows else '<div class="empty">Chưa có dữ liệu crypto — kiểm tra COINGECKO_API_KEY.</div>'


def main():
    fred = load_json("fred.json")
    finnhub = load_json("finnhub.json")
    crypto = load_json("crypto.json")
    vnstock = load_json("vnstock.json")
    news = load_json("news.json")

    now_vn = datetime.now(VN_TZ).strftime("%A, %d/%m/%Y %H:%M ICT")

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mắt Xích Vốn — Cập nhật {now_vn}</title>
<style>
  :root{{--ink:#0A0F1A;--panel:#111826;--line:#232D40;--text:#E7EAF0;--muted:#8B96A8;
  --gold:#CDA349;--jade:#3AA57C;--red:#C1544A;
  --serif:Georgia,serif;--mono:ui-monospace,Menlo,Consolas,monospace;--sans:-apple-system,"Segoe UI",Arial,sans-serif;}}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:var(--ink);color:var(--text);font-family:var(--sans);}}
  .wrap{{max-width:1200px;margin:0 auto;padding:28px 22px 60px;}}
  header{{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:26px;display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px;}}
  h1{{font-family:var(--serif);font-size:22px;margin:0;}}
  .updated{{font-family:var(--mono);font-size:11px;color:var(--muted);}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin-bottom:32px;}}
  .tick{{background:var(--panel);padding:14px;}}
  .tick-label{{font-family:var(--mono);font-size:10px;color:var(--muted);text-transform:uppercase;margin-bottom:6px;}}
  .tick-val{{font-family:var(--mono);font-size:16px;font-weight:600;}}
  .tick-chg{{font-family:var(--mono);font-size:11px;margin-top:3px;}}
  .up{{color:var(--jade);}}
