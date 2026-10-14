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

CSS = """<style>
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
</style>""".replace("__COLS__", _COLS)


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
                    if is_game:
                        clicked = st.button(
                            f'Open {item["name"]} on {day.strftime("%d %b")}',
                            key=f'pk_game_{day.isoformat()}',
                            on_click=select_game, args=(key, day.isoformat()),
                        )
                        if clicked:
                            vpoc_dialog(key, day)




# ---- Tab: Peak Tracker -------------------------------------------------------
def _focus_badge_input() -> None:
    """Put the cursor back into the badge box after every scan (the scanner types into it)."""
    try:
        components.html(
            """<script>
            setTimeout(function () {
              try {
                var el = window.parent.document.querySelector('input[aria-label="Scan employee badge"]');
                if (el) { el.focus(); }
              } catch (e) {}
            }, 120);
            </script>""",
            height=0,
        )
    except Exception:          # cosmetic only: never let autofocus break the tracker
        pass


def render_tracker() -> None:
    site = current_site()
    st.caption(f"Site: {site}")

    # The selectbox only exists while this dialog is open, so re-seed its value from the shared
    # active_occ (also updated by calendar clicks) on every run.
    if st.session_state.active_occ not in OCC_IDS:
        st.session_state.active_occ = default_occ()
    st.session_state.tracker_game_select = st.session_state.active_occ
    occ = st.selectbox(
        "Game being tracked", options=OCC_IDS, format_func=occ_label,
        key="tracker_game_select", on_change=sync_tracker_game,
    )

    mode = st.radio("Add scanned employee as", ["Participant", "Winner"], horizontal=True,
                    key="scan_mode", help="Choose Winner to save the next scanned logins as winners.")

    # A form: nothing runs while the scanner types; one clean run happens on Enter.
    with st.form("scan_form", clear_on_submit=True, border=False):
        raw = st.text_input("Scan employee badge", key="badge_input",
                            placeholder="Click here, then scan the badge")
        submitted = st.form_submit_button("Add", type="primary")
    if submitted:
        process_scan(raw, mode)

    # --- messages ---
    dup = st.session_state.scan_dup
    if dup and dup["site"] == site:
        w1, w2 = st.columns([3, 1], vertical_alignment="center")
        w1.warning(f"**Duplicate entry**: {dup['badge']} is already in the {site} database "
                   f"({dup['where']}).")
        w2.button("Still want to add", key="force_add_btn", on_click=force_add,
                  use_container_width=True)
    feedback = st.session_state.scan_feedback
    if feedback:
        kind, message = feedback
        {"success": st.success, "error": st.error, "warning": st.warning}[kind](message)

    # --- one list for the whole site ---
    all_rows = get_tracker()
    g_id, g_day = split_occ(occ)
    here = all_rows[(all_rows["game_id"] == g_id) & (all_rows["game_date"] == g_day.isoformat())]
    m1, m2 = st.columns(2)
    m1.metric("Participants", len(here))
    m2.metric("Winners", int((here["Status"] == WINNER).sum()))
    st.caption(f"{occ_label(occ)} is selected. New scans are saved under this game and date. "
               f"All {site} entries: {len(all_rows)}.")

    if all_rows.empty:
        st.info(f"No badges scanned for {site} yet. Scan the first one above.")
        _focus_badge_input()
        return

    only_selected = st.checkbox("Show only the selected game and date", key="only_selected")
    df = here if only_selected else all_rows

    st.session_state.editor_ids = df["id"].tolist()
    st.session_state.editor_key = (f"editor_{site}_{st.session_state.editor_version}_"
                                   f"{len(df)}_{int(only_selected)}_{occ if only_selected else ''}")

    st.data_editor(
        df[["id", "Badge ID", "Game", "Date", "Status", "Scanned at"]],
        key=st.session_state.editor_key,
        on_change=handle_status_edit,
        hide_index=True,
        use_container_width=True,
        disabled=["Badge ID", "Game", "Date", "Scanned at"],
        column_config={
            "id": None,
            "Status": st.column_config.SelectboxColumn(
                "Result", help="Choose Winner to mark this employee as a winner",
                options=STATUS_OPTIONS, required=True),
        },
    )
    st.download_button(f"⬇ Download {site} tracker file (CSV)", tracker_csv_bytes(),
                       file_name=f"peak_tracker_{site}.csv", mime="text/csv",
                       key="tracker_download")
    _focus_badge_input()


# ---- Tab: Auto Email ---------------------------------------------------------
def _fmt_dates(dates: list) -> str:
    return ", ".join(d.strftime("%d %b") for d in dates)


