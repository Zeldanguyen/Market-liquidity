"""
Lay du lieu crypto tu CoinGecko - MIEN PHI (10.000 credit/thang, can key Demo)
Bao gom: BTC, BNB va cac token lon dai dien he sinh thai Ethereum
"""
import os
import json
import urllib.request
from datetime import datetime

COINGECKO_KEY = os.environ.get("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3"

COINS = {
    # Tai san goc
    "bitcoin": "Bitcoin",
    "binancecoin": "BNB",
    # He sinh thai Ethereum - lop nen
    "ethereum": "Ethereum (ETH)",
    # Layer 2 tren Ethereum
    "arbitrum": "Arbitrum",
    "optimism": "Optimism",
    "matic-network": "Polygon",
    # DeFi lon nhat tren Ethereum
    "uniswap": "Uniswap",
    "chainlink": "Chainlink",
    "aave": "Aave",
    "maker": "Maker (Sky)",
    "lido-dao": "Lido DAO",
    # Token dang chu y khac tren ETH
    "shiba-inu": "Shiba Inu",
    "pepe": "Pepe",
    # Layer 1 khac de doi chieu
    "solana": "Solana",
}


def fetch_prices():
    ids = ",".join(COINS.keys())
    url = f"{BASE_URL}/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
    headers = {}
    if COINGECKO_KEY:
        headers["x-cg-demo-api-key"] = COINGECKO_KEY
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
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
        "coin_labels": COINS,
        "prices": fetch_prices(),
        "global_market": fetch_global(),
    }
    os.makedirs("data", exist_ok=True)
    with open("data/crypto.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Da ghi data/crypto.json")


if __name__ == "__main__":
    main()
