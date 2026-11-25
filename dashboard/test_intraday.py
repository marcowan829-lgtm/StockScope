from __future__ import annotations

import sys
import pandas as pd

try:
    import yfinance as yf
except Exception as exc:
    print("无法导入 yfinance。请先在项目文件夹运行：python -m pip install -r requirements.txt")
    print(type(exc).__name__, str(exc))
    input("按回车退出...")
    raise SystemExit(1)


def test_symbol(symbol: str) -> None:
    print("\n" + "=" * 65)
    print(f"测试 {symbol} 的 1 分钟行情")
    print("=" * 65)
    now_utc = pd.Timestamp.now(tz="UTC")
    now_et = pd.Timestamp.now(tz="America/New_York")
    print("当前 UTC：", now_utc.strftime("%Y-%m-%d %H:%M:%S %Z"))
    print("当前美东时间：", now_et.strftime("%Y-%m-%d %H:%M:%S %Z"))
    try:
        df = yf.Ticker(symbol).history(
            period="1d", interval="1m", prepost=True, auto_adjust=False, actions=False
        )
    except Exception as exc:
        print("请求失败：", type(exc).__name__, str(exc))
        return
    if df is None or df.empty:
        print("接口没有返回数据。可能是网络、数据源限制、交易时段或标的可用性导致。")
        return
    last_ts = pd.Timestamp(df.index[-1])
    if last_ts.tzinfo is None:
        last_ts_et = last_ts.tz_localize("America/New_York")
    else:
        last_ts_et = last_ts.tz_convert("America/New_York")
    age = (pd.Timestamp.now(tz="America/New_York") - last_ts_et).total_seconds() / 60
    print("返回记录数：", len(df))
    print("最新 K 线时间（美东）：", last_ts_et.strftime("%Y-%m-%d %H:%M:%S %Z"))
    print(f"当前时间与 K 线时间戳之差：{age:.1f} 分钟（不等同于实际传输延迟）")
    print("最新行情：")
    print(df[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]].tail(5))


def main() -> None:
    print("StockScope 分钟行情诊断")
    test_symbol("NVDA")
    test_symbol("BTC-USD")
    print("\n如果 NVDA 在周末停留在上一交易日的数据，属于可能出现的正常情况。")
    print("BTC-USD 全天候交易，但其更新时间不能用于推断美股行情延迟。")
    input("\n测试结束。按回车关闭窗口...")


if __name__ == "__main__":
    main()
