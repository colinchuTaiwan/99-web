"""
99乘法我最強 🚀 — Streamlit 版 v2
- 每題30秒倒數，答對得分 = 30 - 秒數（越快分越高）
- 排行榜只保留，移除：跨裝置代碼、清空紀錄、分享、學生歷程、答對率
- Firebase Realtime Database（JS SDK）+ localStorage 降級
- 訪客計數：firebase_admin Python SDK
"""

import json
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

# ── Firebase Admin 初始化（訪客計數）─────────────────────────────────────────
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

# ── Firebase Web SDK 設定（給 JS 用）─────────────────────────────────────────
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
    FIREBASE_CONFIG = {}

firebase_config_json = json.dumps(FIREBASE_CONFIG)

# ── 側邊欄 ────────────────────────────────────────────────────────────────────
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
    st.caption("本工具僅供學習娛樂使用，請搭配正式課程使用。")

# ── HTML 主體 ─────────────────────────────────────────────────────────────────
HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>99乘法我最強 🚀</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@300..700&family=Noto+Sans+TC:wght@400;700;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
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
              '0%, 100%': { transform: 'scale(1)' },
              '50%': { transform: 'scale(1.02)' },
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

    /* 每題倒數圓形進度條 */
    #countdown-ring {
      transform: rotate(-90deg);
      transform-origin: 50% 50%;
    }
    #countdown-ring circle.track {
      fill: none; stroke: #e2e8f0; stroke-width: 5;
    }
    #countdown-ring circle.progress {
      fill: none; stroke-width: 5;
      stroke-linecap: round;
      stroke-dasharray: 188.4;   /* 2π×30 */
      stroke-dashoffset: 0;
      transition: stroke-dashoffset 1s linear, stroke 0.3s;
    }
  </style>
