"""
Peak 2026 Dashboard
===================
Left column  : Calendar styled like the Peak 2026 poster (Mon-Sun grid, one card per day).
               Games are clickable; food days and events are plain cards.
Right column : Peak Tracker (badge scanner, duplicate check, winner selection).

Requirements : streamlit >= 1.39 (st.dialog + container keys), pandas
Run          : streamlit run peak_dashboard.py
"""

import html
import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# =============================================================================
# 1. CONFIG
# =============================================================================
APP_TITLE = "Peak 2026 Dashboard"
DB_PATH = Path("peak_dashboard.db")
STATUS_OPTIONS = ["Participant", "🏆 Winner"]

# Barcode scanners usually send plain alphanumeric IDs. Adjust if yours differ.
BADGE_PATTERN = re.compile(r"^[A-Z0-9_-]{1,32}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ---- Calendar content (transcribed from the Peak 2026 poster) ----------------
# kind: "game" = clickable (VPOC/HR form), "food" / "event" = display only.
# tint (optional): colour variant of the card -> pink | red | dark | navy
# The emoji stands in for the poster artwork. Swap in your own images later.
ITEMS = {
    "breast-cancer": {"name": "Breast Cancer Awareness Month", "emoji": "🎀", "kind": "event", "tint": "pink"},
    "cup-tower":     {"name": "Build Tallest Cup Tower With No Hands", "emoji": "🥛", "kind": "game"},
    "dont-sit":      {"name": "Don't Sit at the Same Time!", "emoji": "🪑", "kind": "game"},
    "pass-ball":     {"name": "Pass the Ball", "emoji": "🏐", "kind": "game"},
    "ring-toss":     {"name": "Ring Toss", "emoji": "🎯", "kind": "game"},
    "touch-color":   {"name": "Touch the Wrong Color", "emoji": "🎨", "kind": "game"},
    "back-same":     {"name": "Back to the Same Time!", "emoji": "💺", "kind": "game"},
    "hula":          {"name": "Pass the Hula Hoop", "emoji": "⭕", "kind": "game"},
    "halloween":     {"name": "Happy Halloween", "emoji": "🎃", "kind": "event", "tint": "dark"},
    "raffle":        {"name": "Raffle Contest", "emoji": "🎁", "kind": "event"},
    "diwali":        {"name": "Happy Diwali", "emoji": "🪔", "kind": "event"},
    "amazon":        {"name": "Amazon Gift Voucher", "emoji": "🎟️", "kind": "event", "tint": "navy"},
    "mens-day":      {"name": "International Men's Day", "emoji": "🧔", "kind": "event"},
    "birthday":      {"name": "Happy Birthday", "emoji": "🎂", "kind": "event"},
    "uae":           {"name": "UAE National Day", "emoji": "🇦🇪", "kind": "event"},
    "momenteer":     {"name": "Momenteer Award Day", "emoji": "🏆", "kind": "event", "tint": "navy"},
    "coke-day":      {"name": "Coke Day", "emoji": "🥤", "kind": "food", "tint": "red"},
    "vadapav":       {"name": "Vadapav Day", "emoji": "🍔", "kind": "food"},
    "lemonade":      {"name": "Happy Lemonade Day", "emoji": "🍋", "kind": "food"},
    "churros":       {"name": "Churros Day", "emoji": "🥖", "kind": "food"},
    "potato-spiral": {"name": "Potato Spiral Day", "emoji": "🥔", "kind": "food"},
}

START_DATE = date(2026, 10, 26)  # the poster starts on Monday 26 Oct 2026
# One entry per consecutive day, starting from START_DATE (40 days, to Fri 4 Dec).
SCHEDULE = [
    # Oct 26 - Nov 1
    "breast-cancer", "cup-tower", "dont-sit", "pass-ball", "ring-toss", "halloween", "ring-toss",
    # Nov 2 - Nov 8
    "touch-color", "raffle", "coke-day", "vadapav", "ring-toss", "back-same", "cup-tower",
    # Nov 9 - Nov 15
    "diwali", "raffle", "amazon", "vadapav", "mens-day", "pass-ball", "touch-color",
    # Nov 16 - Nov 22
    "cup-tower", "raffle", "lemonade", "churros", "birthday", "hula", "touch-color",
    # Nov 23 - Nov 29
    "amazon", "raffle", "uae", "potato-spiral", "ring-toss", "dont-sit", "cup-tower",
    # Nov 30 - Dec 4
    "hula", "raffle", "uae", "potato-spiral", "momenteer",
]
assert all(key in ITEMS for key in SCHEDULE), "SCHEDULE has a key missing from ITEMS"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Clickable games only: {game_id: display name}
GAMES = {k: v["name"] for k, v in ITEMS.items() if v["kind"] == "game"}

logger = logging.getLogger("peak_dashboard")


# =============================================================================
# 2. DATABASE LAYER (all SQL lives here; every query is parameterised)
# =============================================================================
@contextmanager
def db():
    """Short-lived connection: commits on success, rolls back on error."""
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
    """Create tables once per server process."""
    with db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")  # better for concurrent HR users
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
                UNIQUE (badge_id, game_id)   -- the real duplicate guard
            );
            CREATE INDEX IF NOT EXISTS idx_scans_game ON scans (game_id);
            """
        )
    return True


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---- VPOC assignments --------------------------------------------------------
def upsert_vpoc(game_id: str, vpoc_name: str, vpoc_email: str,
                hr_name: str, hr_email: str) -> None:
    """Insert a VPOC/HR assignment, or update it if the game already has one."""
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
    """One query for the whole calendar: {game_id: row-as-dict}."""
    with db() as conn:
        rows = conn.execute("SELECT * FROM vpoc_assignments").fetchall()
    return {r["game_id"]: dict(r) for r in rows}


# ---- Scans -------------------------------------------------------------------
def add_scan(badge_id: str, game_id: str) -> bool:
    """Save a scan. Returns False (and saves nothing) if it is a duplicate."""
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
    """Participants for one game. Oldest first, so row positions stay stable."""
    with db() as conn:
        return pd.read_sql_query(
            """
            SELECT id,
                   badge_id   AS "Badge ID",
                   status     AS "Status",
                   scanned_at AS "Scanned at"
            FROM scans
            WHERE game_id = ?
            ORDER BY id ASC
            """,
            conn,
            params=(game_id,),
        )


def update_status(scan_id: int, status: str) -> None:
    """Set Participant / Winner for one scan row."""
    if status not in STATUS_OPTIONS:
        raise ValueError(f"Invalid status: {status!r}")
    with db() as conn:
        conn.execute("UPDATE scans SET status = ? WHERE id = ?", (status, scan_id))


# =============================================================================
# 3. NOTIFICATIONS (plug your SMTP code in here)
# =============================================================================
def send_vpoc_assignment_email(game_name: str, vpoc_name: str, vpoc_email: str,
                               hr_name: str, hr_email: str) -> bool:
    """
    Placeholder for the auto-email sent after a VPOC/HR assignment is saved.
    Return True if the email was sent, False otherwise (the UI shows the result).

    Suggested SMTP code (keep credentials in .streamlit/secrets.toml):

        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = st.secrets["smtp"]["sender"]
        msg["To"] = [vpoc_email, hr_email]
        msg.set_content(body)

        with smtplib.SMTP(st.secrets["smtp"]["host"], st.secrets["smtp"]["port"]) as s:
            s.starttls()
            s.login(st.secrets["smtp"]["user"], st.secrets["smtp"]["password"])
            s.send_message(msg)
    """
    subject = f"Peak 2026: you are assigned to {game_name}"
    body = (
        f"Hi {vpoc_name} and {hr_name},\n\n"
        f"You have been assigned as VPOC ({vpoc_name}) and HR ({hr_name}) "
        f"for the game '{game_name}'.\n\nThanks,\nPeak 2026 Team"
    )

    # TODO: replace this log line with your SMTP code, then return True on success.
    logger.info("EMAIL PLACEHOLDER -> to=%s, %s | subject=%s\n%s",
                vpoc_email, hr_email, subject, body)
    return True


# =============================================================================
# 4. STATE + CALLBACKS
# =============================================================================
def init_state() -> None:
    first_game = next(iter(GAMES))
    st.session_state.setdefault("active_game", first_game)
    st.session_state.setdefault("scan_feedback", None)   # (kind, message)
    st.session_state.setdefault("pending_toast", None)   # (message, icon)
    st.session_state.setdefault("editor_version", 0)     # bump to reset the editor
    st.session_state.setdefault("editor_key", "")
    st.session_state.setdefault("editor_ids", [])


def select_game(game_id: str) -> None:
    """Called when a game card is clicked: make it the active tracker game."""
    st.session_state.active_game = game_id


def handle_scan() -> None:
    """text_input on_change: runs when the scanner presses Enter."""
    raw = st.session_state.badge_input
    st.session_state.badge_input = ""  # clear so the box is ready for the next scan
    badge = raw.strip().upper()
    game_id = st.session_state.active_game

    if not badge:
        return
    if not BADGE_PATTERN.match(badge):
        st.session_state.scan_feedback = (
            "warning", f"“{badge}” is not a valid badge ID. Scan again.")
        st.toast("Invalid badge ID", icon="⚠️")
        return

    if add_scan(badge, game_id):
        st.session_state.scan_feedback = (
            "success", f"Badge {badge} added to {GAMES[game_id]}.")
        st.toast(f"Badge {badge} added", icon="✅")
    else:
        st.session_state.scan_feedback = (
            "error", f"Badge {badge} has already played {GAMES[game_id]}. Nothing was saved.")
        st.toast(f"Duplicate: {badge}", icon="🚫")


def handle_status_edit() -> None:
    """data_editor on_change: write dropdown changes to the database."""
    state = st.session_state.get(st.session_state.editor_key) or {}
    ids = st.session_state.editor_ids
    changed = 0
    for position, changes in state.get("edited_rows", {}).items():
        new_status = changes.get("Status")
        if new_status in STATUS_OPTIONS and int(position) < len(ids):
            update_status(int(ids[int(position)]), new_status)
            changed += 1
    if changed:
        st.session_state.editor_version += 1  # fresh editor, rebuilt from the DB
        st.session_state.pending_toast = ("Result saved", "💾")


# =============================================================================
# 5. STYLING (matches the Peak 2026 poster)
# =============================================================================
CSS = """
<style>
.block-container { padding-top: 2rem; max-width: 1680px; }