def render_email() -> None:
    vpocs = get_all_vpocs()
    today = date.today()

    if not vpocs:
        st.info(f"No VPOCs assigned yet for {current_site()}. Click a game in the calendar to assign one.")
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
            "Sender": sender_for(a),
            "VPOC": f'{a["vpoc_name"]} ({a["vpoc_email"]})',
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
    subject, text, _ = build_reminder_email(GAMES[game_id], a["vpoc_name"], run_date)
    with st.expander("Preview email"):
        st.markdown(f"**From:** {sender_for(a)}  \n**To:** {a['vpoc_email']}  \n"
                    f"**Subject:** {subject}")
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

@st.dialog("Peak Tracker", width="large")
def tracker_dialog() -> None:
    render_tracker()


@st.dialog("Auto Email", width="large")
def email_dialog() -> None:
    render_email()


@st.dialog("Peak Gallery", width="large")
def gallery_dialog() -> None:
    st.caption(f"Site: {current_site()}. Save pictures from the Peak events here. "
               f"Everyone using the dashboard can see them (this gallery is only for {current_site()}).")
    files = st.file_uploader(
        "Add images", type=GALLERY_TYPES, accept_multiple_files=True,
        key=f"gallery_upload_{st.session_state.gallery_ver}",
    )
    if files and st.button("💾 Save to gallery", type="primary", key="gallery_save"):
        saved, skipped = 0, 0
        for f in files:
            if f.size > GALLERY_MAX_MB * 1024 * 1024:
                skipped += 1
                continue
            add_image(f.name, f.type, f.getvalue())
            saved += 1
        st.session_state.gallery_ver += 1                       # clears the uploader
        msg = f"{saved} image(s) saved to the gallery."
        if skipped:
            msg += f" {skipped} skipped (over {GALLERY_MAX_MB} MB)."
        st.toast(msg, icon="🖼️")
        st.rerun(scope="fragment")

    images = list_images()
    if not images:
        st.info("No images yet. Add the first one above.")
        return
    st.markdown(f"**{len(images)} image(s)**")
    cols = st.columns(3)
    for n, img in enumerate(images):
        with cols[n % 3]:
            with st.container(border=True):
                st.image(img["data"], use_container_width=True)
                st.caption(f'{img["filename"]} · {img["uploaded_at"][:10]}')
                d1, d2 = st.columns(2)
                d1.download_button("⬇ Save", img["data"], file_name=img["filename"],
                                   mime=img["mime"], key=f'gal_dl_{img["id"]}',
                                   use_container_width=True)
                d2.button("🗑 Delete", key=f'gal_del_{img["id"]}', use_container_width=True,
                          on_click=delete_image, args=(img["id"],))


def render_right_panel() -> None:
    """Small capsules on top (Peak Tracker / Auto Email open as pop-ups); the calendar is always shown below."""
    with st.container(key="pk_tabs"):
        c_site, c_track, c_banner, c_gallery, c_email = st.columns(
            [1, 1, 2.4, 1, 1], gap="small", vertical_alignment="center")
        c_site.selectbox("Site", options=SITES, key="site", on_change=on_site_change,
                         format_func=lambda s: f"Site: {s}", label_visibility="collapsed")
        if c_track.button("Peak Tracker", key="pk_pill_tracker", use_container_width=True):
            tracker_dialog()
        if HBANNER_B64:
            c_banner.markdown(f'<img class="pk-hbanner" alt="Peak 2026 - Oct-Dec \'26" '
                              f'src="data:image/webp;base64,{HBANNER_B64}">', unsafe_allow_html=True)
        if c_gallery.button("Peak Gallery", key="pk_pill_gallery", use_container_width=True):
            gallery_dialog()
        if c_email.button("Auto Email", key="pk_pill_email", use_container_width=True):
            email_dialog()
    render_calendar()


# =============================================================================
# 7. MAIN
# =============================================================================
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="⛰️", layout="wide")
    init_state()
    get_conn(current_site())          # opens (and creates / upgrades) the selected site's database once
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(build_banner_css(), unsafe_allow_html=True)

    if st.session_state.pending_toast:
        message, icon = st.session_state.pending_toast
        st.toast(message, icon=icon)
        st.session_state.pending_toast = None

    render_right_panel()


# =============================================================================
# 8. POSTER ARTWORK (embedded images)
# =============================================================================
HBANNER_B64 = "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 pairings = [v["name"] for v in ITEMS.values() if v["kind"] == "game"]
