"""
Doc toan bo du lieu trong data/*.json va dung thanh trang HTML tinh
de publish qua GitHub Pages (thu muc /docs).
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
            rows.append(f'<div class="news-item"><div class="news-src">{source}</div><a class="news-headline" href="{link}" target="_blank" rel="noopener">{title}</a></div>')
    return "\n".join(rows) if rows else '<div class="empty">Chua co du lieu tin tuc.</div>'


def render_equities_html(finnhub_data):
    rows = []
    for name, quote in finnhub_data.get("equities", {}).items():
        if not isinstance(quote, dict) or "c" not in quote:
            continue
        price = quote.get("c", "-")
        change_pct = quote.get("dp", 0)
        if not isinstance(change_pct, (int, float)):
            change_pct = 0
        direction = "up" if change_pct >= 0 else "down"
        arrow = "UP" if direction == "up" else "DOWN"
        rows.append(f'<div class="tick"><div class="tick-label">{name.replace("_"," ").upper()}</div><div class="tick-val">{price}</div><div class="tick-chg {direction}">{arrow} {change_pct}%</div></div>')
    return "\n".join(rows) if rows else '<div class="empty">Chua co du lieu chi so.</div>'


def render_crypto_html(crypto_data):
    prices = crypto_data.get("prices", {})
    labels = crypto_data.get("coin_labels", {})
    rows = []
    for coin_id, vals in prices.items():
        if not isinstance(vals, dict):
            continue
        usd = vals.get("usd", None)
        if not isinstance(usd, (int, float)):
            continue
        chg = vals.get("usd_24h_change", 0)
        if not isinstance(chg, (int, float)):
            chg = 0.0
        direction = "up" if chg >= 0 else "down"
        arrow = "UP" if direction == "up" else "DOWN"
        label = labels.get(coin_id, coin_id.upper())
        price_str = f"${usd:,.4f}" if usd < 1 else f"${usd:,.2f}" if usd < 100 else f"${usd:,.0f}"
        rows.append(f'<div class="tick"><div class="tick-label">{label}</div><div class="tick-val">{price_str}</div><div class="tick-chg {direction}">{arrow} {chg:.2f}%</div></div>')
    return "\n".join(rows) if rows else '<div class="empty">Chua co du lieu crypto.</div>'


def render_fx_html(fx_data):
    rates = fx_data.get("rates", {})
    r = rates.get("rates", {}) if isinstance(rates, dict) else {}
    if not r:
        return '<div class="empty">Chua co du lieu ty gia.</div>'
    rows = []
    labels = {"JPY": "USD/JPY", "CNY": "USD/CNY", "VND": "USD/VND", "EUR": "USD/EUR"}
    for code, label in labels.items():
        val = r.get(code)
        if not isinstance(val, (int, float)):
            continue
        rows.append(f'<div class="tick"><div class="tick-label">{label}</div><div class="tick-val">{val:,.2f}</div></div>')
    return "\n".join(rows) if rows else '<div class="empty">Chua co du lieu ty gia.</div>'


def render_vnstock_html(vnstock_data):
    if vnstock_data.get("status") != "ok":
        err = vnstock_data.get("error", "khong ro nguyen nhan")
        return f'<div class="empty">VN-Index: chua lay duoc du lieu ({err}). Thu vien vnstock hay doi cu phap, can kiem tra lai.</div>'
    hist = vnstock_data.get("vnindex_history", [])
    if not hist:
        return '<div class="empty">VN-Index: khong co du lieu lich su.</div>'
    latest = hist[-1]
    rows = "".join([f"<li>{k}: {v}</li>" for k, v in latest.items()])
    return f'<div class="tick" style="grid-column:1/-1;"><div class="tick-label">VN-INDEX (phien gan nhat)</div><ul style="margin:6px 0 0;padding-left:18px;font-size:12px;color:#8B96A8;">{rows}</ul></div>'


def main():
    finnhub = load_json("finnhub.json")
    crypto = load_json("crypto.json")
    news = load_json("news.json")
    fx = load_json("fx.json")
    vnstock = load_json("vnstock.json")

    now_vn = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M ICT")

    equities_html = render_equities_html(finnhub)
    crypto_html = render_crypto_html(crypto)
    news_html = render_news_html(news)
    fx_html = render_fx_html(fx)
    vnstock_html = render_vnstock_html(vnstock)

    style = "body{margin:0;background:#0A0F1A;color:#E7EAF0;font-family:Arial,sans-serif;} .wrap{max-width:1200px;margin:0 auto;padding:28px 22px;} h1{font-size:22px;} .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1px;background:#232D40;border:1px solid #232D40;margin-bottom:32px;} .tick{background:#111826;padding:14px;} .tick-label{font-size:10px;color:#8B96A8;text-transform:uppercase;margin-bottom:6px;} .tick-val{font-size:16px;font-weight:600;} .tick-chg{font-size:11px;margin-top:3px;} .up{color:#3AA57C;} .down{color:#C1544A;} h2{font-size:18px;border-bottom:1px solid #232D40;padding-bottom:8px;margin-top:36px;} .news-item{padding:12px 0;border-bottom:1px solid #232D40;} .news-src{font-size:10px;color:#CDA349;margin-bottom:4px;} .news-headline{color:#E7EAF0;text-decoration:none;font-size:13.5px;} .empty{color:#8B96A8;font-size:12px;padding:14px 0;}"

    html_parts = []
    html_parts.append("<!DOCTYPE html><html lang=\"vi\"><head><meta charset=\"UTF-8\">")
    html_parts.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
    html_parts.append("<title>Mat Xich Von</title><style>" + style + "</style></head><body>")
    html_parts.append("<div class=\"wrap\"><h1>Mat Xich Von - Nhat ky dong chay von toan cau</h1>")
    html_parts.append("<p>Cap nhat tu dong luc " + now_vn + "</p>")
    html_parts.append("<h2>Chi so toan cau (Finnhub) - gom ca Dong va BDS My</h2><div class=\"grid\">" + equities_html + "</div>")
    html_parts.append("<h2>Ty gia (JPY / CNY / VND / EUR)</h2><div class=\"grid\">" + fx_html + "</div>")
    html_parts.append("<h2>Crypto - BTC, BNB va he sinh thai Ethereum</h2><div class=\"grid\">" + crypto_html + "</div>")
    html_parts.append("<h2>VN-Index (vnstock)</h2><div class=\"grid\">" + vnstock_html + "</div>")
    html_parts.append("<h2>Tin tuc moi nhat</h2>" + news_html)
    html_parts.append("</div></body></html>")

    html = "".join(html_parts)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Da dung " + OUTPUT_DIR + "/index.html")


if __name__ == "__main__":
    main()
