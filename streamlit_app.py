"""
99乘法我最強 🚀 — Streamlit 版
- 核心測驗邏輯：HTML/JS 元件內建（st.components.v1.html）
- 排行榜 / 答對率 / 學生歷程：Firebase Realtime Database（JS SDK 直接讀寫）
- 訪客人數：firebase_admin Python SDK（與你現有 streamlit_app.py 相同模式）
- 導航連結：側邊欄
"""

import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, db as firebase_db
from datetime import datetime, timezone, timedelta

# ── 頁面設定 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="99乘法我最強 🚀",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Firebase Admin 初始化（訪客計數用）────────────────────────────────────────
@st.cache_resource
def init_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()
    s = st.secrets["firebase"]
    cert_dict = {
        "type":                        s["type"],
        "project_id":                  s["project_id"],
        "private_key_id":              s["private_key_id"],
        "private_key":                 s["private_key"].replace("\\n", "\n"),
        "client_email":                s["client_email"],
        "client_id":                   s["client_id"],
        "auth_uri":                    s["auth_uri"],
        "token_uri":                   s["token_uri"],
        "client_x509_cert_url":        s.get("client_x509_cert_url", ""),
        "auth_provider_x509_cert_url": s.get("auth_provider_x509_cert_url", ""),
    }
    cred = credentials.Certificate(cert_dict)
    return firebase_admin.initialize_app(cred, {"databaseURL": s["database_url"]})

def track_visitor(site_id: str) -> int:
    init_firebase()
    ref = firebase_db.reference(f"visitor_counts/{site_id}")
    def increment(current):
        return (current or 0) + 1
    try:
        if "counted" not in st.session_state:
            count = ref.transaction(increment)
            st.session_state["counted"] = True
            return count
        return ref.get() or 0
    except Exception:
        return 0

SITE_ID = st.secrets.get("SITE_ID", "99quiz")
visitor_count = track_visitor(SITE_ID)

tz = timezone(timedelta(hours=8))
now_taipei = datetime.now(tz).strftime("%H:%M:%S")

# ── Firebase 設定（傳給 JS SDK）───────────────────────────────────────────────
# 從 st.secrets 讀取 Firebase Web API 設定（與 Admin SDK 不同，是給前端 JS 用的）
# 請在 .streamlit/secrets.toml 加入 [firebase_web] 區塊：
#   api_key = "..."
#   auth_domain = "..."
#   database_url = "..."
#   project_id = "..."
#   storage_bucket = "..."
#   messaging_sender_id = "..."
#   app_id = "..."
try:
    fw = st.secrets["firebase_web"]
    FIREBASE_CONFIG = {
        "apiKey":            fw["api_key"],
        "authDomain":        fw["auth_domain"],
        "databaseURL":       fw["database_url"],
        "projectId":         fw["project_id"],
        "storageBucket":     fw["storage_bucket"],
        "messagingSenderId": fw["messaging_sender_id"],
        "appId":             fw["app_id"],
    }
except Exception:
    # 若尚未設定，用空值讓頁面仍可顯示（localStorage 降級模式）
    FIREBASE_CONFIG = {}

