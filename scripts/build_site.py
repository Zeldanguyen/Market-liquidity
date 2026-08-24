"""
Doc du lieu tu data/*.json va dung thanh trang HTML tinh phong cach dashboard.
Crypto va Ty gia duoc bo sung JS goi truc tiep API luc trinh duyet tai trang (F5 la nhay so).
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
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tick(label, val, chg_str=None, direction=None):
    chg_html = ""
    if chg_str is not None:
        cls = "up" if direction == "up" else "down"
        chg_html = '<div class="tick-chg ' + cls + '">' + chg_str + '</div>'
    return '<div class="tick"><div class="tick-label">' + label + '</div><div class="tick-val">' + str(val) + '</div>' + chg_html + '</div>'


def render_equities(finnhub_data):
    items = finnhub_data.get("equities", {})
    rows = []
    for name, quote in items.items():
        if not isinstance(quote, dict) or "c" not in quote:
            continue
        price = quote.get("c", "-")
        dp = quote.get("dp", 0)
        if not isinstance(dp, (int, float)):
            dp = 0
        direction = "up" if dp >= 0 else "down"
        arrow = "&#9650;" if direction == "up" else "&#9660;"
        label = name.replace("_", " ").upper()
        rows.append(tick(label, price, arrow + " " + format(dp, ".2f") + "%", direction))
    return "".join(rows) if rows else '<div class="empty">Chua co du lieu.</div>'


def render_vnindex(vnstock_data):
    if vnstock_data.get("status") != "ok":
        return '<div class="empty">VN-Index dang cho du lieu (thu vien vnstock can kiem tra lai).</div>'
    hist = vnstock_data.get("vnindex_history", [])
    if not hist:
        return '<div class="empty">Chua co du lieu VN-Index.</div>'
    latest = hist[-1]
    rows = ""
    for k, v in latest.items():
        rows += '<div class="vn-row"><span>' + str(k) + '</span><span>' + str(v) + '</span></div>'
    return '<div class="vn-box">' + rows + '</div>'


def render_top_stocks(vnstock_data):
    stocks = vnstock_data.get("top_stocks", [])
    if not stocks:
        return '<div class="empty">Chua co du lieu top co phieu.</div>'
    rows = []
    for s in stocks:
        symbol = s.get("symbol", "-")
        if s.get("status") != "ok":
            rows.append(tick(symbol, "N/A"))
            continue
        close_price = s.get("close", s.get("Close", "-"))
        rows.append(tick(symbol, close_price))
    return "".join(rows)


def render_news(news_data):
    feeds = news_data.get("feeds", {})
    rows = []
    for source, items in feeds.items():
        for item in items[:4]:
            if "error" in item:
                continue
            title = item.get("title", "")
            link = item.get("link", "#")
            rows.append(
                '<div class="news-item"><div class="news-src">' + source + '</div>'
                '<a class="news-headline" href="' + link + '" target="_blank" rel="noopener">' + title + '</a></div>'
            )
    return "".join(rows) if rows else '<div class="empty">Chua co tin tuc.</div>'


def render_module_status():
    modules = [
        ("Fed / FOMC", True), ("CPI / Lam phat", True), ("DXY & Loi suat", True),
        ("Vang", True), ("Dau (WTI/Brent qua ETF)", True), ("Dong (Copper)", True),
        ("JPY (real-time)", True), ("CNY (real-time)", True), ("USD/VND (real-time)", True),
        ("Chung khoan toan cau + top 10 co phieu VN", True), ("Trai phieu (loi suat qua FRED)", True),
        ("Crypto (real-time, BTC/BNB/he sinh thai ETH)", True),
        ("BDS (proxy qua ETF IYR, chua co du lieu VN rieng)", False),
        ("VIX", True), ("Lien ngan hang (SOFR)", False),
    ]
    rows = []
    for name, live in modules:
        status = "LIVE" if live else "SAP NOI"
        cls = "live" if live else "pending"
        rows.append('<div class="mod-row"><span>' + name + '</span><span class="mod-status ' + cls + '">' + status + '</span></div>')
    return "".join(rows)


LIVE_SCRIPT = """
<script>
var COIN_LABELS = {
  "bitcoin": "Bitcoin", "binancecoin": "BNB", "ethereum": "Ethereum (ETH)",
  "arbitrum": "Arbitrum", "optimism": "Optimism", "matic-network": "Polygon",
  "uniswap": "Uniswap", "chainlink": "Chainlink", "aave": "Aave",
  "maker": "Maker (Sky)", "lido-dao": "Lido DAO", "shiba-inu": "Shiba Inu",
  "pepe": "Pepe", "solana": "Solana"
};
var FX_LABELS = { "jpy": "USD/JPY", "cny": "USD/CNY", "vnd": "USD/VND", "eur": "USD/EUR" };

function tickHtml(label, val, chgStr, direction) {
  var cls = direction === "up" ? "up" : "down";
  var chgHtml = chgStr ? ('<div class="tick-chg ' + cls + '">' + chgStr + '</div>') : "";
  return '<div class="tick"><div class="tick-label">' + label + '</div><div class="tick-val">' + val + '</div>' + chgHtml + '</div>';
}

