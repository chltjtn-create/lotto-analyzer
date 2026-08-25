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
[data-testid="block-container"] {
    padding: 1.3rem 2rem 3rem;
    max-width: 1040px;
    margin: 0 auto;
}
html { font-size: 15.5px; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--text); word-break: keep-all; overflow-wrap: break-word; }
h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; letter-spacing: -0.02em; }

/* Phone: tighter gutters, and never let a wide element scroll the page sideways. */
@media (max-width: 768px) {
    html { font-size: 15px; }
    [data-testid="block-container"] { padding: 1rem 0.9rem 2.5rem; }
    [data-testid="stAppViewContainer"] { overflow-x: hidden; }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0a0c10 !important;
    border-right: 1px solid var(--border) !important;
}

/* Desktop/tablet: pin the sidebar open and hide the collapse toggle. */
@media (min-width: 769px) {
    [data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        width: 210px !important;
        min-width: 210px !important;
        max-width: 210px !important;
    }
    [data-testid="stSidebar"] > div {
        width: 210px !important;
        min-width: 210px !important;
    }
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"] { display: none !important; }
}

/* Mobile: leave the sidebar's width and collapse toggle to Streamlit. It slides
   the panel by its own inline width, so overriding the width here would leave a
   strip of it covering the page when collapsed. */
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.75rem;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
/* Compact sidebar: tighter gutters and denser menu rows. */
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 0.9rem 0.7rem 1rem; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 1px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 5px 6px;
    border-radius: 7px;
    transition: background .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,0.04); }
[data-testid="stSidebar"] [role="radiogroup"] label p {
    font-size: 0.83rem !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    color: var(--text) !important;
    white-space: nowrap;      /* keep every menu item on one line at 210px */
}
[data-testid="stSidebar"] [role="radiogroup"] label > div:last-child { min-width: 0; }

/* ── Page header (flat, no gradient banner) ── */
.hero {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px;
    padding: 0 0 0.9rem;
    margin-bottom: 1.4rem;
    border-bottom: 1px solid var(--border);
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
    line-height: 1.2;
    margin: 0;
}
.hero-sub {
    font-size: 0.8rem;
    color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
}

/* ── Cards ── */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 10px;
    transition: border-color .18s ease;
}
.card:hover { border-color: var(--border-h); }
.card-glass { background: var(--bg-card); border: 1px solid var(--border); }

/* ── Section heading ── */
.sec {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding-bottom: 6px;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

/* ── KPI Cards ── */
.kpi-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    min-height: 82px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: border-color .18s;
}
.kpi-wrap:hover { border-color: var(--border-h); }
.kpi-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    white-space: nowrap;
}
.kpi-val {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}
.kpi-delta-pos { color: var(--success); font-size: 0.78rem; font-weight: 600; margin-top: 2px; }
.kpi-delta-neg { color: var(--danger);  font-size: 0.78rem; font-weight: 600; margin-top: 2px; }
.kpi-delta-neu { color: var(--muted);   font-size: 0.78rem; font-weight: 600; margin-top: 2px; }

/* ── Lotto Balls ── */
/* Default: long lists (hot/warm/cold, missing numbers) wrap onto more lines. */
.balls-row {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: clamp(5px, 1.4vw, 10px);
    flex-wrap: wrap;
    padding: 2px 0;
    width: 100%;
}
/* `spread` is for a single draw (6 balls + optional bonus): the row is spread
   evenly across the card and never wraps — balls shrink to fit a phone screen
   instead of breaking onto a second line. */
.balls-row.spread {
    flex-wrap: nowrap;
    justify-content: space-evenly;
    gap: clamp(4px, 1vw, 10px);
}
.balls-row.spread .ball { flex: 0 1 var(--bs, 48px); min-width: 0; }
.ball {
    flex: 0 0 var(--bs, 48px);
    aspect-ratio: 1 / 1;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: clamp(0.72rem, 2.6vw, 1rem);
    font-weight: 700;
    color: #fff;
    position: relative;
    cursor: default;
    transition: filter .15s ease;
}
.ball-plus {
    flex: 0 0 auto;
    color: var(--muted);
    font-size: clamp(0.85rem, 2.4vw, 1.2rem);
    line-height: 1;
}
.ball:hover { filter: brightness(1.12); }

