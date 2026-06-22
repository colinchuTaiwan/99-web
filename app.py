import streamlit as st
import random
import time
import json
from datetime import datetime, timezone, timedelta
import firebase_admin
from firebase_admin import credentials, db
import pytz

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="99乘法我最強 🚀",
    page_icon="🔢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Firebase init ─────────────────────────────────────────────────────────────
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            key_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred, {
                "databaseURL": st.secrets["firebase"]["database_url"]
            })
        except Exception as e:
            st.error(f"Firebase 初始化失敗：{e}")
    return db

firebase_db = init_firebase()

TW_TZ = pytz.timezone("Asia/Taipei")

def get_now_tw():
    return datetime.now(TW_TZ)

# ── Firebase helpers ──────────────────────────────────────────────────────────
def increment_visitor():
    ref = firebase_db.reference("visitors/count")
    try:
        ref.transaction(lambda cur: (cur or 0) + 1)
    except Exception:
        pass

def get_visitor_count():
    try:
        val = firebase_db.reference("visitors/count").get()
        return val or 0
    except Exception:
        return 0

def save_score(name, score, correct, total, elapsed, accuracy):
    now = get_now_tw()
    entry = {
        "name": name,
        "score": score,
        "correct": correct,
        "total": total,
        "elapsed": elapsed,
        "accuracy": round(accuracy, 1),
        "timestamp": now.isoformat(),
        "year": now.year,
        "month": now.month,
        "week": now.isocalendar()[1],
    }
    firebase_db.reference("scores").push(entry)

def get_leaderboard(mode="all"):
    """mode: 'all' | 'year' | 'month' | 'week'"""
    try:
        data = firebase_db.reference("scores").get()
        if not data:
            return []
        now = get_now_tw()
        entries = []
        for k, v in data.items():
            if mode == "week" and v.get("week") != now.isocalendar()[1]:
                continue
            if mode == "month" and (v.get("month") != now.month or v.get("year") != now.year):
                continue
            if mode == "year" and v.get("year") != now.year:
                continue
            entries.append(v)
        entries.sort(key=lambda x: (-x["score"], x["elapsed"]))
        return entries[:20]
    except Exception:
        return []

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #fce4ec 0%, #e3f2fd 40%, #e8f5e9 75%, #fff9c4 100%);
    min-height: 100vh;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; max-width: 760px; }

/* Card */
.card {
    background: rgba(255,255,255,0.88);
    border-radius: 24px;
    padding: 2rem 2.2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.09);
    backdrop-filter: blur(6px);
}

