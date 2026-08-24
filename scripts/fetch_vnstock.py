"""
Lay VN-Index, top 10 co phieu, va khoi ngoai mua/ban rong qua vnstock.
Co gian cach 3.5s giua moi request de tranh vuot gioi han 20 req/phut cua goi mien phi.
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime, timedelta

TOP_TICKERS = ["VCB", "VIC", "VHM", "HPG", "FPT", "GAS", "MSN", "MWG", "TCB", "VPB"]
SLEEP_SECONDS = 3.5  # 60s / 20 req = 3s toi thieu, them bien de an toan


def safe_sleep():
    time.sleep(SLEEP_SECONDS)


def fetch_one_ticker(vn, symbol, start, end):
    try:
        print(f"  Dang lay {symbol}...")
        stock_obj = vn.stock(symbol=symbol, source="VCI")
        df = stock_obj.quote.history(start=start, end=end, interval="1D")
        safe_sleep()
        if df is None or len(df) == 0:
            return {"symbol": symbol, "status": "no_data"}
        latest = df.tail(1).to_dict(orient="records")[0]
        latest["symbol"] = symbol
        latest["status"] = "ok"
        print(f"  {symbol}: OK")
        return latest
    except Exception as e:
        print(f"  {symbol}: LOI - {repr(e)}")
        safe_sleep()
        return {"symbol": symbol, "status": "error", "error": str(e)}


def fetch_foreign_flow(vn, symbol="VNINDEX"):
    """
    Lay du lieu khoi ngoai mua/ban rong. Thu vien vnstock hay doi ten ham,
    nen thu lan luot vai cach goi kha di, khong chac chan ham nao con dung.
    """
    candidates = []
    try:
        stock_obj = vn.stock(symbol=symbol, source="VCI")
        # Cach 1: neu co san ham trading.foreign_trade hoac tuong tu
        if hasattr(stock_obj, "trading"):
            try:
                data = stock_obj.trading.foreign_trade()
                candidates.append(("trading.foreign_trade", data))
            except Exception as e:
                print(f"  Thu trading.foreign_trade() loi: {e}")
        safe_sleep()
    except Exception as e:
        print(f"  Khong the khoi tao stock object cho khoi ngoai: {e}")

    for name, data in candidates:
        if data is not None:
            try:
                if hasattr(data, "to_dict"):
                    return {"status": "ok", "method": name, "data": data.tail(5).to_dict(orient="records")}
            except Exception:
                pass

    return {"status": "unavailable", "note": "Thu vien vnstock khong co ham cong khai on dinh cho du lieu khoi ngoai o phien ban hien tai. Can kiem tra lai github.com/thinh-vu/vnstock hoac bo sung nguon khac."}


def main():
    print(f"Bat dau fetch vnstock luc {datetime.utcnow().isoformat()}")
    result = {"fetched_at": datetime.utcnow().isoformat(), "status": "ok"}
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    try:
        from vnstock import Vnstock
        print("Import vnstock: OK")
    except ImportError as e:
        result["status"] = "error"
        result["error"] = f"import_error: {e}"
        _write_result(result)
        return

    try:
        vn = Vnstock()

        print("Dang lay VNINDEX...")
        idx_stock = vn.stock(symbol="VNINDEX", source="VCI")
        idx_df = idx_stock.quote.history(start=start, end=end, interval="1D")
        safe_sleep()
        result["vnindex_history"] = idx_df.tail(5).to_dict(orient="records") if idx_df is not None else []
        print(f"VNINDEX: {'OK' if idx_df is not None else 'khong co du lieu'}")

        print(f"Dang lay {len(TOP_TICKERS)} ma co phieu (co gian cach {SLEEP_SECONDS}s moi lan)...")
        top_stocks = []
        for ticker in TOP_TICKERS:
            top_stocks.append(fetch_one_ticker(vn, ticker, start, end))
        result["top_stocks"] = top_stocks

        ok_count = sum(1 for s in top_stocks if s.get("status") == "ok")
        print(f"Ket qua co phieu: {ok_count}/{len(TOP_TICKERS)} thanh cong")

        print("Dang thu lay du lieu khoi ngoai...")
        result["foreign_flow"] = fetch_foreign_flow(vn)

    except Exception as e:
        print(f"LOI: {repr(e)}")
        result["status"] = "error"
        result["error"] = str(e)

    _write_result(result)


def _write_result(result):
    os.makedirs("data", exist_ok=True)
    with open("data/vnstock.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("DA GHI: data/vnstock.json")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        os.makedirs("data", exist_ok=True)
        with open("data/vnstock.json", "w", encoding="utf-8") as f:
            json.dump({"status": "fatal_error"}, f)
        sys.exit(0)
