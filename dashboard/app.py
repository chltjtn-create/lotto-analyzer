"""Streamlit dashboard — Lotto 6/45 Analysis Hub (v2 Premium)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 내부 모듈들은 "from lotto_analyzer.xxx import yyy" 형태로 서로를 import한다.
# 로컬에서는 D:\GoogleDrive(부모 폴더)가 항상 실행 경로라 이 폴더 자체가
# lotto_analyzer 패키지로 자연히 인식되지만, Streamlit Cloud는 저장소를
# lotto-analyzer(GitHub repo 이름, 하이픈)로 클론하므로 그 이름의 패키지가
# 없어서 깨진다. 저장소 루트를 lotto_analyzer 패키지로 별칭 등록해 해결한다.
if "lotto_analyzer" not in sys.modules:
    import types

    _alias = types.ModuleType("lotto_analyzer")
    _alias.__path__ = [str(ROOT)]
    sys.modules["lotto_analyzer"] = _alias

import streamlit as st

st.set_page_config(
    page_title="로또 6/45 분석 허브",
    page_icon="🎱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (v2 Premium) ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@700;800;900&display=swap');

/* ── CSS Variables ── */
:root {
    --bg:        #0e1015;
    --bg-card:   #16191f;
    --bg-raise:  #1d2029;
    --border:    #252932;
    --border-h:  #363d4a;
    --accent:    #7c3aed;
    --accent2:   #06b6d4;
    --gold:      #f59e0b;
    --text:      #e8eaf0;
    --muted:     #636b78;
    --success:   #10b981;
    --warn:      #f59e0b;
    --danger:    #ef4444;
    --hot:       #ef4444;
    --cold:      #06b6d4;
}

/* ── Base ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stAppViewContainer"] { background: var(--bg); }
[data-testid="block-container"] { padding: 1.5rem 2.5rem 3rem; }
html { font-size: 17px; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); word-break: keep-all; overflow-wrap: break-word; }
h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; letter-spacing: -0.02em; }

/* ── Sidebar (always expanded, non-collapsible) ── */
[data-testid="stSidebar"] {
    background: #0a0c10 !important;
    border-right: 1px solid var(--border) !important;
    transform: none !important;
    visibility: visible !important;
    width: 300px !important;
    min-width: 300px !important;
    max-width: 300px !important;
}
[data-testid="stSidebar"] > div {
    width: 300px !important;
    min-width: 300px !important;
}
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stExpandSidebarButton"] { display: none !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.75rem;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0e1015 0%, #1a0f2e 45%, #0a1628 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -100px; right: -100px;
    width: 350px; height: 350px;
    background: radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 65%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -80px; left: 25%;
    width: 250px; height: 250px;
    background: radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 65%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin: 0;
}
.hero-sub {
    font-size: 0.9rem;
    color: var(--muted);
    margin-top: 6px;
}
.hero-badge {
    display: inline-block;
    background: rgba(124,58,237,0.2);
    border: 1px solid rgba(124,58,237,0.4);
    color: #c4b5fd;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Cards ── */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.3rem 1.6rem;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease;
}
.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0;
    transition: opacity .3s ease;
}
.card:hover { border-color: var(--border-h); box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 20px rgba(124,58,237,0.12); transform: translateY(-3px); }
.card:hover::before { opacity: 1; }
.card-glass {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.07);
}

/* ── Section heading ── */
.sec {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
}

/* ── KPI Cards ── */
.kpi-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    min-height: 108px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: border-color .25s, box-shadow .25s;
}
.kpi-wrap:hover { border-color: var(--accent); box-shadow: 0 0 20px rgba(124,58,237,0.15); }
.kpi-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    white-space: nowrap;
}
.kpi-val {
    font-family: 'Outfit', sans-serif;
    font-size: 2.1rem;
    font-weight: 900;
    color: var(--text);
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
}
.kpi-delta-pos { color: var(--success); font-size: 0.78rem; font-weight: 600; margin-top: 2px; }
.kpi-delta-neg { color: var(--danger);  font-size: 0.78rem; font-weight: 600; margin-top: 2px; }
.kpi-delta-neu { color: var(--muted);   font-size: 0.78rem; font-weight: 600; margin-top: 2px; }

/* ── Lotto Balls ── */
.balls-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 6px 0; }
.ball {
    width: 48px; height: 48px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.7);
    position: relative;
    cursor: default;
    transition: transform .2s ease, filter .2s ease;
    animation: ballPop .45s cubic-bezier(0.34,1.56,0.64,1) both;
}
.ball::after {
    content: '';
    position: absolute;
    top: 8px; left: 12px;
    width: 12px; height: 8px;
    background: radial-gradient(ellipse, rgba(255,255,255,0.65), transparent);
    border-radius: 50%;
    pointer-events: none;
}
.ball:hover { transform: scale(1.18) translateY(-3px); filter: brightness(1.25); z-index: 10; }

/* Zone colors — official Korean Lotto 645 */
.b1  { background: radial-gradient(circle at 33% 33%, #fde68a, #b45309); box-shadow: 0 4px 14px rgba(251,191,36,.65), inset 0 -4px 10px rgba(0,0,0,.35); }
.b11 { background: radial-gradient(circle at 33% 33%, #93c5fd, #1d4ed8); box-shadow: 0 4px 14px rgba(59,130,246,.65), inset 0 -4px 10px rgba(0,0,0,.35); }
.b21 { background: radial-gradient(circle at 33% 33%, #fca5a5, #b91c1c); box-shadow: 0 4px 14px rgba(239,68,68,.65), inset 0 -4px 10px rgba(0,0,0,.35); }
.b31 { background: radial-gradient(circle at 33% 33%, #d1d5db, #4b5563); box-shadow: 0 4px 14px rgba(107,114,128,.55), inset 0 -4px 10px rgba(0,0,0,.35); }
.b41 { background: radial-gradient(circle at 33% 33%, #86efac, #065f46); box-shadow: 0 4px 14px rgba(16,185,129,.65), inset 0 -4px 10px rgba(0,0,0,.35); }

/* Bonus ball */
.bonus {
    background: radial-gradient(circle at 33% 33%, #fef9c3, #ca8a04);
    box-shadow: 0 0 8px #fbbf24, 0 0 20px #fbbf24, 0 0 40px #f59e0b, inset 0 -4px 10px rgba(0,0,0,.35);
    animation: ballPop .45s cubic-bezier(0.34,1.56,0.64,1) both, neonPulse 2.2s ease-in-out infinite;
}
.ball:nth-child(1) { animation-delay: .00s; }
.ball:nth-child(2) { animation-delay: .08s; }
.ball:nth-child(3) { animation-delay: .16s; }
.ball:nth-child(4) { animation-delay: .24s; }
.ball:nth-child(5) { animation-delay: .32s; }
.ball:nth-child(6) { animation-delay: .40s; }
.ball:nth-child(7) { animation-delay: .55s; }
@keyframes ballPop {
    0%   { opacity:0; transform:scale(0.3) rotate(-20deg); }
    75%  { transform:scale(1.08) rotate(4deg); }
    100% { opacity:1; transform:scale(1) rotate(0); }
}
@keyframes neonPulse {
    0%,100% { box-shadow: 0 0 8px #fbbf24, 0 0 20px #fbbf24, 0 0 40px #f59e0b, inset 0 -4px 10px rgba(0,0,0,.35); }
    50%      { box-shadow: 0 0 14px #fbbf24, 0 0 36px #fbbf24, 0 0 70px #f59e0b, inset 0 -4px 10px rgba(0,0,0,.35); }
}

/* ── Badges ── */
.badge-hot  { display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(239,68,68,.18),rgba(239,68,68,.05));border:1px solid rgba(239,68,68,.4);color:#fca5a5;font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px; }
.badge-warm { display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(245,158,11,.18),rgba(245,158,11,.05));border:1px solid rgba(245,158,11,.4);color:#fde68a;font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px; }
.badge-cold { display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(6,182,212,.18),rgba(6,182,212,.05));border:1px solid rgba(6,182,212,.4);color:#67e8f9;font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px; }

/* ── Combo card ── */
.combo {
    background: var(--bg-raise);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 10px;
    transition: border-color .2s, box-shadow .2s, transform .2s;
}
.combo:hover { border-color: var(--accent); box-shadow: 0 6px 24px rgba(124,58,237,0.2); transform: translateY(-2px); }
.combo-meta { font-size: 0.74rem; color: var(--muted); margin-top: 6px; font-family: 'JetBrains Mono', monospace; }

/* ── Draw history row ── */
.draw-row { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid var(--border); }
.draw-row:last-child { border-bottom: none; }
.draw-no { font-family:'JetBrains Mono',monospace; font-size:.9rem; font-weight:700; color:var(--accent2); min-width:52px; }
.draw-date { font-size:.78rem; color:var(--muted); min-width:76px; }

/* ── Disclaimer ── */
.disclaimer {
    background: rgba(239,68,68,0.07);
    border-left: 3px solid rgba(239,68,68,0.5);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.8rem;
    color: #fca5a5;
    margin-top: 10px;
}

/* ── Streamlit overrides ── */
[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: .9rem 1.1rem;
    transition: border-color .25s, box-shadow .25s;
}
[data-testid="stMetric"]:hover { border-color: var(--accent); box-shadow: 0 0 18px rgba(124,58,237,.14); }
[data-testid="stMetricLabel"] > div { font-size:.7rem !important; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:var(--muted) !important; }
[data-testid="stMetricValue"] > div { font-family:'Outfit',sans-serif !important; font-size:1.9rem !important; font-weight:900 !important; }

/* ── Progress bar ── */
.prog-wrap { margin-bottom: 1rem; }
.prog-label { display:flex; justify-content:space-between; color:var(--muted); font-size:.78rem; margin-bottom:5px; }
.prog-track { background:var(--bg-raise); border-radius:999px; height:7px; overflow:hidden; }
.prog-fill { height:100%; border-radius:999px; box-shadow:0 0 8px var(--accent); animation:fillGrow 1.2s ease-out both; }
@keyframes fillGrow { from { width:0%; } }

/* ── Tab styling ── */
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif;
    font-size: .85rem;
    font-weight: 600;
    color: var(--muted);
    padding: 6px 16px;
    border-radius: 8px 8px 0 0;
}
[data-testid="stTabs"] [aria-selected="true"] { color: var(--text) !important; border-bottom: 2px solid var(--accent) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

# ── Imports (after set_page_config) ─────────────────────────────────────────
from datetime import date

from database.db_manager import LottoDatabaseManager
from analysis.frequency import analyze_number_frequency
from analysis.pattern import analyze_patterns
from analysis.scoring import calculate_number_scores
from domain.models import LottoDraw

# ── Helpers ─────────────────────────────────────────────────────────────────

def _bz(n: int) -> str:
    """Return ball CSS class for number n."""
    if n <= 10:  return "b1"
    if n <= 20:  return "b11"
    if n <= 30:  return "b21"
    if n <= 40:  return "b31"
    return "b41"

def balls_html(nums, bonus=None, size=48) -> str:
    """Render lotto balls as HTML string."""
    s = f'<div class="balls-row" style="--bs:{size}px">'
    for n in nums:
        s += f'<div class="ball {_bz(n)}" style="width:{size}px;height:{size}px">{n}</div>'
    if bonus is not None:
        s += f'<span style="color:var(--muted);font-size:1.2rem;line-height:{size}px">+</span>'
        s += f'<div class="ball bonus" style="width:{size}px;height:{size}px">{bonus}</div>'
    s += '</div>'
    return s

def kpi(label: str, value: str, delta: str = "", delta_type: str = "neu") -> str:
    dclass = f"kpi-delta-{delta_type}"
    d_html = f'<div class="{dclass}">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-wrap">
        <div class="kpi-label">{label}</div>
        <div class="kpi-val">{value}</div>
        {d_html}
    </div>"""