/* Title */
.main-title {
    font-size: 2.6rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg, #f48fb1, #90caf9, #a5d6a7, #fff176);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
    line-height: 1.2;
}
.sub-title {
    text-align: center;
    color: #90a4ae;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

/* Question display */
.question-box {
    background: linear-gradient(135deg, #bbdefb, #f8bbd0);
    border-radius: 20px;
    padding: 1.8rem;
    text-align: center;
    font-size: 2.8rem;
    font-weight: 900;
    color: #37474f;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    letter-spacing: 2px;
}

/* Timer */
.timer-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255,255,255,0.7);
    border-radius: 14px;
    padding: 0.7rem 1.2rem;
    margin-bottom: 1rem;
    font-size: 1.1rem;
    font-weight: 700;
}
.timer-urgent { color: #e53935; animation: pulse 0.6s infinite alternate; }
@keyframes pulse { from {opacity:1} to {opacity:0.5} }

/* Progress bar */
.prog-bar-wrap {
    background: #e0e0e0;
    border-radius: 99px;
    height: 10px;
    margin-bottom: 1rem;
    overflow: hidden;
}
.prog-bar-fill {
    height: 10px;
    border-radius: 99px;
    background: linear-gradient(90deg, #f48fb1, #90caf9);
    transition: width 0.4s;
}

/* Option buttons via CSS */
.opt-btn {
    display: block;
    width: 100%;
    padding: 1rem 1.4rem;
    margin: 0.5rem 0;
    border-radius: 16px;
    border: 3px solid transparent;
    font-size: 1.35rem;
    font-weight: 700;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
}

/* Links section */
.links-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.6rem;
    margin-top: 0.5rem;
}
.link-card {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    background: rgba(255,255,255,0.75);
    border-radius: 12px;
    text-decoration: none;
    color: #37474f;
    font-weight: 700;
    font-size: 0.9rem;
    border: 2px solid #e0e0e0;
    transition: all 0.2s;
}
.link-card:hover {
    background: #bbdefb;
    border-color: #90caf9;
    color: #1565c0;
}

/* Score card */
.score-big {
    font-size: 4rem;
    font-weight: 900;
    text-align: center;
    color: #e91e63;
}
.score-info {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 0.8rem;
    margin: 1rem 0;
}
.score-chip {
    background: #f3e5f5;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    font-weight: 700;
    font-size: 1rem;
    color: #6a1b9a;
    text-align: center;
}

/* Answer review */
.ans-row {
    border-radius: 14px;
    padding: 0.9rem 1.2rem;
    margin: 0.5rem 0;
    font-size: 1rem;
    font-weight: 600;
}
.ans-correct { background: #e8f5e9; border-left: 5px solid #43a047; }
.ans-wrong   { background: #fce4ec; border-left: 5px solid #e53935; }

/* Leaderboard */
.lb-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.7rem 1rem;
    border-radius: 12px;
    margin: 0.3rem 0;
    background: rgba(255,255,255,0.6);
    font-weight: 700;
}
.lb-medal { font-size: 1.4rem; min-width: 2rem; text-align: center; }
.lb-name { flex: 1; color: #37474f; }
.lb-score { color: #e91e63; font-size: 1.1rem; }
.lb-acc { color: #43a047; font-size: 0.9rem; }

/* Visitor badge */
.visitor-badge {
    text-align: center;
    color: #78909c;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* Streamlit button overrides */
.stButton > button {
    border-radius: 14px !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    transition: all 0.2s !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
LINKS = [
    ("📖", "英文測驗挑戰網", "https://english-examine.streamlit.app/"),
    ("➕", "數學測驗挑戰網", "https://math-examine.streamlit.app/"),
    ("✍️", "國語測驗挑戰網", "https://chinese-examine.streamlit.app/"),
    ("🔬", "理化測驗挑戰網", "https://science-examine.streamlit.app/"),
    ("📜", "歷史測驗挑戰網", "https://history-examine.streamlit.app/"),
    ("🏛️", "公民測驗挑戰網", "https://civics-examine.streamlit.app/"),
    ("🧬", "生物測驗挑戰網", "https://biology-examine.streamlit.app/"),
    ("🌍", "地球科學測驗網", "https://earth-science-examine.streamlit.app/"),
    ("📋", "公文專案管理系統", "https://doc-project.streamlit.app/"),
]

MEDAL = ["🥇", "🥈", "🥉"] + ["🔢"] * 17

TIME_PER_Q = 30  # seconds per question

# ── State helpers ─────────────────────────────────────────────────────────────
def ss(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

def reset_quiz():
    for k in ["questions","answers","q_start_times","q_elapsed",
              "cur_q","quiz_start","finished","streak"]:
        if k in st.session_state:
            del st.session_state[k]

# ── Question generation ───────────────────────────────────────────────────────
def generate_questions(n):
    """Generate n unique multiplication questions from 1–9 × 1–9."""
    pool = [(a, b) for a in range(1, 10) for b in range(1, 10)]
    random.shuffle(pool)
    selected = pool[:n]
    questions = []
    for a, b in selected:
        correct = a * b
        # Generate 3 confusing distractors
        distractors = set()
        attempts = 0
        while len(distractors) < 3 and attempts < 200:
            attempts += 1
            kind = random.randint(0, 4)
            if kind == 0:
                d = correct + random.choice([-1, 1, -2, 2])
            elif kind == 1:
                d = (a + random.choice([-1, 1])) * b
            elif kind == 2:
                d = a * (b + random.choice([-1, 1]))
            elif kind == 3:
                d = correct + random.choice([-7, -6, -5, 5, 6, 7])
            else:
                d = random.randint(max(1, correct - 10), correct + 10)
            if d != correct and d > 0:
                distractors.add(d)
        options = [correct] + list(distractors)[:3]
        random.shuffle(options)
        questions.append({
            "a": a, "b": b,
            "correct": correct,
            "options": options,
        })
    return questions

# ── Mnemonic ──────────────────────────────────────────────────────────────────
ZH_NUMS = {1:"一",2:"二",3:"三",4:"四",5:"五",6:"六",7:"七",8:"八",9:"九",
           10:"十",12:"十二",14:"十四",15:"十五",16:"十六",18:"十八",
           20:"二十",21:"二十一",24:"二十四",25:"二十五",27:"二十七",
           28:"二十八",30:"三十",32:"三十二",35:"三十五",36:"三十六",
           40:"四十",42:"四十二",45:"四十五",48:"四十八",49:"四十九",
           54:"五十四",56:"五十六",63:"六十三",64:"六十四",72:"七十二",
           81:"八十一"}

def zh_num(n):
    if n in ZH_NUMS:
        return ZH_NUMS[n]
    tens = n // 10
    ones = n % 10
    if ones == 0:
        return ZH_NUMS.get(tens, str(tens)) + "十"
    return ZH_NUMS.get(tens, str(tens)) + "十" + ZH_NUMS.get(ones, str(ones))

def _n(n):
    return ZH_NUMS.get(n, str(n))

def mnemonic(a, b, c):
    """Generate a Chinese mnemonic for a × b = c."""
    return f"{_n(a)}{'乘以' if a>5 else 'x'}{_n(b)}得{zh_num(c)}，口訣：{_n(a)}{_n(b)}{zh_num(c)}"

# ── Scoring ───────────────────────────────────────────────────────────────────
def calc_score(is_correct, elapsed_sec, streak_before):
    """Returns (points_earned, new_streak)."""
    if not is_correct:
        return 0, 0
    base = max(0, TIME_PER_Q - int(elapsed_sec))
    bonus = max(0, streak_before) * 3  # +3 for each in streak (streak_before already ≥1 means 2nd+)
    return base + bonus, streak_before + 1

# ── Pages ─────────────────────────────────────────────────────────────────────

def page_home():
    st.markdown('<div class="main-title">99乘法我最強 🚀</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">挑戰自我，成為乘法小達人！</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        name = st.text_input("👤 你的姓名", placeholder="請輸入姓名…", key="input_name",
                             max_chars=20)
        st.markdown("### 📝 選擇題數")
        cols = st.columns(3)
        num_q_options = [5, 10, 20]
        cur_num = ss("num_q", 10)
        for i, n in enumerate(num_q_options):
            label = f"{'✅ ' if cur_num == n else ''}{n} 題"
            if cols[i].button(label, key=f"nq_{n}", use_container_width=True):
                st.session_state["num_q"] = n
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🚀 開始測驗", use_container_width=True, type="primary"):
        if not name.strip():
            st.error("請先填寫姓名！")
        else:
            st.session_state["player_name"] = name.strip()
            st.session_state["questions"] = generate_questions(st.session_state.get("num_q", 10))
            st.session_state["answers"] = {}
            st.session_state["q_elapsed"] = {}  # per-question elapsed seconds
            st.session_state["q_start_times"] = {}
            st.session_state["cur_q"] = 0
            st.session_state["quiz_start"] = time.time()
            st.session_state["finished"] = False
            st.session_state["streak"] = 0
            st.session_state["page"] = "quiz"
            increment_visitor()
            st.rerun()

    # Leaderboard preview
    st.markdown("---")
    _render_leaderboard_section()

    # Links
    st.markdown("### 🔗 更多測驗挑戰")
    links_html = '<div class="links-grid">'
    for icon, label, url in LINKS:
        links_html += f'<a class="link-card" href="{url}" target="_blank">{icon} {label}</a>'
    links_html += "</div>"
    st.markdown(links_html, unsafe_allow_html=True)

    # Visitor count
    v = get_visitor_count()
    st.markdown(f'<div class="visitor-badge">👥 累計訪客人數：{v:,}</div>', unsafe_allow_html=True)


def page_quiz():
    qs = st.session_state.get("questions", [])
    cur = st.session_state.get("cur_q", 0)
    total = len(qs)
    answers = st.session_state.get("answers", {})
    streak = st.session_state.get("streak", 0)

    if cur not in st.session_state.get("q_start_times", {}):
        st.session_state.setdefault("q_start_times", {})[cur] = time.time()

    q_start = st.session_state["q_start_times"][cur]
    elapsed_q = time.time() - q_start
    time_left = max(0, TIME_PER_Q - elapsed_q)

    # Total elapsed
    total_elapsed = int(time.time() - st.session_state["quiz_start"])
    mins, secs = divmod(total_elapsed, 60)

    # ── Header bar
    timer_class = "timer-urgent" if time_left <= 5 else ""
    st.markdown(f"""
    <div class="timer-box">
        <span>⏱ 總時間 {mins:02d}:{secs:02d}</span>
        <span>題目 {cur+1} / {total}</span>
        <span class="{timer_class}">⏳ 剩餘 {int(time_left)}s</span>
    </div>
    """, unsafe_allow_html=True)

    # Progress
    pct = int((cur / total) * 100)
    st.markdown(f"""
    <div class="prog-bar-wrap">
        <div class="prog-bar-fill" style="width:{pct}%"></div>
    </div>""", unsafe_allow_html=True)

    # Streak badge
    if streak >= 2:
        st.markdown(f"🔥 連續答對 **{streak}** 題！加油！", unsafe_allow_html=True)

    # Question
    q = qs[cur]
    st.markdown(f'<div class="question-box">{q["a"]} × {q["b"]} = ?</div>',
                unsafe_allow_html=True)

    # Time-out check
    already_answered = cur in answers
    timed_out = time_left <= 0 and not already_answered

    if timed_out:
        # Auto-record as wrong
        st.session_state["answers"][cur] = {"chosen": None, "correct": q["correct"],
                                             "elapsed": TIME_PER_Q, "points": 0}
        st.session_state["streak"] = 0
        st.session_state["q_elapsed"][cur] = TIME_PER_Q
        if cur + 1 < total:
            st.session_state["cur_q"] = cur + 1
            st.rerun()
        else:
            st.session_state["page"] = "result"
            st.rerun()

    # Options
    opts = q["options"]
    chosen = answers.get(cur, {}).get("chosen")

    if not already_answered:
        cols = st.columns(1)
        for opt in opts:
            if st.button(f"　{opt}", key=f"opt_{cur}_{opt}", use_container_width=True):
                elapsed = time.time() - q_start
                is_correct = (opt == q["correct"])
                pts, new_streak = calc_score(is_correct, elapsed, streak if is_correct else 0)
                st.session_state["answers"][cur] = {
                    "chosen": opt,
                    "correct": q["correct"],
                    "elapsed": elapsed,
                    "points": pts,
                    "is_correct": is_correct,
                }
                st.session_state["streak"] = new_streak if is_correct else 0
                st.session_state["q_elapsed"][cur] = elapsed
                # Auto-advance
                if cur + 1 < total:
                    st.session_state["cur_q"] = cur + 1
                st.rerun()
    else:
        # Show answered state
        rec = answers[cur]
        for opt in opts:
            if opt == rec["correct"]:
                st.success(f"✅　{opt}　← 正確答案")
            elif opt == rec.get("chosen"):
                st.error(f"❌　{opt}　← 你的選擇")
            else:
                st.button(f"　{opt}", key=f"opt_{cur}_{opt}_done",
                          use_container_width=True, disabled=True)

    # Navigation
    st.markdown("---")
    nav_c = st.columns([1, 1, 1])
    if nav_c[0].button("◀ 上一題", use_container_width=True, disabled=(cur == 0)):
        st.session_state["cur_q"] = max(0, cur - 1)
        st.rerun()

    if nav_c[2].button("下一題 ▶", use_container_width=True, disabled=(cur == total - 1)):
        st.session_state["cur_q"] = min(total - 1, cur + 1)
        st.rerun()

    # Submit
    st.markdown("")
    answered_count = len(answers)
    submit_label = f"📨 繳交測驗（已答 {answered_count}/{total} 題）"
    if st.button(submit_label, use_container_width=True, type="primary"):
        # Fill unanswered as wrong
        for i, qq in enumerate(qs):
            if i not in st.session_state["answers"]:
                st.session_state["answers"][i] = {
                    "chosen": None, "correct": qq["correct"],
                    "elapsed": TIME_PER_Q, "points": 0, "is_correct": False
                }
        st.session_state["page"] = "result"
        st.rerun()

    # Auto-refresh every second
    time.sleep(1)
    st.rerun()


def page_result():
    qs = st.session_state.get("questions", [])
    answers = st.session_state.get("answers", {})
    name = st.session_state.get("player_name", "匿名")
    quiz_start = st.session_state.get("quiz_start", time.time())

    total_elapsed = int(time.time() - quiz_start)
    mins, secs = divmod(total_elapsed, 60)
    elapsed_str = f"{mins:02d}:{secs:02d}"

    total = len(qs)
    correct_count = sum(1 for i, rec in answers.items() if rec.get("is_correct"))
    total_score = sum(rec.get("points", 0) for rec in answers.values())
    accuracy = (correct_count / total * 100) if total else 0

    # Save to Firebase (only once)
    if not st.session_state.get("score_saved"):
        save_score(name, total_score, correct_count, total, total_elapsed, accuracy)
        st.session_state["score_saved"] = True

    st.markdown(f'<div class="main-title">🎉 測驗結果</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="score-big">{total_score} 分</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="score-info">
        <div class="score-chip">👤 {name}</div>
        <div class="score-chip">⏱ {elapsed_str}</div>
        <div class="score-chip">✅ {correct_count}/{total} 題</div>
        <div class="score-chip">🎯 {accuracy:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Detail review
    st.markdown("### 📋 詳細解析")
    for i, q in enumerate(qs):
        rec = answers.get(i, {})
        is_cor = rec.get("is_correct", False)
        chosen = rec.get("chosen")
        pts = rec.get("points", 0)
        elapsed_sec = rec.get("elapsed", 0)
        css_cls = "ans-correct" if is_cor else "ans-wrong"
        icon = "✅" if is_cor else "❌"
        chosen_txt = str(chosen) if chosen is not None else "（未作答）"
        memo = mnemonic(q["a"], q["b"], q["correct"])
        st.markdown(f"""
        <div class="ans-row {css_cls}">
            {icon} 第{i+1}題　<b>{q['a']} × {q['b']} = ?</b><br>
            你的選擇：<b>{chosen_txt}</b>　正確答案：<b>{q['correct']}</b>　
            得分：<b>{pts}</b>　用時：<b>{elapsed_sec:.1f}s</b><br>
            <small>💡 {memo}</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    _render_leaderboard_section()

    if st.button("🔄 再挑戰一次", use_container_width=True, type="primary"):
        reset_quiz()
        st.session_state["score_saved"] = False
        st.session_state["page"] = "home"
        st.rerun()


def _render_leaderboard_section():
    st.markdown("### 🏆 排行榜")
    tab_labels = ["🏆 總排行", "📅 年排行", "🗓️ 月排行", "📆 週排行"]
    tabs = st.tabs(tab_labels)
    modes = ["all", "year", "month", "week"]
    for tab, mode in zip(tabs, modes):
        with tab:
            entries = get_leaderboard(mode)
            if not entries:
                st.info("還沒有記錄，快去挑戰吧！")
            else:
                for rank, e in enumerate(entries):
                    medal = MEDAL[rank] if rank < len(MEDAL) else "🔢"
                    st.markdown(f"""
                    <div class="lb-row">
                        <span class="lb-medal">{medal}</span>
                        <span class="lb-name">{e['name']}</span>
                        <span class="lb-score">{e['score']}分</span>
                        <span class="lb-acc">{e.get('accuracy',0):.1f}%</span>
                        <span style="color:#90a4ae;font-size:0.85rem">{e['correct']}/{e['total']}</span>
                    </div>
                    """, unsafe_allow_html=True)


# ── Router ────────────────────────────────────────────────────────────────────
def main():
    page = ss("page", "home")
    if page == "home":
        page_home()
    elif page == "quiz":
        page_quiz()
    elif page == "result":
        page_result()

main()
