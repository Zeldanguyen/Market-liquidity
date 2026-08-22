"""
Lay ty gia JPY, CNY, VND qua exchangerate.host - MIEN PHI, khong can API key
"""
import os
import json
import urllib.request
from datetime import datetime

BASE_URL = "https://api.exchangerate.host/latest"


def fetch_rates():
    url = f"{BASE_URL}?base=USD&symbols=JPY,CNY,VND,EUR"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def main():
    result = {
        "fetched_at": datetime.utcnow().isoformat(),
        "rates": fetch_rates(),
    }
    os.makedirs("data", exist_ok=True)
    with open("data/fx.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Da ghi data/fx.json")


if __name__ == "__main__":
    main()
