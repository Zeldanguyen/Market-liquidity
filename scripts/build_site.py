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
        chg_html = f'<div class="tick-chg {cls}">{chg_str}</div>'
    return f'<div class="tick"><div class="tick-label">{label}</div><div class="tick-val">{val}</div>{chg_html}</div>'


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
        rows.append(tick(name.replace("_", " ").upper(), price, f"{arrow} {dp:.2f}%", direction))
    return "".join(rows) if rows else '<div class="empty">Chua co du lieu.</div>'


def render_vnindex(vnstock_data):
    if vnstock_data.get("status") != "ok":
        return '<div class="empty">VN-Index dang cho du lieu (thu vien vnstock can kiem tra lai).</div>'
    hist = vnstock_data.get("vnindex_history", [])
    if not hist:
        return '<div class="empty">Chua co du lieu VN-Index.</div>'
    latest = hist[-1]
    rows = "".join([f'<div class="vn-row"><span>{k}</span><span>{v}</span></div>' for k, v in latest.items()])
    return f'<div class="vn-box">{rows}</div>'


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
                f'<div class="news-item"><div class="news-src">{source}</div>'
                f'<a class="news-headline" href="{link}" target="_blank" rel="noopener">{title}</a></div>'
            )
    return "".join(rows) if rows else '<div class="empty">Chua co tin tuc.</div>'


def render_module_status():
    modules = [
        ("Fed / FOMC", True), ("CPI / Lam phat", True), ("DXY & Loi suat", True),
        ("Vang", True), ("Dau (WTI/Brent qua ETF)", True), ("Dong (Copper)", True),
        ("JPY (real-time)", True), ("CNY (real-time)", True), ("USD/VND (real-time)", True),
        ("Chung khoan toan cau + VN", True), ("Trai phieu (loi suat qua FRED)", True),
        ("Crypto (real-time, BTC/BNB/he sinh thai ETH)", True),
        ("BDS (proxy qua ETF IYR, chua co du lieu VN rieng)", False),
        ("VIX", True), ("Lien ngan hang (SOFR)", False),
    ]
    rows = []
    for name, live in modules:
        status = "LIVE" if live else "SAP NOI"
        cls = "live" if live else "pending"
        rows.append(f'<div class="mod-row"><span>{name}</span><span class="mod-status {cls}">{status}</span></div>')
    return "".join(rows)


LIVE_SCRIPT = """
<script>
const COIN_LABELS = {
  "bitcoin": "Bitcoin", "binancecoin": "BNB", "ethereum": "Ethereum (ETH)",
  "arbitrum": "Arbitrum", "optimism": "Optimism", "matic-network": "Polygon",
  "uniswap": "Uniswap", "chainlink": "Chainlink", "aave": "Aave",
  "maker": "Maker (Sky)", "lido-dao": "Lido DAO", "shiba-inu": "Shiba Inu",
  "pepe": "Pepe", "solana": "Solana"
};
const FX_LABELS = { "JPY": "USD/JPY", "CNY": "USD/CNY", "VND": "USD/VND", "EUR": "USD/EUR" };

function tickHtml(label, val, chgStr, direction) {
  const cls = direction === "up" ? "up" : "down";
  const chgHtml = chgStr ? `<div class="tick-chg ${cls}">${chgStr}</div>` : "";
  return `<div class="tick"><div class="tick-label">${label}</div><div class="tick-val">${val}</div>${chgHtml}</div>`;
}

async function loadLiveCrypto() {
  const el = document.getElementById("crypto-grid");
  const ids = Object.keys(COIN_LABELS).join(",");
  try {
    const res = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true`);
    const data = await res.json();
    let html = "";
    for (const [id, vals] of Object.entries(data)) {
      if (!vals || typeof vals.usd !== "number") continue;
      const chg = typeof vals.usd_24h_change === "number" ? vals.usd_24h_change : 0;
      const direction = chg >= 0 ? "up" : "down";
      const arrow = direction === "up" ? "&#9650;" : "&#9660;";
      const priceStr = vals.usd < 1 ? `$${vals.usd.toFixed(4)}` : (vals.usd < 100 ? `$${vals.usd.toFixed(2)}` : `$${vals.usd.toLocaleString(undefined,{maximumFractionDigits:0})}`);
      html += tickHtml(COIN_LABELS[id] || id.toUpperCase(), priceStr, `${arrow} ${chg.toFixed(2)}%`, direction);
    }
    if (html) el.innerHTML = html;
    document.getElementById("crypto-live-badge").textContent = "LIVE - vua cap nhat luc " + new Date().toLocaleTimeString("vi-VN");
  } catch (e) {
    document.getElementById("crypto-live-badge").textContent = "Khong the tai du lieu real-time, dang hien ban du phong.";
  }
}

async function loadLiveFx() {
  const el = document.getElementById("fx-grid");
  try {
    const res = await fetch("https://api.exchangerate.host/latest?base=USD&symbols=JPY,CNY,VND,EUR");
    const data = await res.json();
    const rates = data.rates || {};
    let html = "";
    for (const [code, label] of Object.entries(FX_LABELS)) {
      const val = rates[code];
      if (typeof val !== "number") continue;
      html += tickHtml(label, val.toLocaleString(undefined,{maximumFractionDigits:2}), null, null);
    }
    if (html) el.innerHTML = html;
    document.getElementById("fx-live-badge").textContent = "LIVE - vua cap nhat luc " + new Date().toLocaleTimeString("vi-VN");
  } catch (e) {
    document.getElementById("fx-live-badge").textContent = "Khong the tai du lieu real-time, dang hien ban du phong.";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  loadLiveCrypto();
  loadLiveFx();
});
</script>
"""