# ── 側邊欄：導覽連結 + 系統資訊 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏫 學科測驗導覽")
    nav_links = [
        ("📖", "英文測驗挑戰網", "https://english-examine.streamlit.app/"),
        ("➕", "數學測驗挑戰網", "https://math-examine.streamlit.app/"),
        ("✍️", "國語測驗挑戰網", "https://chinese-examine.streamlit.app/"),
        ("🔬", "理化測驗挑戰網", "https://science-examine.streamlit.app/"),
        ("📜", "歷史測驗挑戰網", "https://history-examine.streamlit.app/"),
        ("🏛️", "公民測驗挑戰網", "https://civics-examine.streamlit.app/"),
        ("🧬", "生物測驗挑戰網", "https://biology-examine.streamlit.app/"),
        ("🌍", "地球科學測驗網", "https://earth-science-examine.streamlit.app/"),
    ]
    for icon, label, url in nav_links:
        st.markdown(
            f'{icon} <a href="{url}" target="_blank" style="text-decoration:none;">{label}</a>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("⏰ 系統時間")
    st.title(now_taipei)
    st.metric("👥 累計訪客", visitor_count)
    st.caption(f"網站識別碼：`{SITE_ID}`")

    st.markdown("---")
    st.markdown("#### ⚠️ 投資免責聲明")
    st.caption(
        "本工具僅供學習娛樂使用，題目結果不代表任何學業成績認定，"
        "請搭配正式課程使用。"
    )

# ── 主內容：HTML 測驗元件 ──────────────────────────────────────────────────────
import json

firebase_config_json = json.dumps(FIREBASE_CONFIG)

HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>99乘法我最強 🚀</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@300..700&family=Noto+Sans+TC:wght@400;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>

  <!-- Firebase JS SDK v9 compat -->
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-database-compat.js"></script>

  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { sans: ['Fredoka', 'Noto Sans TC', 'sans-serif'] },
          animation: {
            'bounce-slow': 'bounce 3s infinite',
            'pulse-soft': 'pulseSoft 2s infinite',
            'fade-in': 'fadeIn 0.4s ease-out forwards',
          },
          keyframes: {
            pulseSoft: {
              '0%, 100%': { transform: 'scale(1)', boxShadow: '0 10px 25px -5px rgba(16,185,129,0.2)' },
              '50%': { transform: 'scale(1.02)', boxShadow: '0 20px 25px -5px rgba(16,185,129,0.4)' },
            },
            fadeIn: {
              '0%': { opacity: '0', transform: 'translateY(15px)' },
              '100%': { opacity: '1', transform: 'translateY(0)' },
            }
          }
        }
      }
    }
  </script>
  <style>
    body {
      background: linear-gradient(135deg, #F0F8FF 0%, #FFF0F5 100%);
      color: #2C3E50;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #F0F8FF; }
    ::-webkit-scrollbar-thumb { background: #FFD1DC; border-radius: 99px; }
    .option-btn { transition: all 0.2s cubic-bezier(0.175,0.885,0.32,1.275); }
    .option-btn:active { transform: scale(0.97); }
  </style>
</head>
<body class="font-sans antialiased p-3 md:p-6 flex flex-col items-center justify-between">

  <!-- 背景裝飾 -->
  <div class="fixed inset-0 pointer-events-none overflow-hidden opacity-25 select-none z-0">
    <div class="absolute text-4xl top-10 left-10 animate-bounce-slow" style="animation-delay:0.5s">🎈</div>
    <div class="absolute text-5xl bottom-20 left-20 animate-bounce-slow" style="animation-delay:1.2s">✨</div>
    <div class="absolute text-4xl top-24 right-12 animate-bounce-slow" style="animation-delay:0.1s">🎨</div>
    <div class="absolute text-5xl bottom-16 right-24 animate-bounce-slow" style="animation-delay:2s">🚀</div>
    <div class="absolute text-4xl top-1/2 left-8 animate-bounce-slow" style="animation-delay:1.5s">⭐</div>
    <div class="absolute text-4xl top-1/3 right-10 animate-bounce-slow" style="animation-delay:0.8s">🎒</div>
  </div>

  <!-- 頂部導覽 -->
  <header class="w-full max-w-2xl flex justify-between items-center z-10 mb-4 px-2">
    <div id="invited-badge" class="hidden bg-pink-100 text-pink-700 text-xs px-3 py-1.5 rounded-full font-black shadow-sm border border-pink-200">
      <i class="fa-solid fa-envelope-open-text mr-1"></i> 受邀挑戰模式
    </div>
    <div class="flex-grow"></div>
    <button id="toggle-console-btn" onclick="toggleViewMode()"
      class="bg-white/80 backdrop-blur-sm border-2 border-indigo-100 text-indigo-700 text-xs md:text-sm font-bold px-4 py-2 rounded-xl shadow-sm hover:bg-indigo-50 transition-all flex items-center gap-1.5">
      <i class="fa-solid fa-chart-line"></i> <span id="mode-btn-text">切換至教師主控台</span>
    </button>
  </header>

  <!-- 主卡片 -->
  <main class="w-full max-w-2xl bg-white/95 backdrop-blur-md rounded-3xl shadow-xl border-4 border-white p-5 md:p-8 z-10 transition-all duration-300 flex-grow mb-6">

    <!-- 1. 首頁 -->
    <section id="home-view" class="space-y-5 animate-fade-in">
      <div class="text-center space-y-2">
        <h1 id="app-title-display" class="text-3xl md:text-5xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-pink-500 to-orange-400 py-1">
          99乘法我最強 🚀
        </h1>
        <p class="text-sm md:text-base text-slate-500 font-bold">歡迎來到乘法大挑戰！快來設定並開始闖關吧！</p>
      </div>

      <div class="bg-blue-50/50 p-5 rounded-2xl border-2 border-indigo-100 space-y-3">
        <h3 class="text-md font-bold text-indigo-700"><i class="fa-solid fa-user-astronaut mr-2"></i>第一步：告訴我們你是誰</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="block font-bold text-slate-700 text-xs">你的姓名：</label>
            <input type="text" id="student-name" placeholder="例如：小智"
              class="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 focus:border-indigo-400 focus:outline-none text-md font-bold transition-all">
          </div>
          <div class="space-y-1">
            <label class="block font-bold text-slate-700 text-xs">座號 / 學號：</label>
            <input type="text" id="student-id" placeholder="例如：09"
              class="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 focus:border-indigo-400 focus:outline-none text-md font-bold transition-all">
          </div>
        </div>
      </div>

      <div class="bg-amber-50/50 p-5 rounded-2xl border-2 border-amber-100 space-y-3">
        <h3 class="text-md font-bold text-amber-700"><i class="fa-solid fa-list-ol mr-2"></i>第二步：選擇挑戰題數</h3>
        <div class="flex flex-wrap gap-3 justify-around items-center" id="question-count-picker">
          <label class="flex-1 min-w-[80px] max-w-[100px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100/20 transition-all">
            <input type="radio" name="question-count" value="10" checked class="hidden peer">
            <span class="text-lg font-black text-slate-600 peer-checked:text-amber-600">10 題</span>
            <span class="text-[10px] text-slate-400">標準測驗</span>
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
          <label class="flex-1 min-w-[80px] max-w-[100px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100/20 transition-all">
            <input type="radio" name="question-count" value="20" class="hidden peer">
            <span class="text-lg font-black text-slate-600 peer-checked:text-amber-600">20 題</span>
            <span class="text-[10px] text-slate-400">實力升級</span>
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
          <label class="flex-1 min-w-[80px] max-w-[100px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100/20 transition-all">
            <input type="radio" name="question-count" value="50" class="hidden peer">
            <span class="text-lg font-black text-slate-600 peer-checked:text-amber-600">50 題</span>
            <span class="text-[10px] text-slate-400">專家挑戰</span>
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
          <label class="flex-1 min-w-[110px] max-w-[130px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-100/20 transition-all" id="custom-count-wrapper">
            <input type="radio" name="question-count" value="custom" class="hidden peer" id="count-radio-custom">
            <span class="text-xs font-black text-slate-600 peer-checked:text-amber-600 mb-1">自訂題數</span>
            <input type="number" id="custom-question-count" min="1" max="100" value="15"
              onclick="document.getElementById('count-radio-custom').checked = true;"
              class="w-16 px-1.5 py-0.5 border-2 border-amber-100 rounded text-center text-xs font-bold text-slate-700 focus:outline-none focus:border-amber-400">
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
        </div>
      </div>

      <div class="bg-pink-50/50 p-5 rounded-2xl border-2 border-pink-100 space-y-3" id="range-picker-container">
        <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
          <h3 class="text-md font-bold text-pink-700"><i class="fa-solid fa-calculator mr-2"></i>第三步：選擇乘數範圍 (可複選)</h3>
          <div class="flex gap-2">
            <button type="button" onclick="selectAllRanges(true)" class="text-[11px] bg-pink-100 text-pink-700 px-2 py-1 rounded-lg hover:bg-pink-200 font-bold transition-all">全選 2~9</button>
            <button type="button" onclick="selectAllRanges(false)" class="text-[11px] bg-slate-100 text-slate-600 px-2 py-1 rounded-lg hover:bg-slate-200 font-bold transition-all">全部取消</button>
          </div>
        </div>
        <div class="grid grid-cols-4 gap-2" id="range-checkboxes-container"></div>
      </div>

      <div class="text-center pt-2">
        <button id="start-btn" onclick="startQuiz()"
          class="w-full md:w-3/4 py-3.5 rounded-2xl text-xl md:text-2xl font-black tracking-widest text-emerald-800 bg-[#E8F8F5] hover:bg-emerald-200/80 border-b-8 border-emerald-300 hover:border-emerald-400 active:border-b-2 hover:scale-[1.01] active:scale-[0.99] transition-all shadow-md animate-pulse-soft">
          開始挑戰 🎯
        </button>
      </div>
    </section>

    <!-- 2. 測驗頁面 -->
    <section id="quiz-view" class="hidden space-y-5 animate-fade-in">
      <div class="flex justify-between items-center bg-indigo-50/50 p-3.5 rounded-2xl border border-indigo-100">
        <div class="flex items-center gap-2 text-indigo-700 font-bold text-base md:text-lg">
          <i class="fa-regular fa-clock animate-pulse"></i>
          <span>時間：</span>
          <span id="timer-display" class="font-mono bg-white px-2.5 py-0.5 rounded-lg shadow-inner text-indigo-800">00:00</span>
        </div>
        <div class="flex flex-col items-end gap-1">
          <span id="progress-text" class="text-xs font-bold text-slate-500">第 1 / 10 題</span>
          <div class="w-24 md:w-40 bg-slate-200 h-2.5 rounded-full overflow-hidden shadow-inner">
            <div id="progress-bar" class="bg-gradient-to-r from-pink-400 to-indigo-500 h-full w-[10%] rounded-full transition-all duration-300"></div>
          </div>
        </div>
      </div>

      <div class="bg-[#FFFDF9] py-10 rounded-2xl border-4 border-dashed border-amber-200 flex flex-col items-center justify-center shadow-inner relative">
        <span class="absolute top-2.5 left-3 text-[10px] font-bold text-amber-500/70 select-none">
          <i class="fa-solid fa-pencil mr-1"></i> 請點選正確答案喔！
        </span>
        <div id="quiz-question" class="text-4xl md:text-5xl font-black text-[#2C3E50] tracking-wider select-none leading-none"></div>
      </div>

      <div class="flex flex-col gap-3" id="options-container"></div>

      <div class="flex justify-between items-center gap-3 pt-3 border-t-2 border-slate-100">
        <button id="prev-btn" onclick="prevQuestion()"
          class="flex-1 py-3 px-3 rounded-xl font-bold text-base text-slate-600 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5">
          <i class="fa-solid fa-chevron-left"></i> 上一題
        </button>
        <button id="next-btn" onclick="nextQuestion()"
          class="flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-indigo-500 hover:bg-indigo-600 shadow-md shadow-indigo-100 transition-all flex items-center justify-center gap-1.5">
          下一題 <i class="fa-solid fa-chevron-right"></i>
        </button>
      </div>
    </section>

    <!-- 3. 結算頁面 -->
    <section id="result-view" class="hidden space-y-5 animate-fade-in">
      <div id="report-card-container" class="bg-white p-5 md:p-6 rounded-2xl border-4 border-indigo-50 space-y-4">
        <div class="text-center border-b-2 border-dashed border-indigo-100 pb-3">
          <h2 class="text-2xl font-black text-indigo-700 flex items-center justify-center gap-1.5">
            👑 <span id="report-quiz-title">99乘法大挑戰成績單</span>
          </h2>
          <p class="text-slate-400 text-[10px] font-bold">乘法能力即時檢測系統認證</p>
        </div>
        <div class="flex flex-col items-center justify-center space-y-1">
          <div class="relative flex items-center justify-center">
            <div class="absolute w-28 h-28 bg-amber-100 rounded-full animate-ping opacity-15"></div>
            <div class="w-24 h-24 rounded-full border-4 border-amber-300 bg-amber-50 flex flex-col items-center justify-center shadow-md">
              <span class="text-slate-500 text-[10px] font-bold">得分</span>
              <span id="final-score" class="text-4xl font-black text-amber-600">100</span>
              <span class="text-slate-500 text-[10px] font-bold">分</span>
            </div>
          </div>
          <div id="score-comment" class="text-lg md:text-xl font-black text-center text-indigo-600 pt-1">太棒了！你真的是乘法大師！🏆</div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-center">
          <div class="bg-[#F0F8FF] p-2 rounded-xl border border-indigo-50/50 flex flex-col justify-center">
            <span class="text-[10px] font-bold text-slate-400">學生姓名</span>
            <span id="res-name" class="text-base font-black text-slate-700 mt-0.5">---</span>
          </div>
          <div class="bg-[#FFF0F5] p-2 rounded-xl border border-pink-50/50 flex flex-col justify-center">
            <span class="text-[10px] font-bold text-slate-400">座號/學號</span>
            <span id="res-id" class="text-base font-black text-slate-700 mt-0.5">---</span>
          </div>
          <div class="bg-[#FFFDF0] p-2 rounded-xl border border-amber-50/50 flex flex-col justify-center">
            <span class="text-[10px] font-bold text-slate-400">作答花費</span>
            <span id="res-time" class="text-base font-black text-slate-700 mt-0.5">---</span>
          </div>
          <div class="bg-[#E8F8F5] p-2 rounded-xl border border-emerald-50/50 flex flex-col justify-center">
            <span class="text-[10px] font-bold text-slate-400">答對題數</span>
            <span id="res-correct-rate" class="text-base font-black text-slate-700 mt-0.5">---</span>
          </div>
        </div>
        <div class="space-y-2">
          <h3 class="text-sm font-black text-indigo-700 border-l-4 border-indigo-500 pl-1.5 flex items-center gap-1">
            <i class="fa-solid fa-square-poll-horizontal"></i> 答題紀錄與詳解口訣
          </h3>
          <div id="review-list" class="space-y-3 max-h-[220px] overflow-y-auto pr-1"></div>
        </div>
      </div>

      <div class="bg-indigo-50 p-4 rounded-2xl border-2 border-indigo-100 space-y-2">
        <div class="flex justify-between items-center">
          <span class="text-xs font-black text-indigo-800"><i class="fa-solid fa-share-nodes mr-1"></i> 跨裝置數據彙整代碼</span>
          <button onclick="copySubmissionCode()" class="text-[10px] bg-indigo-600 text-white px-2.5 py-1 rounded-lg hover:bg-indigo-700 font-bold transition-all">
            <i class="fa-regular fa-copy mr-1"></i> 複製代碼
          </button>
        </div>
        <p class="text-[10px] text-slate-500 font-bold leading-normal">
          💡 如果老師需要收集你的成績，請點選「複製代碼」並把產生的文字傳給老師。
        </p>
        <textarea id="submission-code-box" readonly onclick="this.select()"
          class="w-full text-[10px] p-2 font-mono bg-white border border-indigo-200 rounded-lg h-12 focus:outline-none resize-none select-all text-slate-600"></textarea>
      </div>

      <div class="flex flex-col sm:flex-row gap-2.5 pt-1">
        <button onclick="exportToPDF()"
          class="flex-1 py-2.5 px-3 rounded-xl font-bold text-sm text-white bg-red-400 hover:bg-red-500 transition-all flex items-center justify-center gap-1.5 shadow-sm">
          <i class="fa-regular fa-file-pdf"></i> 下載成績單 (PDF)
        </button>
        <button onclick="exportToCSV()"
          class="flex-1 py-2.5 px-3 rounded-xl font-bold text-sm text-white bg-emerald-500 hover:bg-emerald-600 transition-all flex items-center justify-center gap-1.5 shadow-sm">
          <i class="fa-solid fa-file-csv"></i> 下載成績 (CSV)
        </button>
        <button onclick="restartQuiz()"
          class="flex-1 py-2.5 px-3 rounded-xl font-black text-sm text-indigo-700 bg-indigo-100 hover:bg-indigo-200 transition-all flex items-center justify-center gap-1.5 shadow-sm">
          <i class="fa-solid fa-rotate-left"></i> 再測一次 🔄
        </button>
      </div>
    </section>

    <!-- 4. 教師主控台 -->
    <section id="console-view" class="hidden space-y-5 animate-fade-in text-slate-700">
      <div class="border-b-2 border-indigo-100 pb-2.5 flex justify-between items-center">
        <div>
          <h2 class="text-2xl font-black text-indigo-800"><i class="fa-solid fa-graduation-cap mr-1"></i> 教師數據主控台</h2>
          <p class="text-xs text-slate-400 font-bold mt-0.5">即時統計、成績整合與出題設定（資料存於 Firebase）</p>
        </div>
        <button onclick="clearAllRecords()" class="text-xs bg-rose-50 hover:bg-rose-100 text-rose-600 px-3 py-1.5 rounded-lg border border-rose-200 font-bold transition-all">
          <i class="fa-regular fa-trash-can mr-1"></i> 清空班級紀錄
        </button>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="bg-blue-50/60 p-3 rounded-xl border border-blue-100 text-center">
          <div class="text-[10px] font-bold text-blue-500">總施測人次</div>
          <div id="stat-total-count" class="text-2xl font-black text-blue-800 mt-1">0</div>
        </div>
        <div class="bg-emerald-50/60 p-3 rounded-xl border border-emerald-100 text-center">
          <div class="text-[10px] font-bold text-emerald-500">班級平均分數</div>
          <div id="stat-avg-score" class="text-2xl font-black text-emerald-800 mt-1">0 <span class="text-xs">分</span></div>
        </div>
        <div class="bg-amber-50/60 p-3 rounded-xl border border-amber-100 text-center">
          <div class="text-[10px] font-bold text-amber-500">平均作答時間</div>
          <div id="stat-avg-time" class="text-2xl font-black text-amber-800 mt-1">0 <span class="text-xs">秒</span></div>
        </div>
        <div class="bg-purple-50/60 p-3 rounded-xl border border-purple-100 text-center">
          <div class="text-[10px] font-bold text-purple-500">及格率 (≥60分)</div>
          <div id="stat-pass-rate" class="text-2xl font-black text-purple-800 mt-1">0%</div>
        </div>
      </div>

      <div class="flex border-b border-slate-200 text-sm">
        <button onclick="switchConsoleTab('tab-leaderboard')" id="btn-tab-leaderboard" class="flex-1 py-2 font-black border-b-2 border-indigo-600 text-indigo-700 transition-all">🏆 排行榜</button>
        <button onclick="switchConsoleTab('tab-analysis')" id="btn-tab-analysis" class="flex-1 py-2 font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all">📈 答對率</button>
        <button onclick="switchConsoleTab('tab-history')" id="btn-tab-history" class="flex-1 py-2 font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all">🔍 學生歷程</button>
        <button onclick="switchConsoleTab('tab-sync')" id="btn-tab-sync" class="flex-1 py-2 font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all">🔗 分享</button>
      </div>

      <div id="tab-leaderboard" class="space-y-3">
        <div class="overflow-x-auto max-h-[300px] border border-slate-100 rounded-xl">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                <th class="p-3">名次</th><th class="p-3">學號</th><th class="p-3">姓名</th>
                <th class="p-3 text-center">分數</th><th class="p-3 text-center">時間</th><th class="p-3 text-center">日期</th>
              </tr>
            </thead>
            <tbody id="leaderboard-tbody" class="divide-y divide-slate-100"></tbody>
          </table>
        </div>
      </div>

      <div id="tab-analysis" class="hidden space-y-3">
        <p class="text-xs text-slate-400 font-bold"><i class="fa-solid fa-circle-info mr-1"></i> 依正確率由低到高排序（便於針對弱點輔導）：</p>
        <div id="accuracy-analysis-list" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-1"></div>
      </div>

      <div id="tab-history" class="hidden space-y-3">
        <div class="flex gap-2 items-center">
          <span class="text-xs font-bold text-slate-500 shrink-0">選擇學生：</span>
          <select id="student-selector" onchange="loadStudentHistory()"
            class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none text-xs font-bold bg-white"></select>
        </div>
        <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
          <h4 class="text-xs font-black text-slate-600 mb-2"><i class="fa-solid fa-history mr-1"></i> 作答歷史紀錄</h4>
          <div id="student-history-timeline" class="space-y-3 max-h-[220px] overflow-y-auto pr-1 text-xs"></div>
        </div>
      </div>

      <div id="tab-sync" class="hidden space-y-4 text-xs font-bold">
        <div class="bg-amber-50/50 p-4 rounded-xl border border-amber-200 space-y-2">
          <h4 class="text-sm font-black text-amber-800"><i class="fa-solid fa-link"></i> 自訂線上測驗並產生分享連結</h4>
          <div class="space-y-2">
            <div>
              <label class="block text-[10px] text-slate-500 mb-1">測驗專屬名稱：</label>
              <input type="text" id="share-quiz-title" value="九九乘法大挑戰 🚀"
                class="w-full px-2.5 py-2 border rounded-lg focus:outline-none focus:border-amber-400 bg-white">
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[10px] text-slate-500 mb-1">鎖定題數：</label>
                <div class="flex gap-1">
                  <select id="share-quiz-count" onchange="toggleShareCustomCountInput()" class="w-full px-2 py-2 border rounded-lg bg-white">
                    <option value="10" selected>10 題</option>
                    <option value="20">20 題</option>
                    <option value="50">50 題</option>
                    <option value="custom">自訂題數</option>
                  </select>
                  <input type="number" id="share-quiz-custom-count" value="15" min="1" max="100"
                    class="hidden w-16 px-1.5 py-1 border rounded-lg text-center font-bold text-xs bg-white focus:outline-none focus:border-amber-400">
                </div>
              </div>
              <div>
                <label class="block text-[10px] text-slate-500 mb-1">限制乘數範圍：</label>
                <button type="button" onclick="toggleShareRangeModal()" class="w-full px-2 py-2 border rounded-lg bg-white text-left text-[10px] flex justify-between items-center">
                  <span id="share-range-preview">已選 2~9 範圍</span> <i class="fa-solid fa-caret-down"></i>
                </button>
              </div>
            </div>
            <div id="share-range-box" class="hidden p-3 bg-white border rounded-lg grid grid-cols-4 gap-2"></div>
            <button onclick="generateCustomShareLink()"
              class="w-full py-2.5 bg-amber-500 text-white font-black rounded-lg hover:bg-amber-600 transition-all flex items-center justify-center gap-1.5 shadow-sm">
              <i class="fa-solid fa-copy"></i> 產生並複製分享網址
            </button>
          </div>
        </div>

        <div class="bg-indigo-50/50 p-4 rounded-xl border border-indigo-200 space-y-2">
          <h4 class="text-sm font-black text-indigo-800"><i class="fa-solid fa-file-import"></i> 匯入學生作答代碼</h4>
          <textarea id="import-codes-input" placeholder="請在此貼上 99QUIZ-... 代碼"
            class="w-full p-2 h-16 font-mono border rounded-lg focus:outline-none focus:border-indigo-400 bg-white"></textarea>
          <button onclick="importStudentCodes()"
            class="w-full py-2 bg-indigo-600 text-white font-black rounded-lg hover:bg-indigo-700 transition-all flex items-center justify-center gap-1.5 shadow-sm">
            <i class="fa-solid fa-file-circle-plus"></i> 匯入並整合班級成績
          </button>
        </div>
      </div>
    </section>
  </main>

  <footer class="text-xs text-slate-400 font-bold text-center z-10 space-y-1 py-2">
    <p>99乘法我最強 🚀 Online Quiz Web App</p>
    <p>© 2026 Designed for Happy Learning. All Rights Reserved.</p>
  </footer>

  <script>
    // ── Firebase 初始化 ────────────────────────────────────────────────────────
    const FIREBASE_CONFIG = {firebaseConfigJson};
    let firebaseDB = null;
    let useFirebase = false;

    try {
      if (FIREBASE_CONFIG.apiKey) {
        if (!firebase.apps.length) {
          firebase.initializeApp(FIREBASE_CONFIG);
        }
        firebaseDB = firebase.database();
        useFirebase = true;
        console.log("✅ Firebase 已連線");
      } else {
        console.warn("⚠️ Firebase 設定不完整，降級為 localStorage 模式");
      }
    } catch(e) {
      console.error("Firebase 初始化失敗:", e);
    }

    // ── Firebase / localStorage 雙模儲存層 ────────────────────────────────────
    const DB_KEY = "99_multiplication_records";
    const FIREBASE_PATH = "99quiz_records";

    async function saveRecord(record) {
      if (useFirebase) {
        try {
          await firebaseDB.ref(`${FIREBASE_PATH}/${record.id}`).set(record);
          return;
        } catch(e) { console.error("Firebase 寫入失敗，降級 localStorage:", e); }
      }
      // localStorage 降級
      const records = JSON.parse(localStorage.getItem(DB_KEY) || "[]");
      records.unshift(record);
      localStorage.setItem(DB_KEY, JSON.stringify(records));
    }

    async function loadAllRecords() {
      if (useFirebase) {
        try {
          const snap = await firebaseDB.ref(FIREBASE_PATH).once("value");
          const data = snap.val();
          if (!data) return [];
          // 轉成陣列並按時間倒序
          return Object.values(data).sort((a, b) => (b.ts || 0) - (a.ts || 0));
        } catch(e) { console.error("Firebase 讀取失敗，降級 localStorage:", e); }
      }
      return JSON.parse(localStorage.getItem(DB_KEY) || "[]");
    }

    async function deleteAllRecords() {
      if (useFirebase) {
        try {
          await firebaseDB.ref(FIREBASE_PATH).remove();
          return;
        } catch(e) { console.error("Firebase 刪除失敗:", e); }
      }
      localStorage.removeItem(DB_KEY);
    }

    // ── 系統狀態 ──────────────────────────────────────────────────────────────
    let appState = {
      viewMode: 'student',
      studentName: '',
      studentId: '',
      totalQuestionCount: 10,
      selectedRanges: [2,3,4,5,6,7,8,9],
      questions: [],
      currentQuestionIndex: 0,
      userAnswers: {},
      elapsedSeconds: 0,
      timerInterval: null,
      quizTitle: "99乘法我最強 🚀",
      isInvitedMode: false,
      shareSelectedRanges: [2,3,4,5,6,7,8,9]
    };

    // ── 初始化 ────────────────────────────────────────────────────────────────
    document.addEventListener("DOMContentLoaded", () => {
      checkUrlParams();
      renderRangeCheckboxes();
      renderShareRangeCheckboxes();
    });

    function checkUrlParams() {
      const urlParams = new URLSearchParams(window.location.search);
      const quizParam = urlParams.get('quiz');
      if (quizParam) {
        try {
          const decodedData = JSON.parse(decodeURIComponent(escape(atob(quizParam))));
          if (decodedData) {
            appState.quizTitle = decodedData.title || "受邀版乘法小測驗";
            appState.totalQuestionCount = parseInt(decodedData.count, 10) || 10;
            appState.selectedRanges = decodedData.ranges || [2,3,4,5,6,7,8,9];
            appState.isInvitedMode = true;
            document.getElementById("app-title-display").textContent = appState.quizTitle;
            document.getElementById("report-quiz-title").textContent = `${appState.quizTitle}成績單`;
            document.getElementById("invited-badge").classList.remove("hidden");
            document.getElementById("question-count-picker").classList.add("pointer-events-none","opacity-50");
            document.getElementById("range-picker-container").classList.add("hidden");
          }
        } catch(e) { console.error("無法解析分享參數:", e); }
      }
    }

    function renderRangeCheckboxes() {
      const container = document.getElementById("range-checkboxes-container");
      container.innerHTML = "";
      const colors = getRangeColors();
      for (let i = 2; i <= 9; i++) {
        const color = colors[i-2];
        const isChecked = appState.selectedRanges.includes(i) ? 'checked' : '';
        container.insertAdjacentHTML('beforeend', `
          <label class="flex items-center justify-between p-2 rounded-xl border-2 cursor-pointer transition-all hover:shadow-sm ${color.bg} ${color.border}">
            <span class="font-black text-sm md:text-base ${color.text}">${i} 🚀</span>
            <input type="checkbox" name="range-num" value="${i}" ${isChecked} class="w-4 h-4 accent-indigo-600 rounded cursor-pointer">
          </label>`);
      }
    }

    function renderShareRangeCheckboxes() {
      const container = document.getElementById("share-range-box");
      container.innerHTML = "";
      const colors = getRangeColors();
      for (let i = 2; i <= 9; i++) {
        const color = colors[i-2];
        const isChecked = appState.shareSelectedRanges.includes(i) ? 'checked' : '';
        container.insertAdjacentHTML('beforeend', `
          <label class="flex items-center justify-between p-1.5 rounded-lg border cursor-pointer transition-all ${color.bg} ${color.border}">
            <span class="font-bold text-xs ${color.text}">${i} 🚀</span>
            <input type="checkbox" name="share-range-num" value="${i}" ${isChecked} onchange="updateShareRangePreview()" class="w-3.5 h-3.5 accent-amber-600 rounded cursor-pointer">
          </label>`);
      }
      updateShareRangePreview();
    }

    function getRangeColors() {
      return [
        { bg:'bg-[#FEFDE8]', text:'text-yellow-800', border:'border-yellow-200' },
        { bg:'bg-[#FFF3E0]', text:'text-orange-800', border:'border-orange-200' },
        { bg:'bg-[#FFF0F5]', text:'text-pink-800',   border:'border-pink-200' },
        { bg:'bg-[#F3E5F5]', text:'text-purple-800', border:'border-purple-200' },
        { bg:'bg-[#E8F8F5]', text:'text-teal-800',   border:'border-teal-200' },
        { bg:'bg-[#EBF5FB]', text:'text-blue-800',   border:'border-blue-200' },
        { bg:'bg-[#F4F6F7]', text:'text-slate-800',  border:'border-slate-300' },
        { bg:'bg-[#FFF8E1]', text:'text-amber-800',  border:'border-amber-200' },
      ];
    }

    function selectAllRanges(checked) {
      document.querySelectorAll('input[name="range-num"]').forEach(cb => cb.checked = checked);
    }

    function toggleShareRangeModal() {
      document.getElementById("share-range-box").classList.toggle("hidden");
    }

    function updateShareRangePreview() {
      const checkedArr = Array.from(document.querySelectorAll('input[name="share-range-num"]:checked')).map(cb => cb.value);
      appState.shareSelectedRanges = checkedArr.map(Number);
      document.getElementById("share-range-preview").textContent = checkedArr.length === 0 ? "未選取" : `已選 ${checkedArr.join(',')} 範圍`;
    }

    function toggleShareCustomCountInput() {
      const val = document.getElementById("share-quiz-count").value;
      document.getElementById("share-quiz-custom-count").classList.toggle("hidden", val !== 'custom');
    }

    // ── 開始測驗 ──────────────────────────────────────────────────────────────
    function startQuiz() {
      const nameInput = document.getElementById("student-name").value.trim();
      const idInput   = document.getElementById("student-id").value.trim();
      if (!nameInput || !idInput) { alert("💡 小朋友，請記得填寫「姓名」與「學號/座號」！"); return; }

      appState.studentName = nameInput;
      appState.studentId   = idInput;
      appState.userAnswers = {};
      appState.currentQuestionIndex = 0;
      appState.elapsedSeconds = 0;

      if (!appState.isInvitedMode) {
        const countRadio = document.querySelector('input[name="question-count"]:checked');
        if (countRadio.value === 'custom') {
          const customVal = parseInt(document.getElementById("custom-question-count").value, 10);
          if (isNaN(customVal) || customVal <= 0) { alert("💡 請輸入正確的自訂題數！"); return; }
          appState.totalQuestionCount = customVal;
        } else {
          appState.totalQuestionCount = parseInt(countRadio.value, 10);
        }
        const selectedCbs = document.querySelectorAll('input[name="range-num"]:checked');
        if (selectedCbs.length === 0) { alert("💡 請至少勾選一個乘數範圍！"); return; }
        appState.selectedRanges = Array.from(selectedCbs).map(cb => parseInt(cb.value, 10));
      }

      generateQuizQuestions();
      document.getElementById("home-view").classList.add("hidden");
      document.getElementById("quiz-view").classList.remove("hidden");
      startTimer();
      loadQuestion(0);
    }

    function generateQuizQuestions() {
      let pool = [];
      appState.selectedRanges.forEach(a => {
        for (let b = 2; b <= 9; b++) pool.push({ a, b });
      });
      shuffleArray(pool);
      let generated = [];
      while (generated.length < appState.totalQuestionCount) {
        const copyPool = pool.map(item => ({ ...item }));
        shuffleArray(copyPool);
        generated = generated.concat(copyPool);
      }
      appState.questions = generated.slice(0, appState.totalQuestionCount).map((q, idx) => ({
        id: idx + 1,
        a: q.a,
        b: q.b,
        correctAns: q.a * q.b,
        options: generateConfusingOptions(q.a, q.b),
        mnemonic: getChineseMnemonic(q.a, q.b)
      }));
    }

    function generateConfusingOptions(a, b) {
      const correctAns = a * b;
      const candidates = new Set();
      for (let offset of [-1,1,-2,2,-3,3]) { const n = correctAns + offset; if (n > 0 && n <= 100) candidates.add(n); }
      if (correctAns > 10 && correctAns % 10 !== 0) {
        const swapped = (correctAns % 10) * 10 + Math.floor(correctAns / 10);
        if (swapped !== correctAns && swapped <= 100) candidates.add(swapped);
      }
      [(a-1)*b,(a+1)*b,a*(b-1),a*(b+1),(a-1)*(b-1),(a+1)*(b+1)].forEach(p => {
        if (p > 0 && p !== correctAns && p <= 100) candidates.add(p);
      });
      const candList = shuffleArray(Array.from(candidates));
      const wrongAnswers = [];
      for (let i = 0; i < candList.length && wrongAnswers.length < 3; i++) {
        if (candList[i] !== correctAns) wrongAnswers.push(candList[i]);
      }
      while (wrongAnswers.length < 3) {
        const r = Math.floor(Math.random() * 80) + 2;
        if (r !== correctAns && !wrongAnswers.includes(r)) wrongAnswers.push(r);
      }
      return shuffleArray([correctAns, ...wrongAnswers]);
    }

    function getChineseMnemonic(a, b) {
      const x = Math.min(a, b), y = Math.max(a, b), p = x * y;
      const ch = ['','一','二','三','四','五','六','七','八','九','十'];
      if (p < 10) return `${ch[x]}${ch[y]}得${ch[p]}`;
      const tens = Math.floor(p / 10), ones = p % 10;
      const pCh = tens === 1 ? '十' + (ones > 0 ? ch[ones] : '') : ch[tens] + '十' + (ones > 0 ? ch[ones] : '');
      if (x === 2 && y === 5) return '二五一十';
      return `${ch[x]}${ch[y]}${pCh}`;
    }

    function shuffleArray(array) {
      for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
      }
      return array;
    }

    // ── 測驗頁控制 ────────────────────────────────────────────────────────────
    function loadQuestion(index) {
      if (index < 0 || index >= appState.questions.length) return;
      appState.currentQuestionIndex = index;
      const q = appState.questions[index];
      const percent = ((index + 1) / appState.totalQuestionCount) * 100;
      document.getElementById("progress-text").textContent = `第 ${index+1} / ${appState.totalQuestionCount} 題`;
      document.getElementById("progress-bar").style.width = `${percent}%`;
      document.getElementById("quiz-question").innerHTML = `
        <span class="text-slate-800">${q.a}</span>
        <span class="text-pink-500 mx-3">×</span>
        <span class="text-slate-800">${q.b}</span>
        <span class="text-indigo-500 mx-3">=</span>
        <span class="text-slate-400">?</span>`;

      const container = document.getElementById("options-container");
      container.innerHTML = "";
      const letters = ['A','B','C','D'];
      const styles = [
        'bg-blue-50/70 hover:bg-blue-100/80 border-blue-200 text-blue-900',
        'bg-orange-50/70 hover:bg-orange-100/80 border-orange-200 text-orange-900',
        'bg-purple-50/70 hover:bg-purple-100/80 border-purple-200 text-purple-900',
        'bg-pink-50/70 hover:bg-pink-100/80 border-pink-200 text-pink-900'
      ];
      q.options.forEach((val, i) => {
        const isSelected = appState.userAnswers[index] === val;
        const activeClass = isSelected
          ? 'ring-4 ring-indigo-400 border-indigo-500 bg-gradient-to-r from-indigo-50 to-indigo-100/40 scale-[1.01]'
          : 'border-slate-200';
        container.insertAdjacentHTML('beforeend', `
          <button onclick="selectOption(${index}, ${val})"
            class="option-btn w-full p-5 rounded-2xl border-2 text-2xl font-black text-left flex items-center gap-4 transition-all shadow-sm ${styles[i % styles.length]} ${activeClass}">
            <span class="w-9 h-9 rounded-full flex items-center justify-center bg-white border shadow-sm text-sm text-slate-500 shrink-0 font-black">
              ${isSelected ? '<i class="fa-solid fa-check text-indigo-600"></i>' : letters[i]}
            </span>
            <span class="tracking-wide">${val}</span>
          </button>`);
      });

      document.getElementById("prev-btn").disabled = index === 0;
      const nextBtn = document.getElementById("next-btn");
      if (index === appState.questions.length - 1) {
        nextBtn.innerHTML = `繳交試卷 📝`;
        nextBtn.className = "flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-emerald-500 hover:bg-emerald-600 transition-all flex items-center justify-center gap-1.5 shadow-md";
      } else {
        nextBtn.innerHTML = `下一題 <i class="fa-solid fa-chevron-right"></i>`;
        nextBtn.className = "flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-indigo-500 hover:bg-indigo-600 transition-all flex items-center justify-center gap-1.5 shadow-md";
      }
    }

    function selectOption(qIndex, val) { appState.userAnswers[qIndex] = val; loadQuestion(qIndex); }
    function prevQuestion() { if (appState.currentQuestionIndex > 0) loadQuestion(appState.currentQuestionIndex - 1); }
    function nextQuestion() {
      if (appState.currentQuestionIndex < appState.questions.length - 1) loadQuestion(appState.currentQuestionIndex + 1);
      else submitQuiz();
    }

    // ── 繳交 ─────────────────────────────────────────────────────────────────
    function submitQuiz() {
      let emptyCount = 0;
      for (let i = 0; i < appState.totalQuestionCount; i++) {
        if (appState.userAnswers[i] === undefined) emptyCount++;
      }
      const confirmMsg = emptyCount > 0
        ? `💡 還有 ${emptyCount} 題沒有回答！確定要交卷嗎？`
        : "💡 所有題目都回答完畢了！確定交卷嗎？";
      if (!confirm(confirmMsg)) return;
      clearInterval(appState.timerInterval);
      document.getElementById("quiz-view").classList.add("hidden");
      document.getElementById("result-view").classList.remove("hidden");
      saveAndRenderResults();
    }

    async function saveAndRenderResults() {
      let correctCount = 0;
      const parsedAnswers = [];
      appState.questions.forEach((q, idx) => {
        const uAns = appState.userAnswers[idx];
        const isCorrect = uAns === q.correctAns;
        if (isCorrect) correctCount++;
        parsedAnswers.push({ equation:`${q.a} × ${q.b}`, correct:isCorrect, userAns:uAns !== undefined ? uAns : '未答', correctAns:q.correctAns, mnemonic:q.mnemonic });
      });

      const finalScore = Math.round((correctCount / appState.totalQuestionCount) * 100);
      document.getElementById("final-score").textContent = finalScore;
      document.getElementById("res-name").textContent = appState.studentName;
      document.getElementById("res-id").textContent = appState.studentId;
      document.getElementById("res-time").textContent = formatTime(appState.elapsedSeconds);
      document.getElementById("res-correct-rate").textContent = `${correctCount} / ${appState.totalQuestionCount} 題`;

      const commentEl = document.getElementById("score-comment");
      if (finalScore === 100) { commentEl.textContent = "完美全對！你是乘法大師！🏆"; commentEl.className = "text-lg md:text-xl font-black text-center text-emerald-600 pt-1"; triggerCelebration(true); }
      else if (finalScore >= 80) { commentEl.textContent = "超級棒！實力不凡喔！🌟"; commentEl.className = "text-lg md:text-xl font-black text-center text-indigo-600 pt-1"; triggerCelebration(false); }
      else if (finalScore >= 60) { commentEl.textContent = "及格了，再接再厲！✨"; commentEl.className = "text-lg md:text-xl font-black text-center text-amber-600 pt-1"; }
      else { commentEl.textContent = "加油加油！多練習就會更厲害！💪"; commentEl.className = "text-lg md:text-xl font-black text-center text-rose-500 pt-1"; }

      const reviewContainer = document.getElementById("review-list");
      reviewContainer.innerHTML = "";
      parsedAnswers.forEach((ans, idx) => {
        const stateColor = ans.correct ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800';
        const stateBadge = ans.correct
          ? '<span class="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded-full font-black"><i class="fa-solid fa-circle-check mr-1"></i>答對</span>'
          : '<span class="bg-rose-100 text-rose-800 text-[10px] px-2 py-0.5 rounded-full font-black"><i class="fa-solid fa-circle-xmark mr-1"></i>答錯</span>';
        reviewContainer.insertAdjacentHTML('beforeend', `
          <div class="p-3.5 rounded-xl border-2 ${stateColor} space-y-1">
            <div class="flex justify-between items-center text-xs"><span class="font-bold text-slate-400">第 ${idx+1} 題</span>${stateBadge}</div>
            <div class="text-xl font-black tracking-wide">${ans.equation} = ${ans.correctAns}</div>
            <div class="text-xs font-bold flex gap-4"><span>你答：${ans.userAns}</span><span>正確：${ans.correctAns}</span></div>
            <div class="bg-white/75 p-2 rounded-lg text-[10px] font-bold text-slate-500 border border-dashed flex items-start gap-1">
              <span>💡 口訣：</span><span>「${ans.mnemonic}，所以答案是 ${ans.correctAns} 喔！」</span>
            </div>
          </div>`);
      });

      // 儲存到 Firebase（或 localStorage）
      const record = {
        id: 'rec_' + Date.now(),
        ts: Date.now(),
        studentId: appState.studentId,
        studentName: appState.studentName,
        score: finalScore,
        elapsedSeconds: appState.elapsedSeconds,
        ranges: appState.selectedRanges,
        date: new Date().toLocaleDateString('zh-TW'),
        answers: parsedAnswers
      };

      await saveRecord(record);

      const b64 = btoa(unescape(encodeURIComponent(JSON.stringify(record))));
      document.getElementById("submission-code-box").value = `99QUIZ-${b64}`;

      refreshConsoleData();
    }

    // ── 教師主控台 ────────────────────────────────────────────────────────────
    async function refreshConsoleData() {
      const records = await loadAllRecords();
      const total = records.length;
      document.getElementById("stat-total-count").textContent = total;

      if (total === 0) {
        document.getElementById("stat-avg-score").innerHTML = '0 <span class="text-xs">分</span>';
        document.getElementById("stat-avg-time").innerHTML = '0 <span class="text-xs">秒</span>';
        document.getElementById("stat-pass-rate").textContent = "0%";
        document.getElementById("leaderboard-tbody").innerHTML = `<tr><td colspan="6" class="text-center p-6 text-slate-400 font-bold">目前無任何測驗數據</td></tr>`;
        document.getElementById("accuracy-analysis-list").innerHTML = `<div class="col-span-2 text-center p-6 text-slate-400 font-bold">暫無分析數據</div>`;
        return;
      }

      const sumScore = records.reduce((s,r) => s + r.score, 0);
      const sumTime  = records.reduce((s,r) => s + r.elapsedSeconds, 0);
      const passCount = records.filter(r => r.score >= 60).length;
      document.getElementById("stat-avg-score").innerHTML = `${Math.round(sumScore/total)} <span class="text-xs">分</span>`;
      document.getElementById("stat-avg-time").innerHTML  = `${Math.round(sumTime/total)} <span class="text-xs">秒</span>`;
      document.getElementById("stat-pass-rate").textContent = `${Math.round((passCount/total)*100)}%`;

      const rankedRecords = [...records].sort((a,b) => b.score - a.score || a.elapsedSeconds - b.elapsedSeconds);
      const tbody = document.getElementById("leaderboard-tbody");
      tbody.innerHTML = "";
      rankedRecords.forEach((r, idx) => {
        const medal = idx===0?'🥇':idx===1?'🥈':idx===2?'🥉':`${idx+1}`;
        tbody.insertAdjacentHTML('beforeend', `
          <tr class="hover:bg-slate-50 transition-colors font-bold text-slate-600">
            <td class="p-3 text-sm">${medal}</td>
            <td class="p-3">${r.studentId}</td>
            <td class="p-3 text-slate-800">${r.studentName}</td>
            <td class="p-3 text-center text-amber-600 font-black">${r.score}</td>
            <td class="p-3 text-center text-slate-500">${formatTime(r.elapsedSeconds)}</td>
            <td class="p-3 text-center text-xs text-slate-400">${r.date}</td>
          </tr>`);
      });

      const eqStats = {};
      records.forEach(r => {
        r.answers.forEach(ans => {
          if (!eqStats[ans.equation]) eqStats[ans.equation] = { correct:0, total:0 };
          eqStats[ans.equation].total++;
          if (ans.correct) eqStats[ans.equation].correct++;
        });
      });

      const analysisContainer = document.getElementById("accuracy-analysis-list");
      analysisContainer.innerHTML = "";
      Object.keys(eqStats).map(eq => {
        const rate = Math.round((eqStats[eq].correct / eqStats[eq].total) * 100);
        return { eq, rate, ...eqStats[eq] };
      }).sort((a,b) => a.rate - b.rate).forEach(item => {
        const barColor = item.rate >= 80 ? 'bg-emerald-500' : item.rate >= 60 ? 'bg-amber-500' : 'bg-rose-500';
        const bgTrack  = item.rate >= 80 ? 'bg-emerald-50'  : item.rate >= 60 ? 'bg-amber-50'  : 'bg-rose-50';
        analysisContainer.insertAdjacentHTML('beforeend', `
          <div class="p-3 rounded-xl border border-slate-100 shadow-sm flex flex-col justify-between space-y-1.5 bg-white">
            <div class="flex justify-between items-center text-xs font-black">
              <span class="text-base text-slate-800">${item.eq}</span>
              <span class="text-slate-500">答對率：<span class="${item.rate < 60 ? 'text-rose-600':'text-emerald-600'} text-sm">${item.rate}%</span> (${item.correct}/${item.total}次)</span>
            </div>
            <div class="w-full ${bgTrack} h-2 rounded-full overflow-hidden">
              <div class="${barColor} h-full" style="width:${item.rate}%"></div>
            </div>
          </div>`);
      });

      const studentSelector = document.getElementById("student-selector");
      const currentSelected = studentSelector.value;
      studentSelector.innerHTML = '<option value="">-- 請選擇學生 --</option>';
      const studentSet = {};
      records.forEach(r => { studentSet[`${r.studentId}_${r.studentName}`] = { id:r.studentId, name:r.studentName }; });
      Object.keys(studentSet).forEach(key => {
        const item = studentSet[key];
        studentSelector.insertAdjacentHTML('beforeend', `<option value="${key}" ${currentSelected===key?'selected':''}> 座號 ${item.id} - ${item.name}</option>`);
      });
      loadStudentHistory();
    }

    async function loadStudentHistory() {
      const val = document.getElementById("student-selector").value;
      const container = document.getElementById("student-history-timeline");
      container.innerHTML = "";
      if (!val) { container.innerHTML = `<div class="text-center py-4 text-slate-400 font-bold">請先選擇一位學生</div>`; return; }

      const [id, name] = val.split('_');
      const records = await loadAllRecords();
      const personal = records.filter(r => r.studentId === id && r.studentName === name);

      personal.forEach((r, idx) => {
        const wrongAnswers = r.answers.filter(a => !a.correct).map(a => `${a.equation}=${a.correctAns}(你寫${a.userAns})`);
        const wrongTxt = wrongAnswers.length > 0
          ? `<div class="text-rose-500 mt-1 font-bold">❌ 答錯：${wrongAnswers.join('、')}</div>`
          : `<div class="text-emerald-600 mt-1 font-bold">🎉 完美全對！</div>`;
        container.insertAdjacentHTML('beforeend', `
          <div class="p-2.5 bg-white rounded-lg border border-slate-200 hover:shadow-sm transition-all">
            <div class="flex justify-between items-center text-[10px] text-slate-400 font-bold">
              <span>第 ${personal.length - idx} 次挑戰 - ${r.date}</span>
              <span class="text-amber-600 text-xs font-black">得分：${r.score} 分</span>
            </div>
            <div class="mt-1 font-bold text-slate-600">作答時間：${formatTime(r.elapsedSeconds)}</div>
            ${wrongTxt}
          </div>`);
      });
    }

    // ── 分享連結 ──────────────────────────────────────────────────────────────
    function generateCustomShareLink() {
      const customTitle = document.getElementById("share-quiz-title").value.trim() || "九九乘法大挑戰 🚀";
      let customCount = document.getElementById("share-quiz-count").value;
      if (customCount === 'custom') {
        customCount = parseInt(document.getElementById("share-quiz-custom-count").value, 10);
        if (isNaN(customCount) || customCount <= 0) { alert("💡 請輸入合法的自訂分享題數！"); return; }
      } else { customCount = parseInt(customCount, 10); }
      if (appState.shareSelectedRanges.length === 0) { alert("💡 請至少勾選一個乘數範圍！"); return; }
      const shareObj = { title:customTitle, count:customCount, ranges:appState.shareSelectedRanges };
      try {
        const b64 = btoa(unescape(encodeURIComponent(JSON.stringify(shareObj))));
        const shareUrl = `${window.location.origin}${window.location.pathname}?quiz=${b64}`;
        navigator.clipboard.writeText(shareUrl).then(() => {
          alert(`🎉 分享連結已複製！\n【${shareObj.title}（共${shareObj.count}題）】`);
        }).catch(() => alert(`連結：${shareUrl}\n（請手動複製）`));
      } catch(e) { console.error("產生連結出錯:", e); }
    }

    // ── 匯入代碼 ──────────────────────────────────────────────────────────────
    async function importStudentCodes() {
      const textarea = document.getElementById("import-codes-input");
      const lines = textarea.value.split('\\n');
      let successCount = 0, duplicateCount = 0, failCount = 0;
      const records = await loadAllRecords();

      for (const line of lines) {
        const cleanLine = line.trim();
        if (!cleanLine) continue;
        if (cleanLine.startsWith("99QUIZ-")) {
          try {
            const record = JSON.parse(decodeURIComponent(escape(atob(cleanLine.replace("99QUIZ-","")))));
            if (record && record.id) {
              const exist = records.some(r => r.id === record.id || (r.studentId===record.studentId && r.elapsedSeconds===record.elapsedSeconds && r.score===record.score && r.date===record.date));
              if (exist) { duplicateCount++; }
              else {
                await saveRecord(record);
                records.unshift(record);
                successCount++;
              }
            } else failCount++;
          } catch(e) { failCount++; }
        } else failCount++;
      }

      refreshConsoleData();
      textarea.value = "";
      alert(`📊 匯入結果：\n✅ 成功：${successCount} 筆\n⚠️ 重複：${duplicateCount} 筆\n❌ 失敗：${failCount} 筆`);
    }

    // ── 清空紀錄 ──────────────────────────────────────────────────────────────
    async function clearAllRecords() {
      if (confirm("⚠️ 確定要清空所有班級紀錄嗎？此動作無法復原！")) {
        await deleteAllRecords();
        refreshConsoleData();
        alert("班級紀錄已清空！");
      }
    }

    // ── UI 切換 ───────────────────────────────────────────────────────────────
    function switchConsoleTab(tabId) {
      ['tab-leaderboard','tab-analysis','tab-history','tab-sync'].forEach(tid => {
        document.getElementById(tid).classList.add("hidden");
        document.getElementById(`btn-${tid}`).className = "flex-1 py-2 font-black border-b-2 border-transparent text-slate-400 hover:text-slate-600 transition-all";
      });
      document.getElementById(tabId).classList.remove("hidden");
      document.getElementById(`btn-${tabId}`).className = "flex-1 py-2 font-black border-b-2 border-indigo-600 text-indigo-700 transition-all";
    }

    function toggleViewMode() {
      const isStudent = appState.viewMode === 'student';
      appState.viewMode = isStudent ? 'console' : 'student';
      const toggleBtn = document.getElementById("toggle-console-btn");
      const btnText   = document.getElementById("mode-btn-text");

      if (appState.viewMode === 'console') {
        ['home-view','quiz-view','result-view'].forEach(id => document.getElementById(id).classList.add("hidden"));
        document.getElementById("console-view").classList.remove("hidden");
        btnText.textContent = "返回學生首頁";
        toggleBtn.className = "bg-white/80 backdrop-blur-sm border-2 border-emerald-100 text-emerald-700 text-xs md:text-sm font-bold px-4 py-2 rounded-xl shadow-sm hover:bg-emerald-50 transition-all flex items-center gap-1.5";
        refreshConsoleData();
      } else {
        document.getElementById("console-view").classList.add("hidden");
        document.getElementById("home-view").classList.remove("hidden");
        btnText.textContent = "切換至教師主控台";
        toggleBtn.className = "bg-white/80 backdrop-blur-sm border-2 border-indigo-100 text-indigo-700 text-xs md:text-sm font-bold px-4 py-2 rounded-xl shadow-sm hover:bg-indigo-50 transition-all flex items-center gap-1.5";
      }
    }

    // ── 計時 ─────────────────────────────────────────────────────────────────
    function startTimer() {
      appState.elapsedSeconds = 0;
      updateTimerDisplay();
      appState.timerInterval = setInterval(() => { appState.elapsedSeconds++; updateTimerDisplay(); }, 1000);
    }
    function updateTimerDisplay() {
      const m = Math.floor(appState.elapsedSeconds / 60);
      const s = appState.elapsedSeconds % 60;
      document.getElementById("timer-display").textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }
    function formatTime(totalSecs) {
      const m = Math.floor(totalSecs / 60), s = totalSecs % 60;
      return m > 0 ? `${m}分${s}秒` : `${s}秒`;
    }

    function copySubmissionCode() {
      const box = document.getElementById("submission-code-box");
      box.select();
      navigator.clipboard.writeText(box.value).then(() => alert("🎉 作答代碼已複製！"));
    }

    function triggerCelebration(isPerfect) {
      if (!window.confetti) return;
      if (isPerfect) {
        const end = Date.now() + 2000;
        const interval = setInterval(() => {
          if (Date.now() > end) return clearInterval(interval);
          confetti({ startVelocity:25, spread:360, ticks:50, zIndex:100, origin:{ x:Math.random(), y:Math.random()-0.2 } });
        }, 200);
      } else {
        confetti({ particleCount:80, spread:60, origin:{ y:0.65 } });
      }
    }

    function exportToPDF() {
      const element = document.getElementById('report-card-container');
      const opt = {
        margin: 10,
        filename: `99乘法成績單_${appState.studentName}_${appState.studentId}.pdf`,
        image: { type:'jpeg', quality:0.98 },
        html2canvas: { scale:2, useCORS:true, letterRendering:true },
        jsPDF: { unit:'mm', format:'a4', orientation:'portrait' }
      };
      html2pdf().set(opt).from(element).save();
    }

    async function exportToCSV() {
      const records = await loadAllRecords();
      if (records.length === 0) { alert("無可用數據進行匯出"); return; }
      const headers = ["學號","姓名","得分","作答時間(秒)","日期","考題範圍"];
      const rows = records.map(r => [r.studentId, r.studentName, r.score, r.elapsedSeconds, r.date, `"${r.ranges.join(', ')} 乘法"`]);
      const csvContent = [headers.join(","), ...rows.map(row => row.join(","))].join("\\r\\n");
      const blob = new Blob(["\\uFEFF" + csvContent], { type:'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", "99乘法班級成績彙整表.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    function restartQuiz() {
      document.getElementById("result-view").classList.add("hidden");
      document.getElementById("home-view").classList.remove("hidden");
    }
  </script>
</body>
</html>"""

# 將 Firebase config 注入 HTML
HTML_FINAL = HTML_CONTENT.replace("{firebaseConfigJson}", firebase_config_json)

# ── 渲染 HTML 元件 ────────────────────────────────────────────────────────────
components.html(HTML_FINAL, height=1000, scrolling=True)