.peak-title { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; }
.peak-sub   { margin: .15rem 0 1.25rem; opacity: .7; }

/* ---- Calendar frame: green "PEAK 2026" + black "OCT-DEC '26" side banner ---- */
.st-key-pk_cal, .st-key-pk_cal > [data-testid="stVerticalBlock"] { gap: 10px !important; }
.st-key-pk_cal { position: relative; padding-left: 86px; }
.st-key-pk_cal::before, .st-key-pk_cal::after {
    position: absolute; left: 0; width: 68px; box-sizing: border-box;
    display: flex; align-items: center; justify-content: center;
    writing-mode: vertical-rl; transform: rotate(180deg);
    color: #fff; font-weight: 800; white-space: nowrap;
}
.st-key-pk_cal::before {
    content: "PEAK 2026"; top: 0; height: 41%;
    background: #62c96b; font-size: 1.7rem; letter-spacing: .14em;
}
.st-key-pk_cal::after {
    content: "OCT\\2013DEC \\2019 26"; top: 41%; bottom: 0;
    background: #15171c; font-size: 2.2rem; letter-spacing: .04em;
}
.st-key-pk_cal [data-testid="stHorizontalBlock"] { gap: 10px; }
.st-key-pk_cal [data-testid="stColumn"], .st-key-pk_cal [data-testid="column"] { position: relative; }

