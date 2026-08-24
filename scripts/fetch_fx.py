"""
Lay ty gia JPY, CNY, VND, EUR - MIEN PHI, khong can API key.
Nguon chinh: fawazahmed0/currency-api qua CDN jsDelivr (bao gom VND).
Nguon du phong: cung du an nhung host qua Cloudflare Pages, dung khi jsDelivr bi cham/loi.
"""
import os
import sys
import json
import traceback
import urllib.request
import urllib.error
from datetime import datetime

PRIMARY_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
FALLBACK_URL = "https://latest.currency-api.pages.dev/v1/currencies/usd.json"

TARGET_CODES = ["jpy", "cny", "vnd", "eur"]


def fetch_from(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            data = json.loads(raw)
            rates = data.get("usd", {})
            if not rates:
                print(f"Canh bao: {url} tra ve du lieu rong (khong co key 'usd')")
                return None
            return rates
    except urllib.error.HTTPError as e:
        print(f"HTTPError khi goi {url}: {e.code}")
        return None
    except urllib.error.URLError as e:
        print(f"URLError khi goi {url}: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"Loi parse JSON tu {url}: {e}")
        return None
    except Exception as e:
        print(f"Loi khong xac dinh khi goi {url}: {repr(e)}")
        return None


def fetch_rates():
    print(f"Dang thu nguon chinh: {PRIMARY_URL}")
    rates = fetch_from(PRIMARY_URL)
    if rates:
        print("Nguon chinh thanh cong.")
        return rates, "primary"

    print(f"Nguon chinh that bai, thu nguon du phong: {FALLBACK_URL}")
    rates = fetch_from(FALLBACK_URL)
    if rates:
        print("Nguon du phong thanh cong.")
        return rates, "fallback"

    print("CA HAI NGUON DEU THAT BAI.")
    return {}, "failed"


def main():
    all_rates, source_used = fetch_rates()

    # Chi giu lai cac ma tien can dung, tranh file qua nang (nguon co ~200 dong tien)
    filtered = {}
    for code in TARGET_CODES:
        val = all_rates.get(code)
        if isinstance(val, (int, float)):
            filtered[code] = val
        else:
            print(f"Thieu hoac sai kieu du lieu cho ma: {code}")

    result = {
        "fetched_at": datetime.utcnow().isoformat(),
        "source_used": source_used,
        "status": "ok" if filtered else "error",
        "rates": filtered,
    }

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "fx.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"DA GHI: {out_path}")
    print(f"Noi dung: status={result['status']}, source={source_used}, so ma tien lay duoc={len(filtered)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("LOI NGHIEM TRONG - traceback day du:")
        traceback.print_exc()
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "fx.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "fatal_error"}, f)
        sys.exit(0)
