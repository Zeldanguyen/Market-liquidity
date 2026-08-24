"""
Dashboard 6 lop trach nhiem dong chay von toan cau.
Tong mau: den + xanh la. Crypto va Ty gia real-time qua JS phia trinh duyet.
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


def get_equity(finnhub_data, key, label):
    items = finnhub_data.get("equities", {})
    quote = items.get(key)
    if not isinstance(quote, dict) or "c" not in quote:
        return '<div class="tick"><div class="tick-label">' + label + '</div><div class="tick-val">-</div></div>'
    price = quote.get("c", "-")
    dp = quote.get("dp", 0)
    if not isinstance(dp, (int, float)):
        dp = 0
    direction = "up" if dp >= 0 else "down"
    arrow = "&#9650;" if direction == "up" else "&#9660;"
    return tick(label, price, arrow + " " + format(dp, ".2f") + "%", direction)


def render_layer0(fred_data, finnhub_data):
    return get_equity(finnhub_data, "dollar_etf", "USD (DXY proxy)") + get_equity(finnhub_data, "vix_etf", "VIX (rui ro thi truong)")


def render_layer3_flows(finnhub_data, vnstock_data):
    html = get_equity(finnhub_data, "vietnam_etf", "VN ETF (von ngoai)")
    html += get_equity(finnhub_data, "sp500_etf", "S&P500 ETF (dong chinh)")

    foreign = vnstock_data.get("foreign_flow", {})
    if foreign.get("status") == "ok":
        rows = foreign.get("data", [])
        if rows:
            latest = rows[-1]
            summary = ", ".join([f"{k}: {v}" for k, v in latest.items()])
            html += '<div class="tick wide"><div class="tick-label">Khoi ngoai VN (moi nhat)</div><div class="tick-val small">' + summary + '</div></div>'
    else:
        html += '<div class="tick wide"><div class="tick-label">Khoi ngoai VN mua/ban rong</div><div class="empty-inline">Chua lay duoc du lieu tu vnstock - dang can tra lai ten ham API</div></div>'
    return html


def render_top_stocks(vnstock_data):
    stocks = vnstock_data.get("top_stocks", [])
    if not stocks:
        return '<div class="empty">Chua co du lieu.</div>'
    rows = []
    for s in stocks:
        symbol = s.get("symbol", "-")
        if s.get("status") != "ok":
            rows.append(tick(symbol, "N/A"))
            continue
        close_price = s.get("close", s.get("Close", "-"))
        rows.append(tick(symbol, close_price))
    return "".join(rows)


def render_vnindex(vnstock_data):
    hist = vnstock_data.get("vnindex_history", [])
    if not hist:
        return '<div class="empty">Chua co du lieu VN-Index.</div>'
    latest = hist[-1]
    rows = ""
    for k, v in latest.items():
        rows += '<div class="row"><span>' + str(k) + '</span><span>' + str(v) + '</span></div>'
    return '<div class="box">' + rows + '</div>'


def render_news(news_data, layer_keywords):
    """Loc tin tuc theo tu khoa cua tung lop neu co, khong thi hien tat ca"""
    feeds = news_data.get("feeds", {})
    rows = []
    for source, items in feeds.items():
        for item in items[:3]:
            if "error" in item:
                continue
            title = item.get("title", "")
            link = item.get("link", "#")
            rows.append('<div class="news-item"><div class="news-src">' + source + '</div><a class="news-headline" href="' + link + '" target="_blank" rel="noopener">' + title + '</a></div>')
    return "".join(rows) if rows else '<div class="empty">Chua co tin tuc.</div>'


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
      badge.textContent = "LIVE - " + new Date().toLocaleTimeString("vi-VN");
    })
    .catch(function(err) { badge.textContent = "Loi: " + err.message; });
}

function loadLiveFx() {
  var el = document.getElementById("fx-grid");
  var badge = document.getElementById("fx-live-badge");
  fetch("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json")
    .then(function(res) { if (!res.ok) throw new Error("HTTP " + res.status); return res.json(); })
    .then(function(data) {
      var rates = data.usd || {};
      var html = "";
      for (var code in FX_LABELS) {
        var val = rates[code];
        if (typeof val !== "number") continue;
        html += tickHtml(FX_LABELS[code], val.toLocaleString(undefined, {maximumFractionDigits: 2}), null, null);
      }
      if (html) { el.innerHTML = html; badge.textContent = "LIVE - " + new Date().toLocaleTimeString("vi-VN"); }
      else { throw new Error("rong"); }
    })
    .catch(function() {
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
          badge.textContent = "LIVE (du phong) - " + new Date().toLocaleTimeString("vi-VN");
        })
        .catch(function(err2) { badge.textContent = "Loi: " + err2.message; });
    });
}

window.addEventListener("DOMContentLoaded", function() { loadLiveCrypto(); loadLiveFx(); });
</script>
"""


