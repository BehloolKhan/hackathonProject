import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from create_database import SCHEMA   # the exact four tables: categories, tags, images, image_tags

ROOT = Path("Screenshots")
DB_PATH = ROOT / "image_repository.db"

# Agreed category tree (parent -> children). The AI may only pick from this.
# Anything that doesn't match becomes "Other".
SEED_CATEGORIES = {
    "Code": ["Python Errors", "Web Errors"],
    "Diagrams": [],
    "Receipts": [],
    "Deadlines": [],
    "Messages": [],
    "Shopping": [],
    "Travel": [],
    "Inspiration": [],
    "Other": [],
}


# ---------- database setup ----------
def _connect():
    ROOT.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _seed_categories(conn)
    return conn


def _seed_categories(conn):
    """Fill the category tree the first time only."""
    if conn.execute("SELECT 1 FROM categories LIMIT 1").fetchone():
        return
    with conn:
        for parent, children in SEED_CATEGORIES.items():
            cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (parent,))
            for child in children:
                conn.execute(
                    "INSERT INTO categories (name, parent_id) VALUES (?, ?)",
                    (child, cur.lastrowid),
                )


# ---------- category helpers ----------
def _other_id(conn):
    return conn.execute(
        "SELECT id FROM categories WHERE name = 'Other' AND parent_id IS NULL"
    ).fetchone()["id"]


def _resolve_category(conn, category):
    """
    'Code', 'code/python errors' or 'Code > Python Errors' -> category id.
    Each part is looked up in the database, so unknown or malicious text
    (e.g. '../../etc') simply falls back to 'Other'.
    """
    parts = [p.strip() for p in re.split(r"[/>]", str(category)) if p.strip()]
    if not parts:
        return _other_id(conn)
    parent_id = None
    for part in parts:
        row = conn.execute(
            "SELECT id FROM categories WHERE LOWER(name) = LOWER(?) AND parent_id IS ?",
            (part, parent_id),
        ).fetchone()
        if row is None:
            return _other_id(conn)
        parent_id = row["id"]
    return parent_id


