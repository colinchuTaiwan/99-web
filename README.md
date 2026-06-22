# 99乘法我最強 🚀 — 部署說明

## 📁 檔案結構

```
multiplication_app/
├── app.py                  # 主程式
├── requirements.txt        # 套件需求
├── secrets_template.toml   # Firebase 金鑰範本
├── firebase_rules.json     # Firebase 規則設定
└── README.md
```

---

## 🔥 Step 1：設定 Firebase

1. 前往 [Firebase Console](https://console.firebase.google.com/)
2. 建立新專案（或使用現有的 `quiz-bc56f`）
3. 啟用 **Realtime Database**（選 asia-southeast1）
4. 匯入 `firebase_rules.json` 中的規則
5. 前往「專案設定 > 服務帳戶」→ 產生新的私密金鑰 → 下載 JSON

---

## ⚙️ Step 2：設定 Streamlit Secrets

### 本機測試
建立 `.streamlit/secrets.toml`，填入 Firebase 服務帳戶 JSON 的各欄位：

```toml
[firebase]
type = "service_account"
project_id = "quiz-bc56f"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxxx@quiz-bc56f.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
database_url = "https://quiz-bc56f-default-rtdb.asia-southeast1.firebasedatabase.app"
```

### Streamlit Cloud
前往 App Settings > Secrets，貼上上方 TOML 內容。

---

## 🚀 Step 3：部署到 Streamlit Cloud

1. 將所有檔案推送到 GitHub 公開 repo
2. 前往 [share.streamlit.io](https://share.streamlit.io)
3. 選擇 repo → 主檔案選 `app.py`
4. 填入 Secrets → Deploy

---

## 🎮 功能說明

| 功能 | 說明 |
|------|------|
| 動態題目生成 | 從 1–9 × 1–9 隨機抽題，不重複 |
| 每題計時 | 30 秒倒數，逾時自動 0 分 |
| 計分規則 | 答對得 (30 − 用時)秒 分，連續答對第 N 題加 (N-1)×3 分 |
| 連續答對加成 | 2題+3分、3題+6分、依此類推 |
| 排行榜 | 總排、年排、月排、週排，存於 Firebase |
| 訪客計數 | 每次按「開始測驗」累計 |
| 詳解 | 結算頁每題附中文口訣 |

---

## 🏠 本機執行

```bash
pip install -r requirements.txt
streamlit run app.py
```
