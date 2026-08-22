"""
Lấy dữ liệu chứng khoán Việt Nam qua thư viện vnstock (mã nguồn mở, miễn phí)
pip install vnstock
"""
import os
import json
from datetime import datetime, timedelta

def main():
    result = {"fetched_at": datetime.utcnow().isoformat(), "status": "ok"}
    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol="VNINDEX", source="VCI")
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        df = stock.quote.history(start=start, end=end, interval="1D")
        result["vnindex_history"] = df.tail(5).to_dict(orient="records")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["note"] = "Kiểm tra lại cú pháp vnstock — thư viện này cập nhật API khá thường xuyên, nên xem README mới nhất tại github.com/thinh-vu/vnstock nếu lỗi."

    os.makedirs("data", exist_ok=True)
    with open("data/vnstock.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("Đã ghi data/vnstock.json")


if __name__ == "__main__":
    main()
