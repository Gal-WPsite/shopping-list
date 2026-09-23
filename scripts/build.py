#!/usr/bin/env python3
"""Render the shopping-list page from a categories JSON file.

Usage: build.py <data.json> <out-dir>
data.json: {"🥬 ירקות": [["2", "בטטות קטנות", "optional note"], ...], ...}
Each item is [quantity or "", name, optional note]. Category order is store order.
"""
import datetime, json, pathlib, sys

data_path, out_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
data = json.loads(data_path.read_text(encoding="utf-8"))
for cat, items in data.items():
    for item in items:
        if not (2 <= len(item) <= 3) or not item[1]:
            sys.exit(f"bad item in {cat}: {item}")

template = (pathlib.Path(__file__).parent.parent / "assets/template.html").read_text(encoding="utf-8")
stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
html = template.replace("/*DATA*/{}", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")).replace("/*DATE*/", stamp)
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "index.html").write_text(html, encoding="utf-8")
print(out_dir / "index.html")