/* Zone colors — official Korean Lotto 645 (flat, no outer glow) */
.b1  { background: #f0a020; }
.b11 { background: #2f7fd8; }
.b21 { background: #d23c3c; }
.b31 { background: #7b8290; }
.b41 { background: #1f9e63; }

/* Bonus ball */
.bonus { background: #c98a06; box-shadow: inset 0 0 0 2px rgba(255,255,255,0.35); }

/* Hit / miss marking — used when a recommendation is compared to a draw. */
.ball-miss { opacity: .28; filter: grayscale(1); }
.ball-hit  { box-shadow: 0 0 0 2px var(--bg-card), 0 0 0 4px var(--success); }
/* ── Badges ── */
.badge-hot  { display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(239,68,68,.18),rgba(239,68,68,.05));border:1px solid rgba(239,68,68,.4);color:#fca5a5;font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px; }
.badge-warm { display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(245,158,11,.18),rgba(245,158,11,.05));border:1px solid rgba(245,158,11,.4);color:#fde68a;font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px; }
.badge-cold { display:inline-flex;align-items:center;gap:3px;background:linear-gradient(135deg,rgba(6,182,212,.18),rgba(6,182,212,.05));border:1px solid rgba(6,182,212,.4);color:#67e8f9;font-family:'JetBrains Mono',monospace;font-size:.72rem;font-weight:700;padding:2px 9px;border-radius:999px; }

/* ── Combo card ── */
.combo {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.45rem 0.8rem;
    margin-bottom: 6px;
    transition: border-color .18s;
}
.combo:hover { border-color: var(--border-h); }
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
    border-radius: 10px;
    padding: .75rem .95rem;
    transition: border-color .18s;
}
[data-testid="stMetric"]:hover { border-color: var(--border-h); }
[data-testid="stMetricLabel"] > div { font-size:.68rem !important; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:var(--muted) !important; }
[data-testid="stMetricValue"] > div { font-family:'Outfit',sans-serif !important; font-size:1.5rem !important; font-weight:800 !important; }

/* ── Progress bar ── */
.prog-wrap { margin-bottom: 1rem; }
.prog-label { display:flex; justify-content:space-between; color:var(--muted); font-size:.78rem; margin-bottom:5px; }
.prog-track { background:var(--bg-raise); border-radius:999px; height:7px; overflow:hidden; }
.prog-fill { height:100%; border-radius:999px; }

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

from lotto_analyzer.database.db_manager import LottoDatabaseManager
from lotto_analyzer.analysis.frequency import analyze_number_frequency
from lotto_analyzer.analysis.pattern import analyze_patterns
from lotto_analyzer.analysis.scoring import calculate_number_scores
from lotto_analyzer.domain.models import LottoDraw

# ── Helpers ─────────────────────────────────────────────────────────────────

def _bz(n: int) -> str:
    """Return ball CSS class for number n."""
    if n <= 10:  return "b1"
    if n <= 20:  return "b11"
    if n <= 30:  return "b21"
    if n <= 40:  return "b31"
    return "b41"

def balls_html(nums, bonus=None, size=48, spread=False, hits=None) -> str:
    """Render lotto balls as HTML string.

    `size` is the ideal ball diameter. Long lists wrap onto several lines by
    default; `spread=True` (for a single 6-ball draw) instead spreads them
    evenly across the full width on one line, shrinking them to fit on a phone.

    Pass `hits` (a set of winning numbers) to mark each ball: numbers in the set
    get a green ring, the rest are dimmed. Used to show how a recommendation
    scored against an actual draw.
    """
    cls = "balls-row spread" if spread else "balls-row"
    s = f'<div class="{cls}" style="--bs:{size}px">'
    for n in nums:
        mark = ""
        if hits is not None:
            mark = " ball-hit" if n in hits else " ball-miss"
        s += f'<div class="ball {_bz(n)}{mark}">{n}</div>'
    if bonus is not None:
        s += '<span class="ball-plus">+</span>'
        s += f'<div class="ball bonus">{bonus}</div>'
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
    <div style="padding:2px 2px 12px;border-bottom:1px solid var(--border);margin-bottom:10px">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:700;color:var(--text);line-height:1.2">
            🎱 로또 분석기
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
    hot_nums  = [n for n, sc in scores.items() if sc.category == "Hot"]
    cold_nums = [n for n, sc in scores.items() if sc.category == "Cold"]
    next_no   = latest.draw_no + 1

    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">🎱 로또 6/45 분석 허브</div>
        <div class="hero-sub">{total:,}회차 분석 · 최신 {latest.draw_no}회</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 1. 이번 주 추천 번호 (맨 위) ─────────────────────────────────────────
    # 보통은 최신 회차 + 1이지만, 추천이 그보다 앞선 회차에 저장돼 있으면
    # 아직 추첨되지 않은 회차 중 가장 가까운 쪽을 보여준다.
    future_nos = sorted({r.target_draw_no for r in recommendations
                         if r.target_draw_no > latest.draw_no})
    if next_no not in future_nos and future_nos:
        next_no = future_nos[0]

    next_recs = sorted(
        [r for r in recommendations if r.target_draw_no == next_no],
        key=lambda r: r.recommendation_id,
    )[:5]

    st.markdown(f'<div class="sec">🔮 이번 주 {next_no}회 추천 번호</div>',
                unsafe_allow_html=True)

    if not next_recs:
        st.markdown(
            f'<div class="card" style="color:var(--muted);font-size:.85rem">'
            f'{next_no}회 추천 조합이 아직 없습니다. '
            f'“🎰 조합 생성” 페이지에서 만들 수 있습니다.</div>',
            unsafe_allow_html=True)
    else:
        for i, rec in enumerate(next_recs, 1):
            c = rec.combination
            st.markdown(f"""
            <div class="combo">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
                    <div style="font-size:.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace">
                        #{i} · {c.strategy}
                    </div>
                    <div style="font-size:.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace">
                        합계 {c.total_sum} · 🔥{c.hot_count} 🌡️{c.warm_count} ❄️{c.cold_count}
                    </div>
                </div>
                {balls_html(c.numbers, size=34, spread=True)}
            </div>
            """, unsafe_allow_html=True)

    # ── 2. 전 회차 결과 (당첨 번호 + 그 회차 추천 적중) ──────────────────────
    # 전 회차 하나만 보여준다. 추천이 없는 회차가 섞여 있을 수 있으므로
    # "추첨이 끝났고 추천도 있는" 가장 최근 회차를 고르고, 없으면 최신 회차의
    # 당첨 번호만 표시한다.
    draw_by_no = {d.draw_no: d for d in draws}
    scored_nos = sorted(
        {r.target_draw_no for r in recommendations if r.target_draw_no in draw_by_no},
        reverse=True,
    )
    scored_no = scored_nos[0] if scored_nos else latest.draw_no
    target_draw = draw_by_no[scored_no]
    win_set = set(target_draw.numbers)
    prev_recs = sorted(
        [r for r in recommendations if r.target_draw_no == scored_no],
        key=lambda r: r.recommendation_id,
    )[:5]

    st.markdown(f'<div class="sec" style="margin-top:1.3rem">🏆 전 회차 {scored_no}회 결과</div>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card">
        <div style="font-family:'JetBrains Mono',monospace;font-size:.72rem;color:var(--muted);margin-bottom:6px">
            {target_draw.draw_date} 당첨 번호
        </div>
        {balls_html(sorted(target_draw.numbers), target_draw.bonus, size=40, spread=True)}
    </div>
    """, unsafe_allow_html=True)

    if not prev_recs:
        st.markdown(
            f'<div style="font-size:.78rem;color:var(--muted);margin-bottom:4px">'
            f'{scored_no}회를 대상으로 저장된 추천이 없습니다.</div>',
            unsafe_allow_html=True)
    else:
        best = 0
        for rec in prev_recs:
            c = rec.combination
            n_hit = len([n for n in c.numbers if n in win_set])
            best = max(best, n_hit)
            bonus_hit = target_draw.bonus in c.numbers

            tone = "var(--success)" if n_hit >= 3 else "var(--muted)"
            label = f"{n_hit}개 적중" if n_hit else "미적중"
            if bonus_hit:
                label += " +보너스"

            st.markdown(f"""
            <div class="combo">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
                    <div style="font-size:.7rem;color:var(--muted);font-family:'JetBrains Mono',monospace">
                        {c.strategy}
                    </div>
                    <div style="font-size:.72rem;font-weight:700;color:{tone};font-family:'JetBrains Mono',monospace">
                        {label}
                    </div>
                </div>
                {balls_html(c.numbers, size=34, spread=True, hits=win_set)}
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            f'<div style="font-size:.76rem;color:var(--muted);margin:-2px 0 4px">'
            f'추천 {len(prev_recs)}개 중 최고 성적 <b style="color:var(--text)">{best}개 적중</b></div>',
            unsafe_allow_html=True)

    # ── 4. 핫 / 콜드 번호 (맨 아래) ──────────────────────────────────────────
    st.markdown('<div class="sec" style="margin-top:1.1rem">🌡️ 핫 · 콜드 번호</div>',
                unsafe_allow_html=True)
    h_col, c_col = st.columns(2, gap="medium")

    with h_col:
        st.markdown('<div style="font-size:.78rem;color:var(--muted);margin-bottom:4px">'
                    '🔥 핫 번호 — 최근 출현 활발</div>', unsafe_allow_html=True)
        hot_sorted = sorted(hot_nums, key=lambda n: scores[n].final_score, reverse=True)[:9]
        st.markdown(balls_html(hot_sorted, size=36), unsafe_allow_html=True)

    with c_col:
        st.markdown('<div style="font-size:.78rem;color:var(--muted);margin-bottom:4px">'
                    '❄️ 콜드 번호 — 장기 미출현</div>', unsafe_allow_html=True)
        cold_sorted = sorted(cold_nums, key=lambda n: scores[n].final_score)[:9]
        st.markdown(balls_html(cold_sorted, size=36), unsafe_allow_html=True)

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
    from lotto_analyzer.generator.combination import (
        CombinationConstraints,
        CombinationGenerationError,
        generate_combinations,
    )

    st.markdown('<div class="sec">🎰 번호 조합 생성</div>', unsafe_allow_html=True)

    # 화면에 보이는 이름과 생성기가 받는 전략 이름을 명시적으로 이어준다.
    # 예전에는 "Hot"/"Cold"를 그대로 넘겨서 항상 생성에 실패했다.
    STRATEGY_LABELS = {
        "Hybrid (기본)": "Hybrid",
        "Balanced (균형)": "Balanced",
        "Hot Mix (과열 위주)": "Hot Mix",
        "Cold Mix (냉각 위주)": "Cold Mix",
        "Random (무작위)": "Random",
    }

    with st.form("combo_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            strategy_label = st.selectbox("전략", list(STRATEGY_LABELS), key="strat")
            games = st.number_input("게임 수", 1, 100, 5, key="cnt",
                                    help="1~100게임까지 한 번에 생성합니다.")
        with c2:
            sum_min = st.number_input("합계 최솟값", 21, 230, 100, key="smin")
            sum_max = st.number_input("합계 최댓값", 21, 230, 180, key="smax")
        with c3:
            max_consec = st.selectbox("최대 연속쌍", [0, 1, 2, 3], index=1, key="mconsec")
            exclude_latest = st.checkbox("최신 회차 번호 제외", value=False, key="excl")

        st.markdown('<div style="font-size:.8rem;color:var(--muted);margin:6px 0 2px">'
                    '내 번호 지정 (선택)</div>', unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            include_numbers = st.multiselect(
                "반드시 포함할 번호", list(range(1, 46)), key="incl_nums",
                help="최대 5개. 지정한 번호는 모든 게임에 들어갑니다.",
            )
        with p2:
            exclude_numbers = st.multiselect(
                "제외할 번호", list(range(1, 46)), key="excl_nums",
                help="지정한 번호는 어떤 게임에도 들어가지 않습니다.",
            )

        save = st.checkbox("추천 이력 저장", value=True, key="save_rec")
        submitted = st.form_submit_button("✨ 조합 생성", use_container_width=True)

    if submitted:
        strategy = STRATEGY_LABELS[strategy_label]
        count = int(games)

        # 남은 자리가 없으면 전략이 개입할 여지가 사라진다. 6개를 다 지정하면
        # 조합이 하나로 확정되므로 그때는 1게임만 만들 수 있다.
        blocked = None
        if len(include_numbers) > 5:
            blocked = ("포함할 번호는 최대 5개까지 지정할 수 있습니다. "
                       f"지금 {len(include_numbers)}개를 골랐습니다.")
        elif len(set(range(1, 46)) - set(exclude_numbers)) < 6:
            blocked = "제외할 번호가 너무 많아 남은 번호가 6개 미만입니다."

        combos, error = [], blocked
        if not blocked:
            constraints = CombinationConstraints(
                sum_min=sum_min, sum_max=sum_max,
                max_consecutive_pairs=max_consec,
                exclude_latest_draw_numbers=exclude_latest,
                include_numbers=tuple(sorted(include_numbers)),
                exclude_numbers=tuple(sorted(exclude_numbers)),
            )
            with st.spinner(f"{count}게임 생성 중..."):
                try:
                    combos = generate_combinations(
                        scores_by_number=scores,
                        latest_draw=latest,
                        constraints=constraints,
                        strategy=strategy,
                        count=count,
                    )
                except CombinationGenerationError as exc:
                    error = str(exc)

        if not combos:
            st.error(f"조합을 생성하지 못했습니다. {error or ''}")
            if include_numbers:
                odd = sum(1 for n in include_numbers if n % 2)
                st.info(
                    "지정한 번호가 조건과 충돌했을 수 있습니다. 확인해보세요:\n\n"
                    f"- 고른 번호 합계 {sum(include_numbers)} "
                    f"(합계 범위 {sum_min}~{sum_max})\n"
                    f"- 홀수 {odd}개 / 짝수 {len(include_numbers) - odd}개 "
                    "(한쪽이 5개 이상이면 홀짝 조건에 걸립니다)\n"
                    "- 합계 범위를 넓히거나 지정 번호를 줄여보세요."
                )
        else:
            if save:
                try:
                    from lotto_analyzer.analysis.evaluation import RecommendationRecord

                    db = LottoDatabaseManager()
                    target_draw_no = latest.draw_no + 1
                    strategy_key = strategy.lower().replace(" ", "_")
                    today = date.today()
                    for index, combo in enumerate(combos, start=1):
                        record = RecommendationRecord(
                            recommendation_id=f"{target_draw_no}-{strategy_key}-{index:03d}",
                            target_draw_no=target_draw_no,
                            created_date=today,
                            combination=combo,
                        )
                        db.save_recommendation(record)
                    _load_raw.clear()
                    st.success(f"{len(combos)}개 조합이 {target_draw_no}회 추천 이력에 저장됐습니다.")
                    if len(combos) > 5:
                        st.warning(
                            f"{target_draw_no}회 추천이 이미 저장돼 있으므로, 월요일 자동 실행은 "
                            "이 회차의 추천을 새로 만들지 않고 건너뜁니다. "
                            "홈 화면에는 저장된 것 중 앞 5개만 표시됩니다."
                        )
                except Exception as e:
                    st.warning(f"이력 저장 실패: {e}")

            st.markdown(f"""
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;
                        color:var(--text);margin:16px 0 12px">
                ✨ {len(combos)}게임 생성 완료
            </div>""", unsafe_allow_html=True)

            # 게임이 많으면 공을 줄이고 메타 정보를 한 줄로 접어 목록이 끝없이
            # 길어지지 않게 한다.
            many = len(combos) > 10
            ball_size = 30 if many else 46

            for i, combo in enumerate(combos, 1):
                if many:
                    meta = (f"합계 {combo.total_sum} · 홀짝 {combo.odd_even} · "
                            f"🔥{combo.hot_count} 🌡️{combo.warm_count} ❄️{combo.cold_count}")
                    st.markdown(f"""
                    <div class="combo" style="padding:.35rem .7rem">
                        <div style="display:flex;justify-content:space-between;align-items:center;
                                    font-size:.68rem;color:var(--muted);
                                    font-family:'JetBrains Mono',monospace;margin-bottom:3px">
                            <span>#{i}</span><span>{meta}</span>
                        </div>
                        {balls_html(combo.numbers, size=ball_size, spread=True)}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="combo">
                        <div style="font-size:.72rem;color:var(--muted);margin-bottom:6px;
                                    font-family:'JetBrains Mono',monospace">
                            #{i} · {combo.strategy} · 점수 {combo.score:.1f}
                        </div>
                        {balls_html(combo.numbers, size=ball_size, spread=True)}
                        <div class="combo-meta">
                            홀짝 {combo.odd_even} · 고저 {combo.high_low} · 합계 {combo.total_sum}
                            <span class="badge-hot" style="margin-left:6px">🔥 {combo.hot_count}</span>
                            <span class="badge-warm" style="margin-left:4px">🌡️ {combo.warm_count}</span>
                            <span class="badge-cold" style="margin-left:4px">❄️ {combo.cold_count}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # 용지에 옮겨 적거나 보관할 수 있게 번호만 뽑아준다.
            plain = "\n".join(
                f"{i:3d}. " + "  ".join(f"{n:02d}" for n in combo.numbers)
                for i, combo in enumerate(combos, 1)
            )
            with st.expander(f"📋 번호만 보기 ({len(combos)}게임)"):
                st.code(plain, language=None)
                st.download_button(
                    "번호 목록 내려받기 (.txt)",
                    data=plain,
                    file_name=f"lotto_{latest.draw_no + 1}회_{len(combos)}게임.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

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
    from lotto_analyzer.analysis.backtest import run_backtest

    st.markdown('<div class="sec">🧪 전략 백테스트</div>', unsafe_allow_html=True)

    with st.form("bt_form"):
        c1, c2 = st.columns(2)
        with c1:
            bt_strategy = st.selectbox(
                "전략", ["Hybrid", "Balanced", "Hot Mix", "Cold Mix", "Random"], key="bt_strat")
            bt_rounds = st.number_input("테스트 회차 수", 10, 200, 50, key="bt_rounds")
        with c2:
            bt_sum_min = st.number_input("합계 최솟값", 21, 230, 100, key="bt_smin")
            bt_sum_max = st.number_input("합계 최댓값", 21, 230, 180, key="bt_smax")
        bt_submit = st.form_submit_button("▶ 백테스트 실행", use_container_width=True)

    if bt_submit:
        if len(draws) < int(bt_rounds) + 10:
            st.warning(f"데이터 부족: {len(draws)}회차 (요청 {bt_rounds}회차)")
        else:
            from lotto_analyzer.analysis.backtest import BacktestError
            from lotto_analyzer.generator.combination import CombinationConstraints
            constraints = CombinationConstraints(sum_min=bt_sum_min, sum_max=bt_sum_max)
            bt_end = latest.draw_no
            bt_start = draws[-int(bt_rounds)].draw_no
            with st.spinner("백테스트 실행 중..."):
                try:
                    result = run_backtest(
                        draws,
                        start_draw_no=bt_start,
                        end_draw_no=bt_end,
                        strategy=bt_strategy,
                        constraints=constraints,
                    )
                except BacktestError as e:
                    st.error(f"백테스트 실패: {e}")
                    st.stop()
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
                {balls_html(c.numbers, size=42, spread=True)}
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
            from lotto_analyzer.collector.crawler import LottoCrawler, LottoCrawlerError
            with st.spinner("수집 중..."):
                try:
                    crawler = LottoCrawler()
                    fetched = crawler.fetch_range(int(draw_from), int(draw_to), skip_missing=True)
                except LottoCrawlerError as e:
                    st.error(f"수집 실패: {e}")
                    fetched = []
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
            from lotto_analyzer.collector.local_loader import LocalDataLoadError, load_draws_from_excel
            with st.spinner("가져오는 중..."):
                try:
                    imported = load_draws_from_excel(excel_path)
                    db = LottoDatabaseManager()
                    db.initialize_database()
                    for d in imported:
                        db.save_draw(d)
                    st.success(f"{len(imported)}개 회차 가져오기 완료!")
                    _load_raw.clear()
                    _load_analysis.clear()
                    st.rerun()
                except LocalDataLoadError as e:
                    st.error(f"가져오기 실패: {e}")

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
            from automation.weekly_update import run_weekly_update
            with st.spinner("주간 업데이트 실행 중..."):
                result = run_weekly_update(recommendation_count=int(wk_count), strategy=wk_strat)
            if result.errors:
                st.error("주간 업데이트 중 오류 발생: " + "; ".join(result.errors))
            else:
                st.success(
                    f"주간 업데이트 완료! 신규 회차 {len(result.fetched_draws)}개, "
                    f"추천 {result.generated_recommendations}개 생성"
                )
            _load_raw.clear()
            _load_analysis.clear()
            st.rerun()