.pk-weekday {
    text-align: center; font-weight: 800; font-size: .82rem;
    letter-spacing: .04em; text-transform: uppercase; color: #2fb45a;
}

/* ---- Day card ---- */
.pk-card {
    position: relative; box-sizing: border-box; height: 132px; overflow: hidden;
    display: flex; flex-direction: column; padding: 8px 9px;
    border-radius: 12px; border: 1px solid #cfe8f3;
    background: linear-gradient(160deg, #ffffff 0%, #e7f5fb 100%);
    color: #1b2a41; transition: transform .15s ease, box-shadow .15s ease;
}
.pk-card.food { background: linear-gradient(160deg, #ffffff 0%, #fdf0d3 100%); border-color: #f1dfb0; }

.pk-date { line-height: 1; }
.pk-date b    { display: block; font-size: 1.3rem; font-weight: 800; }
.pk-date span { font-size: .6rem; font-weight: 700; letter-spacing: .06em; opacity: .65; }

.pk-emoji { flex: 1; display: flex; align-items: center; justify-content: center; font-size: 2.2rem; }
.pk-title {
    text-align: center; font-weight: 800; font-size: .74rem; line-height: 1.15;
    display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
/* yellow "tape" behind game and food names, like on the poster */
.pk-card.game .pk-title, .pk-card.food .pk-title {
    align-self: center; background: #ffe27a; padding: 2px 6px; border-radius: 3px;
}

/* ---- Colour variants ---- */
.pk-card.tint-pink { background: linear-gradient(160deg, #fff, #ffe3ee); border-color: #f8c3d9; }
.pk-card.tint-pink .pk-title { color: #d6246e; }
.pk-card.tint-red  { background: #d9232d; border-color: #b81b24; color: #fff; }
.pk-card.tint-dark { background: #1d1a2b; border-color: #2c2840; color: #fff; }
.pk-card.tint-dark .pk-title { color: #ff9a1f; }
.pk-card.tint-navy { background: #14253f; border-color: #213a5e; color: #fff; }
.pk-card.tint-navy .pk-title { color: #ffd36b; }

/* ---- Status marks ---- */
.pk-card.is-today  { box-shadow: 0 0 0 3px #ffb400; }
.pk-card.is-active { outline: 3px solid #2fb45a; outline-offset: -3px; }
.pk-flag {
    position: absolute; top: 7px; right: 7px; width: 18px; height: 18px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .68rem; font-weight: 800; background: #ffb400; color: #3b2a00;
}
.pk-flag.ok { background: #2fb45a; color: #fff; }

/* ---- Clickable games: an invisible button covers the whole card ---- */
[class*="st-key-pk_game_"] { position: absolute !important; inset: 0; z-index: 3; }
[class*="st-key-pk_game_"] [data-testid="stButton"],
[class*="st-key-pk_game_"] button { width: 100%; height: 100%; }
[class*="st-key-pk_game_"] button { opacity: 0; cursor: pointer; padding: 0; min-height: 0; }
[data-testid="stColumn"]:has([class*="st-key-pk_game_"]:hover) .pk-card,
[data-testid="column"]:has([class*="st-key-pk_game_"]:hover) .pk-card {
    transform: translateY(-3px); box-shadow: 0 8px 18px rgba(20, 60, 90, .22);
}

@media (max-width: 900px) {
    .st-key-pk_cal { padding-left: 0; }
    .st-key-pk_cal::before, .st-key-pk_cal::after { display: none; }
}
</style>
"""


# =============================================================================
# 6. UI COMPONENTS
# =============================================================================
@st.dialog("Assign VPOC and HR")
def vpoc_dialog(game_id: str, when: date) -> None:
    """Popup form opened by clicking a game card."""
    existing = get_all_vpocs().get(game_id, {})
    st.markdown(f"**{GAMES[game_id]}**  \n{when.strftime('%A, %d %b %Y')}")

    with st.form(f"vpoc_form_{game_id}"):
        c1, c2 = st.columns(2)
        vpoc_name = c1.text_input("VPOC name", value=existing.get("vpoc_name", ""))
        vpoc_email = c2.text_input("VPOC email", value=existing.get("vpoc_email", ""))
        hr_name = c1.text_input("HR name", value=existing.get("hr_name", ""))
        hr_email = c2.text_input("HR email", value=existing.get("hr_email", ""))
        submitted = st.form_submit_button(
            "Save and notify", type="primary", use_container_width=True)

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
    sent = send_vpoc_assignment_email(GAMES[game_id], *values)
    st.session_state.pending_toast = (
        ("Assignment saved and email sent", "📧") if sent
        else ("Assignment saved, but the email failed", "⚠️")
    )
    st.rerun()  # closes the dialog and refreshes the calendar


def build_weeks() -> list:
    """Split the schedule into Monday-Sunday rows. Empty trailing days are None."""
    cells = [(START_DATE + timedelta(days=i), key) for i, key in enumerate(SCHEDULE)]
    cells += [None] * (-len(cells) % 7)
    return [cells[i:i + 7] for i in range(0, len(cells), 7)]


def card_html(day: date, item: dict, *, vpoc_set: bool, is_today: bool, is_active: bool) -> str:
    """HTML for one day card. Kept on one line so Markdown never treats it as code."""
    classes = ["pk-card", item["kind"]]
    if item.get("tint"):
        classes.append(f"tint-{item['tint']}")
    if is_today:
        classes.append("is-today")
    if is_active:
        classes.append("is-active")

    flag = ""
    if item["kind"] == "game":
        flag = ('<span class="pk-flag ok" title="VPOC assigned">✓</span>' if vpoc_set
                else '<span class="pk-flag" title="No VPOC assigned yet">!</span>')

    return (
        f'<div class="{" ".join(classes)}">'
        f'<div class="pk-date"><b>{day.day}</b><span>{day.strftime("%b").upper()}</span></div>'
        f'{flag}'
        f'<div class="pk-emoji">{item["emoji"]}</div>'
        f'<div class="pk-title">{html.escape(item["name"])}</div>'
        f'</div>'
    )


def render_calendar() -> None:
    """Left column: poster-style month grid. Games are clickable, the rest are not."""
    st.subheader("Calendar")
    st.caption("Click a game to assign its VPOC and HR. A green tick means one is assigned.")

    vpocs = get_all_vpocs()  # single query for the whole grid
    today = date.today()
    active = st.session_state.active_game

    with st.container(key="pk_cal"):
        for col, name in zip(st.columns(7), WEEKDAYS):
            col.markdown(f'<div class="pk-weekday">{name}</div>', unsafe_allow_html=True)

        for week in build_weeks():
            for col, cell in zip(st.columns(7), week):
                if cell is None:
                    continue
                day, key = cell
                item = ITEMS[key]
                with col:
                    st.markdown(
                        card_html(day, item,
                                  vpoc_set=key in vpocs,
                                  is_today=(day == today),
                                  is_active=(item["kind"] == "game" and key == active)),
                        unsafe_allow_html=True,
                    )
                    if item["kind"] == "game":
                        # Invisible button stretched over the card by the CSS above.
                        clicked = st.button(
                            f'Open {item["name"]} on {day.strftime("%d %b")}',
                            key=f'pk_game_{day.isoformat()}',
                            on_click=select_game,
                            args=(key,),
                        )
                        if clicked:
                            vpoc_dialog(key, day)


def render_tracker() -> None:
    """Right column: scanner, feedback, metrics and the winner editor."""
    st.subheader("Peak Tracker")

    game_id = st.selectbox(
        "Game being tracked",
        options=list(GAMES),
        format_func=GAMES.get,
        key="active_game",
    )

    st.text_input(
        "Scan employee badge",
        key="badge_input",
        on_change=handle_scan,
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

    # Remember which DB ids the visible rows map to, so edits hit the right rows.
    st.session_state.editor_ids = df["id"].tolist()
    st.session_state.editor_key = (
        f"editor_{game_id}_{st.session_state.editor_version}_{len(df)}")

    st.data_editor(
        df,
        key=st.session_state.editor_key,
        on_change=handle_status_edit,
        hide_index=True,
        use_container_width=True,
        disabled=["Badge ID", "Scanned at"],
        column_config={
            "id": None,  # hide the internal id
            "Status": st.column_config.SelectboxColumn(
                "Result",
                help="Choose Winner to mark this employee as a winner",
                options=STATUS_OPTIONS,
                required=True,
            ),
        },
    )


# =============================================================================
# 7. MAIN
# =============================================================================
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="⛰️", layout="wide")
    init_db()
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)

    # Toasts queued by callbacks or the dialog before a rerun are shown here.
    if st.session_state.pending_toast:
        message, icon = st.session_state.pending_toast
        st.toast(message, icon=icon)
        st.session_state.pending_toast = None

    st.markdown(f'<h1 class="peak-title">{APP_TITLE}</h1>', unsafe_allow_html=True)
    st.markdown('<p class="peak-sub">Plan the games on the left, track players and winners on the right.</p>',
                unsafe_allow_html=True)

    left, right = st.columns([2.4, 1], gap="large")
    with left:
        render_calendar()
    with right:
        render_tracker()


if __name__ == "__main__":
    main()