def prog_bar(label: str, value: float, max_val: float, color: str = "var(--accent)") -> str:
    pct = min(value / max_val * 100, 100) if max_val else 0
    return f"""
    <div class="prog-wrap">
        <div class="prog-label"><span>{label}</span>
            <span style="font-family:'JetBrains Mono',monospace;color:var(--text)">{value:.0f}</span>
        </div>
        <div class="prog-track">
            <div class="prog-fill" style="width:{pct:.1f}%;background:{color}"></div>
        </div>
    </div>"""

# ── Data loading ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _load_raw():
    db = LottoDatabaseManager()
    db.initialize_database()
    return db.list_draws(), db.list_recommendations(), db.list_evaluations()

@st.cache_data(ttl=60, show_spinner=False)
def _load_analysis(_n_draws: int):
    db = LottoDatabaseManager()
    db.initialize_database()
    draws = db.list_draws()
    stats = analyze_number_frequency(draws)
    patterns = analyze_patterns(draws)
    scores = calculate_number_scores(draws)
    return stats, patterns, scores

def refresh():
    _load_raw.clear()
    _load_analysis.clear()
    st.rerun()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 8px 20px;border-bottom:1px solid var(--border);margin-bottom:12px">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.35rem;font-weight:700;color:#fff;line-height:1.2">
            🎱 로또 분석기
        </div>
        <div style="font-size:.72rem;color:var(--muted);margin-top:4px;text-transform:uppercase;letter-spacing:.1em">
            Lotto 6/45 Analysis Hub
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "메뉴",
        ["🏠 홈", "📊 번호 통계", "🔥 과열·냉각 분석", "🔍 패턴 분석",
         "🎰 조합 생성", "🧪 백테스트", "📋 추천 이력", "🔄 데이터 업데이트"],
        label_visibility="collapsed",
    )
    st.markdown("<hr style='border-color:var(--border);margin:16px 0'>", unsafe_allow_html=True)
    if st.button("↺ 캐시 새로고침", use_container_width=True):
        refresh()

