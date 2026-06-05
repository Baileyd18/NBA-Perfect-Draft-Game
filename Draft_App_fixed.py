import random
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="NBA Draft Game",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_PATH = "nba_game_database_current.csv"

ROSTER_SIZE = 6
BUDGET = 500
MIN_PLAYER_COST = 20
POSITIONS = ["PG", "SG", "SF", "PF", "C", "6TH"]
POSITION_ORDER = {"PG": 0, "SG": 1, "SF": 2, "PF": 3, "C": 4, "6TH": 5}

TEAM_ABBR_TO_NAME = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BRK": "Brooklyn Nets",
    "BKN": "Brooklyn Nets", "CHA": "Charlotte Hornets", "CHO": "Charlotte Hornets",
    "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers", "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets", "DET": "Detroit Pistons", "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets", "IND": "Indiana Pacers", "LAC": "LA Clippers",
    "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies", "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves", "NOP": "New Orleans Pelicans",
    "NOH": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}

DECADE_ORDER = ["50s", "60s", "70s", "80s", "90s", "00s", "10s", "20s"]


# ============================================================
# State
# ============================================================

def init_state():
    defaults = {
        "round": 1,
        "budget": BUDGET,
        "spent": 0,
        "roster": [],
        "team": None,
        "decade": None,
        "options": pd.DataFrame(),
        "has_active_spin": False,
        "team_respin_used": False,
        "decade_respin_used": False,
        "show_results": False,
        "spin_number": 0,
        "pending_player": None,
        "dark_mode": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_state()


init_state()


# ============================================================
# CSS / Theme
# ============================================================

IS_DARK = st.session_state.get("dark_mode", False)
BG = "#0f172a" if IS_DARK else "#f7f8fb"
CARD = "#111827" if IS_DARK else "#ffffff"
TEXT = "#f8fafc" if IS_DARK else "#07142f"
MUTED = "#94a3b8" if IS_DARK else "#64748b"
BORDER = "#334155" if IS_DARK else "#e5e7eb"
NOTICE_BG = "#111827" if IS_DARK else "#ffffff"
SLOT_BG = "#111827" if IS_DARK else "#ffffff"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800;900&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: {BG};
    }}

    .block-container {{
        padding-top: 0.8rem !important;
        padding-bottom: 0.3rem !important;
        max-width: 1240px;
    }}

    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    footer,
    #MainMenu {{
        display: none;
    }}

    .brand {{
        font-size: 18px;
        font-weight: 900;
        color: {TEXT};
        padding-top: 8px;
    }}

    .round-top {{
        font-size: 16px;
        font-weight: 900;
        color: {TEXT};
        text-align: center;
        padding-top: 10px;
    }}

    .app-divider {{
        border: 0;
        border-top: 1px solid {BORDER};
        margin: 10px 0 32px 0;
    }}

    div[data-testid="column"]:first-child {{
        padding-right: 18px;
    }}

    .team-spin-card,
    .era-spin-card {{
        width: 170px;
        height: 115px;
        background: {CARD};
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
    }}

    .team-spin-card {{
        border: 12px solid #ffa600;
        box-shadow: 0 14px 30px rgba(255,166,0,.28);
    }}

    .era-spin-card {{
        border: 12px solid #a855f7;
        box-shadow: 0 14px 30px rgba(168,85,247,.28);
    }}

    .flip-wrap {{
        text-align: center;
    }}

    .card-label {{
        color: #ff5a00;
        font-size: 13px;
        font-weight: 900;
        margin-bottom: 8px;
    }}

    .card-value {{
        color: {TEXT};
        font-size: 35px;
        font-weight: 900;
        line-height: 1;
    }}

    .below-label {{
        color: {MUTED};
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 14px;
    }}

    .info-row {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 16px;
    }}

    .info-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 6px;
        text-align: center;
        box-shadow: 0 6px 18px rgba(15,23,42,.05);
    }}

    .info-label {{
        color: {MUTED};
        font-size: 9px;
        font-weight: 900;
        letter-spacing: .08em;
        text-transform: uppercase;
    }}

    .info-value {{
        color: {TEXT};
        font-size: 18px;
        font-weight: 900;
    }}

    .purple {{ color: #7c3aed; }}
    .green {{ color: #16a34a; }}

    .section-title {{
        color: {TEXT};
        font-size: 21px;
        font-weight: 900;
        margin-bottom: 8px;
    }}

    .notice-card {{
        background: {NOTICE_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 14px;
        color: {MUTED};
        font-weight: 800;
        box-shadow: 0 10px 25px rgba(15,23,42,.05);
    }}

    .player-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 10px;
        margin-bottom: 6px;
        box-shadow: 0 6px 15px rgba(15,23,42,.04);
    }}

    .player-name {{
        font-size: 14px;
        font-weight: 900;
        color: {TEXT};
        margin-bottom: 1px;
    }}

    .player-meta {{
        font-size: 11px;
        color: #ff4d00;
        font-weight: 800;
    }}

    .stat-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 5px;
        margin-top: 5px;
        text-align: center;
    }}

    .stat-num {{
        font-size: 14px;
        color: {TEXT};
        font-weight: 900;
        line-height: 1;
    }}

    .stat-lab {{
        font-size: 8px;
        color: {MUTED};
        font-weight: 800;
        margin-top: 2px;
    }}

    .slot-card {{
        border-radius: 14px;
        padding: 11px 13px;
        margin-bottom: 8px;
        display: grid;
        grid-template-columns: 56px 1fr;
        align-items: center;
        min-height: 52px;
        background: {SLOT_BG};
        border: 1px solid {BORDER};
        box-shadow: 0 8px 20px rgba(15,23,42,.04);
    }}

    .slot-label {{
        color: {TEXT};
        font-size: 14px;
        font-weight: 900;
    }}

    .slot-empty {{
        color: #94a3b8;
        font-size: 14px;
        font-weight: 800;
    }}

    .slot-player {{
        color: {TEXT};
        font-size: 14px;
        font-weight: 900;
    }}

    .slot-meta {{
        color: {MUTED};
        font-size: 11px;
        margin-top: 2px;
        font-weight: 700;
    }}

    .total-cost-row {{
        display: flex;
        justify-content: space-between;
        font-size: 17px;
        font-weight: 900;
        color: {TEXT};
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid {BORDER};
    }}

    .draft-player-card {{
        background: #07142f;
        color: white;
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 18px;
    }}

    .draft-player-name {{
        font-size: 26px;
        font-weight: 900;
    }}

    .draft-player-meta {{
        color: #cbd5e1;
        font-weight: 700;
        margin-top: 6px;
    }}

    .results-page {{
        max-width: 980px;
        margin: 0 auto;
        text-align: left;
        padding-top: 12px;
    }}

    .results-logo {{
        font-size: 62px;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 8px;
        text-align: center;
    }}

    .results-title {{
        font-size: 34px;
        font-weight: 900;
        color: {TEXT};
        margin-bottom: 34px;
        text-align: center;
    }}

    .projected-label {{
        color: {MUTED};
        font-size: 13px;
        letter-spacing: .22em;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}

    .big-record {{
        font-size: 72px;
        font-weight: 900;
        color: {TEXT};
        letter-spacing: -4px;
        line-height: 1;
        margin-bottom: 14px;
    }}

    .record-dash {{
        color: #c7c7c7;
        padding: 0 8px;
    }}

    .grade-line {{
        font-size: 18px;
        font-weight: 900;
        margin-bottom: 36px;
    }}

    .grade-letter {{
        color: #22c55e;
        font-size: 26px;
        margin-right: 10px;
    }}

    .tier-text {{
        color: #22c55e;
        margin-right: 10px;
    }}

    .score-small {{
        color: {MUTED};
        font-size: 14px;
    }}

    .result-player-card {{
        display: grid;
        grid-template-columns: 76px 1fr 420px;
        align-items: center;
        text-align: left;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 0;
        border-left: 5px solid #ff5a00;
        box-shadow: 0 8px 20px rgba(15,23,42,.05);
    }}

    .rp-avatar {{
        width: 48px;
        height: 48px;
        background: #07142f;
        color: #ffb000;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 13px;
        line-height: 1;
        text-align: center;
    }}

    .rp-name {{
        font-size: 18px;
        font-weight: 900;
        color: #07142f;
    }}

    .rp-meta {{
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
    }}

    .rp-stats {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        text-align: center;
    }}

    .rp-stat-num {{
        color: #07142f;
        font-size: 14px;
        font-weight: 900;
    }}

    .rp-stat-lab {{
        color: #64748b;
        font-size: 9px;
        font-weight: 800;
    }}

    .team-total-row {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 20px;
        margin: 24px 0 18px 0;
        text-align: center;
    }}

    .team-total-num {{
        color: {TEXT};
        font-size: 18px;
        font-weight: 900;
    }}

    .team-total-label {{
        color: {MUTED};
        font-size: 11px;
        font-weight: 800;
    }}

    .footer-note {{
        color: {MUTED};
        font-size: 13px;
        margin-top: 16px;
        text-align: center;
    }}

    .stButton > button {{
        border-radius: 10px;
        font-weight: 900;
        min-height: 36px;
        border: 1px solid {BORDER};
        box-shadow: 0 5px 12px rgba(15,23,42,.04);
    }}

    div[data-testid="stVerticalBlock"] {{
        gap: .45rem;
    }}

    div[data-testid="stHorizontalBlock"] {{
        gap: .65rem;
    }}

    .element-container {{
        margin-bottom: 0 !important;
    }}

    div[data-testid="stDialog"] > div {{
        border-radius: 28px;
        padding: 8px;
    }}

    /* Mobile-native mode: add ?mobile=1 to the URL */
    .mobile-app-shell {{ background:#0b0f1d; color:#f8fafc; min-height:100vh; padding:0 0 118px; }}
    .mobile-topbar {{ display:grid; grid-template-columns:1fr auto; align-items:center; gap:12px; padding:14px 4px; border-bottom:1px solid #293043; margin-bottom:16px; }}
    .mobile-brand-row {{ display:flex; align-items:center; gap:10px; font-weight:900; color:#f8fafc; font-size:18px; }}
    .mobile-logo {{ width:44px; height:44px; border-radius:12px; background:linear-gradient(135deg,#ff7a18,#ff4d00); color:#07142f; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:12px; line-height:1; text-align:center; border:2px solid rgba(255,255,255,.16); box-shadow:0 8px 24px rgba(255,90,0,.25); }}
    .mobile-mini-actions .stButton > button {{ min-height:42px!important; border-radius:10px!important; background:#151b2c!important; border:1px solid #30384c!important; color:#cbd5e1!important; box-shadow:none!important; font-size:14px!important; padding:0 8px!important; }}
    .mobile-spin-zone {{ padding:66px 0 28px; min-height:480px; }}
    .mobile-card-row {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; padding:0 10px; }}
    .mobile-spin-card {{ height:150px; border-radius:15px; background:#1a2032; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 18px 40px rgba(0,0,0,.35); }}
    .mobile-team-card {{ border:9px solid #ffa51f; outline:4px solid rgba(255,165,31,.22); }}
    .mobile-era-card {{ border:9px solid #a855f7; outline:4px solid rgba(168,85,247,.22); }}
    .mobile-card-label {{ color:#ff7a18; font-size:13px; font-weight:900; margin-bottom:10px; }}
    .mobile-card-value {{ color:#fff; font-size:44px; font-weight:900; line-height:1; }}
    .mobile-card-caption {{ color:#a1a1aa; text-align:center; font-size:16px; margin-top:12px; font-weight:700; }}
    .mobile-primary .stButton > button {{ background:#f97316!important; color:white!important; border:none!important; border-radius:12px!important; min-height:58px!important; font-size:22px!important; font-weight:900!important; box-shadow:0 14px 32px rgba(249,115,22,.32)!important; }}
    .mobile-pill-row {{ display:flex; justify-content:space-between; align-items:center; gap:10px; padding:0 0 14px; border-bottom:1px solid #293043; margin-bottom:14px; }}
    .mobile-pills-left,.mobile-pills-right {{ display:flex; align-items:center; gap:10px; }}
    .mobile-pill {{ border-radius:999px; padding:10px 18px; font-weight:900; font-size:15px; }}
    .mobile-pill-team {{ background:#14532d; color:#dcfce7; }}
    .mobile-pill-era {{ background:#431407; color:#fdba74; border:1px solid #9a3412; }}
    .mobile-respin .stButton > button {{ min-height:38px!important; border-radius:10px!important; background:transparent!important; border:none!important; color:#ffbf2f!important; box-shadow:none!important; font-weight:900!important; }}
    .mobile-respin-purple .stButton > button {{ color:#c084fc!important; }}
    .mobile-count {{ color:#a1a1aa; font-size:15px; margin:8px 0 14px; font-weight:700; }}
    .mobile-player-card {{ background:#171c2c; border:1px solid #30384c; border-radius:13px; padding:13px 12px; margin-bottom:8px; display:grid; grid-template-columns:1.65fr 2.1fr; align-items:center; gap:8px; box-shadow:0 10px 22px rgba(0,0,0,.18); }}
    .mobile-player-name {{ color:#f8fafc; font-size:17px; font-weight:900; line-height:1.05; }}
    .mobile-player-pos {{ color:#fef3c7; font-size:13px; font-weight:900; margin-top:3px; }}
    .mobile-player-meta {{ color:#a1a1aa; font-size:12px; font-weight:700; margin-top:2px; }}
    .mobile-stat-grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:5px; text-align:center; }}
    .mobile-stat-num {{ color:#f8fafc; font-size:16px; font-weight:900; line-height:1; }}
    .mobile-stat-lab {{ color:#a1a1aa; font-size:10px; font-weight:800; margin-top:4px; }}
    .mobile-pick .stButton > button {{ min-height:38px!important; border-radius:10px!important; background:#f97316!important; color:white!important; border:none!important; box-shadow:none!important; font-weight:900!important; font-size:13px!important; margin-top:-6px!important; }}
    .mobile-dock {{ position:fixed; left:0; right:0; bottom:0; z-index:9999; background:rgba(11,15,29,.96); backdrop-filter:blur(12px); border-top:1px solid #293043; padding:18px 16px 20px; }}
    .mobile-dock-inner {{ display:grid; grid-template-columns:repeat(6,1fr); gap:8px; max-width:640px; margin:0 auto; text-align:center; }}
    .mobile-slot-dot {{ width:52px; height:52px; border-radius:50%; border:2px dashed #4b5563; display:flex; align-items:center; justify-content:center; margin:0 auto 5px; color:#a1a1aa; font-weight:900; font-size:14px; background:#171c2c; overflow:hidden; white-space:nowrap; }}
    .mobile-slot-dot.filled {{ border:2px solid #16a34a; background:#14532d; color:#dcfce7; }}
    .mobile-slot-label {{ color:#a1a1aa; font-size:11px; font-weight:800; }}
    .mobile-budget-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:9px; margin:12px 0 18px; }}
    .mobile-budget-card {{ border:1px solid #30384c; background:#171c2c; border-radius:12px; padding:12px 8px; text-align:center; }}
    .mobile-budget-label {{ color:#a1a1aa; text-transform:uppercase; font-size:10px; letter-spacing:.08em; font-weight:900; }}
    .mobile-budget-value {{ color:#f8fafc; font-size:22px; font-weight:900; margin-top:4px; }}
    .mobile-results-title {{ color:#94a3b8; font-size:12px; font-weight:900; letter-spacing:.22em; text-transform:uppercase; }}
    .mobile-record {{ color:#f8fafc; font-size:64px; font-weight:900; letter-spacing:-3px; line-height:1; margin:10px 0 12px; }}
    .mobile-grade {{ color:#22c55e; font-size:20px; font-weight:900; margin-bottom:18px; }}

    .mobile-roster-title {{
        color: #f8fafc;
        font-size: 15px;
        font-weight: 900;
        letter-spacing: .04em;
        margin: 20px 0 10px 0;
    }}

    .mobile-slot-card {{
        display: grid;
        grid-template-columns: 48px 1fr 52px;
        align-items: center;
        gap: 10px;
        background: #111827;
        border: 1px solid #263247;
        border-radius: 12px;
        padding: 9px 10px;
        margin-bottom: 8px;
    }}

    .mobile-slot-card.empty {{
        grid-template-columns: 48px 1fr;
    }}

    .mobile-slot-badge {{
        width: 40px;
        height: 40px;
        border: 2px dashed #475569;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #cbd5e1;
        font-size: 13px;
        font-weight: 900;
    }}

    .mobile-slot-badge.filled {{
        background: #166534;
        border: 1px solid #166534;
        color: #ffffff;
    }}

    .mobile-slot-player {{
        color: #f8fafc;
        font-size: 14px;
        font-weight: 900;
    }}

    .mobile-slot-meta {{
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
    }}

    .mobile-slot-empty {{
        color: #94a3b8;
        font-size: 14px;
        font-weight: 800;
    }}

    .mobile-slot-cost {{
        color: #ff5a00;
        font-size: 13px;
        font-weight: 900;
        text-align: right;
    }}

    @media (max-width:520px) {{
        .block-container {{ padding:0.55rem 0.75rem 0!important; max-width:100%!important; }}
        .mobile-spin-zone {{ padding-top:64px; }}
        .mobile-card-row {{ gap:14px; padding:0; }}
        .mobile-spin-card {{ height:130px; }}
        .mobile-card-value {{ font-size:36px; }}
        .mobile-player-card {{ grid-template-columns:1.45fr 1.75fr; padding:12px 10px; gap:6px; }}
        .mobile-player-name {{ font-size:15px; }}
        .mobile-stat-num {{ font-size:14px; }}
        .mobile-stat-lab {{ font-size:8px; }}
        .mobile-slot-dot {{ width:46px; height:46px; font-size:12px; }}
        .mobile-slot-label {{ font-size:10px; }}
        div[data-testid="stDialog"] > div {{ position:fixed!important; left:0!important; right:0!important; bottom:0!important; top:auto!important; width:100vw!important; max-width:100vw!important; border-radius:22px 22px 0 0!important; background:#0b0f1d!important; color:#f8fafc!important; border-top:1px solid #293043!important; padding:18px!important; }}
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# Data
# ============================================================

@st.cache_data(show_spinner=False)
def load_data(data_path, min_player_cost, file_modified_time):
    df = pd.read_csv(data_path)

    if "MVPPointPct" not in df.columns and "MVPShare" in df.columns:
        df["MVPPointPct"] = df["MVPShare"]

    required_cols = [
        "Player", "Franchise", "TeamAbbr", "Decade", "Position",
        "Cost", "PPG", "RPG", "APG", "SPG", "BPG",
        "AllStarSelections", "MVPPointPct"
    ]

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Dataset is missing required columns: {missing}")
        st.stop()

    numeric_cols = [
        "Age", "Games", "MPG", "PPG", "RPG", "APG", "BPG", "SPG",
        "Cost", "AllStarSelections", "MVPPointPct"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["TeamAbbr"] = df["TeamAbbr"].astype(str).str.upper().str.strip()
    df["Decade"] = df["Decade"].astype(str).str.strip()
    df["Position"] = df["Position"].astype(str).fillna("").str.upper().str.strip()
    df["Franchise"] = df["Franchise"].astype(str).str.strip()
    df["Player"] = df["Player"].astype(str).str.strip()

    df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce").fillna(min_player_cost)
    df["Cost"] = df["Cost"].clip(lower=min_player_cost).round().astype(int)

    if "PlayerID" not in df.columns:
        df["PlayerID"] = (
            df["Player"].astype(str)
            + "_"
            + df["TeamAbbr"].astype(str)
            + "_"
            + df["Decade"].astype(str)
            + "_"
            + df["Position"].astype(str)
        )

    df = df[df["TeamAbbr"].isin(TEAM_ABBR_TO_NAME.keys())]
    df = df[df["Decade"].isin(DECADE_ORDER)]

    return df.reset_index(drop=True)


DATA_MODIFIED_TIME = Path(DATA_PATH).stat().st_mtime
df = load_data(DATA_PATH, MIN_PLAYER_COST, DATA_MODIFIED_TIME)


# ============================================================
# Helpers
# ============================================================

def available_slots():
    used_slots = [p["DraftPosition"] for p in st.session_state.roster]
    return [slot for slot in POSITIONS if slot not in used_slots]


def parse_positions(player_pos):
    raw = str(player_pos).upper().replace(" ", "")
    found = []

    for pos in ["PG", "SG", "SF", "PF", "C"]:
        if pos in raw:
            found.append(pos)

    return found


def eligible_slots_for_player(player_pos):
    open_slots = available_slots()
    listed_positions = parse_positions(player_pos)

    eligible = []

    for slot in open_slots:
        if slot in listed_positions:
            eligible.append(slot)

    if "6TH" in open_slots:
        eligible.append("6TH")

    return eligible


def max_allowed_cost_for_next_pick():
    remaining_slots_after_pick = ROSTER_SIZE - len(st.session_state.roster) - 1
    reserve_needed = remaining_slots_after_pick * MIN_PLAYER_COST
    return max(0, st.session_state.budget - reserve_needed)


def build_options():
    team = st.session_state.team
    decade = st.session_state.decade

    if not team or not decade:
        st.session_state.options = pd.DataFrame()
        return

    selected_ids = {p["PlayerID"] for p in st.session_state.roster}
    max_allowed_cost = max_allowed_cost_for_next_pick()

    options = df[
        (df["TeamAbbr"] == team)
        & (df["Decade"] == decade)
        & (~df["PlayerID"].isin(selected_ids))
        & (df["Cost"] <= max_allowed_cost)
    ].copy()

    options["EligibleSlots"] = options["Position"].apply(eligible_slots_for_player)
    options = options[options["EligibleSlots"].apply(lambda x: len(x) > 0)]

    options = options.sort_values(
        by=["PPG", "RPG", "APG"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    st.session_state.options = options


def safe_combo_with_affordable_players():
    selected_ids = {p["PlayerID"] for p in st.session_state.roster}
    max_allowed_cost = max_allowed_cost_for_next_pick()

    available = df[
        (~df["PlayerID"].isin(selected_ids))
        & (df["Cost"] <= max_allowed_cost)
    ].copy()

    if available.empty:
        return None

    available["EligibleSlots"] = available["Position"].apply(eligible_slots_for_player)
    available = available[available["EligibleSlots"].apply(lambda x: len(x) > 0)]

    if available.empty:
        return None

    combos = available[["TeamAbbr", "Decade"]].drop_duplicates().reset_index(drop=True)
    return combos.sample(1).iloc[0]


def spin():
    combo = safe_combo_with_affordable_players()

    if combo is None:
        st.warning("No affordable players fit your remaining roster slots.")
        return

    st.session_state.team = combo["TeamAbbr"]
    st.session_state.decade = combo["Decade"]
    st.session_state.has_active_spin = True
    st.session_state.spin_number += 1

    build_options()


def respin_team():
    current_decade = st.session_state.decade

    if not current_decade:
        return

    selected_ids = {p["PlayerID"] for p in st.session_state.roster}
    max_allowed_cost = max_allowed_cost_for_next_pick()

    valid_pool = df[
        (df["Decade"] == current_decade)
        & (~df["PlayerID"].isin(selected_ids))
        & (df["Cost"] <= max_allowed_cost)
    ].copy()

    valid_pool["EligibleSlots"] = valid_pool["Position"].apply(eligible_slots_for_player)
    valid_pool = valid_pool[valid_pool["EligibleSlots"].apply(lambda x: len(x) > 0)]

    valid_teams = sorted(valid_pool["TeamAbbr"].unique())

    if not valid_teams:
        st.warning("No valid team respins are available.")
        return

    st.session_state.team = random.choice(valid_teams)
    st.session_state.team_respin_used = True
    build_options()


def respin_decade():
    current_team = st.session_state.team

    if not current_team:
        return

    selected_ids = {p["PlayerID"] for p in st.session_state.roster}
    max_allowed_cost = max_allowed_cost_for_next_pick()

    valid_pool = df[
        (df["TeamAbbr"] == current_team)
        & (~df["PlayerID"].isin(selected_ids))
        & (df["Cost"] <= max_allowed_cost)
    ].copy()

    valid_pool["EligibleSlots"] = valid_pool["Position"].apply(eligible_slots_for_player)
    valid_pool = valid_pool[valid_pool["EligibleSlots"].apply(lambda x: len(x) > 0)]

    valid_decades = [d for d in DECADE_ORDER if d in set(valid_pool["Decade"].unique())]

    if not valid_decades:
        st.warning("No valid era respins are available.")
        return

    st.session_state.decade = random.choice(valid_decades)
    st.session_state.decade_respin_used = True
    build_options()


def draft_player(player, slot):
    player = dict(player)
    player["DraftPosition"] = slot
    player_cost = int(player["Cost"])

    if slot not in eligible_slots_for_player(player["Position"]):
        st.warning("That player cannot be drafted into that position.")
        return

    remaining_slots_after_pick = ROSTER_SIZE - len(st.session_state.roster) - 1
    minimum_needed_after_pick = remaining_slots_after_pick * MIN_PLAYER_COST

    if player_cost + minimum_needed_after_pick > st.session_state.budget:
        st.error(
            f"You can't draft {player['Player']}. You need to save at least "
            f"{minimum_needed_after_pick} for the remaining {remaining_slots_after_pick} roster slot(s)."
        )
        return

    if player_cost > st.session_state.budget:
        st.error("This player would put you over budget.")
        return

    st.session_state.roster.append(player)
    st.session_state.spent += player_cost
    st.session_state.budget -= player_cost

    st.session_state.round += 1
    st.session_state.team = None
    st.session_state.decade = None
    st.session_state.options = pd.DataFrame()
    st.session_state.has_active_spin = False
    st.session_state.team_respin_used = False
    st.session_state.decade_respin_used = False
    st.session_state.pending_player = None

    if len(st.session_state.roster) >= ROSTER_SIZE:
        st.session_state.show_results = True


def sorted_roster():
    return sorted(
        st.session_state.roster,
        key=lambda p: POSITION_ORDER.get(str(p.get("DraftPosition", "")).upper(), 99)
    )


def initials(name):
    parts = str(name).replace(".", "").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return str(name)[:2].upper()


# ============================================================
# Scoring
# ============================================================

def grade_category(value, elite, strong, good, average, weak):
    if value >= elite:
        return 20
    if value >= strong:
        return 17
    if value >= good:
        return 14
    if value >= average:
        return 10
    if value >= weak:
        return 6
    return 3


def calculate_results():
    roster = st.session_state.roster

    team_ppg = sum(float(p.get("PPG", 0)) for p in roster)
    team_rpg = sum(float(p.get("RPG", 0)) for p in roster)
    team_apg = sum(float(p.get("APG", 0)) for p in roster)
    team_spg = sum(float(p.get("SPG", 0)) for p in roster)
    team_bpg = sum(float(p.get("BPG", 0)) for p in roster)

    team_allstars = sum(float(p.get("AllStarSelections", 0)) for p in roster)
    team_mvp = sum(float(p.get("MVPPointPct", 0)) for p in roster)

    defense_total = team_spg + team_bpg

    scoring_grade = grade_category(team_ppg, 150, 136, 122, 108, 94)
    rebounding_grade = grade_category(team_rpg, 62, 55, 48, 41, 34)
    playmaking_grade = grade_category(team_apg, 38, 33, 28, 23, 18)
    defense_grade = grade_category(defense_total, 15, 13, 11, 9, 7)

    balance_values = [
        scoring_grade,
        rebounding_grade,
        playmaking_grade,
        defense_grade,
    ]

    balance_grade = round(sum(balance_values) / len(balance_values), 2)

    category_score = (
        scoring_grade
        + rebounding_grade
        + playmaking_grade
        + defense_grade
        + balance_grade
    )

    weakest_category = min(balance_values)

    if weakest_category <= 6:
        category_score -= 10
    elif weakest_category <= 10:
        category_score -= 4

    if all(g >= 14 for g in balance_values):
        category_score += 3

    if all(g >= 17 for g in balance_values):
        category_score += 4

    star_power = (team_allstars * 0.75) + (team_mvp * 33)
    star_power = min(40, star_power)

    final_score = (category_score * 0.60) + (star_power * 0.40)

    wins = round(max(15, min(82, 27 + (final_score * 0.90))))
    losses = 82 - wins

    if wins >= 82:
        tier = "Perfect Team"
        letter = "A+"
    elif wins >= 79:
        tier = "All-Time Great"
        letter = "A+"
    elif wins >= 75:
        tier = "Historic Champion"
        letter = "A+"
    elif wins >= 70:
        tier = "Dynasty"
        letter = "A"
    elif wins >= 64:
        tier = "Elite Contender"
        letter = "A-"
    elif wins >= 56:
        tier = "Playoff Team"
        letter = "B+"
    elif wins >= 48:
        tier = "Playoff Team"
        letter = "B"
    elif wins >= 40:
        tier = "Play-In Team"
        letter = "C"
    else:
        tier = "Lottery Team"
        letter = "D"

    return {
        "wins": wins,
        "losses": losses,
        "tier": tier,
        "letter": letter,
        "spent": st.session_state.spent,
        "remaining": st.session_state.budget,
        "category_score": category_score,
        "final_score": final_score,
        "scoring_grade": scoring_grade,
        "rebounding_grade": rebounding_grade,
        "playmaking_grade": playmaking_grade,
        "defense_grade": defense_grade,
        "balance_grade": balance_grade,
        "star_power": star_power,
        "team_ppg": team_ppg,
        "team_rpg": team_rpg,
        "team_apg": team_apg,
        "team_spg": team_spg,
        "team_bpg": team_bpg,
        "defense_total": defense_total,
    }


# ============================================================
# Position Dialog
# ============================================================

@st.dialog("Draft Player")
def position_dialog():
    player = st.session_state.pending_player

    if player is None:
        return

    slots = eligible_slots_for_player(player["Position"])

    st.markdown(
        f"""
        <div class="draft-player-card">
            <div class="draft-player-name">{player["Player"]}</div>
            <div class="draft-player-meta">
                {player["TeamAbbr"]} • {player["Decade"]} • Listed: {player["Position"]} • Cost {int(player["Cost"])}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not slots:
        st.warning("This player does not fit any remaining roster slot.")
        if st.button("Close", use_container_width=True):
            st.session_state.pending_player = None
            st.rerun()
        return

    st.markdown("#### Choose roster slot")

    cols = st.columns(len(slots))

    for i, slot in enumerate(slots):
        with cols[i]:
            if st.button(slot, key=f"slot_choice_{slot}", use_container_width=True):
                draft_player(player, slot)
                st.rerun()

    st.write("")

    if st.button("Cancel", use_container_width=True):
        st.session_state.pending_player = None
        st.rerun()


if st.session_state.pending_player is not None:
    position_dialog()




# ============================================================
# Mobile Native UI
# ============================================================

def is_mobile_mode():
    val = st.query_params.get("mobile", "0")
    if isinstance(val, list):
        val = val[0] if val else "0"
    return str(val).lower() in {"1", "true", "yes", "mobile"}


def mobile_slot_dock():
    roster_by_slot = {p["DraftPosition"]: p for p in st.session_state.roster}
    items = []
    for slot in POSITIONS:
        p = roster_by_slot.get(slot)
        if p:
            label = initials(p["Player"])
            dot_class = "mobile-slot-dot filled"
        else:
            label = slot
            dot_class = "mobile-slot-dot"
        items.append(f'''<div><div class="{dot_class}">{label}</div><div class="mobile-slot-label">{slot}</div></div>''')
    st.markdown(f'''<div class="mobile-dock"><div class="mobile-dock-inner">{"".join(items)}</div></div>''', unsafe_allow_html=True)


def mobile_header():
    st.markdown('<div class="mobile-app-shell">', unsafe_allow_html=True)
    st.markdown(f'''<div class="mobile-topbar"><div class="mobile-brand-row"><div class="mobile-logo">82-0<br><span style="font-size:8px;">EST.</span></div><div>Round {min(st.session_state.round, ROSTER_SIZE)} / {ROSTER_SIZE}</div></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="mobile-mini-actions">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("☀", key="mobile_dark", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.get("dark_mode", True)
            st.rerun()
    with c2:
        if st.button("☰", key="mobile_menu", use_container_width=True):
            st.toast("Menu coming soon.")
    with c3:
        if st.button("↪", key="mobile_restart", use_container_width=True):
            reset_game()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def mobile_results_screen():
    results = calculate_results()
    roster = sorted_roster()
    colors = ["#fee2e2", "#eef2ff", "#e5e7eb", "#e0f2fe", "#ede9fe", "#dcfce7"]
    border_colors = ["#ef4444", "#312e81", "#111827", "#0f172a", "#6d28d9", "#15803d"]
    st.markdown('<div class="mobile-results-title">Projected Record</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mobile-record">{results["wins"]}<span style="color:#64748b;">—</span>{results["losses"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mobile-grade">{results["letter"]} &nbsp; {results["tier"].upper()} &nbsp; <span style="color:#94a3b8;font-size:14px;">· {results["final_score"]:.1f} pts</span></div>', unsafe_allow_html=True)
    for i, p in enumerate(roster):
        bg = colors[i % len(colors)]
        border = border_colors[i % len(border_colors)]
        slot = str(p.get("DraftPosition", "")).upper()
        st.markdown(f'''<div class="result-player-card" style="background:{bg}; border-left-color:{border};"><div class="rp-avatar">{slot}</div><div><div class="rp-name">{slot} • {p["Player"]}</div><div class="rp-meta">{p["TeamAbbr"]} · {p["Decade"]}</div></div><div class="rp-stats"><div><div class="rp-stat-num">{float(p.get("PPG", 0)):.1f}</div><div class="rp-stat-lab">PPG</div></div><div><div class="rp-stat-num">{float(p.get("RPG", 0)):.1f}</div><div class="rp-stat-lab">RPG</div></div><div><div class="rp-stat-num">{float(p.get("APG", 0)):.1f}</div><div class="rp-stat-lab">APG</div></div><div><div class="rp-stat-num">{float(p.get("SPG", 0)):.1f}</div><div class="rp-stat-lab">SPG</div></div><div><div class="rp-stat-num">{float(p.get("BPG", 0)):.1f}</div><div class="rp-stat-lab">BPG</div></div></div></div>''', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Share", key="mobile_share_results", use_container_width=True):
            st.toast("Share feature coming soon.")
    with c2:
        if st.button("Restart Draft", key="mobile_restart_results", use_container_width=True):
            reset_game(); st.rerun()


def mobile_spin_screen():
    team = st.session_state.team or "---"
    decade = st.session_state.decade or "---"
    st.markdown('<div class="mobile-spin-zone">', unsafe_allow_html=True)
    st.markdown(f'''<div class="mobile-card-row"><div><div class="mobile-spin-card mobile-team-card"><div class="mobile-card-label">TEAM</div><div class="mobile-card-value">{team}</div></div><div class="mobile-card-caption">Team</div></div><div><div class="mobile-spin-card mobile-era-card"><div class="mobile-card-label">ERA</div><div class="mobile-card-value">{decade}</div></div><div class="mobile-card-caption">Decade</div></div></div>''', unsafe_allow_html=True)
    st.write(""); st.write("")
    center = st.columns([1, 1.4, 1])
    with center[1]:
        st.markdown('<div class="mobile-primary">', unsafe_allow_html=True)
        if st.button("SPIN", key="mobile_spin", disabled=st.session_state.has_active_spin, use_container_width=True):
            spin(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def mobile_player_browser():
    team = st.session_state.team or "---"
    decade = st.session_state.decade or "---"
    st.markdown(f'''<div class="mobile-pill-row"><div class="mobile-pills-left"><div class="mobile-pill mobile-pill-team">{team}</div><div class="mobile-pill mobile-pill-era">{decade}</div></div></div>''', unsafe_allow_html=True)
    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div class="mobile-respin">', unsafe_allow_html=True)
        if st.button("↻ Team", key="mobile_team_respin", disabled=not st.session_state.has_active_spin or st.session_state.team_respin_used, use_container_width=True):
            respin_team(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with r2:
        st.markdown('<div class="mobile-respin mobile-respin-purple">', unsafe_allow_html=True)
        if st.button("↻ Era", key="mobile_era_respin", disabled=not st.session_state.has_active_spin or st.session_state.decade_respin_used, use_container_width=True):
            respin_decade(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.1, 2.2, 1.1])
    with f1:
        position_filter = st.selectbox("Position", ["All", "PG", "SG", "SF", "PF", "C"], label_visibility="collapsed", key="mobile_pos_filter")
    with f2:
        search_term = st.text_input("Search", placeholder="Search players...", label_visibility="collapsed", key="mobile_search")
    with f3:
        sort_choice = st.selectbox("Sort", ["PPG", "RPG", "APG", "SPG", "BPG", "Cost Low", "Cost High"], label_visibility="collapsed", key="mobile_sort")
    options = st.session_state.options.copy()
    if position_filter != "All":
        options = options[options["Position"].astype(str).str.contains(position_filter, case=False, na=False)]
    if search_term:
        options = options[options["Player"].astype(str).str.contains(search_term, case=False, na=False)]
    sort_map = {"PPG": False, "RPG": False, "APG": False, "SPG": False, "BPG": False, "Cost Low": True, "Cost High": False}
    sort_col = "Cost" if "Cost" in sort_choice else sort_choice
    options = options.sort_values(sort_col, ascending=sort_map[sort_choice]).reset_index(drop=True)
    st.markdown(f'<div class="mobile-count">{len(options)} players available</div>', unsafe_allow_html=True)
    if options.empty:
        st.markdown('<div class="notice-card">No affordable players fit your remaining roster slots.</div>', unsafe_allow_html=True); return
    for idx, row in options.iterrows():
        st.markdown(f'''<div class="mobile-player-card"><div><div class="mobile-player-name">{row["Player"]}</div><div class="mobile-player-pos">{row["Position"]}</div><div class="mobile-player-meta">{row["TeamAbbr"]} · {row["Decade"]}</div></div><div class="mobile-stat-grid"><div><div class="mobile-stat-num">{float(row.get("PPG", 0)):.1f}</div><div class="mobile-stat-lab">PPG</div></div><div><div class="mobile-stat-num">{float(row.get("RPG", 0)):.1f}</div><div class="mobile-stat-lab">RPG</div></div><div><div class="mobile-stat-num">{float(row.get("APG", 0)):.1f}</div><div class="mobile-stat-lab">APG</div></div><div><div class="mobile-stat-num">{float(row.get("SPG", 0)):.1f}</div><div class="mobile-stat-lab">SPG</div></div><div><div class="mobile-stat-num">{float(row.get("BPG", 0)):.1f}</div><div class="mobile-stat-lab">BPG</div></div></div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="mobile-pick">', unsafe_allow_html=True)
        if st.button("Pick Player", key=f"mobile_pick_{st.session_state.spin_number}_{idx}", use_container_width=True):
            st.session_state.pending_player = row.to_dict(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def mobile_roster_full():
    st.markdown(
        f"""
        <div class="mobile-budget-grid">
            <div class="mobile-budget-card">
                <div class="mobile-budget-label">Budget</div>
                <div class="mobile-budget-value">${BUDGET}</div>
            </div>
            <div class="mobile-budget-card">
                <div class="mobile-budget-label">Spent</div>
                <div class="mobile-budget-value">${st.session_state.spent}</div>
            </div>
            <div class="mobile-budget-card">
                <div class="mobile-budget-label">Remaining</div>
                <div class="mobile-budget-value">${st.session_state.budget}</div>
            </div>
        </div>
        <div class="mobile-roster-title">ROSTER ({len(st.session_state.roster)}/{ROSTER_SIZE})</div>
        """,
        unsafe_allow_html=True
    )

    roster_by_slot = {p["DraftPosition"]: p for p in st.session_state.roster}

    for slot in POSITIONS:
        p = roster_by_slot.get(slot)
        if p:
            st.markdown(
                f"""
                <div class="mobile-slot-card">
                    <div class="mobile-slot-badge filled">{slot}</div>
                    <div class="mobile-slot-main">
                        <div class="mobile-slot-player">{p["Player"]}</div>
                        <div class="mobile-slot-meta">{p["TeamAbbr"]} · {p["Decade"]}</div>
                    </div>
                    <div class="mobile-slot-cost">${int(p["Cost"])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="mobile-slot-card empty">
                    <div class="mobile-slot-badge">{slot}</div>
                    <div class="mobile-slot-main">
                        <div class="mobile-slot-empty">Empty</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_mobile_app():
    mobile_header()
    if st.session_state.show_results:
        mobile_results_screen(); st.markdown('</div>', unsafe_allow_html=True); return
    if not st.session_state.has_active_spin:
        mobile_spin_screen()
    else:
        mobile_player_browser()
    with st.expander("Roster / Budget", expanded=True):
        mobile_roster_full()
    mobile_slot_dock()
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# Results Screen
# ============================================================

if is_mobile_mode():
    render_mobile_app()
    st.stop()

if st.session_state.show_results:
    results = calculate_results()
    roster = sorted_roster()

    colors = ["#fee2e2", "#eef2ff", "#e5e7eb", "#e0f2fe", "#ede9fe", "#dcfce7"]
    border_colors = ["#ef4444", "#312e81", "#111827", "#0f172a", "#6d28d9", "#15803d"]

    st.markdown('<div class="results-page">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="projected-label">Projected Record</div>
        <div class="big-record">
            {results["wins"]}<span class="record-dash">—</span>{results["losses"]}
        </div>

        <div class="grade-line">
            <span class="grade-letter">{results["letter"]}</span>
            <span class="tier-text">{results["tier"].upper()}</span>
            <span class="score-small">· {results["final_score"]:.1f} pts</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    for i, p in enumerate(roster):
        bg = colors[i % len(colors)]
        border = border_colors[i % len(border_colors)]
        slot = str(p.get("DraftPosition", "")).upper()
        slot_display = "6TH" if slot == "6TH" else slot

        st.markdown(
            f"""
            <div class="result-player-card" style="background:{bg}; border-left-color:{border};">
                <div class="rp-avatar">{slot_display}</div>
                <div>
                    <div class="rp-name">{slot_display} • {p["Player"]}</div>
                    <div class="rp-meta">{p["TeamAbbr"]} · {p["Decade"]}</div>
                </div>
                <div class="rp-stats">
                    <div><div class="rp-stat-num">{float(p.get("PPG", 0)):.1f}</div><div class="rp-stat-lab">PPG</div></div>
                    <div><div class="rp-stat-num">{float(p.get("RPG", 0)):.1f}</div><div class="rp-stat-lab">RPG</div></div>
                    <div><div class="rp-stat-num">{float(p.get("APG", 0)):.1f}</div><div class="rp-stat-lab">APG</div></div>
                    <div><div class="rp-stat-num">{float(p.get("SPG", 0)):.1f}</div><div class="rp-stat-lab">SPG</div></div>
                    <div><div class="rp-stat-num">{float(p.get("BPG", 0)):.1f}</div><div class="rp-stat-lab">BPG</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class="team-total-row">
            <div><div class="team-total-num">{results["team_ppg"]:.1f}</div><div class="team-total-label">PPG</div></div>
            <div><div class="team-total-num">{results["team_rpg"]:.1f}</div><div class="team-total-label">RPG</div></div>
            <div><div class="team-total-num">{results["team_apg"]:.1f}</div><div class="team-total-label">APG</div></div>
            <div><div class="team-total-num">{results["team_spg"]:.1f}</div><div class="team-total-label">SPG</div></div>
            <div><div class="team-total-num">{results["team_bpg"]:.1f}</div><div class="team-total-label">BPG</div></div>
        </div>

        <div class="footer-note">
            Scoring is based on team category balance plus controlled star-power impact.
        </div>
        """,
        unsafe_allow_html=True
    )

    action_left, action_right = st.columns(2)

    with action_left:
        if st.button("Share", use_container_width=True):
            st.toast("Share feature coming soon.")

    with action_right:
        if st.button("Restart Draft", use_container_width=True):
            reset_game()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# ============================================================
# Header
# ============================================================

header_left, header_mid, header_right = st.columns([4, 2, 3])

with header_left:
    st.markdown('<div class="brand">🏀 NBA Draft Game</div>', unsafe_allow_html=True)

with header_mid:
    st.markdown(
        f'<div class="round-top">Round {min(st.session_state.round, ROSTER_SIZE)} / {ROSTER_SIZE}</div>',
        unsafe_allow_html=True
    )

with header_right:
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("Dark Mode", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.get("dark_mode", False)
            st.rerun()

    with b2:
        if st.button("Share", use_container_width=True):
            st.toast("Share feature coming soon.")

    with b3:
        if st.button("Restart", use_container_width=True):
            reset_game()
            st.rerun()

st.markdown('<hr class="app-divider">', unsafe_allow_html=True)


# ============================================================
# Main UI
# ============================================================

team = st.session_state.team or "---"
decade = st.session_state.decade or "---"

mobile_mode = st.query_params.get("mobile", "0") == "1"


def render_budget_cards():
    st.markdown(
        f"""
        <div class="info-row">
            <div class="info-card">
                <div class="info-label">Budget</div>
                <div class="info-value purple">${BUDGET}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Spent</div>
                <div class="info-value">${st.session_state.spent}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Remaining</div>
                <div class="info-value green">${st.session_state.budget}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_roster_mobile():
    roster_by_slot = {p["DraftPosition"]: p for p in st.session_state.roster}

    st.markdown(
        f"""
        <div class="mobile-roster-title">
            ROSTER ({len(st.session_state.roster)}/{ROSTER_SIZE})
        </div>
        """,
        unsafe_allow_html=True
    )

    for slot in POSITIONS:
        if slot in roster_by_slot:
            p = roster_by_slot[slot]

            st.markdown(
                f"""
                <div class="mobile-slot-card">
                    <div class="mobile-slot-badge filled">{slot}</div>
                    <div class="mobile-slot-main">
                        <div class="mobile-slot-player">{p["Player"]}</div>
                        <div class="mobile-slot-meta">{p["TeamAbbr"]} · {p["Decade"]}</div>
                    </div>
                    <div class="mobile-slot-cost">${int(p["Cost"])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.markdown(
                f"""
                <div class="mobile-slot-card empty">
                    <div class="mobile-slot-badge">{slot}</div>
                    <div class="mobile-slot-main">
                        <div class="mobile-slot-empty">Empty</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_spin_cards():
    card_left, card_right = st.columns(2, gap="large")

    with card_left:
        st.markdown(
            f"""
            <div class="flip-wrap">
                <div class="team-spin-card">
                    <div class="card-label">TEAM</div>
                    <div class="card-value">{team}</div>
                </div>
                <div class="below-label">Team</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with card_right:
        st.markdown(
            f"""
            <div class="flip-wrap">
                <div class="era-spin-card">
                    <div class="card-label">ERA</div>
                    <div class="card-value">{decade}</div>
                </div>
                <div class="below-label">Decade</div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_available_players():
    st.markdown('<div class="section-title">Available Players</div>', unsafe_allow_html=True)

    if not st.session_state.has_active_spin:
        st.markdown('<div class="notice-card">Spin to reveal available players.</div>', unsafe_allow_html=True)
        return

    if st.session_state.options.empty:
        st.markdown('<div class="notice-card">No affordable players fit your remaining roster slots.</div>', unsafe_allow_html=True)
        return

    tools = st.columns([1.15, 1.1, 1.0], gap="small")

    with tools[0]:
        position_filter = st.selectbox(
            "Position",
            ["All", "PG", "SG", "SF", "PF", "C"],
            label_visibility="collapsed"
        )

    with tools[1]:
        search_term = st.text_input(
            "Search",
            placeholder="Search...",
            label_visibility="collapsed"
        )

    with tools[2]:
        sort_choice = st.selectbox(
            "Sort",
            ["PPG", "RPG", "APG", "SPG", "BPG", "Cost Low", "Cost High"],
            label_visibility="collapsed"
        )

    options = st.session_state.options.copy()

    if position_filter != "All":
        options = options[
            options["Position"].astype(str).str.contains(position_filter, case=False, na=False)
        ]

    if search_term:
        options = options[
            options["Player"].astype(str).str.contains(search_term, case=False, na=False)
        ]

    if sort_choice == "PPG":
        options = options.sort_values("PPG", ascending=False)
    elif sort_choice == "RPG":
        options = options.sort_values("RPG", ascending=False)
    elif sort_choice == "APG":
        options = options.sort_values("APG", ascending=False)
    elif sort_choice == "SPG":
        options = options.sort_values("SPG", ascending=False)
    elif sort_choice == "BPG":
        options = options.sort_values("BPG", ascending=False)
    elif sort_choice == "Cost Low":
        options = options.sort_values("Cost", ascending=True)
    elif sort_choice == "Cost High":
        options = options.sort_values("Cost", ascending=False)

    options = options.reset_index(drop=True)

    st.caption(f"{len(options)} players available")

    container_height = 520 if mobile_mode else 300

    with st.container(height=container_height):
        for idx, row in options.iterrows():
            row_cols = st.columns([4.4, 1.0], gap="small")

            with row_cols[0]:
                st.markdown(
                    f"""
                    <div class="player-card">
                        <div class="player-name">{row["Player"]}</div>
                        <div class="player-meta">{row["Position"]} • {row["TeamAbbr"]} • {row["Decade"]} • Cost {int(row["Cost"])}</div>
                        <div class="stat-grid">
                            <div><div class="stat-num">{float(row.get("PPG", 0)):.1f}</div><div class="stat-lab">PPG</div></div>
                            <div><div class="stat-num">{float(row.get("RPG", 0)):.1f}</div><div class="stat-lab">RPG</div></div>
                            <div><div class="stat-num">{float(row.get("APG", 0)):.1f}</div><div class="stat-lab">APG</div></div>
                            <div><div class="stat-num">{float(row.get("SPG", 0)):.1f}</div><div class="stat-lab">SPG</div></div>
                            <div><div class="stat-num">{float(row.get("BPG", 0)):.1f}</div><div class="stat-lab">BPG</div></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with row_cols[1]:
                if st.button(
                    "Select",
                    key=f"select_{st.session_state.spin_number}_{idx}",
                    use_container_width=True
                ):
                    st.session_state.pending_player = row.to_dict()
                    st.rerun()


def render_roster_desktop():
    st.markdown('<div class="section-title">Roster</div>', unsafe_allow_html=True)

    roster_by_slot = {p["DraftPosition"]: p for p in st.session_state.roster}

    for slot in POSITIONS:
        if slot in roster_by_slot:
            p = roster_by_slot[slot]

            st.markdown(
                f"""
                <div class="slot-card">
                    <div class="slot-label">{slot}</div>
                    <div>
                        <div class="slot-player">{p["Player"]}</div>
                        <div class="slot-meta">
                            {p["TeamAbbr"]} • {p["Decade"]} • Cost {int(p["Cost"])}
                            • {float(p.get("PPG", 0)):.1f} PPG
                            • {float(p.get("RPG", 0)):.1f} RPG
                            • {float(p.get("APG", 0)):.1f} APG
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="slot-card">
                    <div class="slot-label">{slot}</div>
                    <div class="slot-empty">Empty</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        f"""
        <div class="total-cost-row">
            <div>TOTAL COST</div>
            <div>{st.session_state.spent} / {BUDGET}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


if mobile_mode:
    # Mobile: spin/cards first, then players, then roster-focused section
    render_spin_cards()

    if st.button("SPIN", disabled=st.session_state.has_active_spin, use_container_width=True):
        spin()
        st.rerun()

    controls = st.columns(3)

    with controls[0]:
        if st.button(
            "🔄 Team",
            disabled=not st.session_state.has_active_spin or st.session_state.team_respin_used,
            use_container_width=True
        ):
            respin_team()
            st.rerun()

    with controls[1]:
        if st.button(
            "🔄 Era",
            disabled=not st.session_state.has_active_spin or st.session_state.decade_respin_used,
            use_container_width=True
        ):
            respin_decade()
            st.rerun()

    with controls[2]:
        if st.button("Reset", use_container_width=True):
            reset_game()
            st.rerun()

    render_budget_cards()
    render_available_players()
    render_roster_mobile()

    if len(st.session_state.roster) == ROSTER_SIZE:
        if st.button("CONFIRM TEAM", use_container_width=True):
            st.session_state.show_results = True
            st.rerun()

else:
    # Desktop: keep your original two-column layout
    left, right = st.columns([1, 1.05], gap="large")

    with left:
        render_spin_cards()

        if st.button("SPIN", disabled=st.session_state.has_active_spin, use_container_width=True):
            spin()
            st.rerun()

        controls = st.columns(3)

        with controls[0]:
            if st.button(
                "🔄 Team",
                disabled=not st.session_state.has_active_spin or st.session_state.team_respin_used,
                use_container_width=True
            ):
                respin_team()
                st.rerun()

        with controls[1]:
            if st.button(
                "🔄 Era",
                disabled=not st.session_state.has_active_spin or st.session_state.decade_respin_used,
                use_container_width=True
            ):
                respin_decade()
                st.rerun()

        with controls[2]:
            if st.button("Reset", use_container_width=True):
                reset_game()
                st.rerun()

        reserve_note = max(0, (ROSTER_SIZE - len(st.session_state.roster) - 1) * MIN_PLAYER_COST)
        max_next_cost = max_allowed_cost_for_next_pick() if len(st.session_state.roster) < ROSTER_SIZE else 0

        render_budget_cards()

        if len(st.session_state.roster) < ROSTER_SIZE:
            st.caption(f"Max next pick: {max_next_cost} · Reserved minimum after pick: {reserve_note}")

        render_available_players()

    with right:
        render_roster_desktop()
