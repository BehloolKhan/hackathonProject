import sqlite3
import tkinter as tk
from tkinter import ttk

DB_PATH = "images.db"  # <-- path to your SQLite file


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


root = tk.Tk()
root.title("Image Repository")
root.geometry("600x550")

# ---- load categories and tags from the database ----
categories = query("SELECT id, name FROM categories ORDER BY name")
tags = query("SELECT id, name FROM tags ORDER BY name")

category_ids = {"All categories": None}
category_ids.update({name: cid for cid, name in categories})
tag_ids = [tid for tid, _ in tags]  # same order as the listbox rows

# ---- category dropdown (single select) ----
ttk.Label(root, text="Category:").pack(anchor="w", padx=10, pady=(10, 0))
category_box = ttk.Combobox(root, values=list(category_ids), state="readonly")
category_box.current(0)
category_box.pack(fill="x", padx=10)

# ---- tags list (multi select) ----
ttk.Label(root, text="Tags (Ctrl+click to select several):").pack(anchor="w", padx=10, pady=(10, 0))
tag_frame = ttk.Frame(root)
tag_frame.pack(fill="x", padx=10)
tag_list = tk.Listbox(tag_frame, selectmode="multiple", height=8, exportselection=False)
tag_scroll = ttk.Scrollbar(tag_frame, command=tag_list.yview)
tag_list.config(yscrollcommand=tag_scroll.set)
tag_list.pack(side="left", fill="x", expand=True)
tag_scroll.pack(side="right", fill="y")
for _, name in tags:
    tag_list.insert("end", name)

# ---- results ----
results = tk.Listbox(root)


def search():
    sql = "SELECT file_path FROM images WHERE 1=1"
    params = []

    cat_id = category_ids[category_box.get()]
    if cat_id is not None:
        sql += " AND category_id = ?"
        params.append(cat_id)

    selected = [tag_ids[i] for i in tag_list.curselection()]
    if selected:  # image must have ALL selected tags
        marks = ",".join("?" * len(selected))
        sql += (f" AND id IN (SELECT image_id FROM image_tags WHERE tag_id IN ({marks})"
                f" GROUP BY image_id HAVING COUNT(DISTINCT tag_id) = ?)")
        params += selected + [len(selected)]

    results.delete(0, "end")
    for (path,) in query(sql, params):
        results.insert("end", path)


ttk.Button(root, text="Search", command=search).pack(pady=10)
ttk.Label(root, text="Matching file paths:").pack(anchor="w", padx=10)
results.pack(fill="both", expand=True, padx=10, pady=(0, 10))

root.mainloop()