def main():
    finnhub = load_json("finnhub.json")
    vnstock = load_json("vnstock.json")
    news = load_json("news.json")

    now_vn = datetime.now(VN_TZ).strftime("%H:%M, %d/%m/%Y (ICT)")

    layer0_html = render_layer0({}, finnhub)
    layer3_html = render_layer3_flows(finnhub, vnstock)
    top_stocks_html = render_top_stocks(vnstock)
    vnindex_html = render_vnindex(vnstock)
    news_html = render_news(news, [])

    style = (
        ":root{--bg:#050807;--panel:#0D1410;--line:#1C2A22;--text:#E4F0E8;--muted:#7C9587;"
        "--green:#3ECF7A;--green-dim:#1F5C3C;--red:#D9534F;}"
        "*{box-sizing:border-box;}"
        "body{margin:0;background:var(--bg);color:var(--text);"
        "font-family:-apple-system,'Segoe UI',Arial,sans-serif;}"
        ".wrap{max-width:1280px;margin:0 auto;padding:28px 22px 70px;}"
        "header{display:flex;justify-content:space-between;align-items:baseline;"
        "border-bottom:1px solid var(--green-dim);padding-bottom:16px;margin-bottom:24px;flex-wrap:wrap;gap:10px;}"
        "h1{font-size:22px;margin:0;color:var(--green);letter-spacing:0.01em;}"
        ".updated{font-family:monospace;font-size:11.5px;color:var(--muted);}"
        ".layer{border:1px solid var(--line);border-radius:6px;margin-bottom:22px;overflow:hidden;}"
        ".layer-head{background:var(--panel);padding:14px 18px;border-bottom:1px solid var(--line);"
        "display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;}"
        ".layer-num{font-family:monospace;color:var(--green);font-size:11px;letter-spacing:0.08em;}"
        ".layer-title{font-size:16px;font-weight:600;margin-top:2px;}"
        ".layer-desc{font-size:11.5px;color:var(--muted);margin-top:2px;}"
        ".layer-badge{font-family:monospace;font-size:10px;color:var(--green);"
        "background:rgba(62,207,122,0.1);padding:3px 8px;border-radius:3px;}"
        ".layer-body{padding:16px 18px;}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);}"
        ".tick{background:var(--bg);padding:13px;}"
        ".tick.wide{grid-column:1/-1;}"
        ".tick-label{font-family:monospace;font-size:9.5px;color:var(--muted);text-transform:uppercase;letter-spacing:0.04em;margin-bottom:6px;}"
        ".tick-val{font-family:monospace;font-size:16px;font-weight:700;color:var(--text);}"
        ".tick-val.small{font-size:11px;font-weight:400;color:var(--muted);}"
        ".tick-chg{font-family:monospace;font-size:11px;margin-top:3px;}"
        ".up{color:var(--green);} .down{color:var(--red);}"
        ".empty{color:var(--muted);font-family:monospace;font-size:11.5px;padding:12px 0;}"
        ".empty-inline{color:var(--muted);font-family:monospace;font-size:11px;}"
        ".box{background:var(--bg);border:1px solid var(--line);padding:14px;}"
        ".row{display:flex;justify-content:space-between;padding:5px 0;font-family:monospace;font-size:12px;color:var(--muted);border-bottom:1px solid var(--line);}"
        ".row:last-child{border:none;}"
        ".news-item{padding:11px 0;border-bottom:1px solid var(--line);}"
        ".news-item:last-child{border:none;}"
        ".news-src{font-family:monospace;font-size:10px;color:var(--green);margin-bottom:4px;}"
        ".news-headline{color:var(--text);text-decoration:none;font-size:13px;line-height:1.5;}"
        ".news-headline:hover{color:var(--green);}"
        ".live-badge{font-family:monospace;font-size:10px;color:var(--green);}"
        "footer{margin-top:36px;padding-top:16px;border-top:1px solid var(--line);"
        "font-family:monospace;font-size:10.5px;color:var(--muted);line-height:1.8;}"
        ".disclaimer{background:var(--panel);border:1px solid var(--line);padding:12px 16px;"
        "font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:22px;border-radius:6px;}"
        ".disclaimer b{color:var(--green);}"
        ".flow-arrow{text-align:center;color:var(--green-dim);font-size:20px;padding:4px 0;font-family:monospace;}"
    )

    parts = []
    parts.append('<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    parts.append('<title>Mat Xich Von</title><style>' + style + '</style></head><body>')
    parts.append('<div class="wrap">')
    parts.append('<header><h1>MAT XICH VON — He thong luan chuyen von toan cau</h1>')
    parts.append('<div class="updated">Nen: ' + now_vn + ' (30 phut) | Crypto/Ty gia: real-time</div></header>')

    parts.append('<div class="disclaimer"><b>Cau truc:</b> Trang nay theo doi dong tien theo 6 lop trach nhiem, tu noi tien duoc tao ra (Fed) den nha dau tu ca nhan VN. Khong phai khuyen nghi dau tu duoc dam bao loi nhuan.</div>')

    # LOP 0
    parts.append('<div class="layer"><div class="layer-head"><div><div class="layer-num">LOP 0 — TAO TIEN</div><div class="layer-title">Ngan hang Trung uong (Fed)</div><div class="layer-desc">Dat lai suat, quyet dinh thanh khoan goc cho toan he thong</div></div><div class="layer-badge">LIVE</div></div>')
    parts.append('<div class="layer-body"><div class="grid">' + layer0_html + '</div></div></div>')
    parts.append('<div class="flow-arrow">&#8595;</div>')

    # LOP 1-2
    parts.append('<div class="layer"><div class="layer-head"><div><div class="layer-num">LOP 1-2 — PHAN PHOI & DU TRU QUOC GIA</div><div class="layer-title">Thi truong Repo, NHTW cac nuoc</div><div class="layer-desc">Thanh khoan lien ngan hang, dong USD toan cau</div></div><div class="layer-badge">LIVE</div></div>')
    parts.append('<div class="layer-body"><div class="grid">' + get_equity(finnhub, "china_etf", "Trung Quoc (proxy)") + get_equity(finnhub, "japan_etf", "Nhat Ban (proxy)") + get_equity(finnhub, "gold_etf", "Vang (du tru)") + '</div>')
    parts.append('<h3 style="margin-top:16px;color:var(--muted);font-size:11px;font-family:monospace;text-transform:uppercase;">Ty gia (real-time) <span class="live-badge" id="fx-live-badge">Dang tai...</span></h3>')
    parts.append('<div class="grid" id="fx-grid"><div class="empty">Dang tai...</div></div></div></div>')
    parts.append('<div class="flow-arrow">&#8595;</div>')

    # LOP 3
    parts.append('<div class="layer"><div class="layer-head"><div><div class="layer-num">LOP 3 — VON TO CHUC</div><div class="layer-title">Quy dau tu, ETF, khoi ngoai VN</div><div class="layer-desc">Noi tien "chon loc" tai san se chay vao dau</div></div><div class="layer-badge">MOT PHAN</div></div>')
    parts.append('<div class="layer-body"><div class="grid">' + layer3_html + '</div></div></div>')
    parts.append('<div class="flow-arrow">&#8595;</div>')

    # LOP 4
    parts.append('<div class="layer"><div class="layer-head"><div><div class="layer-num">LOP 4 — VON THUONG MAI</div><div class="layer-title">FDI, kieu hoi vao Viet Nam</div><div class="layer-desc">Dong tien thuc, cham nhung ben vung</div></div><div class="layer-badge">CHUA CO DATA</div></div>')
    parts.append('<div class="layer-body"><div class="empty">Chua co nguon mien phi tu dong cho FDI/kieu hoi real-time. Can cap nhat thu cong theo bao cao Tong cuc Thong ke hang thang/quy.</div></div></div>')
    parts.append('<div class="flow-arrow">&#8595;</div>')

    # LOP 5
    parts.append('<div class="layer"><div class="layer-head"><div><div class="layer-num">LOP 5 — NHA DAU TU CA NHAN</div><div class="layer-title">Crypto, VN-Index, co phieu ban le</div><div class="layer-desc">Phan ung nhanh nhat, thuong la chi bao tam ly xac nhan xu huong</div></div><div class="layer-badge">LIVE</div></div>')
    parts.append('<div class="layer-body">')
    parts.append('<h3 style="color:var(--muted);font-size:11px;font-family:monospace;text-transform:uppercase;">Crypto <span class="live-badge" id="crypto-live-badge">Dang tai...</span></h3>')
    parts.append('<div class="grid" id="crypto-grid"><div class="empty">Dang tai...</div></div>')
    parts.append('<h3 style="margin-top:18px;color:var(--muted);font-size:11px;font-family:monospace;text-transform:uppercase;">VN-Index</h3>')
    parts.append(vnindex_html)
    parts.append('<h3 style="margin-top:18px;color:var(--muted);font-size:11px;font-family:monospace;text-transform:uppercase;">Top 10 co phieu von hoa lon</h3>')
    parts.append('<div class="grid">' + top_stocks_html + '</div>')
    parts.append('</div></div>')

    # TIN TUC
    parts.append('<div class="layer"><div class="layer-head"><div><div class="layer-title">Tin tuc lien quan</div></div></div><div class="layer-body">' + news_html + '</div></div>')

    parts.append('<footer>Nguon: FRED - Finnhub - CoinGecko - vnstock - fawazahmed0/currency-api - RSS<br>He thong chay tu dong qua GitHub Actions moi 30 phut.</footer>')
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
