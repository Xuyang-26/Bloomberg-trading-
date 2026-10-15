import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta

st.set_page_config(page_title="StockLab｜自動股價回測", page_icon="📈", layout="wide")

st.markdown("""
<style>
.stApp {background: #0b1020; color: #edf3ff;}
[data-testid="stSidebar"] {background: #111a2d;}
h1,h2,h3,p,label {color: #edf3ff;}
div[data-testid="stMetric"] {background:#131d31;border:1px solid #293854;padding:14px;border-radius:14px;}
</style>
""", unsafe_allow_html=True)

st.title("📈 StockLab｜股票回測工作台")
st.caption("自動取得歷史股價 · 持倉損益 · MA20 策略測試")
st.info("資料來源：Yahoo Finance（透過 yfinance）。行情可能延遲、修訂或暫時無法取得；本工具供學習研究，不構成投資建議。")

with st.sidebar:
    st.header("交易設定")
    ticker = st.text_input("股票代號", value="UNH").strip().upper()
    period = st.selectbox("歷史資料期間", ["6mo", "1y", "2y", "3y", "5y"], index=3,
                          format_func=lambda x: {"6mo":"過去 6 個月","1y":"過去 1 年","2y":"過去 2 年","3y":"過去 3 年","5y":"過去 5 年"}[x])
    buy_price = st.number_input("你的買進價格（USD）", min_value=0.01, value=388.0, step=0.5)
    shares = st.number_input("持有股數", min_value=0.0001, value=1.0, step=1.0)
    fee_pct = st.number_input("單邊交易成本（%）", min_value=0.0, value=0.0, step=0.01)
    run = st.button("取得股價並分析", type="primary", use_container_width=True)

if "run_once" not in st.session_state:
    st.session_state.run_once = True
if run:
    st.session_state.run_once = True

