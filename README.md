[README.md](https://github.com/user-attachments/files/33486000/README.md)
# StockLab 自動股價回測網站

這是一個可部署到 Streamlit Community Cloud 的小型網站，會透過 `yfinance` 嘗試取得 Yahoo Finance 的歷史行情。

## 本機執行
1. 安裝 Python 3.10 或更新版本。
2. 在終端機進入此資料夾。
3. 執行 `pip install -r requirements.txt`
4. 執行 `streamlit run app.py`

## 部署成公開網址（免費方案可用，依平台當下政策為準）
1. 登入 GitHub，建立一個新的 repository。
2. 把 `app.py`、`requirements.txt` 上傳到 repository 根目錄。
3. 登入 https://share.streamlit.io/ 並連結 GitHub。
4. 選擇該 repository、branch 和 `app.py`，點 Deploy。
5. 部署完成後，Streamlit 會提供一個可分享的網址。

## 限制
- 本程式不含 API key，但 `yfinance` 使用的 Yahoo Finance 非官方資料接口可能限流、延遲或改變。
- 股價不保證即時，也不構成投資建議。
- MA20 策略是教學用簡化模型，回測結果不代表未來。