def main():
    finnhub = load_json("finnhub.json")
    crypto = load_json("crypto.json")
    fx = load_json("fx.json")
    vnstock = load_json("vnstock.json")
    news = load_json("news.json")

    now_vn = datetime.now(VN_TZ).strftime("%H:%M, %d/%m/%Y (ICT)")

    equities_html = render_equities(finnhub)
    vnindex_html = render_vnindex(vnstock)
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
        ".vn-box{background:var(--panel);border:1px solid var(--line);padding:18px;}"
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
    parts.append(f'<title>M\u1eaft X\u00edch V\u1ed1n</title><style>{style}</style></head><body>')
    parts.append('<div class="wrap">')
    parts.append('<header>')
    parts.append('<h1>M\u1eaft X\u00edch V\u1ed1n \u2014 Nh\u1eadt k\u00fd d\u00f2ng ch\u1ea3y v\u1ed1n to\u00e0n c\u1ea7u</h1>')
    parts.append(f'<div class="updated">D\u1eef li\u1ec7u n\u1ec1n c\u1eadp nh\u1eadt l\u00fac {now_vn} (m\u1ed7i 30 ph\u00fat)</div>')
    parts.append('</header>')

    parts.append(
        '<div class="disclaimer"><b>L\u01b0u \u00fd:</b> Crypto v\u00e0 T\u1ef7 gi\u00e1 c\u1eadp nh\u1eadt '
        '<b>real-time m\u1ed7i l\u1ea7n b\u1ea1n t\u1ea3i l\u1ea1i trang (F5)</b>. C\u00e1c ph\u1ea7n c\u00f2n l\u1ea1i '
        '(ch\u1ec9 s\u1ed1 CK, VN-Index, tin t\u1ee9c) c\u1eadp nh\u1eadt theo chu k\u1ef3 t\u1ef1 \u0111\u1ed9ng '
        '30 ph\u00fat/l\u1ea7n do gi\u1edbi h\u1ea1n b\u1ea3o m\u1eadt API key v\u00e0 CORS. Kh\u00f4ng ph\u1ea3i '
        'khuy\u1ebfn ngh\u1ecb \u0111\u1ea7u t\u01b0 \u0111\u01b0\u1ee3c \u0111\u1ea3m b\u1ea3o l\u1ee3i nhu\u1eadn.</div>'
    )

    parts.append('<h2>Ch\u1ec9 s\u1ed1 to\u00e0n c\u1ea7u (qua ETF \u0111\u1ea1i di\u1ec7n, c\u1eadp nh\u1eadt 30ph)</h2>')
    parts.append(f'<div class="grid">{equities_html}</div>')

    parts.append('<h2>T\u1ef7 gi\u00e1 <span class="live-badge" id="fx-live-badge">\u0110ang t\u1ea3i real-time...</span></h2>')
    parts.append('<div class="grid" id="fx-grid"><div class="empty">\u0110ang t\u1ea3i...</div></div>')

    parts.append('<h2>Crypto \u2014 BTC, BNB v\u00e0 h\u1ec7 sinh th\u00e1i Ethereum <span class="live-badge" id="crypto-live-badge">\u0110ang t\u1ea3i real-time...</span></h2>')
    parts.append('<div class="grid" id="crypto-grid"><div class="empty">\u0110ang t\u1ea3i...</div></div>')

    parts.append('<h2>VN-Index</h2>')
    parts.append(vnindex_html)

    parts.append('<h2>Tin t\u1ee9c m\u1edbi nh\u1ea5t</h2>')
    parts.append(news_html)

    parts.append('<h2>Tr\u1ea1ng th\u00e1i c\u00e1c module theo d\u00f5i</h2>')
    parts.append(modules_html)

    parts.append('<footer>')
    parts.append(
        'Ngu\u1ed3n: FRED &middot; Finnhub &middot; CoinGecko &middot; vnstock &middot; '
        'exchangerate.host &middot; RSS (Reuters, CafeF, VnEconomy, Vietstock)<br>'
        'Crypto v\u00e0 T\u1ef7 gi\u00e1: g\u1ecdi tr\u1ef1c ti\u1ebfp t\u1eeb tr\u00ecnh duy\u1ec7t c\u1ee7a b\u1ea1n, '
        'kh\u00f4ng qua m\u00e1y ch\u1ee7 trung gian.'
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
