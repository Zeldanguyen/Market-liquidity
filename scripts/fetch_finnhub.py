"""
Lay du lieu chung khoan/FX toan cau tu Finnhub - MIEN PHI (~60 request/phut)
"""
import os
import sys
import json
import traceback
import urllib.request
import urllib.error
from datetime import datetime

FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")
BASE_URL = "https://finnhub.io/api/v1"

SYMBOLS = {
    "sp500_etf": "SPY",
    "dow_etf": "DIA",
    "nasdaq_etf": "QQQ",
    "gold_etf": "GLD",
    "oil_etf": "USO",
    "dollar_etf": "UUP",
    "vix_etf": "VXX",
    "china_etf": "FXI",
    "japan_etf": "EWJ",
    "vietnam_etf": "VNM",
}


def fetch_quote(symbol):
    url = f"{BASE_URL}/quote?symbol={symbol}&token={FINNHUB_KEY}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"HTTPError cho {symbol}: {e.code} - {body}")
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        print(f"Loi khac cho {symbol}: {repr(e)}")
        return {"error": str(e)}


def main():
    print(f"FINNHUB_KEY co ton tai: {bool(FINNHUB_KEY)}")
    print(f"Do dai key: {len(FINNHUB_KEY)}")

    result = {"fetched_at": datetime.utcnow().isoformat(), "equities": {}}

    if not FINNHUB_KEY:
        result["status"] = "skipped_missing_key"
        print("KHONG CO KEY - bo qua fetch")
    else:
        result["status"] = "ok"
        for name, symbol in SYMBOLS.items():
            print(f"Dang fetch {name} ({symbol})...")
            result["equities"][name] = fetch_quote(symbol)

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "finnhub.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"DA GHI XONG: {out_path}")
    print(f"File co ton tai sau khi ghi: {os.path.exists(out_path)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("LOI NGHIEM TRONG - traceback day du:")
        traceback.print_exc()
        # Van co gang ghi file de khong lam gian doan workflow
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "finnhub.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "fatal_error"}, f)
        sys.exit(0)
