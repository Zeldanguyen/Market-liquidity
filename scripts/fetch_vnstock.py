"""
Lay VN-Index va top 10 co phieu von hoa lon nhat qua thu vien vnstock.
Thu nguon VCI truoc, neu loi tung ma thi thu nguon TCBS lam du phong.
"""
import os
import sys
import json
import traceback
from datetime import datetime, timedelta

TOP_TICKERS = ["VCB", "VIC", "VHM", "HPG", "FPT", "GAS", "MSN", "MWG", "TCB", "VPB"]
SOURCES_TO_TRY = ["VCI", "TCBS"]


def fetch_one_ticker(vn, symbol, start, end):
    last_error = "unknown"
    for source in SOURCES_TO_TRY:
        try:
            print(f"  Dang thu {symbol} qua nguon {source}...")
            stock_obj = vn.stock(symbol=symbol, source=source)
            df = stock_obj.quote.history(start=start, end=end, interval="1D")
            if df is None or len(df) == 0:
                print(f"  {symbol} qua {source}: khong co du lieu tra ve")
                last_error = f"{source}: du lieu rong"
                continue
            latest = df.tail(1).to_dict(orient="records")[0]
            latest["symbol"] = symbol
            latest["status"] = "ok"
            latest["source_used"] = source
            print(f"  {symbol} qua {source}: THANH CONG")
            return latest
        except Exception as e:
            print(f"  {symbol} qua {source}: LOI - {repr(e)}")
            last_error = f"{source}: {str(e)}"
            continue
    return {"symbol": symbol, "status": "error", "error": last_error}


def fetch_vnindex(vn, start, end):
    for source in SOURCES_TO_TRY:
        try:
            print(f"Dang thu VNINDEX qua nguon {source}...")
            idx_stock = vn.stock(symbol="VNINDEX", source=source)
            idx_df = idx_stock.quote.history(start=start, end=end, interval="1D")
            if idx_df is not None and len(idx_df) > 0:
                print(f"VNINDEX qua {source}: THANH CONG, {len(idx_df)} dong du lieu")
                return idx_df.tail(5).to_dict(orient="records"), None
            print(f"VNINDEX qua {source}: du lieu rong")
        except Exception as e:
            print(f"VNINDEX qua {source}: LOI - {repr(e)}")
            last_error = str(e)
            continue
    return [], "Khong lay duoc VNINDEX tu ca hai nguon"


def main():
    print(f"Phien ban Python dang chay, bat dau fetch vnstock luc {datetime.utcnow().isoformat()}")

    result = {"fetched_at": datetime.utcnow().isoformat(), "status": "ok"}
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    print(f"Khoang thoi gian lay du lieu: {start} den {end}")

    try:
        from vnstock import Vnstock
        print("Import thu vien vnstock: THANH CONG")
    except ImportError as e:
        print(f"KHONG THE IMPORT vnstock: {e}")
        result["status"] = "error"
        result["error"] = f"import_error: {e}"
        result["note"] = "Kiem tra requirements.txt co dong 'vnstock>=3.0.0' khong"
        _write_result(result)
        return

    try:
        vn = Vnstock()

        vnindex_history, vnindex_error = fetch_vnindex(vn, start, end)
        result["vnindex_history"] = vnindex_history
        if vnindex_error:
            result["vnindex_error"] = vnindex_error

        print(f"\nBat dau fetch {len(TOP_TICKERS)} ma co phieu top...")
        top_stocks = []
        for ticker in TOP_TICKERS:
            top_stocks.append(fetch_one_ticker(vn, ticker, start, end))
        result["top_stocks"] = top_stocks

        ok_count = sum(1 for s in top_stocks if s.get("status") == "ok")
        print(f"\nKet qua: {ok_count}/{len(TOP_TICKERS)} ma co phieu lay thanh cong")

        if not vnindex_history and ok_count == 0:
            result["status"] = "error"
            result["error"] = "Khong lay duoc bat ky du lieu nao (VNINDEX lan top stocks deu that bai)"

    except Exception as e:
        print(f"LOI NGHIEM TRONG trong qua trinh fetch: {repr(e)}")
        result["status"] = "error"
        result["error"] = str(e)
        result["note"] = "Kiem tra lai cu phap vnstock tai github.com/thinh-vu/vnstock, thu vien nay hay doi API"

    _write_result(result)


def _write_result(result):
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "vnstock.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nDA GHI: {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("LOI NGHIEM TRONG NGOAI Y MUON - traceback day du:")
        traceback.print_exc()
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "vnstock.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "fatal_error"}, f)
        sys.exit(0)
