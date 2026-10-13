"""
Peak Dashboard
==============
Left  : poster-style calendar. Every game card is clickable and opens a modal to assign VPOC + HR.
Right : pill-shaped tabs -> [Peak Tracker] [Auto Email]

Requirements : streamlit >= 1.39, pandas
Run          : streamlit run peak_dashboard.py
Secrets      : .streamlit/secrets.toml  ->  [smtp] host / port / password
"""

import html
import logging
import re
import smtplib
import sqlite3
import ssl
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
import streamlit as st

# Poster artwork lives in its own module (your old "section 8"). Falls back to text cards if missing.
try:
    from peak_artwork import BANNER_B64, CARD_B64
except ImportError:
    BANNER_B64, CARD_B64 = "", {}

# =============================================================================
# 1. CONFIG
# =============================================================================
APP_TITLE = "Peak 2026 Dashboard"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "peak_dashboard.db"

SENDER_EMAIL = "javmuhak@amazon.ae"
STATUS_OPTIONS = ["Participant", "🏆 Winner"]
TABS = ["Peak Tracker", "Auto Email"]

BADGE_PATTERN = re.compile(r"^[A-Z0-9_-]{1,32}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

ITEMS = {
    "breast-cancer": {"name": "Breast Cancer Awareness Month", "emoji": "🎀", "kind": "event"},
    "cup-tower":     {"name": "Build Tallest Cup Tower With No Hands", "emoji": "🥛", "kind": "game"},
    "dont-sit":      {"name": "Don't Sit at the Same Time!", "emoji": "🪑", "kind": "game"},
    "pass-ball":     {"name": "Pass the Ball", "emoji": "🏐", "kind": "game"},
    "ring-toss":     {"name": "Ring Toss", "emoji": "🎯", "kind": "game"},
    "touch-color":   {"name": "Touch the Wrong Color", "emoji": "🎨", "kind": "game"},
    "back-same":     {"name": "Back to the Same Time!", "emoji": "💺", "kind": "game"},
    "hula":          {"name": "Pass the Hula Hoop", "emoji": "⭕", "kind": "game"},
    "halloween":     {"name": "Happy Halloween", "emoji": "🎃", "kind": "event"},
    "raffle":        {"name": "Raffle Contest", "emoji": "🎁", "kind": "event"},
    "diwali":        {"name": "Happy Diwali", "emoji": "🪔", "kind": "event"},
    "amazon":        {"name": "Amazon Gift Voucher", "emoji": "🎟️", "kind": "event"},
    "mens-day":      {"name": "International Men's Day", "emoji": "🧔", "kind": "event"},
    "birthday":      {"name": "Happy Birthday", "emoji": "🎂", "kind": "event"},
    "uae":           {"name": "UAE National Day", "emoji": "🇦🇪", "kind": "event"},
    "momenteer":     {"name": "Momenteer Award Day", "emoji": "🏆", "kind": "event"},
    "coke-day":      {"name": "Coke Day", "emoji": "🥤", "kind": "food"},
    "vadapav":       {"name": "Vadapav Day", "emoji": "🍔", "kind": "food"},
    "lemonade":      {"name": "Happy Lemonade Day", "emoji": "🍋", "kind": "food"},
    "churros":       {"name": "Churros Day", "emoji": "🥖", "kind": "food"},
    "potato-spiral": {"name": "Potato Spiral Day", "emoji": "🥔", "kind": "food"},
}

START_DATE = date(2026, 10, 26)
SCHEDULE = [
    "breast-cancer", "cup-tower", "dont-sit", "pass-ball", "ring-toss", "halloween", "ring-toss",
    "touch-color", "raffle", "coke-day", "vadapav", "ring-toss", "back-same", "cup-tower",
    "diwali", "raffle", "amazon", "vadapav", "mens-day", "pass-ball", "touch-color",
    "cup-tower", "raffle", "lemonade", "churros", "birthday", "hula", "touch-color",
    "amazon", "raffle", "uae", "potato-spiral", "ring-toss", "dont-sit", "cup-tower",
    "hula", "raffle", "uae", "potato-spiral", "momenteer",
]
assert all(key in ITEMS for key in SCHEDULE), "SCHEDULE has a key missing from ITEMS"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
ROW_ASPECT = [207 / 157, 207 / 145, 207 / 145, 207 / 144, 207 / 134, 207 / 117]
GAMES = {k: v["name"] for k, v in ITEMS.items() if v["kind"] == "game"}

# {game_id: [date, date, ...]}: a game can run on several days.
GAME_DATES: dict = {}
for _i, _key in enumerate(SCHEDULE):
    if _key in GAMES:
        GAME_DATES.setdefault(_key, []).append(START_DATE + timedelta(days=_i))

logger = logging.getLogger("peak_dashboard")


# =============================================================================
# 2. DATABASE LAYER
# =============================================================================
@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@st.cache_resource
def init_db() -> bool:
    with db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS vpoc_assignments (
                game_id     TEXT PRIMARY KEY,
                vpoc_name   TEXT NOT NULL,
                vpoc_email  TEXT NOT NULL,
                hr_name     TEXT NOT NULL,
                hr_email    TEXT NOT NULL,
                assigned_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_id   TEXT NOT NULL,
                game_id    TEXT NOT NULL,
                status     TEXT NOT NULL DEFAULT 'Participant',
                scanned_at TEXT NOT NULL,
                UNIQUE (badge_id, game_id)
            );
            CREATE INDEX IF NOT EXISTS idx_scans_game ON scans (game_id);
            CREATE TABLE IF NOT EXISTS email_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id    TEXT NOT NULL,
                run_date   TEXT NOT NULL,
                recipients TEXT NOT NULL,
                ok         INTEGER NOT NULL,
                detail     TEXT NOT NULL DEFAULT '',
                sent_at    TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_email_game ON email_log (game_id, run_date);
            """
        )
    return True


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---- VPOC assignments --------------------------------------------------------
def upsert_vpoc(game_id, vpoc_name, vpoc_email, hr_name, hr_email) -> None:
    with db() as conn:
        conn.execute(
            """
            INSERT INTO vpoc_assignments
                (game_id, vpoc_name, vpoc_email, hr_name, hr_email, assigned_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                vpoc_name   = excluded.vpoc_name,
                vpoc_email  = excluded.vpoc_email,
                hr_name     = excluded.hr_name,
                hr_email    = excluded.hr_email,
                assigned_at = excluded.assigned_at
            """,
            (game_id, vpoc_name, vpoc_email, hr_name, hr_email, _now()),
        )


def get_all_vpocs() -> dict:
    with db() as conn:
        rows = conn.execute("SELECT * FROM vpoc_assignments").fetchall()
    return {r["game_id"]: dict(r) for r in rows}


# ---- Scans -------------------------------------------------------------------
def add_scan(badge_id: str, game_id: str) -> bool:
    """False (nothing saved) if this badge already played this game."""
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO scans (badge_id, game_id, scanned_at) VALUES (?, ?, ?)",
                (badge_id, game_id, _now()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_scans(game_id: str) -> pd.DataFrame:
    with db() as conn:
        return pd.read_sql_query(
            """
            SELECT id, badge_id AS "Badge ID", status AS "Status", scanned_at AS "Scanned at"
            FROM scans WHERE game_id = ? ORDER BY id ASC
            """,
            conn,
            params=(game_id,),
        )


def update_status(scan_id: int, status: str) -> None:
    if status not in STATUS_OPTIONS:
        raise ValueError(f"Invalid status: {status!r}")
    with db() as conn:
        conn.execute("UPDATE scans SET status = ? WHERE id = ?", (status, scan_id))


# ---- Email log ---------------------------------------------------------------
def log_email(game_id: str, run_date: date, recipients: list, ok: bool, detail: str) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO email_log (game_id, run_date, recipients, ok, detail, sent_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (game_id, run_date.isoformat(), ", ".join(recipients), int(ok), detail[:500], _now()),
        )


def get_last_email(game_id: str):
    with db() as conn:
        row = conn.execute(
            "SELECT sent_at, ok FROM email_log WHERE game_id = ? ORDER BY id DESC LIMIT 1",
            (game_id,),
        ).fetchone()
    return dict(row) if row else None


def was_sent(game_id: str, run_date: date) -> bool:
    with db() as conn:
        row = conn.execute(
            "SELECT 1 FROM email_log WHERE game_id = ? AND run_date = ? AND ok = 1 LIMIT 1",
            (game_id, run_date.isoformat()),
        ).fetchone()
    return row is not None


# =============================================================================
# 3. EMAIL (smtplib)
# =============================================================================
def build_reminder_email(game_name: str, vpoc_name: str, hr_name: str, run_date: date):
    """Returns (subject, plain_text, html)."""
    day = run_date.strftime("%A, %d %B %Y")
    subject = f"Peak 2026: it's your day to run \"{game_name}\" ({run_date.strftime('%d %b')})"
    text = (
        f"Hi {vpoc_name},\n\n"
        f"This is your reminder that {day} is your day to run the engagement activity "
        f"\"{game_name}\" for Peak 2026.\n\n"
        f"Your HR partner for this activity is {hr_name}. Please coordinate with them ahead of time "
        f"and use the Peak Dashboard to scan badges and record winners.\n\n"
        f"Thanks,\nPeak 2026 Team"
    )
    body = (
        f"<p>Hi {html.escape(vpoc_name)},</p>"
        f"<p>This is your reminder that <b>{html.escape(day)}</b> is your day to run the engagement "
        f"activity <b>{html.escape(game_name)}</b> for Peak 2026.</p>"
        f"<p>Your HR partner for this activity is <b>{html.escape(hr_name)}</b>. Please coordinate "
        f"with them ahead of time and use the Peak Dashboard to scan badges and record winners.</p>"
        f"<p>Thanks,<br>Peak 2026 Team</p>"
    )
    return subject, text, body


def send_email(to: list, cc: list, subject: str, text: str, html_body: str):
    """Send through SMTP using the password stored in st.secrets. Returns (ok, detail)."""
    try:
        cfg = st.secrets["smtp"]
        host = cfg["host"]
        port = int(cfg.get("port", 587))
        user = cfg.get("user", SENDER_EMAIL)
        password = cfg["password"]
    except (KeyError, FileNotFoundError):
        return False, "SMTP settings missing: add [smtp] host and password to .streamlit/secrets.toml."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.set_content(text)
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(user, password)
            server.send_message(msg, to_addrs=to + cc)
        return True, "Sent"
    except (smtplib.SMTPException, OSError) as exc:
        logger.exception("Email failed")
        return False, f"{type(exc).__name__}: {exc}"


def notify_vpoc(game_id: str, run_date: date):
    """Email the assigned VPOC (HR in cc) that run_date is their day. Logs the attempt."""
    assignment = get_all_vpocs().get(game_id)
    if not assignment:
        return False, "No VPOC assigned for this game."
    subject, text, body = build_reminder_email(
        GAMES[game_id], assignment["vpoc_name"], assignment["hr_name"], run_date)
    to, cc = [assignment["vpoc_email"]], [assignment["hr_email"]]
    ok, detail = send_email(to, cc, subject, text, body)
    log_email(game_id, run_date, to + cc, ok, detail)
    return ok, detail


# =============================================================================
# 4. STATE + CALLBACKS
# =============================================================================
def init_state() -> None:
    st.session_state.setdefault("active_game", next(iter(GAMES)))
    st.session_state.setdefault("scan_feedback", None)
    st.session_state.setdefault("pending_toast", None)
    st.session_state.setdefault("editor_version", 0)
    st.session_state.setdefault("editor_key", "")
    st.session_state.setdefault("editor_ids", [])
    st.session_state.setdefault("right_tab", TABS[0])


def select_game(game_id: str) -> None:
    st.session_state.active_game = game_id


def sync_tracker_game() -> None:
    st.session_state.active_game = st.session_state.tracker_game_select


def handle_scan() -> None:
    raw = st.session_state.badge_input
    st.session_state.badge_input = ""
    badge = raw.strip().upper()
    game_id = st.session_state.active_game

    if not badge:
        return
    if not BADGE_PATTERN.match(badge):
        st.session_state.scan_feedback = ("warning", f"“{badge}” is not a valid badge ID. Scan again.")
        st.toast("Invalid badge ID", icon="⚠️")
        return

    if add_scan(badge, game_id):
        st.session_state.scan_feedback = ("success", f"Badge {badge} added to {GAMES[game_id]}.")
        st.toast(f"Badge {badge} added", icon="✅")
    else:
        st.session_state.scan_feedback = (
            "error",
            f"DUPLICATE: badge {badge} has already played {GAMES[game_id]}. Nothing was saved.")
        st.toast(f"Duplicate: {badge}", icon="🚫")


def handle_status_edit() -> None:
    state = st.session_state.get(st.session_state.editor_key) or {}
    ids = st.session_state.editor_ids
    changed = 0
    for position, changes in state.get("edited_rows", {}).items():
        new_status = changes.get("Status")
        if new_status in STATUS_OPTIONS and int(position) < len(ids):
            update_status(int(ids[int(position)]), new_status)
            changed += 1
    if changed:
        st.session_state.editor_version += 1
        st.session_state.pending_toast = ("Result saved", "💾")


# =============================================================================
# 5. STYLING
# =============================================================================
CSS = """
<style>
:root { --pk-gap: 14px; --pk-green: #2fa84f; }

/* Full-width canvas */
.block-container { padding: 1.5rem 2rem 2rem; max-width: 100% !important; }

.peak-title { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; }
.peak-sub   { margin: .15rem 0 1.25rem; opacity: .7; }

/* ---- Calendar sheet ---- */
.st-key-pk_cal, .st-key-pk_cal > [data-testid="stVerticalBlock"] { gap: var(--pk-gap) !important; }
.st-key-pk_cal {
    position: relative; background: #fff; border-radius: 10px;
    padding: 3.4% 1.2% 1.2% 9.1%; box-sizing: border-box; overflow: hidden;
}
.st-key-pk_cal::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 8.3%;
    background-repeat: no-repeat; background-size: 100% 100%; background-position: center;
}
.st-key-pk_cal [data-testid="stHorizontalBlock"] { gap: var(--pk-gap) !important; }
.st-key-pk_cal [data-testid="stColumn"], .st-key-pk_cal [data-testid="column"] { position: relative; }

.pk-weekday {
    text-align: center; font-weight: 800; font-size: .88rem; letter-spacing: .03em;
    text-transform: uppercase; color: var(--pk-green); padding: 4px 0; border-radius: 4px;
}
.pk-weekday.sat { background: #f1f6e3; }

/* ---- Day card ---- */
.pk-card {
    position: relative; box-sizing: border-box; width: 100%; overflow: hidden;
    border-radius: 12px; background: #eef8fc;
    transition: transform .15s ease, box-shadow .15s ease;
}
.pk-card img { display: block; width: 100%; height: 100%; object-fit: fill; }
.pk-card .pk-fallback {
    display: flex; align-items: center; justify-content: center; height: 100%;
    padding: 8px; text-align: center; font-weight: 800; font-size: .8rem; color: #1b2a41;
}
.pk-card.is-today  { box-shadow: 0 0 0 3px #ffb400; }
.pk-card.is-active { outline: 3px solid #2fb45a; outline-offset: -3px; }
.pk-flag {
    position: absolute; top: 7px; right: 7px; width: 18px; height: 18px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .68rem; font-weight: 800; background: #ffb400; color: #3b2a00;
    box-shadow: 0 1px 3px rgba(0, 0, 0, .25);
}
.pk-flag.ok { background: #2fb45a; color: #fff; }

/* Clickable games: invisible button stretched over the card */
[class*="st-key-pk_game_"] { position: absolute !important; inset: 0; z-index: 3; }
[class*="st-key-pk_game_"] [data-testid="stButton"],
[class*="st-key-pk_game_"] button { width: 100%; height: 100%; }
[class*="st-key-pk_game_"] button { opacity: 0; cursor: pointer; padding: 0; min-height: 0; }
[data-testid="stColumn"]:has([class*="st-key-pk_game_"]:hover) .pk-card,
[data-testid="column"]:has([class*="st-key-pk_game_"]:hover) .pk-card {
    transform: translateY(-3px); box-shadow: 0 8px 18px rgba(20, 60, 90, .22);
}

/* ---- Tablet / pill tabs (st.radio) ---- */
.st-key-pk_tabs [role="radiogroup"] { display: flex; flex-direction: row; gap: 10px; flex-wrap: wrap; }
.st-key-pk_tabs label[data-baseweb="radio"] {
    margin: 0; padding: .5rem 1.5rem; border-radius: 999px; cursor: pointer;
    background: rgba(128, 138, 155, .14); border: 1px solid rgba(128, 138, 155, .35);
    transition: all .15s ease;
}
.st-key-pk_tabs label[data-baseweb="radio"]:hover { background: rgba(47, 168, 79, .15); }
.st-key-pk_tabs label[data-baseweb="radio"] > div:first-child { display: none; }  /* hide radio dot */
.st-key-pk_tabs label[data-baseweb="radio"] p { font-weight: 700; font-size: .95rem; margin: 0; }
.st-key-pk_tabs label[data-baseweb="radio"]:has(input:checked) {
    background: var(--pk-green); border-color: var(--pk-green);
    box-shadow: 0 3px 10px rgba(47, 168, 79, .35);
}
.st-key-pk_tabs label[data-baseweb="radio"]:has(input:checked) p { color: #fff; }

/* ---- Big metric tiles ---- */
[data-testid="stMetric"] {
    background: rgba(128, 138, 155, .10); border: 1px solid rgba(128, 138, 155, .30);
    border-radius: 14px; padding: 1rem 1.25rem;
}
[data-testid="stMetricValue"] { font-size: 3.2rem; font-weight: 800; line-height: 1.1; }
[data-testid="stMetricLabel"] p { font-size: 1rem; font-weight: 600; opacity: .8; }

@media (max-width: 900px) {
    .st-key-pk_cal { padding-left: 1.2%; }
    .st-key-pk_cal::before { display: none; }
}
</style>
"""


def build_banner_css() -> str:
    if not BANNER_B64:
        return ""
    return ('<style>.st-key-pk_cal::before { background-image: '
            f'url("data:image/webp;base64,{BANNER_B64}"); }}</style>')


# =============================================================================
# 6. UI COMPONENTS
# =============================================================================
@st.dialog("Assign VPOC and HR")
def vpoc_dialog(game_id: str, when: date) -> None:
    existing = get_all_vpocs().get(game_id, {})
    st.markdown(f"**{GAMES[game_id]}**  \n{when.strftime('%A, %d %b %Y')}")
    runs = ", ".join(d.strftime("%d %b") for d in GAME_DATES.get(game_id, []))
    st.caption(f"This game runs on: {runs}. One VPOC and HR cover all of its dates.")

    with st.form(f"vpoc_form_{game_id}"):
        c1, c2 = st.columns(2)
        vpoc_name = c1.text_input("VPOC name", value=existing.get("vpoc_name", ""))
        vpoc_email = c2.text_input("VPOC email", value=existing.get("vpoc_email", ""))
        hr_name = c1.text_input("HR name", value=existing.get("hr_name", ""))
        hr_email = c2.text_input("HR email", value=existing.get("hr_email", ""))
        submitted = st.form_submit_button("Save assignment", type="primary", use_container_width=True)

    if not submitted:
        return

    values = [v.strip() for v in (vpoc_name, vpoc_email, hr_name, hr_email)]
    if not all(values):
        st.error("Fill in all four fields.")
        return
    if not (EMAIL_PATTERN.match(values[1]) and EMAIL_PATTERN.match(values[3])):
        st.error("Enter valid email addresses for the VPOC and HR.")
        return

    upsert_vpoc(game_id, *values)
    st.session_state.pending_toast = ("Assignment saved. Use the Auto Email tab to notify.", "✅")
    st.rerun()


def build_weeks() -> list:
    cells = [(START_DATE + timedelta(days=i), key) for i, key in enumerate(SCHEDULE)]
    cells += [None] * (-len(cells) % 7)
    return [cells[i:i + 7] for i in range(0, len(cells), 7)]


def card_html(day: date, item: dict, *, ratio: float, vpoc_set: bool,
              is_today: bool, is_active: bool) -> str:
    classes = ["pk-card", item["kind"]]
    if is_today:
        classes.append("is-today")
    if is_active:
        classes.append("is-active")

    flag = ""
    if item["kind"] == "game":
        flag = ('<span class="pk-flag ok" title="VPOC assigned">✓</span>' if vpoc_set
                else '<span class="pk-flag" title="No VPOC assigned yet">!</span>')

    b64 = CARD_B64.get(day.isoformat())
    if b64:
        inner = f'<img src="data:image/webp;base64,{b64}" alt="{html.escape(item["name"])}">'
    else:
        inner = (f'<div class="pk-fallback">{day.day} {day.strftime("%b").upper()}<br>'
                 f'{item["emoji"]} {html.escape(item["name"])}</div>')

    return (f'<div class="{" ".join(classes)}" style="aspect-ratio:{ratio:.4f}">'
            f'{inner}{flag}</div>')


def render_calendar() -> None:
    st.subheader("Calendar")
    st.caption("Click a game to assign its VPOC and HR. A green tick means one is assigned.")

    vpocs = get_all_vpocs()
    today = date.today()
    active = st.session_state.active_game

    with st.container(key="pk_cal"):
        for col, name in zip(st.columns(7), WEEKDAYS):
            css_class = "pk-weekday sat" if name == "Saturday" else "pk-weekday"
            col.markdown(f'<div class="{css_class}">{name}</div>', unsafe_allow_html=True)

        for week_no, week in enumerate(build_weeks()):
            for col, cell in zip(st.columns(7), week):
                if cell is None:
                    continue
                day, key = cell
                item = ITEMS[key]
                with col:
                    st.markdown(
                        card_html(day, item,
                                  ratio=ROW_ASPECT[min(week_no, len(ROW_ASPECT) - 1)],
                                  vpoc_set=key in vpocs,
                                  is_today=(day == today),
                                  is_active=(item["kind"] == "game" and key == active)),
                        unsafe_allow_html=True,
                    )
                    if item["kind"] == "game":
                        clicked = st.button(
                            f'Open {item["name"]} on {day.strftime("%d %b")}',
                            key=f'pk_game_{day.isoformat()}',
                            on_click=select_game, args=(key,),
                        )
                        if clicked:
                            vpoc_dialog(key, day)


# ---- Tab: Peak Tracker -------------------------------------------------------
def render_tracker() -> None:
    # The selectbox only exists while this tab is open, so re-seed its value from the
    # shared active_game (also updated by calendar clicks) on every run.
    st.session_state.tracker_game_select = st.session_state.active_game
    game_id = st.selectbox(
        "Game being tracked", options=list(GAMES), format_func=GAMES.get,
        key="tracker_game_select", on_change=sync_tracker_game,
    )

    st.text_input(
        "Scan employee badge", key="badge_input", on_change=handle_scan,
        placeholder="Click here, then scan the badge",
    )

    feedback = st.session_state.scan_feedback
    if feedback:
        kind, message = feedback
        {"success": st.success, "error": st.error, "warning": st.warning}[kind](message)

    df = get_scans(game_id)
    m1, m2 = st.columns(2)
    m1.metric("Participants", len(df))
    m2.metric("Winners", int((df["Status"] == "🏆 Winner").sum()) if not df.empty else 0)

    if df.empty:
        st.info(f"No badges scanned for {GAMES[game_id]} yet. Scan the first one above.")
        return

    st.session_state.editor_ids = df["id"].tolist()
    st.session_state.editor_key = f"editor_{game_id}_{st.session_state.editor_version}_{len(df)}"

    st.data_editor(
        df,
        key=st.session_state.editor_key,
        on_change=handle_status_edit,
        hide_index=True,
        use_container_width=True,
        disabled=["Badge ID", "Scanned at"],
        column_config={
            "id": None,
            "Status": st.column_config.SelectboxColumn(
                "Result", help="Choose Winner to mark this employee as a winner",
                options=STATUS_OPTIONS, required=True),
        },
    )


# ---- Tab: Auto Email ---------------------------------------------------------
def _fmt_dates(dates: list) -> str:
    return ", ".join(d.strftime("%d %b") for d in dates)


def render_email() -> None:
    vpocs = get_all_vpocs()
    today = date.today()

    if not vpocs:
        st.info("No VPOCs assigned yet. Click a game in the calendar to assign one.")
        return

    # --- Overview table ---
    rows = []
    for gid, a in vpocs.items():
        dates = GAME_DATES[gid]
        upcoming = [d for d in dates if d >= today]
        status = "Today" if today in dates else ("Upcoming" if upcoming else "Completed")
        last = get_last_email(gid)
        rows.append({
            "Game": GAMES[gid],
            "Dates": _fmt_dates(dates),
            "Next run": (upcoming[0] if upcoming else dates[-1]).strftime("%d %b %Y"),
            "Status": status,
            "VPOC": f'{a["vpoc_name"]} ({a["vpoc_email"]})',
            "HR": f'{a["hr_name"]} ({a["hr_email"]})',
            "Last email": (f'{last["sent_at"]} ' + ("✅" if last["ok"] else "❌")) if last else "—",
        })
    st.markdown("##### Assignments")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # --- Send for one game/date ---
    st.markdown("##### Send a reminder")
    game_id = st.selectbox("Game", options=list(vpocs), format_func=GAMES.get, key="email_game")
    dates = GAME_DATES[game_id]
    default_idx = next((i for i, d in enumerate(dates) if d >= today), len(dates) - 1)
    run_date = st.selectbox("Day the VPOC runs it", options=dates, index=default_idx,
                            format_func=lambda d: d.strftime("%A, %d %b %Y"), key="email_date")

    a = vpocs[game_id]
    subject, text, _ = build_reminder_email(GAMES[game_id], a["vpoc_name"], a["hr_name"], run_date)
    with st.expander("Preview email"):
        st.markdown(f"**From:** {SENDER_EMAIL}  \n**To:** {a['vpoc_email']}  \n"
                    f"**Cc:** {a['hr_email']}  \n**Subject:** {subject}")
        st.text(text)

    if st.button("📧 Send reminder to VPOC", type="primary", use_container_width=True):
        with st.spinner("Sending..."):
            ok, detail = notify_vpoc(game_id, run_date)
        (st.success if ok else st.error)(
            f"Email sent to {a['vpoc_email']}." if ok else f"Email failed. {detail}")

    # --- Bulk: everything scheduled today ---
    st.markdown("##### Today")
    due = [g for g in vpocs if today in GAME_DATES[g] and not was_sent(g, today)]
    if not due:
        st.caption("No pending reminders for today.")
    elif st.button(f"Send today's reminders ({len(due)})", use_container_width=True):
        for gid in due:
            ok, detail = notify_vpoc(gid, today)
            (st.success if ok else st.error)(
                f"{GAMES[gid]}: sent." if ok else f"{GAMES[gid]}: {detail}")


def render_right_panel() -> None:
    with st.container(key="pk_tabs"):
        st.radio("View", TABS, key="right_tab", horizontal=True, label_visibility="collapsed")
    st.write("")
    if st.session_state.right_tab == "Peak Tracker":
        render_tracker()
    else:
        render_email()


# =============================================================================
# 7. MAIN
# =============================================================================
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="⛰️", layout="wide")
    init_db()
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(build_banner_css(), unsafe_allow_html=True)

    if st.session_state.pending_toast:
        message, icon = st.session_state.pending_toast
        st.toast(message, icon=icon)
        st.session_state.pending_toast = None

    st.markdown(f'<h1 class="peak-title">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown('<p class="peak-sub">Plan the games on the left, track players and send reminders on the right.</p>',
                unsafe_allow_html=True)

    left, right = st.columns([2.4, 1], gap="large")
    with left:
        render_calendar()
    with right:
        render_right_panel()


if __name__ == "__main__":
    main()