# ── Load data ────────────────────────────────────────────────────────────────
try:
    draws, recommendations, evaluations = _load_raw()
except Exception as exc:
    st.error(f"DB 연결 오류: {exc}")
    st.stop()

if not draws:
    st.warning("저장된 회차 데이터가 없습니다. 데이터 업데이트 페이지에서 데이터를 불러오세요.")
    st.stop()

stats, patterns, scores = _load_analysis(len(draws))
latest = draws[-1]
total = len(draws)

# ════════════════════════════════════════════════════════════════════════════
# 🏠 홈
# ════════════════════════════════════════════════════════════════════════════
if page == "🏠 홈":
    st.markdown(f"""
    <div class="hero">
        <div class="hero-badge">실시간 분석</div>
        <div class="hero-title">🎱 로또 6/45 분석 허브</div>
        <div class="hero-sub">총 {total:,}회차 데이터 기반 · 최신 {latest.draw_no}회 반영</div>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    hot_nums  = [n for n, sc in scores.items() if sc.category == "Hot"]
    cold_nums = [n for n, sc in scores.items() if sc.category == "Cold"]
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1: st.markdown(kpi("총 분석 회차", f"{total:,}회", f"제 1회 ~ {latest.draw_no}회", "neu"), unsafe_allow_html=True)
    with c2: st.markdown(kpi("최근 회차", f"{latest.draw_no}회", str(latest.draw_date), "neu"), unsafe_allow_html=True)
    with c3: st.markdown(kpi("🔥 핫 번호", f"{len(hot_nums)}개", "최근 출현 활발", "pos"), unsafe_allow_html=True)
    with c4: st.markdown(kpi("❄️ 콜드 번호", f"{len(cold_nums)}개", "장기 미출현", "neg"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="sec">🏆 최신 당첨 번호</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card">
            <div style="font-family:'JetBrains Mono',monospace;font-size:.8rem;color:var(--muted);margin-bottom:10px">
                제 {latest.draw_no}회 · {latest.draw_date}
            </div>
            {balls_html(sorted(latest.numbers), latest.bonus, size=52)}
        </div>
        """, unsafe_allow_html=True)

        if recommendations:
            st.markdown('<div class="sec" style="margin-top:1.2rem">🎯 최근 추천 번호</div>', unsafe_allow_html=True)
            recent_recommendations = sorted(recommendations, key=lambda r: r.target_draw_no, reverse=True)[:3]
            for rec in recent_recommendations:
                c = rec.combination
                st.markdown(f"""
                <div class="combo">
                    {balls_html(c.numbers, size=42)}
                    <div class="combo-meta">
                        {c.strategy} · 홀짝 {c.odd_even} · 고저 {c.high_low} ·
                        합계 {c.total_sum} · 🔥{c.hot_count} 🌡️{c.warm_count} ❄️{c.cold_count}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sec">🔥 핫 번호</div>', unsafe_allow_html=True)
        hot_sorted = sorted(hot_nums, key=lambda n: scores[n].final_score, reverse=True)[:9]
        rows = [hot_sorted[i:i+3] for i in range(0, len(hot_sorted), 3)]
        for row in rows:
            st.markdown(balls_html(row, size=42), unsafe_allow_html=True)

        st.markdown('<div class="sec" style="margin-top:1.2rem">❄️ 콜드 번호</div>', unsafe_allow_html=True)
        cold_sorted = sorted(cold_nums, key=lambda n: scores[n].final_score)[:9]
        rows = [cold_sorted[i:i+3] for i in range(0, len(cold_sorted), 3)]
        for row in rows:
            st.markdown(balls_html(row, size=42), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# 📊 번호 통계
# ════════════════════════════════════════════════════════════════════════════
elif page == "📊 번호 통계":
    import plotly.graph_objects as go

    st.markdown('<div class="sec">📊 번호별 출현 통계</div>', unsafe_allow_html=True)

    period_opt = {"전체": None, "최근 10회": 10, "최근 30회": 30, "최근 100회": 100, "최근 300회": 300}
    period = st.segmented_control("기간", list(period_opt.keys()), default="전체")
    p_key = period_opt.get(period or "전체")

    nums = list(range(1, 46))
    if p_key is None:
        counts = [stats[n].total_count for n in nums]
    else:
        counts = [stats[n].recent_counts.get(p_key, 0) for n in nums]

    zone_colors = {1: "#f59e0b", 11: "#3b82f6", 21: "#ef4444", 31: "#6b7280", 41: "#10b981"}
    def zone_color(n):
        for k in sorted(zone_colors.keys(), reverse=True):
            if n >= k: return zone_colors[k]
        return "#6b7280"

    bar_colors = [zone_color(n) for n in nums]
    cat_colors = {"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#06b6d4"}
    border_colors = [cat_colors.get(scores[n].category, "#334155") for n in nums]

    fig = go.Figure(go.Bar(
        x=[str(n) for n in nums], y=counts,
        marker=dict(color=bar_colors, line=dict(color=border_colors, width=2.5)),
        hovertemplate="번호 <b>%{x}</b><br>출현 <b>%{y}</b>회<extra></extra>"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#94a3b8"),
        xaxis=dict(gridcolor="#1e293b", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#1e293b"),
        margin=dict(l=30, r=10, t=20, b=30), height=320, showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 상세 테이블", "📉 미출현 분석"])

    with tab1:
        n_sel = st.selectbox("번호 선택", nums, format_func=lambda x: f"{x}번", key="stat_sel")
        s = stats[n_sel]
        sc = scores[n_sel]
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("전체 출현", f"{s.total_count}회")
        with c2: st.metric("최근 10회", f"{s.recent_counts.get(10,0)}회")
        with c3: st.metric("최근 30회", f"{s.recent_counts.get(30,0)}회")
        with c4: st.metric("최근 100회", f"{s.recent_counts.get(100,0)}회")
        badge = {"Hot": '<span class="badge-hot">🔥 HOT</span>',
                 "Warm": '<span class="badge-warm">🌡️ WARM</span>',
                 "Cold": '<span class="badge-cold">❄️ COLD</span>'}.get(sc.category, "")
        st.markdown(f"""
        <div class="card" style="margin-top:14px">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
                {balls_html([n_sel], size=52)}
                <div>
                    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;font-weight:700">{n_sel}번</div>
                    {badge}
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.82rem">
                <div>미출현 회차: <b style="color:var(--text);font-family:'JetBrains Mono',monospace">{s.missing_draws}</b></div>
                <div>최종 점수: <b style="color:var(--accent);font-family:'JetBrains Mono',monospace">{sc.final_score:.1f}</b></div>
                <div>빈도 점수: <b style="font-family:'JetBrains Mono',monospace">{sc.frequency_score:.1f}</b></div>
                <div>최근성 점수: <b style="font-family:'JetBrains Mono',monospace">{sc.recency_score:.1f}</b></div>
                <div>갭 점수: <b style="font-family:'JetBrains Mono',monospace">{sc.gap_score:.1f}</b></div>
                <div>모멘텀 점수: <b style="font-family:'JetBrains Mono',monospace">{sc.momentum_score:.1f}</b></div>
            </div>
            {prog_bar("종합 점수", sc.final_score, 100, "var(--accent)")}
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        missing = [(n, stats[n].missing_draws) for n in nums]
        missing.sort(key=lambda x: x[1], reverse=True)
        m_nums, m_vals = zip(*missing)
        m_colors = ["#ef4444" if v >= 20 else "#f59e0b" if v >= 10 else "#334155" for v in m_vals]
        fig2 = go.Figure(go.Bar(
            x=[str(n) for n in m_nums], y=list(m_vals),
            marker=dict(color=m_colors, line=dict(color="rgba(0,0,0,0)")),
            hovertemplate="번호 <b>%{x}</b><br>미출현 <b>%{y}</b>회<extra></extra>"
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#1e293b"),
            margin=dict(l=30, r=10, t=20, b=30), height=300, showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
        top_missing = [n for n, _ in missing[:10]]
        st.markdown(f'<div style="font-size:.8rem;color:var(--muted)">미출현 상위 10개 번호</div>', unsafe_allow_html=True)
        st.markdown(balls_html(top_missing, size=42), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# 🔥 과열·냉각 분석
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔥 과열·냉각 분석":
    import plotly.graph_objects as go

    st.markdown('<div class="sec">🔥 번호 점수 분석 (과열·냉각)</div>', unsafe_allow_html=True)

    nums = list(range(1, 46))
    sorted_by_score = sorted(nums, key=lambda n: scores[n].final_score, reverse=True)

    # Score breakdown stacked bar
    fig = go.Figure()
    score_fields = [
        ("빈도 점수", "frequency_score", "#7c3aed"),
        ("최근성 점수", "recency_score", "#06b6d4"),
        ("갭 점수",    "gap_score",       "#10b981"),
        ("모멘텀 점수","momentum_score",  "#f59e0b"),
    ]
    for label, field, color in score_fields:
        fig.add_trace(go.Bar(
            name=label,
            x=[str(n) for n in sorted_by_score],
            y=[getattr(scores[n], field) for n in sorted_by_score],
            marker_color=color,
            hovertemplate=f"{label}: <b>%{{y:.1f}}</b><extra></extra>"
        ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono", color="#94a3b8"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8"), orientation="h", y=1.08),
        xaxis=dict(gridcolor="#1e293b", tickfont=dict(size=9)),
        yaxis=dict(gridcolor="#1e293b"),
        margin=dict(l=30, r=10, t=50, b=30), height=340
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_hot, c_warm, c_cold = st.columns(3, gap="medium")

    hot_list  = sorted([n for n in nums if scores[n].category == "Hot"],  key=lambda n: scores[n].final_score, reverse=True)
    warm_list = sorted([n for n in nums if scores[n].category == "Warm"], key=lambda n: scores[n].final_score, reverse=True)
    cold_list = sorted([n for n in nums if scores[n].category == "Cold"], key=lambda n: scores[n].final_score)

    with c_hot:
        st.markdown(f"""
        <div class="card" style="border-color:rgba(239,68,68,.3)">
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;color:#fca5a5;margin-bottom:10px">
                🔥 HOT ({len(hot_list)}개)
            </div>
            {balls_html(hot_list, size=40)}
        </div>""", unsafe_allow_html=True)

    with c_warm:
        st.markdown(f"""
        <div class="card" style="border-color:rgba(245,158,11,.3)">
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;color:#fde68a;margin-bottom:10px">
                🌡️ WARM ({len(warm_list)}개)
            </div>
            {balls_html(warm_list, size=40)}
        </div>""", unsafe_allow_html=True)

    with c_cold:
        st.markdown(f"""
        <div class="card" style="border-color:rgba(6,182,212,.3)">
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;color:#67e8f9;margin-bottom:10px">
                ❄️ COLD ({len(cold_list)}개)
            </div>
            {balls_html(cold_list, size=40)}
        </div>""", unsafe_allow_html=True)

    # Radar chart for selected number
    st.markdown('<div class="sec" style="margin-top:1.5rem">🎯 번호별 점수 레이더</div>', unsafe_allow_html=True)
    n_sel = st.selectbox("번호 선택", list(range(1, 46)), format_func=lambda x: f"{x}번", key="radar_sel")
    sc = scores[n_sel]
    categories = ["빈도", "최근성", "갭", "모멘텀", "빈도"]
    vals = [sc.frequency_score, sc.recency_score, sc.gap_score, sc.momentum_score, sc.frequency_score]
    fig_r = go.Figure(go.Scatterpolar(
        r=vals, theta=categories, fill="toself",
        fillcolor="rgba(124,58,237,0.18)", line=dict(color="#7c3aed", width=2),
        hovertemplate="%{theta}: <b>%{r:.1f}</b><extra></extra>"
    ))
    fig_r.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,100], gridcolor="#1e293b", tickfont=dict(color="#636b78")),
            angularaxis=dict(gridcolor="#1e293b", tickfont=dict(color="#94a3b8"))
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=30, b=30), height=320
    )
    col_r, col_info = st.columns([2, 1])
    with col_r:
        st.plotly_chart(fig_r, use_container_width=True)
    with col_info:
        badge = {"Hot": '<span class="badge-hot">🔥 HOT</span>',
                 "Warm": '<span class="badge-warm">🌡️ WARM</span>',
                 "Cold": '<span class="badge-cold">❄️ COLD</span>'}.get(sc.category, "")
        st.markdown(f"""
        <div class="card" style="margin-top:8px">
            {balls_html([n_sel], size=52)}
            <div style="margin-top:12px">{badge}</div>
            <div style="margin-top:14px">
                {prog_bar("빈도", sc.frequency_score, 100, "#7c3aed")}
                {prog_bar("최근성", sc.recency_score, 100, "#06b6d4")}
                {prog_bar("갭", sc.gap_score, 100, "#10b981")}
                {prog_bar("모멘텀", sc.momentum_score, 100, "#f59e0b")}
                {prog_bar("종합", sc.final_score, 100, "var(--accent)")}
            </div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# 🔍 패턴 분석
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔍 패턴 분석":
    import plotly.graph_objects as go

    st.markdown('<div class="sec">🔍 당첨 번호 패턴 분석</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("연속번호 보유 회차", f"{patterns.consecutive_draw_count}회")
    with c2: st.metric("연속번호 출현율", f"{patterns.consecutive_rate*100:.1f}%")
    with c3: st.metric("합계 평균", f"{patterns.sum_average:.1f}")
    with c4: st.metric("합계 중앙값", f"{patterns.sum_median:.1f}")

    st.markdown("<br>", unsafe_allow_html=True)
    tab_oe, tab_hl, tab_sum, tab_sec, tab_con = st.tabs(["홀짝 분포", "고저 분포", "합계 분포", "구간 분포", "연속번호"])

    def _bar(x, y, color, htitle):
        fig = go.Figure(go.Bar(
            x=x, y=y, marker_color=color,
            hovertemplate="%{x}: <b>%{y}</b>회<extra></extra>"
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
            margin=dict(l=30, r=10, t=20, b=30), height=280, showlegend=False
        )
        return fig

    with tab_oe:
        oe = patterns.odd_even_frequency
        oe_sorted = sorted(oe.items(), key=lambda x: x[1], reverse=True)
        keys, vals = zip(*oe_sorted) if oe_sorted else ([], [])
        colors_oe = ["#7c3aed" if i == 0 else "#1e293b" for i in range(len(keys))]
        st.plotly_chart(_bar(list(keys), list(vals), colors_oe, "홀짝"), use_container_width=True)
        best = oe_sorted[0] if oe_sorted else ("—", 0)
        st.markdown(f'<div style="text-align:center;color:var(--muted);font-size:.82rem">가장 많은 패턴: <b style="color:var(--text)">{best[0]}</b> ({best[1]}회)</div>', unsafe_allow_html=True)

    with tab_hl:
        hl = patterns.high_low_frequency
        hl_sorted = sorted(hl.items(), key=lambda x: x[1], reverse=True)
        keys, vals = zip(*hl_sorted) if hl_sorted else ([], [])
        colors_hl = ["#ef4444" if i == 0 else "#1e293b" for i in range(len(keys))]
        st.plotly_chart(_bar(list(keys), list(vals), colors_hl, "고저"), use_container_width=True)

    with tab_sum:
        sums = [p.total_sum for p in patterns.patterns]
        fig_h = go.Figure(go.Histogram(
            x=sums, nbinsx=50, marker_color="#7c3aed",
            hovertemplate="합계 %{x}<br>빈도: <b>%{y}</b>회<extra></extra>"
        ))
        fig_h.add_vline(x=patterns.sum_average, line_dash="dash", line_color="#f59e0b",
                        annotation_text=f"평균 {patterns.sum_average:.0f}", annotation_font_color="#f59e0b")
        fig_h.add_vline(x=patterns.sum_median, line_dash="dash", line_color="#10b981",
                        annotation_text=f"중앙값 {patterns.sum_median:.0f}", annotation_font_color="#10b981")
        fig_h.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
            margin=dict(l=30, r=10, t=30, b=30), height=300, showlegend=False
        )
        st.plotly_chart(fig_h, use_container_width=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("합계 최솟값", f"{patterns.sum_min}")
        with c2: st.metric("합계 최댓값", f"{patterns.sum_max}")
        with c3: st.metric("추천 범위", "100 ~ 180")

    with tab_sec:
        sec_keys = ["1-10", "11-20", "21-30", "31-40", "41-45"]
        sec_vals = [patterns.section_totals.get(k, 0) for k in sec_keys]
        sec_colors = ["#f59e0b", "#3b82f6", "#ef4444", "#6b7280", "#10b981"]
        fig_s = go.Figure(go.Bar(
            x=sec_keys, y=sec_vals, marker_color=sec_colors,
            hovertemplate="%{x}: <b>%{y}</b>회<extra></extra>"
        ))
        fig_s.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
            margin=dict(l=30, r=10, t=20, b=30), height=280, showlegend=False
        )
        st.plotly_chart(fig_s, use_container_width=True)

    with tab_con:
        consec_counts = {}
        for p in patterns.patterns:
            k = f"{p.consecutive_pair_count}쌍"
            consec_counts[k] = consec_counts.get(k, 0) + 1
        keys = sorted(consec_counts.keys())
        vals = [consec_counts[k] for k in keys]
        colors_c = ["#7c3aed" if k == "1쌍" else "#334155" for k in keys]
        fig_c = go.Figure(go.Bar(
            x=keys, y=vals, marker_color=colors_c,
            hovertemplate="%{x}: <b>%{y}</b>회<extra></extra>"
        ))
        fig_c.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", color="#94a3b8"),
            xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
            margin=dict(l=30, r=10, t=20, b=30), height=280, showlegend=False
        )
        st.plotly_chart(fig_c, use_container_width=True)
        rate = patterns.consecutive_rate * 100
        st.markdown(f"""
        <div class="card">
            <div style="font-size:.9rem;color:var(--muted)">
                전체 {total}회차 중 연속번호가 포함된 회차:
                <b style="color:var(--text);font-family:'JetBrains Mono',monospace">{patterns.consecutive_draw_count}회 ({rate:.1f}%)</b>
            </div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# 🎰 조합 생성
# ════════════════════════════════════════════════════════════════════════════
elif page == "🎰 조합 생성":
    from generator.combination import CombinationGenerator, CombinationConstraints

    st.markdown('<div class="sec">🎰 번호 조합 생성</div>', unsafe_allow_html=True)

    with st.form("combo_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            strategy = st.selectbox("전략", ["Hybrid", "Hot", "Balanced", "Cold"], key="strat")
            count = st.number_input("생성 수", 1, 20, 5, key="cnt")
        with c2:
            sum_min = st.number_input("합계 최솟값", 21, 230, 100, key="smin")
            sum_max = st.number_input("합계 최댓값", 21, 230, 180, key="smax")
        with c3:
            max_consec = st.selectbox("최대 연속쌍", [0, 1, 2, 3], index=1, key="mconsec")
            exclude_latest = st.checkbox("최신 회차 번호 제외", value=False, key="excl")
        save = st.checkbox("추천 이력 저장", value=True, key="save_rec")
        submitted = st.form_submit_button("✨ 조합 생성", use_container_width=True)

    if submitted:
        constraints = CombinationConstraints(
            sum_min=sum_min, sum_max=sum_max,
            max_consecutive_pairs=max_consec,
            exclude_latest_draw_numbers=exclude_latest,
        )
        with st.spinner("조합 생성 중..."):
            gen = CombinationGenerator(draws, scores)
            combos = gen.generate(count=int(count), strategy=strategy, constraints=constraints)

        if not combos:
            st.error("조건에 맞는 조합을 생성하지 못했습니다. 조건을 완화해보세요.")
        else:
            if save:
                try:
                    db = LottoDatabaseManager()
                    for combo in combos:
                        db.save_recommendation(combo, target_draw_no=latest.draw_no + 1)
                    _load_raw.clear()
                    st.success(f"{len(combos)}개 조합이 추천 이력에 저장됐습니다.")
                except Exception as e:
                    st.warning(f"이력 저장 실패: {e}")

            st.markdown(f"""
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;
                        color:var(--text);margin:16px 0 12px">
                ✨ {len(combos)}개 조합 생성 완료
            </div>""", unsafe_allow_html=True)

            for i, combo in enumerate(combos, 1):
                st.markdown(f"""
                <div class="combo">
                    <div style="font-size:.72rem;color:var(--muted);margin-bottom:6px;
                                font-family:'JetBrains Mono',monospace">
                        #{i} · {combo.strategy} · 점수 {combo.score:.1f}
                    </div>
                    {balls_html(combo.numbers, size=46)}
                    <div class="combo-meta">
                        홀짝 {combo.odd_even} · 고저 {combo.high_low} · 합계 {combo.total_sum}
                        <span class="badge-hot" style="margin-left:6px">🔥 {combo.hot_count}</span>
                        <span class="badge-warm" style="margin-left:4px">🌡️ {combo.warm_count}</span>
                        <span class="badge-cold" style="margin-left:4px">❄️ {combo.cold_count}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="disclaimer">⚠️ 이 조합은 통계적 분석 결과이며, 실제 당첨을 보장하지 않습니다. 로또는 완전한 무작위 추첨입니다.</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card card-glass">
            <div style="text-align:center;padding:1.5rem 0">
                <div style="font-size:2.5rem;margin-bottom:8px">🎰</div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;color:var(--muted)">
                    위 옵션을 설정하고 <b style="color:var(--text)">조합 생성</b> 버튼을 누르세요
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# 🧪 백테스트
# ════════════════════════════════════════════════════════════════════════════
elif page == "🧪 백테스트":
    import plotly.graph_objects as go
    from analysis.backtest import run_backtest

    st.markdown('<div class="sec">🧪 전략 백테스트</div>', unsafe_allow_html=True)

    with st.form("bt_form"):
        c1, c2 = st.columns(2)
        with c1:
            bt_strategy = st.selectbox("전략", ["Hybrid", "Hot", "Balanced", "Cold"], key="bt_strat")
            bt_rounds = st.number_input("테스트 회차 수", 10, 200, 50, key="bt_rounds")
        with c2:
            bt_sum_min = st.number_input("합계 최솟값", 21, 230, 100, key="bt_smin")
            bt_sum_max = st.number_input("합계 최댓값", 21, 230, 180, key="bt_smax")
        bt_submit = st.form_submit_button("▶ 백테스트 실행", use_container_width=True)

    if bt_submit:
        if len(draws) < int(bt_rounds) + 10:
            st.warning(f"데이터 부족: {len(draws)}회차 (요청 {bt_rounds}회차)")
        else:
            from generator.combination import CombinationConstraints
            constraints = CombinationConstraints(sum_min=bt_sum_min, sum_max=bt_sum_max)
            with st.spinner("백테스트 실행 중..."):
                result = run_backtest(draws, scores, strategy=bt_strategy,
                                      rounds=int(bt_rounds), constraints=constraints)
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("테스트 회차", f"{result.total_rounds}회")
            with c2: st.metric("3개 이상 적중", f"{result.match_3_count + result.match_4_count + result.match_5_count + result.match_6_count}회")
            with c3: st.metric("평균 적중 수", f"{result.average_match_count:.2f}개")
            with c4: st.metric("5등 이상", f"{result.match_3_count}회")

            # Distribution bar
            labels = ["0개", "1개", "2개", "3개", "4개", "5개", "6개"]
            dist = {k: 0 for k in range(7)}
            for r in result.rounds:
                dist[r.match_count] = dist.get(r.match_count, 0) + 1
            yvals = [dist[k] for k in range(7)]
            bcolors = ["#ef4444" if k >= 3 else "#1e293b" for k in range(7)]

            fig = go.Figure(go.Bar(
                x=labels, y=yvals, marker_color=bcolors,
                hovertemplate="%{x}: <b>%{y}</b>회<extra></extra>"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color="#94a3b8"),
                xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
                margin=dict(l=30, r=10, t=20, b=30), height=280, showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="sec" style="margin-top:1rem">상세 결과</div>', unsafe_allow_html=True)
            rows_bt = {
                "회차": [r.target_draw_no for r in result.rounds],
                "생성번호": [" ".join(map(str, r.generated.numbers)) for r in result.rounds],
                "실제번호": [" ".join(map(str, sorted(r.actual_numbers))) for r in result.rounds],
                "적중수": [r.match_count for r in result.rounds],
                "결과": [r.result_label for r in result.rounds],
            }
            import pandas as pd
            st.dataframe(pd.DataFrame(rows_bt), use_container_width=True, height=300)

# ════════════════════════════════════════════════════════════════════════════
# 📋 추천 이력
# ════════════════════════════════════════════════════════════════════════════
elif page == "📋 추천 이력":
    import plotly.graph_objects as go

    st.markdown('<div class="sec">📋 추천 번호 이력 및 평가</div>', unsafe_allow_html=True)

    if not recommendations:
        st.info("저장된 추천 이력이 없습니다.")
        st.stop()

    eval_by_id = {e.recommendation_id: e for e in evaluations}
    tab_list, tab_eval = st.tabs(["추천 목록", "평가 통계"])

    with tab_list:
        strategy_opts = ["전체"] + sorted({rec.combination.strategy for rec in recommendations})
        f_strat = st.selectbox("전략 필터", strategy_opts, key="hist_strat")
        filtered = [r for r in recommendations if f_strat == "전체" or r.combination.strategy == f_strat]

        st.markdown(f'<div style="font-size:.78rem;color:var(--muted);margin-bottom:10px">{len(filtered)}건 표시 중</div>', unsafe_allow_html=True)
        for rec in filtered[:30]:
            ev = eval_by_id.get(rec.recommendation_id)
            result_html = ""
            if ev:
                color = {"1등":"#f59e0b","2등":"#7c3aed","3등":"#ef4444","4등":"#06b6d4","5등":"#10b981"}.get(ev.result_label, "#334155")
                result_html = f'<span style="background:{color}22;border:1px solid {color}66;color:{color};font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:999px;font-family:JetBrains Mono,monospace">{ev.result_label} ({ev.match_count}개)</span>'
            c = rec.combination
            st.markdown(f"""
            <div class="combo">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                    <div style="font-size:.72rem;color:var(--muted);font-family:'JetBrains Mono',monospace">
                        {rec.recommendation_id} · 대상 {rec.target_draw_no}회 · {rec.created_date}
                    </div>
                    {result_html}
                </div>
                {balls_html(c.numbers, size=42)}
                <div class="combo-meta">
                    {c.strategy} · 홀짝 {c.odd_even} · 고저 {c.high_low} · 합계 {c.total_sum}
                </div>
            </div>""", unsafe_allow_html=True)

    with tab_eval:
        if not evaluations:
            st.info("아직 평가된 회차가 없습니다.")
        else:
            result_labels = ["1등", "2등", "3등", "4등", "5등", "미당첨"]
            result_counts = {k: 0 for k in result_labels}
            for ev in evaluations:
                result_counts[ev.result_label] = result_counts.get(ev.result_label, 0) + 1

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("평가된 추천 수", f"{len(evaluations)}건")
            with c2: st.metric("3등 이상", f"{sum(result_counts.get(k,0) for k in ['1등','2등','3등'])}건")
            with c3: st.metric("5등 이상 (5등+)", f"{sum(result_counts.get(k,0) for k in ['4등','5등'])}건")

            fig = go.Figure(go.Pie(
                labels=list(result_counts.keys()),
                values=list(result_counts.values()),
                hole=0.55,
                marker=dict(colors=["#f59e0b","#7c3aed","#ef4444","#06b6d4","#10b981","#334155"],
                            line=dict(color=["#0e1015"]*6, width=2)),
                hovertemplate="%{label}: <b>%{value}</b>건 (%{percent})<extra></extra>"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color="#94a3b8"),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
                margin=dict(l=10, r=10, t=20, b=20), height=280
            )
            st.plotly_chart(fig, use_container_width=True)

            import pandas as pd
            rows_e: list[dict] = []
            for ev in evaluations:
                rows_e.append({
                    "추천ID": ev.recommendation_id,
                    "대상회차": ev.target_draw_no,
                    "추천번호": " ".join(map(str, ev.recommended_numbers)),
                    "실제번호": " ".join(map(str, sorted(ev.actual_numbers))),
                    "적중수": ev.match_count,
                    "보너스": "O" if ev.bonus_matched else "",
                    "결과": ev.result_label,
                })
            st.dataframe(pd.DataFrame(rows_e), use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# 🔄 데이터 업데이트
# ════════════════════════════════════════════════════════════════════════════
elif page == "🔄 데이터 업데이트":
    st.markdown('<div class="sec">🔄 데이터 업데이트</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("저장된 회차", f"{total}회")
    with c2: st.metric("최신 회차", f"{latest.draw_no}회")
    with c3: st.metric("최신 날짜", str(latest.draw_date))

    st.markdown('<div style="margin-top:1.5rem"></div>', unsafe_allow_html=True)
    tab_fetch, tab_import, tab_weekly = st.tabs(["최신 데이터 수집", "엑셀 가져오기", "주간 업데이트"])

    with tab_fetch:
        st.markdown("""
        <div class="card">
            <div style="font-size:.9rem;color:var(--muted);margin-bottom:14px">
                동행복권 공식 API에서 최신 회차 데이터를 수집합니다.
            </div>
        </div>""", unsafe_allow_html=True)
        draw_from = st.number_input("시작 회차", 1, latest.draw_no + 50, latest.draw_no + 1, key="fetch_from")
        draw_to   = st.number_input("종료 회차", 1, latest.draw_no + 50, latest.draw_no + 5, key="fetch_to")
        if st.button("⬇️ 데이터 수집", use_container_width=True):
            from crawler.dhlottery import fetch_draws
            with st.spinner("수집 중..."):
                bar = st.progress(0)
                fetched = []
                total_range = int(draw_to) - int(draw_from) + 1
                for i, no in enumerate(range(int(draw_from), int(draw_to) + 1)):
                    draw = fetch_draws(no)
                    if draw:
                        fetched.append(draw)
                    bar.progress((i + 1) / total_range)
            if fetched:
                db = LottoDatabaseManager()
                db.initialize_database()
                for d in fetched:
                    db.save_draw(d)
                _load_raw.clear()
                _load_analysis.clear()
                st.success(f"{len(fetched)}개 회차 저장 완료!")
                st.rerun()
            else:
                st.warning("수집된 데이터가 없습니다.")

    with tab_import:
        st.markdown("""
        <div class="card">
            <div style="font-size:.9rem;color:var(--muted);margin-bottom:14px">
                동행복권 사이트에서 다운로드한 엑셀 파일을 가져옵니다.
            </div>
        </div>""", unsafe_allow_html=True)
        excel_path = st.text_input("엑셀 파일 경로", placeholder="D:/Downloads/lotto.xlsx", key="xls_path")
        if st.button("📥 엑셀 가져오기", use_container_width=True):
            from crawler.excel_importer import import_from_excel
            with st.spinner("가져오는 중..."):
                result = import_from_excel(excel_path)
            st.success(f"{result}개 회차 가져오기 완료!")
            _load_raw.clear()
            _load_analysis.clear()
            st.rerun()

    with tab_weekly:
        st.markdown("""
        <div class="card">
            <div style="font-size:.9rem;color:var(--muted);margin-bottom:14px">
                주간 업데이트: 최신 회차 수집 + 추천 번호 생성 + 이메일 발송
            </div>
        </div>""", unsafe_allow_html=True)
        wk_count  = st.number_input("추천 수", 1, 20, 5, key="wk_cnt")
        wk_strat  = st.selectbox("전략", ["Hybrid", "Hot", "Balanced", "Cold"], key="wk_strat")
        if st.button("🔁 주간 업데이트 실행", use_container_width=True):
            from automation.weekly_runner import run_weekly
            with st.spinner("주간 업데이트 실행 중..."):
                run_weekly(recommendation_count=int(wk_count), strategy=wk_strat)
            st.success("주간 업데이트 완료!")
            _load_raw.clear()
            _load_analysis.clear()
            st.rerun()