if st.session_state.run_once:
    if not ticker:
        st.error("請輸入股票代號，例如 MU 或 UNH。")
        st.stop()
    try:
        with st.spinner(f"正在取得 {ticker} 的歷史股價…"):
            raw = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
        if raw is None or raw.empty:
            st.error("沒有取得股價資料。請確認股票代號，或稍後再試。")
            st.stop()

        # Handle yfinance's single- and multi-level columns.
        if isinstance(raw.columns, pd.MultiIndex):
            if "Close" in raw.columns.get_level_values(0):
                close = raw["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
            else:
                st.error("回傳資料格式與預期不同，請稍後再試。")
                st.stop()
        else:
            close = raw["Close"]

        data = pd.DataFrame({"Close": pd.to_numeric(close, errors="coerce")}).dropna()
        data.index = pd.to_datetime(data.index)
        data["MA20"] = data["Close"].rolling(20).mean()
        data["Daily Return"] = data["Close"].pct_change().fillna(0)

        # Simple signal: hold if the previous day's close was above its MA20.
        # Shifting by one day avoids using today's close to earn today's close-to-close return.
        data["Signal"] = (data["Close"] > data["MA20"]).astype(float)
        data["Position"] = data["Signal"].shift(1).fillna(0)
        data["Strategy Return"] = data["Position"] * data["Daily Return"]
        data["Buy Hold Equity"] = (1 + data["Daily Return"]).cumprod()
        data["Strategy Equity"] = (1 + data["Strategy Return"]).cumprod()
        data["Buy Hold DD"] = data["Buy Hold Equity"] / data["Buy Hold Equity"].cummax() - 1
        data["Strategy DD"] = data["Strategy Equity"] / data["Strategy Equity"].cummax() - 1

        latest = float(data["Close"].iloc[-1])
        first_date = data.index[0].date()
        last_date = data.index[-1].date()
        pnl = (latest - buy_price) * shares
        net_pnl = pnl - (buy_price + latest) * shares * fee_pct / 100
        ret = (latest / buy_price - 1) * 100
        bh_ret = (data["Buy Hold Equity"].iloc[-1] - 1) * 100
        strat_ret = (data["Strategy Equity"].iloc[-1] - 1) * 100
        max_dd = data["Strategy DD"].min() * 100
        latest_ma = data["MA20"].iloc[-1]

        st.subheader(f"{ticker}｜{first_date} 至 {last_date}")
        st.caption(f"共 {len(data)} 個交易日 · 最新可取得收盤價日期：{last_date} · 使用調整後收盤價（auto-adjusted）")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("最新價格", f"${latest:,.2f}")
        c2.metric("相對買進價", f"{ret:+.2f}%")
        c3.metric("持倉估算損益", f"${pnl:+,.2f}")
        c4.metric("估計扣成本後損益", f"${net_pnl:+,.2f}")

        tab1, tab2, tab3 = st.tabs(["股價與 MA20", "歷史策略回測", "每日資料"])
        with tab1:
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(data.index, data["Close"], label="Adjusted Close", linewidth=1.6)
            ax.plot(data.index, data["MA20"], label="MA20", linewidth=1.4)
            ax.axhline(buy_price, linestyle="--", linewidth=1, label=f"Your buy price ${buy_price:.2f}")
            ax.set_title(f"{ticker}: Adjusted Close vs MA20")
            ax.set_ylabel("USD")
            ax.grid(alpha=.25)
            ax.legend()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
            if pd.notna(latest_ma):
                st.write(f"最新 MA20：**${latest_ma:,.2f}**。最新收盤價目前**{'高於' if latest > latest_ma else '低於或等於'}** MA20。這只是價格趨勢訊號，不是買賣建議。")
            else:
                st.write("資料不足以計算 MA20。")

        with tab2:
            a, b, c = st.columns(3)
            a.metric("Buy & Hold 累積報酬", f"{bh_ret:+.2f}%")
            b.metric("MA20 策略累積報酬", f"{strat_ret:+.2f}%")
            c.metric("MA20 策略最大回撤", f"{max_dd:.2f}%")
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(data.index, (data["Buy Hold Equity"] - 1) * 100, label="Buy & Hold")
            ax.plot(data.index, (data["Strategy Equity"] - 1) * 100, label="MA20 Strategy")
            ax.axhline(0, color="gray", linewidth=.8)
            ax.set_title("Historical cumulative return (before fees)")
            ax.set_ylabel("Return (%)")
            ax.grid(alpha=.25)
            ax.legend()
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
            st.warning("回測是歷史模擬，不代表未來報酬。此簡化策略未計入完整交易成本、稅費、滑價與實際成交限制；策略在收盤後確認訊號，並以次日持倉計算，仍屬簡化模型。")

        with tab3:
            view = data[["Close", "MA20", "Daily Return", "Signal", "Strategy Return"]].copy()
            view.columns = ["調整後收盤價", "MA20", "每日報酬", "收盤價高於MA20", "策略每日報酬"]
            st.dataframe(view.sort_index(ascending=False).style.format({
                "調整後收盤價":"${:,.2f}", "MA20":"${:,.2f}",
                "每日報酬":"{:.2%}", "收盤價高於MA20":"{:.0f}", "策略每日報酬":"{:.2%}"
            }), use_container_width=True, height=430)
            csv = view.to_csv(index=True).encode("utf-8-sig")
            st.download_button("下載每日資料 CSV", data=csv, file_name=f"{ticker}_{period}_history.csv", mime="text/csv")

        st.caption("注意：買進價損益以你輸入的價格與最新可取得的調整後收盤價估算。調整後價格可能包含股息及拆股調整，與券商顯示的未調整成交價不同。")
    except Exception as e:
        st.error("取得或分析股價時發生錯誤。請檢查網路、代號或稍後再試。")
        st.caption(f"技術訊息：{type(e).__name__}: {e}")
else:
    st.write("在左側輸入股票代號和買進資料，再按「取得股價並分析」。")