function loadLiveCrypto() {
  var el = document.getElementById("crypto-grid");
  var badge = document.getElementById("crypto-live-badge");
  var ids = Object.keys(COIN_LABELS).join(",");
  fetch("https://api.coingecko.com/api/v3/simple/price?ids=" + ids + "&vs_currencies=usd&include_24hr_change=true")
    .then(function(res) { return res.json(); })
    .then(function(data) {
      var html = "";
      for (var id in data) {
        var vals = data[id];
        if (!vals || typeof vals.usd !== "number") continue;
        var chg = typeof vals.usd_24h_change === "number" ? vals.usd_24h_change : 0;
        var direction = chg >= 0 ? "up" : "down";
        var arrow = direction === "up" ? "&#9650;" : "&#9660;";
        var priceStr;
        if (vals.usd < 1) { priceStr = "$" + vals.usd.toFixed(4); }
        else if (vals.usd < 100) { priceStr = "$" + vals.usd.toFixed(2); }
        else { priceStr = "$" + vals.usd.toLocaleString(undefined, {maximumFractionDigits: 0}); }
        html += tickHtml(COIN_LABELS[id] || id.toUpperCase(), priceStr, arrow + " " + chg.toFixed(2) + "%", direction);
      }
      if (html) el.innerHTML = html;
      badge.textContent = "LIVE - vua cap nhat luc " + new Date().toLocaleTimeString("vi-VN");
    })
    .catch(function(err) {
      badge.textContent = "Loi tai crypto: " + err.message;
    });
}

function loadLiveFx() {
  var el = document.getElementById("fx-grid");
  var badge = document.getElementById("fx-live-badge");
  fetch("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json")
    .then(function(res) {
      if (!res.ok) { throw new Error("HTTP " + res.status); }
      return res.json();
    })
    .then(function(data) {
      var rates = data.usd || {};
      var html = "";
      for (var code in FX_LABELS) {
        var val = rates[code];
        if (typeof val !== "number") continue;
        html += tickHtml(FX_LABELS[code], val.toLocaleString(undefined, {maximumFractionDigits: 2}), null, null);
      }
      if (html) {
        el.innerHTML = html;
        badge.textContent = "LIVE - vua cap nhat luc " + new Date().toLocaleTimeString("vi-VN");
      } else {
        throw new Error("Du lieu rong");
      }
    })
    .catch(function(err) {
      // Thu nguon du phong neu nguon chinh loi
      fetch("https://latest.currency-api.pages.dev/v1/currencies/usd.json")
        .then(function(res) { return res.json(); })
        .then(function(data) {
          var rates = data.usd || {};
          var html = "";
          for (var code in FX_LABELS) {
            var val = rates[code];
            if (typeof val !== "number") continue;
            html += tickHtml(FX_LABELS[code], val.toLocaleString(undefined, {maximumFractionDigits: 2}), null, null);
          }
          if (html) el.innerHTML = html;
          badge.textContent = "LIVE (nguon du phong) - " + new Date().toLocaleTimeString("vi-VN");
        })
        .catch(function(err2) {
          badge.textContent = "Loi tai ty gia: " + err2.message;
        });
    });
}