</head>
<body class="font-sans antialiased p-3 md:p-6 flex flex-col items-center justify-between">

  <!-- 背景裝飾 -->
  <div class="fixed inset-0 pointer-events-none overflow-hidden opacity-20 select-none z-0">
    <div class="absolute text-4xl top-10 left-10 animate-bounce-slow" style="animation-delay:0.5s">🎈</div>
    <div class="absolute text-5xl bottom-20 left-20 animate-bounce-slow" style="animation-delay:1.2s">✨</div>
    <div class="absolute text-4xl top-24 right-12 animate-bounce-slow" style="animation-delay:0.1s">🎨</div>
    <div class="absolute text-5xl bottom-16 right-24 animate-bounce-slow" style="animation-delay:2s">🚀</div>
    <div class="absolute text-4xl top-1/2 left-8 animate-bounce-slow" style="animation-delay:1.5s">⭐</div>
    <div class="absolute text-4xl top-1/3 right-10 animate-bounce-slow" style="animation-delay:0.8s">🎒</div>
  </div>

  <!-- 頂部 -->
  <header class="w-full max-w-2xl flex justify-end items-center z-10 mb-4 px-2">
    <button id="toggle-console-btn" onclick="toggleViewMode()"
      class="bg-white/80 backdrop-blur-sm border-2 border-indigo-100 text-indigo-700 text-xs md:text-sm font-bold px-4 py-2 rounded-xl shadow-sm hover:bg-indigo-50 transition-all flex items-center gap-1.5">
      <i class="fa-solid fa-chart-line"></i> <span id="mode-btn-text">切換至教師主控台</span>
    </button>
  </header>

  <main class="w-full max-w-2xl bg-white/95 backdrop-blur-md rounded-3xl shadow-xl border-4 border-white p-5 md:p-8 z-10 flex-grow mb-6">

    <!-- ① 首頁 -->
    <section id="home-view" class="space-y-5 animate-fade-in">
      <div class="text-center space-y-2">
        <h1 class="text-3xl md:text-5xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 via-pink-500 to-orange-400 py-1">
          99乘法我最強 🚀
        </h1>
        <p class="text-sm text-slate-500 font-bold">每題30秒，答得越快分數越高！</p>
      </div>

      <!-- 姓名/座號 -->
      <div class="bg-blue-50/50 p-5 rounded-2xl border-2 border-indigo-100 space-y-3">
        <h3 class="text-md font-bold text-indigo-700"><i class="fa-solid fa-user-astronaut mr-2"></i>第一步：輸入你的姓名</h3>
        <input type="text" id="student-name" placeholder="例如：小智"
          class="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 focus:border-indigo-400 focus:outline-none text-md font-bold transition-all">
      </div>

      <!-- 題數 -->
      <div class="bg-amber-50/50 p-5 rounded-2xl border-2 border-amber-100 space-y-3">
        <h3 class="text-md font-bold text-amber-700"><i class="fa-solid fa-list-ol mr-2"></i>第二步：選擇挑戰題數</h3>
        <div class="flex flex-wrap gap-3 justify-around items-center" id="question-count-picker">
          <label class="flex-1 min-w-[80px] max-w-[100px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-50 transition-all">
            <input type="radio" name="question-count" value="10" checked class="hidden peer">
            <span class="text-lg font-black text-slate-600 peer-checked:text-amber-600">10 題</span>
            <span class="text-[10px] text-slate-400">標準測驗</span>
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
          <label class="flex-1 min-w-[80px] max-w-[100px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-50 transition-all">
            <input type="radio" name="question-count" value="20" class="hidden peer">
            <span class="text-lg font-black text-slate-600 peer-checked:text-amber-600">20 題</span>
            <span class="text-[10px] text-slate-400">實力升級</span>
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
          <label class="flex-1 min-w-[80px] max-w-[100px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-50 transition-all">
            <input type="radio" name="question-count" value="50" class="hidden peer">
            <span class="text-lg font-black text-slate-600 peer-checked:text-amber-600">50 題</span>
            <span class="text-[10px] text-slate-400">專家挑戰</span>
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
          <label class="flex-1 min-w-[110px] max-w-[130px] flex flex-col items-center p-2.5 bg-white border-2 border-amber-200 rounded-xl cursor-pointer hover:bg-amber-50 transition-all">
            <input type="radio" name="question-count" value="custom" class="hidden peer" id="count-radio-custom">
            <span class="text-xs font-black text-slate-600 peer-checked:text-amber-600 mb-1">自訂題數</span>
            <input type="number" id="custom-question-count" min="1" max="100" value="15"
              onclick="document.getElementById('count-radio-custom').checked = true;"
              class="w-16 px-1.5 py-0.5 border-2 border-amber-100 rounded text-center text-xs font-bold focus:outline-none focus:border-amber-400">
            <div class="w-3.5 h-3.5 rounded-full border border-slate-300 mt-1.5 flex items-center justify-center peer-checked:border-amber-500 peer-checked:bg-amber-500"><div class="w-1.5 h-1.5 rounded-full bg-white"></div></div>
          </label>
        </div>
      </div>



      <div class="text-center pt-2">
        <button onclick="startQuiz()"
          class="w-full md:w-3/4 py-3.5 rounded-2xl text-xl md:text-2xl font-black tracking-widest text-emerald-800 bg-[#E8F8F5] hover:bg-emerald-200/80 border-b-8 border-emerald-300 hover:border-emerald-400 active:border-b-2 hover:scale-[1.01] active:scale-[0.99] transition-all shadow-md animate-pulse-soft">
          開始挑戰 🎯
        </button>
      </div>
    </section>

    <!-- ② 測驗頁面 -->
    <section id="quiz-view" class="hidden space-y-4 animate-fade-in">
      <!-- 頂部狀態列 -->
      <div class="flex justify-between items-center bg-indigo-50/50 p-3 rounded-2xl border border-indigo-100">
        <!-- 總得分 -->
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-slate-500">累計得分</span>
          <span id="running-score" class="text-2xl font-black text-amber-600">0</span>
          <span class="text-xs font-bold text-slate-400">分</span>
        </div>
        <!-- 進度 -->
        <div class="flex flex-col items-end gap-1">
          <span id="progress-text" class="text-xs font-bold text-slate-500">第 1 / 10 題</span>
          <div class="w-24 md:w-36 bg-slate-200 h-2 rounded-full overflow-hidden shadow-inner">
            <div id="progress-bar" class="bg-gradient-to-r from-pink-400 to-indigo-500 h-full w-[10%] rounded-full transition-all duration-300"></div>
          </div>
        </div>
      </div>

      <!-- 每題30秒倒數 + 題目 -->
      <div class="bg-[#FFFDF9] py-8 rounded-2xl border-4 border-dashed border-amber-200 flex flex-col items-center gap-4 shadow-inner relative">
        <!-- 倒數圓圈 -->
        <div class="relative flex items-center justify-center">
          <svg id="countdown-ring" width="70" height="70" viewBox="0 0 70 70">
            <circle class="track" cx="35" cy="35" r="30"/>
            <circle class="progress" id="ring-progress" cx="35" cy="35" r="30" stroke="#6366f1"/>
          </svg>
          <div class="absolute flex flex-col items-center">
            <span id="q-timer-display" class="text-xl font-black text-indigo-700 leading-none">30</span>
            <span class="text-[8px] text-slate-400 font-bold">秒</span>
          </div>
        </div>
        <!-- 題目算式 -->
        <div id="quiz-question" class="text-4xl md:text-5xl font-black text-[#2C3E50] tracking-wider select-none leading-none"></div>
        <!-- 本題得分提示 -->
        <div id="q-score-hint" class="text-xs font-bold text-emerald-600 hidden">
          <i class="fa-solid fa-bolt mr-1"></i>答對得 <span id="q-score-preview">30</span> 分
        </div>
      </div>

      <!-- 選項 -->
      <div class="flex flex-col gap-3" id="options-container"></div>

      <!-- 下一題 / 交卷按鈕 -->
      <div class="flex justify-end pt-2 border-t-2 border-slate-100">
        <button id="next-btn" onclick="nextQuestion()"
          class="flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-indigo-500 hover:bg-indigo-600 shadow-md transition-all flex items-center justify-center gap-1.5">
          下一題 <i class="fa-solid fa-chevron-right"></i>
        </button>
      </div>
    </section>

    <!-- ③ 結算頁面 -->
    <section id="result-view" class="hidden space-y-5 animate-fade-in">
      <div id="report-card-container" class="bg-white p-5 md:p-6 rounded-2xl border-4 border-indigo-50 space-y-4">
        <div class="text-center border-b-2 border-dashed border-indigo-100 pb-3">
          <h2 class="text-2xl font-black text-indigo-700">👑 99乘法大挑戰成績單</h2>
          <p class="text-slate-400 text-[10px] font-bold">每題30秒，越快越高分</p>
        </div>

        <!-- 總分大圓 -->
        <div class="flex flex-col items-center space-y-1">
          <div class="relative flex items-center justify-center">
            <div class="absolute w-28 h-28 bg-amber-100 rounded-full animate-ping opacity-15"></div>
            <div class="w-24 h-24 rounded-full border-4 border-amber-300 bg-amber-50 flex flex-col items-center justify-center shadow-md">
              <span class="text-slate-500 text-[10px] font-bold">總得分</span>
              <span id="final-score" class="text-4xl font-black text-amber-600">0</span>
              <span class="text-slate-500 text-[10px] font-bold">分</span>
            </div>
          </div>
          <div id="score-comment" class="text-lg font-black text-center text-indigo-600 pt-1"></div>
        </div>

        <!-- 基本資訊 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-center">
          <div class="bg-[#F0F8FF] p-2 rounded-xl border border-indigo-50">
            <div class="text-[10px] font-bold text-slate-400">學生姓名</div>
            <div id="res-name" class="text-base font-black text-slate-700 mt-0.5">---</div>
          </div>

          <div class="bg-[#FFFDF0] p-2 rounded-xl border border-amber-50">
            <div class="text-[10px] font-bold text-slate-400">答對題數</div>
            <div id="res-correct" class="text-base font-black text-slate-700 mt-0.5">---</div>
          </div>
          <div class="bg-[#E8F8F5] p-2 rounded-xl border border-emerald-50">
            <div class="text-[10px] font-bold text-slate-400">最高單題得分</div>
            <div id="res-best" class="text-base font-black text-slate-700 mt-0.5">---</div>
          </div>
        </div>

        <!-- 答題明細 -->
        <div class="space-y-2">
          <h3 class="text-sm font-black text-indigo-700 border-l-4 border-indigo-500 pl-1.5">
            <i class="fa-solid fa-square-poll-horizontal mr-1"></i>答題紀錄
          </h3>
          <div id="review-list" class="space-y-2 max-h-[240px] overflow-y-auto pr-1"></div>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row gap-2.5 pt-1">
        <button onclick="exportToPDF()"
          class="flex-1 py-2.5 px-3 rounded-xl font-bold text-sm text-white bg-red-400 hover:bg-red-500 transition-all flex items-center justify-center gap-1.5 shadow-sm">
          <i class="fa-regular fa-file-pdf"></i> 下載成績單 (PDF)
        </button>
        <button onclick="restartQuiz()"
          class="flex-1 py-2.5 px-3 rounded-xl font-black text-sm text-indigo-700 bg-indigo-100 hover:bg-indigo-200 transition-all flex items-center justify-center gap-1.5 shadow-sm">
          <i class="fa-solid fa-rotate-left"></i> 再測一次 🔄
        </button>
      </div>
    </section>

    <!-- ④ 教師主控台（僅排行榜）-->
    <section id="console-view" class="hidden space-y-5 animate-fade-in text-slate-700">
      <div class="border-b-2 border-indigo-100 pb-2.5">
        <h2 class="text-2xl font-black text-indigo-800"><i class="fa-solid fa-graduation-cap mr-1"></i> 教師排行榜</h2>
        <p class="text-xs text-slate-400 font-bold mt-0.5">即時顯示全班累計得分（越快答越高分）</p>
      </div>

      <!-- 統計卡 -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div class="bg-blue-50/60 p-3 rounded-xl border border-blue-100 text-center">
          <div class="text-[10px] font-bold text-blue-500">總施測人次</div>
          <div id="stat-total-count" class="text-2xl font-black text-blue-800 mt-1">0</div>
        </div>
        <div class="bg-emerald-50/60 p-3 rounded-xl border border-emerald-100 text-center">
          <div class="text-[10px] font-bold text-emerald-500">班級平均得分</div>
          <div id="stat-avg-score" class="text-2xl font-black text-emerald-800 mt-1">0</div>
        </div>
        <div class="bg-amber-50/60 p-3 rounded-xl border border-amber-100 text-center">
          <div class="text-[10px] font-bold text-amber-500">最高紀錄</div>
          <div id="stat-max-score" class="text-2xl font-black text-amber-800 mt-1">0</div>
        </div>
      </div>

      <!-- 排行榜 -->
      <div class="overflow-x-auto max-h-[400px] border border-slate-100 rounded-xl">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-500 font-bold border-b border-slate-200 sticky top-0">
              <th class="p-3">名次</th>
              <th class="p-3">學號</th>
              <th class="p-3">姓名</th>
              <th class="p-3 text-center">總得分</th>
              <th class="p-3 text-center">答對題數</th>
              <th class="p-3 text-center">日期</th>
            </tr>
          </thead>
          <tbody id="leaderboard-tbody" class="divide-y divide-slate-100"></tbody>
        </table>
      </div>
    </section>
  </main>

  <footer class="text-xs text-slate-400 font-bold text-center z-10 py-2">
    <p>99乘法我最強 🚀 © 2026 Designed for Happy Learning.</p>
  </footer>

  <script>
    // ── Firebase ──────────────────────────────────────────────────────────────
    const FIREBASE_CONFIG = {firebaseConfigJson};
    let firebaseDB = null, useFirebase = false;
    try {
      if (FIREBASE_CONFIG.apiKey) {
        if (!firebase.apps.length) firebase.initializeApp(FIREBASE_CONFIG);
        firebaseDB = firebase.database();
        useFirebase = true;
      }
    } catch(e) { console.error('Firebase init failed:', e); }

    const DB_KEY = '99_mult_records';
    const FB_PATH = '99quiz_records';

    async function saveRecord(rec) {
      if (useFirebase) {
        try { await firebaseDB.ref(`${FB_PATH}/${rec.id}`).set(rec); return; }
        catch(e) { console.error('FB write fail:', e); }
      }
      const arr = JSON.parse(localStorage.getItem(DB_KEY) || '[]');
      arr.unshift(rec);
      localStorage.setItem(DB_KEY, JSON.stringify(arr));
    }

    async function loadAllRecords() {
      if (useFirebase) {
        try {
          const snap = await firebaseDB.ref(FB_PATH).once('value');
          const data = snap.val();
          return data ? Object.values(data).sort((a,b) => (b.ts||0)-(a.ts||0)) : [];
        } catch(e) { console.error('FB read fail:', e); }
      }
      return JSON.parse(localStorage.getItem(DB_KEY) || '[]');
    }

    // ── 狀態 ──────────────────────────────────────────────────────────────────
    const QUESTION_TIME = 30;  // 每題秒數

    let appState = {
      viewMode: 'student',
      studentName: '', studentId: '',
      totalQuestionCount: 10,
      selectedRanges: [2,3,4,5,6,7,8,9],
      questions: [],
      currentQuestionIndex: 0,
      // 每題答題資訊：{ answered: bool, correct: bool, secsUsed: number, earned: number }
      questionResults: [],
      runningScore: 0,        // 累計得分
      qTimerInterval: null,   // 每題計時器
      qSecondsLeft: QUESTION_TIME,
      answered: false,        // 本題是否已作答
    };

    // ── 初始化 ────────────────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {});



    // ── 開始測驗 ──────────────────────────────────────────────────────────────
    function startQuiz() {
      const name = document.getElementById('student-name').value.trim();
      if (!name) { alert('💡 請填寫你的姓名！'); return; }
      appState.studentName = name;
      appState.studentId   = '';

      const countRadio = document.querySelector('input[name="question-count"]:checked');
      if (countRadio.value === 'custom') {
        const v = parseInt(document.getElementById('custom-question-count').value, 10);
        if (isNaN(v) || v <= 0) { alert('💡 請輸入正確的自訂題數！'); return; }
        appState.totalQuestionCount = v;
      } else {
        appState.totalQuestionCount = parseInt(countRadio.value, 10);
      }

      // 固定全範圍 2~9
      appState.selectedRanges = [2,3,4,5,6,7,8,9];

      generateQuizQuestions();
      appState.questionResults = [];
      appState.runningScore = 0;
      appState.currentQuestionIndex = 0;

      document.getElementById('home-view').classList.add('hidden');
      document.getElementById('quiz-view').classList.remove('hidden');
      loadQuestion(0);
    }

    // ── 產題 ──────────────────────────────────────────────────────────────────
    function generateQuizQuestions() {
      let pool = [];
      appState.selectedRanges.forEach(a => {
        for (let b = 2; b <= 9; b++) pool.push({ a, b });
      });
      shuffleArray(pool);
      let generated = [];
      while (generated.length < appState.totalQuestionCount) {
        generated = generated.concat(shuffleArray(pool.map(x => ({...x}))));
      }
      appState.questions = generated.slice(0, appState.totalQuestionCount).map((q, idx) => ({
        id: idx + 1, a: q.a, b: q.b,
        correctAns: q.a * q.b,
        options: generateConfusingOptions(q.a, q.b),
        mnemonic: getChineseMnemonic(q.a, q.b),
      }));
    }

    function generateConfusingOptions(a, b) {
      const correct = a * b;
      const cands = new Set();
      [-3,-2,-1,1,2,3].forEach(d => { const n = correct+d; if (n>0&&n<=100) cands.add(n); });
      if (correct>10 && correct%10!==0) {
        const sw = (correct%10)*10 + Math.floor(correct/10);
        if (sw!==correct&&sw<=100) cands.add(sw);
      }
      [(a-1)*b,(a+1)*b,a*(b-1),a*(b+1)].forEach(p => { if (p>0&&p!==correct&&p<=100) cands.add(p); });
      const wrong = [];
      for (const c of shuffleArray([...cands])) {
        if (wrong.length === 3) break;
        if (c !== correct) wrong.push(c);
      }
      while (wrong.length < 3) {
        const r = Math.floor(Math.random()*80)+2;
        if (r!==correct&&!wrong.includes(r)) wrong.push(r);
      }
      return shuffleArray([correct, ...wrong]);
    }

    function getChineseMnemonic(a, b) {
      const x = Math.min(a,b), y = Math.max(a,b), p = x*y;
      const ch = ['','一','二','三','四','五','六','七','八','九','十'];
      if (p < 10) return `${ch[x]}${ch[y]}得${ch[p]}`;
      const tens = Math.floor(p/10), ones = p%10;
      const pCh = tens===1 ? '十'+(ones>0?ch[ones]:'') : ch[tens]+'十'+(ones>0?ch[ones]:'');
      if (x===2&&y===5) return '二五一十';
      return `${ch[x]}${ch[y]}${pCh}`;
    }

    function shuffleArray(arr) {
      for (let i = arr.length-1; i > 0; i--) {
        const j = Math.floor(Math.random()*(i+1));
        [arr[i],arr[j]] = [arr[j],arr[i]];
      }
      return arr;
    }

    // ── 載入題目（含每題30秒倒數）────────────────────────────────────────────
    function loadQuestion(index) {
      clearInterval(appState.qTimerInterval);
      appState.qSecondsLeft = QUESTION_TIME;
      appState.answered = false;

      const q = appState.questions[index];
      appState.currentQuestionIndex = index;

      // 進度
      const pct = ((index+1)/appState.totalQuestionCount)*100;
      document.getElementById('progress-text').textContent = `第 ${index+1} / ${appState.totalQuestionCount} 題`;
      document.getElementById('progress-bar').style.width = `${pct}%`;
      document.getElementById('running-score').textContent = appState.runningScore;

      // 題目
      document.getElementById('quiz-question').innerHTML =
        `<span class="text-slate-800">${q.a}</span>
         <span class="text-pink-500 mx-3">×</span>
         <span class="text-slate-800">${q.b}</span>
         <span class="text-indigo-500 mx-3">=</span>
         <span class="text-slate-400">?</span>`;

      // 得分提示初始化
      const hint = document.getElementById('q-score-hint');
      hint.classList.remove('hidden');
      document.getElementById('q-score-preview').textContent = QUESTION_TIME;

      // 倒數環重置
      updateCountdownRing(QUESTION_TIME);
      document.getElementById('q-timer-display').textContent = QUESTION_TIME;

      // 選項
      renderOptions(q, null, false);

      // 下一題按鈕
      const nextBtn = document.getElementById('next-btn');
      nextBtn.disabled = false;
      nextBtn.className = 'flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-slate-300 cursor-not-allowed flex items-center justify-center gap-1.5';
      nextBtn.innerHTML = index === appState.questions.length-1
        ? '查看成績 📊' : '下一題 <i class="fa-solid fa-chevron-right"></i>';

      // 啟動每題計時
      appState.qTimerInterval = setInterval(() => {
        appState.qSecondsLeft--;
        document.getElementById('q-timer-display').textContent = appState.qSecondsLeft;
        document.getElementById('q-score-preview').textContent = appState.qSecondsLeft;
        updateCountdownRing(appState.qSecondsLeft);

        if (appState.qSecondsLeft <= 0) {
          clearInterval(appState.qTimerInterval);
          if (!appState.answered) {
            timeoutQuestion(q);
          }
        }
      }, 1000);
    }

    // 倒數環更新（圓周 2π×30 = 188.4）
    function updateCountdownRing(secsLeft) {
      const total = 188.4;
      const offset = total - (secsLeft / QUESTION_TIME) * total;
      const ring = document.getElementById('ring-progress');
      ring.style.strokeDashoffset = offset;
      // 顏色：綠→黃→紅
      if (secsLeft > 15) ring.style.stroke = '#22c55e';
      else if (secsLeft > 7) ring.style.stroke = '#f59e0b';
      else ring.style.stroke = '#ef4444';
    }

    // 渲染選項按鈕
    function renderOptions(q, selectedVal, locked) {
      const container = document.getElementById('options-container');
      container.innerHTML = '';
      const letters = ['A','B','C','D'];
      const baseStyles = [
        'bg-blue-50/70 border-blue-200 text-blue-900',
        'bg-orange-50/70 border-orange-200 text-orange-900',
        'bg-purple-50/70 border-purple-200 text-purple-900',
        'bg-pink-50/70 border-pink-200 text-pink-900',
      ];

      q.options.forEach((val, i) => {
        let btnClass = `option-btn w-full p-5 rounded-2xl border-2 text-2xl font-black text-left flex items-center gap-4 shadow-sm `;
        let icon = letters[i];

        if (locked) {
          if (val === q.correctAns) {
            btnClass += 'bg-emerald-50 border-emerald-400 text-emerald-900 ring-4 ring-emerald-300';
            icon = '<i class="fa-solid fa-check text-emerald-600"></i>';
          } else if (val === selectedVal) {
            btnClass += 'bg-rose-50 border-rose-400 text-rose-900 opacity-80';
            icon = '<i class="fa-solid fa-xmark text-rose-500"></i>';
          } else {
            btnClass += `${baseStyles[i % 4]} opacity-50`;
          }
        } else {
          btnClass += `${baseStyles[i % 4]} hover:scale-[1.01] cursor-pointer`;
        }

        const clickAttr = locked ? '' : `onclick="selectOption(${q.id-1}, ${val})"`;
        container.insertAdjacentHTML('beforeend', `
          <button ${clickAttr} class="${btnClass}">
            <span class="w-9 h-9 rounded-full flex items-center justify-center bg-white border shadow-sm text-sm text-slate-500 shrink-0 font-black">${icon}</span>
            <span class="tracking-wide">${val}</span>
          </button>`);
      });
    }

    // ── 選答案（答對立即結算，答錯繼續）────────────────────────────────────────
    function selectOption(qIndex, val) {
      if (appState.answered) return;
      clearInterval(appState.qTimerInterval);
      appState.answered = true;

      const q = appState.questions[qIndex];
      const secsUsed = QUESTION_TIME - appState.qSecondsLeft;
      const correct  = val === q.correctAns;
      const earned   = correct ? Math.max(1, appState.qSecondsLeft) : 0;

      appState.runningScore += earned;
      document.getElementById('running-score').textContent = appState.runningScore;

      appState.questionResults.push({
        equation:   `${q.a} × ${q.b}`,
        correctAns: q.correctAns,
        userAns:    val,
        correct,
        secsUsed,
        earned,
        mnemonic:   q.mnemonic,
      });

      // 鎖定選項，顯示正誤
      renderOptions(q, val, true);

      const hint = document.getElementById('q-score-hint');
      hint.classList.remove('hidden');

      if (correct) {
        // ✅ 答對 → 顯示得分，1 秒後出現「查看成績」按鈕，讓使用者自己按
        hint.innerHTML = `<i class="fa-solid fa-star text-amber-500 mr-1"></i>答對！得 <span class="text-amber-600 font-black">${earned}</span> 分（用了 ${secsUsed} 秒）`;
        hint.className = 'text-xs font-bold text-emerald-600';
        // 先隱藏按鈕，1秒後顯示
        const nextBtn = document.getElementById('next-btn');
        nextBtn.classList.add('hidden');
        setTimeout(() => {
          nextBtn.classList.remove('hidden');
          nextBtn.className = 'flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-emerald-500 hover:bg-emerald-600 transition-all flex items-center justify-center gap-1.5 shadow-md';
          nextBtn.innerHTML = '查看成績 📊';
          nextBtn.onclick = () => finishQuiz();
        }, 1000);
      } else {
        // ❌ 答錯 → 顯示錯誤提示，啟用「下一題」繼續作答
        hint.innerHTML = `<i class="fa-solid fa-circle-xmark text-rose-500 mr-1"></i>答錯！正確答案是 ${q.correctAns}，繼續加油！`;
        hint.className = 'text-xs font-bold text-rose-600';

        const nextBtn = document.getElementById('next-btn');
        nextBtn.classList.remove('hidden');
        if (qIndex === appState.questions.length-1) {
          nextBtn.className = 'flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-emerald-500 hover:bg-emerald-600 transition-all flex items-center justify-center gap-1.5 shadow-md';
          nextBtn.innerHTML = '查看成績 📊';
        } else {
          nextBtn.className = 'flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-indigo-500 hover:bg-indigo-600 transition-all flex items-center justify-center gap-1.5 shadow-md';
          nextBtn.innerHTML = '再試一題 <i class="fa-solid fa-chevron-right"></i>';
        }
      }
    }

    // 超時未作答 → 記0分，繼續答題
    function timeoutQuestion(q) {
      appState.answered = true;
      appState.questionResults.push({
        equation: `${q.a} × ${q.b}`,
        correctAns: q.correctAns,
        userAns: '超時',
        correct: false,
        secsUsed: QUESTION_TIME,
        earned: 0,
        mnemonic: q.mnemonic,
      });
      renderOptions(q, null, true);
      const hint = document.getElementById('q-score-hint');
      hint.innerHTML = `<i class="fa-solid fa-clock text-slate-400 mr-1"></i>超時！正確答案是 ${q.correctAns}，繼續下一題`;
      hint.className = 'text-xs font-bold text-slate-500';

      const nextBtn = document.getElementById('next-btn');
      nextBtn.classList.remove('hidden');
      const idx = appState.currentQuestionIndex;
      if (idx === appState.questions.length-1) {
        nextBtn.className = 'flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-emerald-500 hover:bg-emerald-600 transition-all flex items-center justify-center gap-1.5 shadow-md';
        nextBtn.innerHTML = '查看成績 📊';
      } else {
        nextBtn.className = 'flex-1 py-3 px-3 rounded-xl font-bold text-base text-white bg-indigo-500 hover:bg-indigo-600 transition-all flex items-center justify-center gap-1.5 shadow-md';
        nextBtn.innerHTML = '再試一題 <i class="fa-solid fa-chevron-right"></i>';
      }
    }

    // ── 下一題 / 交卷 ─────────────────────────────────────────────────────────
    function nextQuestion() {
      if (!appState.answered) return;   // 還沒作答，不能跳
      const idx = appState.currentQuestionIndex;
      if (idx < appState.questions.length - 1) {
        loadQuestion(idx + 1);
      } else {
        finishQuiz();
      }
    }

    // ── 結算 ──────────────────────────────────────────────────────────────────
    async function finishQuiz() {
      clearInterval(appState.qTimerInterval);
      document.getElementById('quiz-view').classList.add('hidden');
      document.getElementById('result-view').classList.remove('hidden');

      const results = appState.questionResults;
      const correctCount = results.filter(r => r.correct).length;
      const totalScore   = appState.runningScore;
      const bestEarned   = Math.max(...results.map(r => r.earned), 0);

      document.getElementById('final-score').textContent = totalScore;
      document.getElementById('res-name').textContent    = appState.studentName;
      document.getElementById('res-correct').textContent = `${correctCount} / ${appState.totalQuestionCount}`;
      document.getElementById('res-best').textContent    = `${bestEarned} 分`;

      const maxPossible = appState.totalQuestionCount * QUESTION_TIME;
      const pct = Math.round((totalScore / maxPossible) * 100);
      const commentEl = document.getElementById('score-comment');
      if (pct >= 90)      { commentEl.textContent = '完美！神速乘法大師！🏆'; commentEl.className = 'text-lg font-black text-center text-emerald-600 pt-1'; triggerCelebration(true); }
      else if (pct >= 70) { commentEl.textContent = '超級棒！又快又準！🌟';   commentEl.className = 'text-lg font-black text-center text-indigo-600 pt-1'; triggerCelebration(false); }
      else if (pct >= 50) { commentEl.textContent = '不錯喔！繼續加油！✨';   commentEl.className = 'text-lg font-black text-center text-amber-600 pt-1'; }
      else                { commentEl.textContent = '多多練習，速度會更快！💪'; commentEl.className = 'text-lg font-black text-center text-rose-500 pt-1'; }

      // 答題明細
      const reviewContainer = document.getElementById('review-list');
      reviewContainer.innerHTML = '';
      results.forEach((r, idx) => {
        const color = r.correct ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200';
        const badge = r.correct
          ? `<span class="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded-full font-black"><i class="fa-solid fa-check mr-1"></i>+${r.earned}分</span>`
          : `<span class="bg-rose-100 text-rose-800 text-[10px] px-2 py-0.5 rounded-full font-black"><i class="fa-solid fa-xmark mr-1"></i>0分</span>`;
        reviewContainer.insertAdjacentHTML('beforeend', `
          <div class="p-3 rounded-xl border-2 ${color} space-y-1">
            <div class="flex justify-between items-center text-xs">
              <span class="font-bold text-slate-400">第 ${idx+1} 題</span>${badge}
            </div>
            <div class="text-lg font-black">${r.equation} = ${r.correctAns}</div>
            <div class="text-xs font-bold text-slate-500 flex gap-3">
              <span>你答：${r.userAns}</span>
              <span>用時：${r.secsUsed} 秒</span>
            </div>
            <div class="text-[10px] font-bold text-slate-400 border-t border-dashed pt-1">💡 ${r.mnemonic}</div>
          </div>`);
      });

      // 儲存
      const record = {
        id: 'rec_' + Date.now(),
        ts: Date.now(),
        studentId:   appState.studentId,
        studentName: appState.studentName,
        score:       totalScore,
        correctCount,
        totalQuestions: appState.totalQuestionCount,
        ranges: appState.selectedRanges,
        date: new Date().toLocaleDateString('zh-TW'),
      };
      await saveRecord(record);
    }

    // ── 教師主控台 ────────────────────────────────────────────────────────────
    async function refreshConsoleData() {
      const records = await loadAllRecords();
      const total = records.length;
      document.getElementById('stat-total-count').textContent = total;

      if (total === 0) {
        document.getElementById('stat-avg-score').textContent = '0';
        document.getElementById('stat-max-score').textContent = '0';
        document.getElementById('leaderboard-tbody').innerHTML =
          '<tr><td colspan="6" class="text-center p-6 text-slate-400 font-bold">目前無測驗數據</td></tr>';
        return;
      }

      const sumScore = records.reduce((s,r) => s + (r.score||0), 0);
      const maxScore = Math.max(...records.map(r => r.score||0));
      document.getElementById('stat-avg-score').textContent = Math.round(sumScore/total);
      document.getElementById('stat-max-score').textContent = maxScore;

      const ranked = [...records].sort((a,b) => (b.score||0) - (a.score||0));
      const tbody = document.getElementById('leaderboard-tbody');
      tbody.innerHTML = '';
      ranked.forEach((r, idx) => {
        const medal = idx===0?'🥇':idx===1?'🥈':idx===2?'🥉':`${idx+1}`;
        tbody.insertAdjacentHTML('beforeend', `
          <tr class="hover:bg-slate-50 transition-colors font-bold text-slate-600">
            <td class="p-3 text-sm">${medal}</td>
            <td class="p-3">${r.studentId}</td>
            <td class="p-3 text-slate-800">${r.studentName}</td>
            <td class="p-3 text-center text-amber-600 font-black text-base">${r.score}</td>
            <td class="p-3 text-center">${r.correctCount ?? '—'} / ${r.totalQuestions ?? '—'}</td>
            <td class="p-3 text-center text-xs text-slate-400">${r.date}</td>
          </tr>`);
      });
    }

    // ── 畫面切換 ──────────────────────────────────────────────────────────────
    function toggleViewMode() {
      const isStudent = appState.viewMode === 'student';
      appState.viewMode = isStudent ? 'console' : 'student';
      const btn = document.getElementById('toggle-console-btn');
      const txt = document.getElementById('mode-btn-text');

      if (appState.viewMode === 'console') {
        ['home-view','quiz-view','result-view'].forEach(id => document.getElementById(id).classList.add('hidden'));
        document.getElementById('console-view').classList.remove('hidden');
        txt.textContent = '返回學生首頁';
        btn.className = 'bg-white/80 backdrop-blur-sm border-2 border-emerald-100 text-emerald-700 text-xs md:text-sm font-bold px-4 py-2 rounded-xl shadow-sm hover:bg-emerald-50 transition-all flex items-center gap-1.5';
        refreshConsoleData();
      } else {
        document.getElementById('console-view').classList.add('hidden');
        document.getElementById('home-view').classList.remove('hidden');
        txt.textContent = '切換至教師主控台';
        btn.className = 'bg-white/80 backdrop-blur-sm border-2 border-indigo-100 text-indigo-700 text-xs md:text-sm font-bold px-4 py-2 rounded-xl shadow-sm hover:bg-indigo-50 transition-all flex items-center gap-1.5';
      }
    }

    function triggerCelebration(isPerfect) {
      if (!window.confetti) return;
      if (isPerfect) {
        const end = Date.now() + 2000;
        const iv = setInterval(() => {
          if (Date.now() > end) return clearInterval(iv);
          confetti({ startVelocity:25, spread:360, ticks:50, zIndex:100, origin:{ x:Math.random(), y:Math.random()-0.2 } });
        }, 200);
      } else {
        confetti({ particleCount:80, spread:60, origin:{ y:0.65 } });
      }
    }

    function exportToPDF() {
      const el = document.getElementById('report-card-container');
      html2pdf().set({
        margin: 10,
        filename: `99乘法成績單_${appState.studentName}_${appState.studentId}.pdf`,
        image: { type:'jpeg', quality:0.98 },
        html2canvas: { scale:2, useCORS:true },
        jsPDF: { unit:'mm', format:'a4', orientation:'portrait' }
      }).from(el).save();
    }

    function restartQuiz() {
      clearInterval(appState.qTimerInterval);
      document.getElementById('result-view').classList.add('hidden');
      document.getElementById('home-view').classList.remove('hidden');
    }
  </script>
</body>
</html>"""

HTML_FINAL = HTML_CONTENT.replace('{firebaseConfigJson}', firebase_config_json)
components.html(HTML_FINAL, height=1050, scrolling=True)