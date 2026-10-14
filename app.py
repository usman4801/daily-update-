"""
Peak Dashboard
==============
Everything is in this one file (poster artwork is embedded at the bottom).
Top   : small capsules -> [Peak Tracker] [Auto Email] [Site] [Peak Gallery]
Below : the calendar, always visible. It is poster-style; every game card is clickable on its own
        and opens a modal to assign the Sender and the VPOC (the VPOC is also the HR contact).

Sites : DXB5, DXB3 and AUH1 are kept completely separate. Each site has its own SQLite file
        (data/<SITE>/peak_dashboard.db) with its own tables: scans, VPOC assignments, email log, gallery.

Requirements : streamlit >= 1.39, pandas
Run          : streamlit run app.py
Secrets      : .streamlit/secrets.toml  ->  [smtp] host / port / password   (optional: user)
"""

import html
import logging
import re
import smtplib
import sqlite3
import ssl
import threading
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Poster artwork (side banner + one picture per day, cut from the Oct-Dec '26 calendar) is embedded at the very bottom of this file.

# =============================================================================
# 1. CONFIG
# =============================================================================
APP_TITLE = "Peak 2026 Dashboard"
BASE_DIR = Path(__file__).resolve().parent

# ---- Sites: every site gets its own folder + its own database file ----------
SITES = ["DXB5", "DXB3", "AUH1"]
DEFAULT_SITE = SITES[0]
DATA_DIR = BASE_DIR / "data"                         # data/<SITE>/peak_dashboard.db
LEGACY_DB_PATH = BASE_DIR / "peak_dashboard.db"      # the old single-site database (if you have one)
LEGACY_DB_SITE = "DXB5"                              # site that inherits the old database, one time only

DEFAULT_SENDER_EMAIL = "javmuhak@amazon.ae"          # pre-filled in "Sender Email"
WINNER = "🏆 Winner"
PARTICIPANT = "Participant"
STATUS_OPTIONS = [PARTICIPANT, WINNER]
TABS = ["Calendar", "Peak Tracker", "Auto Email"]

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
# Poster proportions (pixels in the calendar picture): width of each weekday column, height of each week row.
COL_W = [154, 154, 154, 154, 154, 154, 154]
ROW_H = [101, 101, 101, 96, 100, 100]
GAMES = {k: v["name"] for k, v in ITEMS.items() if v["kind"] == "game"}

# {game_id: [date, date, ...]}: a game can run on several days.
GAME_DATES: dict = {}
for _i, _key in enumerate(SCHEDULE):
    if _key in GAMES:
        GAME_DATES.setdefault(_key, []).append(START_DATE + timedelta(days=_i))

# ---- Tracker entries: one per game *and* calendar date, e.g. "Ring Toss (30-10-2026)" ----
# Every day on the calendar is listed (games, raffle, festivals, food days...), in calendar order.
OCC_IDS = [f"{k}|{(START_DATE + timedelta(days=i)).isoformat()}"
           for i, k in enumerate(SCHEDULE)]


def occ_id(game_id: str, day) -> str:
    iso = day if isinstance(day, str) else day.isoformat()
    return f"{game_id}|{iso}"


def split_occ(occ: str):
    game_id, iso = occ.split("|")
    return game_id, date.fromisoformat(iso)


def occ_label(occ: str) -> str:
    """Game name with its calendar date in brackets: Game Name (DD-MM-YYYY)."""
    game_id, day = split_occ(occ)
    return f"{ITEMS[game_id]['name']} ({day.strftime('%d-%m-%Y')})"


def default_occ() -> str:
    """Today's calendar entry, else the next upcoming one, else the first one."""
    today = date.today()
    upcoming = [o for o in OCC_IDS if split_occ(o)[1] >= today]
    return upcoming[0] if upcoming else OCC_IDS[0]


logger = logging.getLogger("peak_dashboard")


# =============================================================================
# 2. DATABASE LAYER  (one SQLite file per site -> sites never share a table)
# =============================================================================
_LOCK = threading.RLock()     # one shared connection per site, so writes are serialised


def current_site() -> str:
    site = st.session_state.get("site", DEFAULT_SITE)
    return site if site in SITES else DEFAULT_SITE


def site_db_path(site: str) -> Path:
    return DATA_DIR / site / "peak_dashboard.db"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _columns(conn, table: str) -> set:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _init_schema(conn) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS vpoc_assignments (
            game_id      TEXT PRIMARY KEY,
            sender_email TEXT NOT NULL DEFAULT '',
            vpoc_name    TEXT NOT NULL,
            vpoc_email   TEXT NOT NULL,
            hr_name      TEXT NOT NULL,
            hr_email     TEXT NOT NULL,
            assigned_at  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS scans (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_id   TEXT NOT NULL,
            game_id    TEXT NOT NULL,
            game_date  TEXT NOT NULL DEFAULT '',
            status     TEXT NOT NULL DEFAULT 'Participant',
            scanned_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS email_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id    TEXT NOT NULL,
            run_date   TEXT NOT NULL,
            recipients TEXT NOT NULL,
            ok         INTEGER NOT NULL,
            detail     TEXT NOT NULL DEFAULT '',
            sent_at    TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS gallery (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT NOT NULL,
            mime        TEXT NOT NULL,
            data        BLOB NOT NULL,
            uploaded_at TEXT NOT NULL
        );
        """
    )
    _migrate(conn)
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_scans_occ   ON scans (game_id, game_date);
        CREATE INDEX IF NOT EXISTS idx_scans_badge ON scans (badge_id);
        CREATE INDEX IF NOT EXISTS idx_email_game  ON email_log (game_id, run_date);
        """
    )


def _migrate(conn) -> None:
    """Upgrade a database created by the previous version (safe to run every time)."""
    if "sender_email" not in _columns(conn, "vpoc_assignments"):
        conn.execute("ALTER TABLE vpoc_assignments ADD COLUMN sender_email TEXT NOT NULL DEFAULT ''")

    scans_sql = (conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='scans'").fetchone()[0] or "")
    if "UNIQUE" in scans_sql.upper():
        # Old table: UNIQUE (badge_id, game_id) and no date. Rebuild it without the constraint
        # (duplicates are now handled in code, with the "Still want to add" override).
        conn.executescript(
            """
            DROP INDEX IF EXISTS idx_scans_game;
            ALTER TABLE scans RENAME TO scans_old;
            CREATE TABLE scans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_id   TEXT NOT NULL,
                game_id    TEXT NOT NULL,
                game_date  TEXT NOT NULL DEFAULT '',
                status     TEXT NOT NULL DEFAULT 'Participant',
                scanned_at TEXT NOT NULL
            );
            INSERT INTO scans (id, badge_id, game_id, game_date, status, scanned_at)
                SELECT id, badge_id, game_id, '', status, scanned_at FROM scans_old;
            DROP TABLE scans_old;
            """
        )
    elif "game_date" not in _columns(conn, "scans"):
        conn.execute("ALTER TABLE scans ADD COLUMN game_date TEXT NOT NULL DEFAULT ''")

    # Old rows have no date: give each one the scheduled date of its game (the scan day if it matches).
    for r in conn.execute("SELECT id, game_id, scanned_at FROM scans WHERE game_date = ''").fetchall():
        dates = GAME_DATES.get(r["game_id"], [])
        if not dates:
            continue
        try:
            scan_day = datetime.strptime(r["scanned_at"][:10], "%Y-%m-%d").date()
        except ValueError:
            scan_day = None
        chosen = scan_day if scan_day in dates else dates[0]
        conn.execute("UPDATE scans SET game_date = ? WHERE id = ?", (chosen.isoformat(), r["id"]))
    conn.commit()


@st.cache_resource(show_spinner=False)
def get_conn(site: str) -> sqlite3.Connection:
    """One long-lived connection per site (created once, shared by every session)."""
    path = site_db_path(site)
    path.parent.mkdir(parents=True, exist_ok=True)

    # One-time hand-over of the old single-site database to LEGACY_DB_SITE (the original is kept).
    if site == LEGACY_DB_SITE and not path.exists() and LEGACY_DB_PATH.exists():
        src = sqlite3.connect(LEGACY_DB_PATH)
        dst = sqlite3.connect(path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

    conn = sqlite3.connect(path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")     # far fewer disk syncs per write than FULL
    conn.execute("PRAGMA busy_timeout=10000")
    _init_schema(conn)
    return conn


@contextmanager
def db():
    """Connection of the currently selected site, guarded by a lock; commits on success."""
    conn = get_conn(current_site())
    with _LOCK:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# ---- VPOC assignments --------------------------------------------------------
def upsert_vpoc(game_id, sender_email, vpoc_name, vpoc_email, hr_name, hr_email) -> None:
    with db() as conn:
        conn.execute(
            """
            INSERT INTO vpoc_assignments
                (game_id, sender_email, vpoc_name, vpoc_email, hr_name, hr_email, assigned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                sender_email = excluded.sender_email,
                vpoc_name    = excluded.vpoc_name,
                vpoc_email   = excluded.vpoc_email,
                hr_name      = excluded.hr_name,
                hr_email     = excluded.hr_email,
                assigned_at  = excluded.assigned_at
            """,
            (game_id, sender_email, vpoc_name, vpoc_email, hr_name, hr_email, _now()),
        )


def get_all_vpocs() -> dict:
    with db() as conn:
        rows = conn.execute("SELECT * FROM vpoc_assignments").fetchall()
    return {r["game_id"]: dict(r) for r in rows}


# ---- Scans (participants and winners) ----------------------------------------
def find_badge(badge_id: str) -> list:
    """Every entry of this login on the current site, any game, any date."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, game_id, game_date, status FROM scans WHERE badge_id = ? ORDER BY id",
            (badge_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_scan(badge_id: str, occ: str, status: str = PARTICIPANT) -> None:
    game_id, day = split_occ(occ)
    with db() as conn:
        conn.execute(
            "INSERT INTO scans (badge_id, game_id, game_date, status, scanned_at) VALUES (?, ?, ?, ?, ?)",
            (badge_id, game_id, day.isoformat(), status, _now()),
        )
    export_tracker_csv()


def get_tracker() -> pd.DataFrame:
    """The ONE tracker list of the current site: every login, every game, every date."""
    with db() as conn:
        df = pd.read_sql_query(
            'SELECT id, badge_id AS "Badge ID", game_id, game_date, status AS "Status", '
            'scanned_at AS "Scanned at" FROM scans ORDER BY id DESC', conn)
    df["Game"] = df["game_id"].map(lambda g: ITEMS.get(g, {}).get("name", g))
    df["Date"] = df["game_date"].map(_fmt_iso)
    return df


def tracker_csv_bytes() -> bytes:
    df = get_tracker()
    out = df[["Badge ID", "Game", "Date", "Status", "Scanned at"]].rename(columns={"Status": "Result"})
    out["Result"] = out["Result"].str.replace("🏆 ", "", regex=False)
    return out.to_csv(index=False).encode("utf-8-sig")        # utf-8-sig: opens cleanly in Excel


def export_tracker_csv() -> None:
    """Keep one readable file per site: data/<SITE>/peak_tracker_<SITE>.csv (the database stays the master)."""
    try:
        site = current_site()
        path = site_db_path(site).parent / f"peak_tracker_{site}.csv"
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(tracker_csv_bytes())
        tmp.replace(path)
    except Exception:                      # the file is a convenience copy; never block a scan
        logger.exception("Tracker CSV export failed")


def update_status(scan_id: int, status: str) -> None:
    if status not in STATUS_OPTIONS:
        raise ValueError(f"Invalid status: {status!r}")
    with db() as conn:
        conn.execute("UPDATE scans SET status = ? WHERE id = ?", (status, scan_id))
    export_tracker_csv()


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


# ---- Gallery (per site) ------------------------------------------------------
GALLERY_TYPES = ["png", "jpg", "jpeg", "webp", "gif"]
GALLERY_MAX_MB = 8


def add_image(filename: str, mime: str, data: bytes) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO gallery (filename, mime, data, uploaded_at) VALUES (?, ?, ?, ?)",
            (filename, mime or "image/png", data, _now()),
        )


def list_images() -> list:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, filename, mime, data, uploaded_at FROM gallery ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def delete_image(image_id: int) -> None:
    with db() as conn:
        conn.execute("DELETE FROM gallery WHERE id = ?", (image_id,))


# =============================================================================
# 3. EMAIL (smtplib)
# =============================================================================
def build_reminder_email(game_name: str, vpoc_name: str, run_date: date):
    """Returns (subject, plain_text, html)."""
    day = run_date.strftime("%A, %d %B %Y")
    subject = f"Peak 2026: it's your day to run \"{game_name}\" ({run_date.strftime('%d %b')})"
    text = (
        f"Hi {vpoc_name},\n\n"
        f"This is your reminder that {day} is your day to run the engagement activity "
        f"\"{game_name}\" for Peak 2026.\n\n"
        f"Please use the Peak Dashboard to scan badges and record winners.\n\n"
        f"Thanks,\nPeak 2026 Team"
    )
    body = (
        f"<p>Hi {html.escape(vpoc_name)},</p>"
        f"<p>This is your reminder that <b>{html.escape(day)}</b> is your day to run the engagement "
        f"activity <b>{html.escape(game_name)}</b> for Peak 2026.</p>"
        f"<p>Please use the Peak Dashboard to scan badges and record winners.</p>"
        f"<p>Thanks,<br>Peak 2026 Team</p>"
    )
    return subject, text, body


def send_email(sender: str, to: list, cc: list, subject: str, text: str, html_body: str):
    """Send through SMTP using the password stored in st.secrets. Returns (ok, detail)."""
    try:
        cfg = st.secrets["smtp"]
        host = cfg["host"]
        port = int(cfg.get("port", 587))
        user = cfg.get("user", sender)
        password = cfg["password"]
    except (KeyError, FileNotFoundError):
        return False, "SMTP settings missing: add [smtp] host and password to .streamlit/secrets.toml."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
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


def sender_for(assignment: dict) -> str:
    return (assignment.get("sender_email") or "").strip() or DEFAULT_SENDER_EMAIL


def notify_vpoc(game_id: str, run_date: date):
    """Email the assigned VPOC from the assigned Sender Email. Logs the attempt."""
    assignment = get_all_vpocs().get(game_id)
    if not assignment:
        return False, "No VPOC assigned for this game."
    subject, text, body = build_reminder_email(
        GAMES[game_id], assignment["vpoc_name"], run_date)
    to, cc = [assignment["vpoc_email"]], []
    ok, detail = send_email(sender_for(assignment), to, cc, subject, text, body)
    log_email(game_id, run_date, to + cc, ok, detail)
    return ok, detail


# =============================================================================
# 4. STATE + CALLBACKS
# =============================================================================
def init_state() -> None:
    st.session_state.setdefault("site", DEFAULT_SITE)
    st.session_state.setdefault("active_occ", default_occ())    # "<game_id>|<YYYY-MM-DD>"
    st.session_state.setdefault("active_date", "")              # the one calendar block that was clicked
    st.session_state.setdefault("scan_feedback", None)
    st.session_state.setdefault("scan_dup", None)               # pending "Duplicate entry" decision
    st.session_state.setdefault("pending_toast", None)
    st.session_state.setdefault("editor_version", 0)
    st.session_state.setdefault("editor_key", "")
    st.session_state.setdefault("editor_ids", [])
    st.session_state.setdefault("gallery_ver", 0)


def clear_scan_state() -> None:
    st.session_state.scan_feedback = None
    st.session_state.scan_dup = None


def on_site_change() -> None:
    clear_scan_state()
    st.session_state.editor_version += 1


def select_game(game_id: str, day_iso: str = "") -> None:
    """Calendar click: remember which game *and which date* was clicked."""
    st.session_state.active_occ = occ_id(game_id, day_iso)
    st.session_state.active_date = day_iso
    clear_scan_state()


def sync_tracker_game() -> None:
    occ = st.session_state.tracker_game_select
    st.session_state.active_occ = occ
    st.session_state.active_date = split_occ(occ)[1].isoformat()
    clear_scan_state()


def process_scan(raw: str, mode: str) -> None:
    """Handle one scanned/typed login. Runs inside the tracker's own fragment run (no full rerun)."""
    badge = raw.strip().upper()
    if not badge:
        return
    occ = st.session_state.active_occ
    game_id, day = split_occ(occ)
    st.session_state.scan_dup = None

    if not BADGE_PATTERN.match(badge):
        st.session_state.scan_feedback = ("warning", f"“{badge}” is not a valid badge ID. Scan again.")
        return

    status = WINNER if mode == "Winner" else PARTICIPANT
    existing = find_badge(badge)
    here = next((r for r in existing
                 if r["game_id"] == game_id and r["game_date"] == day.isoformat()), None)

    # Already a participant of this game/date and now being marked as winner -> just upgrade.
    if here and status == WINNER and here["status"] != WINNER:
        update_status(here["id"], WINNER)
        st.session_state.scan_feedback = ("success", f"{badge} is now a Winner of {occ_label(occ)}.")
        st.toast(f"{badge} marked as Winner", icon="🏆")
        return

    if existing:
        where = "; ".join(f"{ITEMS.get(r['game_id'], {}).get('name', r['game_id'])} "
                          f"({_fmt_iso(r['game_date'])}, {r['status'].replace('🏆 ', '')})"
                          for r in existing[:3])
        if len(existing) > 3:
            where += f"; +{len(existing) - 3} more"
        st.session_state.scan_dup = {
            "badge": badge, "occ": occ, "status": status, "where": where, "site": current_site()}
        return

    add_scan(badge, occ, status)
    st.session_state.scan_feedback = ("success", f"{badge} added as {status.replace('🏆 ', '')} "
                                                  f"to {occ_label(occ)}.")
    st.toast(f"{badge} added", icon="✅")


def force_add() -> None:
    """'Still want to add' button: save the pending duplicate anyway."""
    dup = st.session_state.scan_dup
    st.session_state.scan_dup = None
    if not dup or dup["site"] != current_site():
        return
    add_scan(dup["badge"], dup["occ"], dup["status"])
    st.session_state.scan_feedback = (
        "success", f"{dup['badge']} added anyway to {occ_label(dup['occ'])}.")
    st.toast(f"{dup['badge']} added", icon="✅")


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
        st.toast("Result saved", icon="💾")


def _fmt_iso(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d-%m-%Y")
    except ValueError:
        return iso or "no date"


# =============================================================================
# 5. STYLING
# =============================================================================
_COLS = " ".join(f"{w}fr" for w in COL_W)

CSS = """
<style>
:root { --pk-gap: clamp(5px, .45vw, 10px); --pk-green: #2fa84f; }

/* Full-width canvas */
.block-container { padding: 1.7rem 1.25rem 1.5rem; max-width: 100% !important; }

.peak-title { margin: 0; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em; }
.peak-sub   { margin: .1rem 0 .9rem; opacity: .7; font-size: .9rem; }

/* ---- Calendar sheet: a 7-column grid, every day is its own block with a gap around it ---- */
.st-key-pk_cal[data-testid="stVerticalBlock"],
.st-key-pk_cal > [data-testid="stVerticalBlock"] {
    display: grid !important; grid-template-columns: __COLS__;
    gap: var(--pk-gap) !important; align-items: start;
}
.st-key-pk_cal {
    position: relative; background: #fff; border-radius: 10px;
    padding: 3.4% 1% 1.2% 9.1%; box-sizing: border-box; overflow: hidden;
}
.st-key-pk_cal::before {
    content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 8.3%;
    background-repeat: no-repeat; background-size: 100% 100%; background-position: center;
}
/* each day block is its own positioning box (so its invisible click layer covers that block only) */
[class*="st-key-pk_cell_"], [class*="st-key-pk_cell_"] > [data-testid="stVerticalBlock"] {
    position: relative; gap: 0 !important; min-width: 0;
}
/* small, even space between one day block and the one below it */
[class*="st-key-pk_cell_"] { padding-bottom: 7px; box-sizing: border-box; }
.st-key-pk_cal [data-testid="stMarkdownContainer"],
.st-key-pk_cal [data-testid="stMarkdown"] { margin-bottom: 0 !important; }

.pk-weekday {
    text-align: center; font-weight: 800; font-size: .88rem; letter-spacing: .03em;
    text-transform: uppercase; color: var(--pk-green); padding: 4px 0; border-radius: 4px;
}
.pk-weekday.sat { background: #f1f6e3; }

/* ---- Day card ---- */
.pk-card {
    position: relative; box-sizing: border-box; width: 100%; overflow: hidden;
    border-radius: 9px; background: transparent;
    transition: transform .15s ease, box-shadow .15s ease;
}
.pk-card img { display: block; width: 100%; height: 100%; object-fit: fill; }
.pk-card.is-text { height: 112px; background: #eef8fc; border: 1px solid #cfe7f3; }
.pk-card .pk-fallback {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 3px; height: 100%; box-sizing: border-box; padding: 26px 8px 8px;
    text-align: center; font-weight: 800; font-size: .74rem; line-height: 1.2; color: #1b2a41;
}
.pk-fallback .pk-date { font-size: .7rem; opacity: .7; letter-spacing: .04em; }
.pk-fallback .pk-name {
    display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
}
.pk-card.is-today  { box-shadow: 0 0 0 3px #ffb400; }
.pk-card.is-active { outline: 3px solid #2fb45a; outline-offset: -3px; }
.pk-flag {
    position: absolute; top: 6px; right: 6px; width: 16px; height: 16px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .62rem; font-weight: 800; background: #ffb400; color: #3b2a00;
    box-shadow: 0 1px 3px rgba(0, 0, 0, .25);
}
.pk-flag.ok { background: #2fb45a; color: #fff; }

/* Clickable games: invisible button stretched over its own card only */
[class*="st-key-pk_game_"] { position: absolute !important; inset: 0 0 7px 0; z-index: 3; width: auto !important; }
[class*="st-key-pk_game_"] [data-testid="stButton"],
[class*="st-key-pk_game_"] button { width: 100%; height: 100%; }
[class*="st-key-pk_game_"] button { opacity: 0; cursor: pointer; padding: 0; min-height: 0; }
[class*="st-key-pk_cell_game_"]:hover .pk-card {
    transform: translateY(-3px); box-shadow: 0 8px 18px rgba(20, 60, 90, .22);
}

/* ---- Month banner (spans the whole row) + month chip on each card ---- */
.st-key-pk_cal [data-testid="stElementContainer"]:has(.pk-month),
.st-key-pk_cal .element-container:has(.pk-month) { grid-column: 1 / -1; }
.pk-month {
    margin: 6px 0 0; padding: 5px 14px; border-radius: 999px;
    background: var(--pk-green); color: #fff; font-weight: 800; font-size: .85rem;
    letter-spacing: .08em; text-transform: uppercase; width: fit-content;
    box-shadow: 0 2px 8px rgba(47, 168, 79, .30);
}
.pk-mchip {
    position: absolute; top: 6px; left: 6px; z-index: 2; padding: 1px 6px; border-radius: 6px;
    font-size: .58rem; font-weight: 800; letter-spacing: .05em;
    background: rgba(27, 42, 65, .78); color: #fff; pointer-events: none;
}

/* ---- Capsules on top (buttons) ---- */
.st-key-pk_tabs { margin-bottom: -.4rem; }
.pk-hbanner { display: block; height: 58px; width: auto; max-width: 100%; border-radius: 10px; margin: 0 auto; }
.st-key-pk_tabs [data-testid="stButton"] { width: 100%; }
.st-key-pk_tabs [data-testid="stButton"] button {
    width: 100%; height: 40px !important; min-height: 40px !important;
    border-radius: 999px !important; padding: 0 1.1rem !important;
    background: var(--pk-green) !important; border: 1px solid var(--pk-green) !important;
    box-shadow: 0 2px 8px rgba(47, 168, 79, .30); white-space: nowrap;
}
.st-key-pk_tabs [data-testid="stButton"] button p { color: #fff !important; font-weight: 700; font-size: .82rem; margin: 0; }
.st-key-pk_tabs [data-testid="stButton"] button:hover { filter: brightness(.93); }
/* Site dropdown: same size and colour as the capsules */
.st-key-site, .st-key-site [data-testid="stSelectbox"] { width: 100%; }
.st-key-site [data-baseweb="select"] > div {
    height: 40px; min-height: 40px; border-radius: 999px !important; padding: 0 .5rem 0 1.1rem;
    background: var(--pk-green) !important; border: 1px solid var(--pk-green) !important;
    box-shadow: 0 2px 8px rgba(47, 168, 79, .30); cursor: pointer;
}
.st-key-site [data-baseweb="select"] div, .st-key-site [data-baseweb="select"] span {
    color: #fff !important; font-weight: 700; font-size: .82rem;
}
.st-key-site [data-baseweb="select"] svg { fill: #fff !important; color: #fff !important; }
.st-key-site [data-baseweb="select"] input { caret-color: transparent; }

/* ---- Tablet / pill tabs (st.radio) ---- */
.st-key-pk_tabs [role="radiogroup"] { display: flex; flex-direction: row; gap: 6px; flex-wrap: wrap; }
.st-key-pk_tabs label[data-baseweb="radio"] {
    margin: 0; padding: .25rem .85rem; border-radius: 999px; cursor: pointer;
    background: rgba(128, 138, 155, .14); border: 1px solid rgba(128, 138, 155, .35);
    transition: all .15s ease;
}
.st-key-pk_tabs label[data-baseweb="radio"]:hover { background: rgba(47, 168, 79, .15); }
.st-key-pk_tabs label[data-baseweb="radio"] > div:first-child { display: none; }  /* hide radio dot */
.st-key-pk_tabs label[data-baseweb="radio"] p { font-weight: 700; font-size: .8rem; margin: 0; }
.st-key-pk_tabs label[data-baseweb="radio"]:has(input:checked) {
    background: var(--pk-green); border-color: var(--pk-green);
    box-shadow: 0 3px 10px rgba(47, 168, 79, .35);
}
.st-key-pk_tabs label[data-baseweb="radio"]:has(input:checked) p { color: #fff; }

/* ---- Metric tiles (sized for the narrow left panel) ---- */
[data-testid="stMetric"] {
    background: rgba(128, 138, 155, .10); border: 1px solid rgba(128, 138, 155, .30);
    border-radius: 14px; padding: .7rem .9rem;
}
[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; line-height: 1.1; }
[data-testid="stMetricLabel"] p { font-size: .9rem; font-weight: 600; opacity: .8; }

@media (max-width: 900px) {
    .st-key-pk_cal { padding-left: 1.2%; }
    .st-key-pk_cal::before { display: none; }
}
</style>
""".replace("__COLS__", _COLS)


def build_banner_css() -> str:
    if not BANNER_B64:
        return ""
    return ('<style>.st-key-pk_cal::before { background-image: '
            f'url("data:image/webp;base64,{BANNER_B64}"); }}</style>')


# =============================================================================
# 6. UI COMPONENTS
# =============================================================================
@st.dialog("Assign VPOC")
def vpoc_dialog(game_id: str, when: date) -> None:
    existing = get_all_vpocs().get(game_id, {})
    st.markdown(f"**{GAMES[game_id]}**  \n{when.strftime('%A, %d %b %Y')}")
    runs = ", ".join(d.strftime("%d %b") for d in GAME_DATES.get(game_id, []))
    st.caption(f"Site: {current_site()}. This game runs on: {runs}. "
               f"One VPOC covers all of its dates.")

    with st.form(f"vpoc_form_{current_site()}_{game_id}"):
        sender_email = st.text_input(
            "Sender Email", value=existing.get("sender_email") or DEFAULT_SENDER_EMAIL,
            help="The address the notification is sent from.")
        c1, c2 = st.columns(2)
        vpoc_name = c1.text_input("VPOC Name", value=existing.get("vpoc_name", ""))
        vpoc_email = c2.text_input(
            "VPOC Email", value=existing.get("vpoc_email", ""),
            help="The recipient who receives the notification.")
        submitted = st.form_submit_button("Save assignment", type="primary", use_container_width=True)

    if not submitted:
        return

    values = [v.strip() for v in (sender_email, vpoc_name, vpoc_email)]
    if not all(values):
        st.error("Fill in all three fields.")
        return
    if not (EMAIL_PATTERN.match(values[0]) and EMAIL_PATTERN.match(values[2])):
        st.error("Enter valid email addresses for the Sender and the VPOC.")
        return

    upsert_vpoc(game_id, values[0], values[1], values[2], values[1], values[2])
    st.session_state.pending_toast = ("Assignment saved. Use the Auto Email tab to notify.", "✅")
    st.rerun()


def week_month_label(week: list) -> str:
    """'OCTOBER – NOVEMBER 2026' style label for the days present in one calendar week."""
    days = [c[0] for c in week if c]
    names = []
    for d in days:
        n = d.strftime("%B")
        if n not in names:
            names.append(n)
    return f"{' – '.join(names)} {days[-1].year}"


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
        style = f' style="aspect-ratio:{ratio:.4f}"'
    else:
        classes.append("is-text")
        inner = (f'<div class="pk-fallback"><span class="pk-date">{day.day} {day.strftime("%b").upper()}</span>'
                 f'<span class="pk-name">{item["emoji"]} {html.escape(item["name"])}</span></div>')
        style = ""

    chip = f'<span class="pk-mchip">{day.strftime("%b").upper()}</span>'
    return f'<div class="{" ".join(classes)}"{style}>{inner}{chip}{flag}</div>'


def render_calendar() -> None:
    vpocs = get_all_vpocs()
    today = date.today()
    active_date = st.session_state.active_date

    with st.container(key="pk_cal"):
        for name in WEEKDAYS:
            css_class = "pk-weekday sat" if name == "Saturday" else "pk-weekday"
            st.markdown(f'<div class="{css_class}">{name}</div>', unsafe_allow_html=True)

        last_label = None
        for week_no, week in enumerate(build_weeks()):
            label = week_month_label(week)
            if label != last_label:
                st.markdown(f'<div class="pk-month">{label}</div>', unsafe_allow_html=True)
                last_label = label

            for col_no, cell in enumerate(week):
                if cell is None:
                    continue
                day, key = cell
                item = ITEMS[key]
                is_game = item["kind"] == "game"
                # only the block that was clicked is highlighted (not every day of the same game)
                is_active = is_game and (day.isoformat() == active_date if active_date else False)
                ratio = COL_W[col_no] / ROW_H[min(week_no, len(ROW_H) - 1)]
                cell_key = f"pk_cell_game_{day.isoformat()}" if is_game else f"pk_cell_{day.isoformat()}"
                with st.container(key=cell_key):
                    st.markdown(
                        card_html(day, item, ratio=ratio, vpoc_set=key in vpocs,
                                  is_today=(day == today), is_active=is_active),
                        unsafe_allow_html=True,
                    )
                    if is_game
