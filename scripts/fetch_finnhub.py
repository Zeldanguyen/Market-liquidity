"""
Lấy dữ liệu crypto từ CoinGecko — MIỄN PHÍ (10.000 credit/tháng, cần key Demo)
Đăng ký tại: https://www.coingecko.com/en/api
"""
import os
import json
import urllib.request
from datetime import datetime

COINGECKO_KEY = os.environ.get("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3"

COINS = ["bitcoin", "ethereum", "solana"]


def fetch_prices():
    ids = ",".join(COINS)
    url = f"{BASE_URL}/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
    headers = {}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def fetch_global():
    url = f"{BASE_URL}/global"
    headers = {}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def main():
    result = {
        "fetched_at": datetime.utcnow().isoformat(),
        "prices": fetch_prices(),
        "global_market": fetch_global(),
    }
    os.makedirs("data", exist_ok=True)
    with open("data/crypto.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Đã ghi data/crypto.json")


if __name__ == "__main__":
    main()