window.addEventListener("DOMContentLoaded", function() {
  loadLiveCrypto();
  loadLiveFx();
});
</script>
"""


def main():
    finnhub = load_json("finnhub.json")
    vnstock = load_json("vnstock.json")
    news = load_json("news.json")

    now_vn = datetime.now(VN_TZ).strftime("%H:%M, %d/%m/%Y (ICT)")

    equities_html = render_equities(finnhub)
    vnindex_html = render_vnindex(vnstock)
    top_stocks_html = render_top_stocks(vnstock)
    news_html = render_news(news)
    modules_html = render_module_status()

    style = (
        ":root{--ink:#0A0F1A;--panel:#111826;--line:#232D40;--text:#E7EAF0;--muted:#8B96A8;"
        "--gold:#CDA349;--jade:#3AA57C;--red:#C1544A;}"
        "*{box-sizing:border-box;}"
        "body{margin:0;background:var(--ink);color:var(--text);"
        "font-family:-apple-system,'Segoe UI',Arial,sans-serif;}"
        ".wrap{max-width:1240px;margin:0 auto;padding:30px 24px 70px;}"
        "header{display:flex;justify-content:space-between;align-items:baseline;"
        "border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:26px;flex-wrap:wrap;gap:10px;}"
        "h1{font-family:Georgia,serif;font-size:24px;margin:0;color:var(--text);}"
        ".updated{font-family:monospace;font-size:12px;color:var(--jade);}"
        "h2{font-family:Georgia,serif;font-size:19px;border-bottom:1px solid var(--line);"
        "padding-bottom:9px;margin-top:38px;color:var(--gold);display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;}"
        ".live-badge{font-family:monospace;font-size:10px;color:var(--jade);font-weight:normal;}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));"
        "gap:1px;background:var(--line);border:1px solid var(--line);}"
        ".tick{background:var(--panel);padding:15px;}"
        ".tick-label{font-family:monospace;font-size:10px;color:var(--muted);"
        "text-transform:uppercase;letter-spacing:0.04em;margin-bottom:7px;}"
        ".tick-val{font-family:monospace;font-size:17px;font-weight:700;}"
        ".tick-chg{font-family:monospace;font-size:11.5px;margin-top:4px;}"
        ".up{color:var(--jade);} .down{color:var(--red);}"
        ".empty{color:var(--muted);font-family:monospace;font-size:12px;padding:16px 0;}"
        ".news-item{padding:14px 0;border-bottom:1px solid var(--line);}"
        ".news-src{font-family:monospace;font-size:10.5px;color:var(--gold);margin-bottom:5px;"
        "letter-spacing:0.04em;}"
        ".news-headline{color:var(--text);text-decoration:none;font-size:14px;line-height:1.55;}"
        ".news-headline:hover{color:var(--gold);}"
        ".vn-box{background:var(--panel);border:1px solid var(--line);padding:18px;margin-bottom:20px;}"
        ".vn-row{display:flex;justify-content:space-between;padding:6px 0;"
        "font-family:monospace;font-size:12.5px;color:var(--muted);border-bottom:1px solid var(--line);}"
        ".vn-row:last-child{border:none;}"
        ".mod-row{display:flex;justify-content:space-between;align-items:center;"
        "padding:9px 0;border-bottom:1px solid var(--line);font-size:13px;}"
        ".mod-status{font-family:monospace;font-size:10px;letter-spacing:0.05em;"
        "padding:3px 9px;border-radius:2px;}"
        ".mod-status.live{background:rgba(58,165,124,0.15);color:var(--jade);}"
        ".mod-status.pending{background:var(--panel);color:var(--muted);}"
        "footer{margin-top:44px;padding-top:20px;border-top:1px solid var(--line);"
        "font-family:monospace;font-size:11px;color:var(--muted);line-height:1.8;}"
        ".disclaimer{background:var(--panel);border:1px solid var(--line);padding:14px 18px;"
        "font-size:12.5px;color:var(--muted);line-height:1.7;margin-bottom:28px;border-radius:4px;}"
        ".disclaimer b{color:var(--gold);}"
    )

    parts = []
    parts.append('<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append('<title>Mat Xich Von</title><style>' + style + '</style></head><body>')
    parts.append('<div class="wrap">')
    parts.append('<header>')
    parts.append('<h1>Mat Xich Von - Nhat ky dong chay von toan cau</h1>')
    parts.append('<div class="updated">Du lieu nen cap nhat luc ' + now_vn + ' (moi 30 phut)</div>')
    parts.append('</header>')

    parts.append(
        '<div class="disclaimer"><b>Luu y:</b> Crypto va Ty gia cap nhat '
        '<b>real-time moi lan ban tai lai trang (F5)</b>. Cac phan con lai '
        '(chi so CK, VN-Index, tin tuc) cap nhat theo chu ky tu dong '
        '30 phut/lan. Khong phai khuyen nghi dau tu duoc dam bao loi nhuan.</div>'
    )

    parts.append('<h2>Chi so toan cau (qua ETF dai dien, cap nhat 30ph)</h2>')
    parts.append('<div class="grid">' + equities_html + '</div>')

    parts.append('<h2>Ty gia <span class="live-badge" id="fx-live-badge">Dang tai real-time...</span></h2>')
    parts.append('<div class="grid" id="fx-grid"><div class="empty">Dang tai...</div></div>')

    parts.append('<h2>Crypto - BTC, BNB va he sinh thai Ethereum <span class="live-badge" id="crypto-live-badge">Dang tai real-time...</span></h2>')
    parts.append('<div class="grid" id="crypto-grid"><div class="empty">Dang tai...</div></div>')

    parts.append('<h2>VN-Index</h2>')
    parts.append(vnindex_html)

    parts.append('<h2>Top 10 co phieu von hoa lon nhat VN</h2>')
    parts.append('<div class="grid">' + top_stocks_html + '</div>')

    parts.append('<h2>Tin tuc moi nhat</h2>')
    parts.append(news_html)

    parts.append('<h2>Trang thai cac module theo doi</h2>')
    parts.append(modules_html)

    parts.append('<footer>')
    parts.append(
        'Nguon: FRED - Finnhub - CoinGecko - vnstock - fawazahmed0/currency-api - '
        'RSS (Reuters, CafeF, VnEconomy, Vietstock)<br>'
        'Crypto va Ty gia: goi truc tiep tu trinh duyet cua ban, khong qua may chu trung gian.'
    )
    parts.append('</footer>')
    parts.append('</div>')
    parts.append(LIVE_SCRIPT)
    parts.append('</body></html>')

    html = "".join(parts)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("Da dung " + OUTPUT_DIR + "/index.html")


if __name__ == "__main__":
    main()