def _category_parts(conn, category_id):
    """id -> ['Code', 'Python Errors'] (root first)."""
    parts = []
    while category_id is not None:
        row = conn.execute(
            "SELECT name, parent_id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        parts.append(row["name"])
        category_id = row["parent_id"]
    return parts[::-1]


def _folder_name(name):
    """Strip anything that isn't safe in a folder name."""
    return re.sub(r"[^A-Za-z0-9 _-]", "", name).strip() or "Other"


def list_categories():
    """Every category as a path string, e.g. ['Code', 'Code/Python Errors', ...]."""
    conn = _connect()
    ids = [r["id"] for r in conn.execute("SELECT id FROM categories ORDER BY id")]
    paths = ["/".join(_category_parts(conn, i)) for i in ids]
    conn.close()
    return sorted(paths)


# ---------- filename helpers ----------
def _slugify(text):
    """'Binary Search Tree: Insertion!' -> 'binary-search-tree-insertion'"""
    text = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return text[:60] or "screenshot"


def _unique_path(folder, stem, suffix):
    """Never overwrite: add -1, -2, ... if the name is taken."""
    candidate = folder / f"{stem}{suffix}"
    n = 1
    while candidate.exists():
        candidate = folder / f"{stem}-{n}{suffix}"
        n += 1
    return candidate


def _clean_tags(tags):
    if isinstance(tags, str):
        tags = tags.split(",")
    cleaned = []
    for t in tags or []:
        t = re.sub(r"\s+", "-", str(t).strip().lower())
        if t and t not in cleaned:
            cleaned.append(t)
    return cleaned


# ---------- reading records ----------
_SELECT = """
SELECT i.id, i.title, i.file_path, i.category_id, GROUP_CONCAT(t.name, ',') AS tags
FROM images i
LEFT JOIN image_tags it ON it.image_id = i.id
LEFT JOIN tags t        ON t.id = it.tag_id
"""


def _row_to_record(conn, row):
    return {
        "id": row["id"],
        "title": row["title"],
        "file_path": row["file_path"],                     # relative to Screenshots/
        "filename": Path(row["file_path"]).name,
        "category": "/".join(_category_parts(conn, row["category_id"])),
        "tags": row["tags"].split(",") if row["tags"] else [],
    }


def _get_record(conn, image_id):
    row = conn.execute(_SELECT + " WHERE i.id = ? GROUP BY i.id", (image_id,)).fetchone()
    return _row_to_record(conn, row)


# ---------- deliverable 1 ----------
def save_screenshot(image_path, metadata):
    """
    metadata = {
        "title": str, "category": str, "tags": list[str] or str,
        "captured_at": ISO string (optional, only used in the filename)
    }
    Moves the image into its category folder, records it in the database,
    and returns the saved record as a dict.
    """
    src = Path(image_path)
    if not src.is_file():
        raise FileNotFoundError(f"Image not found: {src}")

    title = metadata.get("title") or "Untitled"
    tags = _clean_tags(metadata.get("tags", []))

    # capture time -> HHMMSS for the filename (the schema has no time column)
    try:
        stamp = datetime.fromisoformat(metadata["captured_at"]).strftime("%H%M%S")
    except (KeyError, TypeError, ValueError):
        stamp = datetime.now().strftime("%H%M%S")

    conn = _connect()
    try:
        # 1. category from the database, never from raw AI text
        category_id = _resolve_category(conn, metadata.get("category", "Other"))
        folder = ROOT.joinpath(*[_folder_name(p) for p in _category_parts(conn, category_id)])
        folder.mkdir(parents=True, exist_ok=True)

        # 2. safe, non-overwriting filename
        dest = _unique_path(folder, f"{_slugify(title)}_{stamp}", src.suffix.lower())

        # 3. move the file, then record it; undo the move if the database fails
        shutil.move(str(src), str(dest))
        try:
            with conn:   # one transaction: everything succeeds or nothing does
                cur = conn.execute(
                    "INSERT INTO images (title, file_path, category_id) VALUES (?, ?, ?)",
                    (title, dest.relative_to(ROOT).as_posix(), category_id),
                )
                image_id = cur.lastrowid
                for tag in tags:
                    conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
                    tag_id = conn.execute(
                        "SELECT id FROM tags WHERE name = ?", (tag,)
                    ).fetchone()["id"]
                    conn.execute(
                        "INSERT OR IGNORE INTO image_tags (image_id, tag_id) VALUES (?, ?)",
                        (image_id, tag_id),
                    )
        except Exception:
            shutil.move(str(dest), str(src))
            raise

        return _get_record(conn, image_id)
    finally:
        conn.close()


# ---------- deliverable 2 ----------
def search_screenshots(query="", category=None):
    """
    Funnel: category first (includes sub-categories), then every query word
    must match the title or one of the tags.
    """
    conn = _connect()
    try:
        prefix, where, params = "", [], []

        if category:
            prefix = """WITH RECURSIVE sub(id) AS (
                            SELECT ?
                            UNION ALL
                            SELECT c.id FROM categories c JOIN sub ON c.parent_id = sub.id
                        ) """
            params.append(_resolve_category(conn, category))
            where.append("i.category_id IN (SELECT id FROM sub)")

        for word in query.lower().split():
            like = f"%{word}%"
            where.append(
                """(LOWER(i.title) LIKE ? OR EXISTS (
                       SELECT 1 FROM image_tags it2 JOIN tags t2 ON t2.id = it2.tag_id
                       WHERE it2.image_id = i.id AND LOWER(t2.name) LIKE ?))"""
            )
            params += [like, like]

        sql = prefix + _SELECT
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY i.id ORDER BY i.id DESC"   # newest saved first

        return [_row_to_record(conn, r) for r in conn.execute(sql, params)]
    finally:
        conn.close()