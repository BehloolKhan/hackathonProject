import sqlite3

DB_FILE = "image_repository.db"      # the database file
SQL_FILE = "image_repository.sql"    # a readable copy of the schema

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       VARCHAR(100) NOT NULL,
    parent_id  INTEGER NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS tags (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS images (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        VARCHAR(255) NOT NULL,
    file_path    VARCHAR(500) NOT NULL,
    category_id  INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS image_tags (
    image_id  INTEGER NOT NULL,
    tag_id    INTEGER NOT NULL,
    PRIMARY KEY (image_id, tag_id),
    FOREIGN KEY (image_id) REFERENCES images(id),
    FOREIGN KEY (tag_id)   REFERENCES tags(id)
);
"""


def create_database():
    conn = sqlite3.connect(DB_FILE)           # creates the file if it doesn't exist
    conn.execute("PRAGMA foreign_keys = ON")  # make SQLite enforce foreign keys
    conn.executescript(SCHEMA)                # run all the CREATE TABLE statements
    conn.commit()

    # save the schema as a plain .sql file too
    with open(SQL_FILE, "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(line + "\n")

    # show what was created
    for (table,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ):
        print(f"Table: {table}")
        for col in conn.execute(f"PRAGMA table_info({table})"):
            print(f"   {col[1]}  ({col[2]})")

    conn.close()
    print(f"\nDatabase saved to {DB_FILE}")
    print(f"Schema saved to {SQL_FILE}")


if __name__ == "__main__":
    create_database()