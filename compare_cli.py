# -*- coding: utf-8 -*-
"""Headless compare for smoke tests: python compare_cli.py <folder>"""
from __future__ import annotations
import csv
import shutil
import sys
import threading
from pathlib import Path

# Import engines without requiring tkinter display
import importlib.util

def load_mod():
    path = Path(__file__).resolve().parent / "png_compressor.py"
    # Strip tkinter dependency by exec of engine functions only — simpler: patch sys.modules
    import types
    fake_tk = types.ModuleType("tkinter")
    fake_tk.Tk = object
    fake_tk.StringVar = object
    fake_tk.BooleanVar = object
    fake_tk.DISABLED = "disabled"
    fake_tk.NORMAL = "normal"
    fake_tk.END = "end"
    fake_tk.LEFT = "left"
    fake_tk.RIGHT = "right"
    fake_tk.X = "x"
    fake_tk.Y = "y"
    fake_tk.BOTH = "both"
    fake_tk.W = "w"
    fake_tk.E = "e"
    class _F: pass
    fake_filedialog = types.ModuleType("tkinter.filedialog")
    fake_messagebox = types.ModuleType("tkinter.messagebox")
    fake_ttk = types.ModuleType("tkinter.ttk")
    sys.modules["tkinter"] = fake_tk
    sys.modules["tkinter.filedialog"] = fake_filedialog
    sys.modules["tkinter.messagebox"] = fake_messagebox
    sys.modules["tkinter.ttk"] = fake_ttk
    spec = importlib.util.spec_from_file_location("png_compressor", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def main():
    if len(sys.argv) < 2:
        print("usage: compare_cli.py <folder> [limit]")
        return 2
    folder = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    m = load_mod()
    engines = m.available_engines()
    print("engines:", engines)
    files = m.collect_pngs(folder, False)[:limit]
    print("files:", [f.name for f in files])
    out_root = m.compare_folder_name(folder)
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    for e in engines:
        (out_root / e).mkdir()
    cancel = threading.Event()
    rows = []
    for path in files:
        before = path.stat().st_size
        sizes = {}
        for eng in engines:
            dest = out_root / eng / path.name
            ok, msg, sz = m.compress_with_engine(path, dest, eng, cancel)
            sizes[eng] = sz if ok else None
            print(f"  {path.name} {eng}: ok={ok} size={sz} {msg}")
        best = None
        best_sz = None
        for eng, sz in sizes.items():
            if sz is None:
                continue
            if best_sz is None or sz < best_sz:
                best_sz, best = sz, eng
        rows.append((path.name, before, sizes, best))
    csv_path = out_root / "对比结果.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["文件名", "原大小", "oxipng大小", "pngquant大小", "pngdeer大小", "体积最小方案"])
        for name, before, sizes, best in rows:
            w.writerow([
                name,
                before,
                sizes.get("oxipng") or "",
                sizes.get("pngquant") or "",
                sizes.get("pngdeer") or "",
                best or "",
            ])
    print("OUT", out_root)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
