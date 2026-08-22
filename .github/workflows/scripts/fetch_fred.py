"""
Lấy dữ liệu vĩ mô Mỹ từ FRED (Federal Reserve Economic Data) — MIỄN PHÍ
Đăng ký API key tại: https://fred.stlouisfed.org/docs/api/api_key.html
"""
import os
import json
import urllib.request
from datetime import datetime

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

SERIES = {
    "fed_funds_rate": "DFF",
    "cpi": "CPIAUCSL",
    "us_10y_yield": "DGS10",
    "us_2y_yield": "DGS2",
    "us_30y_yield": "DGS30",
    "dxy": "DTWEXBGS",
    "m2_money_supply": "M2SL",
    "real_yield_10y": "DFII10",
}


def fetch_series(series_id, limit=5):
    url = f"{BASE_URL}?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        obs = [o for o in data.get("observations", []) if o["value"] != "."]
        return obs
    except Exception as e:
        return {"error": str(e)}


def main():
    if not FRED_API_KEY:
        print("CẢNH BÁO: Thiếu FRED_API_KEY trong biến môi trường. Bỏ qua fetch FRED.")
        result = {"status": "skipped", "reason": "missing_api_key"}
    else:
        result = {"status": "ok", "fetched_at": datetime.utcnow().isoformat(), "series": {}}
        for name, series_id in SERIES.items():
            obs = fetch_series(series_id)
            result["series"][name] = obs

    os.makedirs("data", exist_ok=True)
    with open("data/fred.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Đã ghi data/fred.json")


if __name__ == "__main__":
    main()
