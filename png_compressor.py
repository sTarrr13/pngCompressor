# -*- coding: utf-8 -*-
"""PNG 本地压缩工具 — oxipng / pngquant / pngdeer 独立方案 + 三方案对比"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

CREATE_NO_WINDOW = 0x08000000

ENGINE_OXIPNG = "oxipng"
ENGINE_PNGQUANT = "pngquant"
ENGINE_PNGDEER = "pngdeer"

WORK_SINGLE = "single"
WORK_COMPARE = "compare"


def app_dir() -> Path:
    """Directory that holds bin/ next to the script or the frozen EXE."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = app_dir()
BIN_DIR = APP_DIR / "bin"


def bin_path(name: str) -> Path:
    return BIN_DIR / name


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def pct_saved(before: int, after: int) -> float:
    if before <= 0:
        return 0.0
    return (1.0 - after / before) * 100.0


def collect_pngs(folder: Path, recursive: bool) -> List[Path]:
    files = list(folder.rglob("*")) if recursive else list(folder.iterdir())
    out: List[Path] = []
    for p in files:
        if not p.is_file():
            continue
        if p.suffix.lower() != ".png":
            continue
        if p.name.startswith("._pngtmp_") or p.name.endswith(".png.tmp"):
            continue
        # skip compare output trees
        parts_lower = {x.lower() for x in p.parts}
        if "原图_对比" in p.parts or any(x.endswith("_对比") for x in p.parts):
            # still allow if user explicitly selected the compare folder
            pass
        out.append(p)
    out.sort(key=lambda x: str(x).lower())
    return out


def run_tool(cmd: List[str], timeout: int = 900) -> Tuple[int, str, str]:
    kwargs = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "timeout": timeout,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = CREATE_NO_WINDOW
        kwargs["encoding"] = "utf-8"
        kwargs["errors"] = "replace"
    else:
        kwargs["encoding"] = "utf-8"
        kwargs["errors"] = "replace"
    try:
        r = subprocess.run(cmd, **kwargs)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "超时"
    except Exception as e:
        return -1, "", str(e)


def engine_exe(engine: str) -> Optional[Path]:
    mapping = {
        ENGINE_OXIPNG: "oxipng.exe",
        ENGINE_PNGQUANT: "pngquant.exe",
        ENGINE_PNGDEER: "pngdeer.exe",
    }
    name = mapping.get(engine)
    if not name:
        return None
    p = bin_path(name)
    return p if p.exists() else None


def available_engines() -> List[str]:
    order = [ENGINE_OXIPNG, ENGINE_PNGQUANT, ENGINE_PNGDEER]
    return [e for e in order if engine_exe(e)]


def compress_with_engine(
    src: Path,
    dest: Path,
    engine: str,
    cancel_flag: threading.Event,
) -> Tuple[bool, str, int]:
    """
    Compress src into dest using a single engine (no chaining).
    Returns (ok, message, output_size_or_0).
    """
    if cancel_flag.is_set():
        return False, "已取消", 0

    exe = engine_exe(engine)
    if exe is None:
        return False, f"{engine} 不可用", 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try:
            dest.unlink()
        except Exception:
            pass

    work_dir = Path(tempfile.mkdtemp(prefix="pngeng_"))
    try:
        work_in = work_dir / "in.png"
        shutil.copy2(src, work_in)

        if engine == ENGINE_OXIPNG:
            # oxipng can write in-place; copy then optimize
            work_out = work_dir / "out.png"
            shutil.copy2(work_in, work_out)
            cmd = [
                str(exe),
                "-o",
                "4",
                "--strip",
                "safe",
                "--quiet",
                str(work_out),
            ]
            code, _o, err = run_tool(cmd)
            if code != 0:
                return False, f"oxipng失败: {err.strip() or code}", 0
            if not work_out.exists():
                return False, "oxipng未产出文件", 0
            shutil.copy2(work_out, dest)

        elif engine == ENGINE_PNGQUANT:
            # Pure pngquant only — quality 80-95, no dither (mild default for single/compare)
            work_out = work_dir / "out.png"
            cmd = [
                str(exe),
                "--quality=80-95",
                "--nofs",
                "--force",
                "--output",
                str(work_out),
                str(work_in),
            ]
            code, _o, err = run_tool(cmd)
            # 0 = ok; 99 = quality not met; 98 = larger than original (with --skip-if-larger)
            if code != 0 or not work_out.exists() or work_out.stat().st_size <= 0:
                # Fallback: allow dither if no-dither path failed quality gate
                work_out2 = work_dir / "out2.png"
                cmd2 = [
                    str(exe),
                    "--quality=65-90",
                    "--force",
                    "--output",
                    str(work_out2),
                    str(work_in),
                ]
                code2, _o2, err2 = run_tool(cmd2)
                if code2 != 0 or not work_out2.exists():
                    return False, f"pngquant失败: {(err2 or err).strip() or code2 or code}", 0
                shutil.copy2(work_out2, dest)
            else:
                shutil.copy2(work_out, dest)

        elif engine == ENGINE_PNGDEER:
            work_out = work_dir / "out.png"
            cmd = [str(exe), str(work_in), "-o", str(work_out)]
            code, _o, err = run_tool(cmd, timeout=1800)
            if code != 0 or not work_out.exists():
                return False, f"pngdeer失败: {err.strip() or code}", 0
            shutil.copy2(work_out, dest)

        else:
            return False, f"未知引擎: {engine}", 0

        size = dest.stat().st_size
        return True, "ok", size
    except Exception as e:
        return False, str(e), 0
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def atomic_replace_if_smaller(src_path: Path, candidate: Path) -> Tuple[str, int, int]:
    before = src_path.stat().st_size
    after = candidate.stat().st_size
    if after >= before:
        try:
            candidate.unlink(missing_ok=True)
        except Exception:
            pass
        return "保持原图（未更小）", before, before

    tmp = src_path.with_name(f"._pngtmp_{os.getpid()}_{src_path.name}")
    try:
        shutil.copy2(candidate, tmp)
        os.replace(tmp, src_path)
        return "已替换", before, after
    except Exception as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return f"替换失败: {e}", before, before
    finally:
        try:
            candidate.unlink(missing_ok=True)
        except Exception:
            pass


def process_one_single(
    path: Path,
    engine: str,
    cancel_flag: threading.Event,
) -> Tuple[str, int, int, str]:
    if cancel_flag.is_set():
        return path.name, 0, 0, "已取消"
    before = path.stat().st_size
    work_dir = Path(tempfile.mkdtemp(prefix="pngone_"))
    try:
        candidate = work_dir / path.name
        ok, msg, _sz = compress_with_engine(path, candidate, engine, cancel_flag)
        if cancel_flag.is_set():
            return path.name, before, before, "已取消"
        if not ok:
            return path.name, before, before, msg
        status, b, a = atomic_replace_if_smaller(path, candidate)
        return path.name, b, a, status
    except Exception as e:
        return path.name, before, before, f"错误: {e}"
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def compare_folder_name(folder: Path) -> Path:
    return folder.parent / f"{folder.name}_对比"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PNG 压缩工具（三方案对比）")
        self.geometry("920x640")
        self.minsize(720, 520)

        self.folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.work_mode_var = tk.StringVar(value=WORK_COMPARE)
        self.engine_var = tk.StringVar(value=ENGINE_OXIPNG)
        self.cancel_flag = threading.Event()
        self.worker: Optional[threading.Thread] = None
        self._engines = available_engines()

        self._build_ui()
        self._check_bins()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm_top = ttk.Frame(self)
        frm_top.pack(fill=tk.X, **pad)
        ttk.Label(frm_top, text="文件夹：").pack(side=tk.LEFT)
        ttk.Entry(frm_top, textvariable=self.folder_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        ttk.Button(frm_top, text="选择文件夹…", command=self.choose_folder).pack(side=tk.LEFT)

        frm_opts = ttk.Frame(self)
        frm_opts.pack(fill=tk.X, **pad)
        ttk.Checkbutton(frm_opts, text="包含子文件夹", variable=self.recursive_var).pack(
            side=tk.LEFT
        )

        frm_work = ttk.LabelFrame(self, text="工作模式")
        frm_work.pack(fill=tk.X, **pad)
        ttk.Radiobutton(
            frm_work,
            text="三方案对比（推荐：不覆盖原图，输出到「文件夹名_对比」）",
            variable=self.work_mode_var,
            value=WORK_COMPARE,
            command=self._sync_mode_ui,
        ).pack(anchor=tk.W, padx=8, pady=2)
        ttk.Radiobutton(
            frm_work,
            text="单方案原位替换（仅在结果更小时覆盖原文件）",
            variable=self.work_mode_var,
            value=WORK_SINGLE,
            command=self._sync_mode_ui,
        ).pack(anchor=tk.W, padx=8, pady=2)

        self.frm_engine = ttk.LabelFrame(self, text="单方案引擎（互不串联）")
        self.frm_engine.pack(fill=tk.X, **pad)

        labels = {
            ENGINE_OXIPNG: "oxipng — 无损重打包（-o 4 --strip safe）",
            ENGINE_PNGQUANT: "pngquant — 有损减色（默认 --quality=80-95 --nofs，失败则试 65-90）",
            ENGINE_PNGDEER: "pngdeer — 感知质量自动搜调色板（接近 TinyPNG）",
        }
        for eng in [ENGINE_OXIPNG, ENGINE_PNGQUANT, ENGINE_PNGDEER]:
            state = tk.NORMAL if eng in self._engines else tk.DISABLED
            text = labels[eng]
            if eng not in self._engines:
                text += "  【暂不可用：缺少 bin 中的 exe】"
            ttk.Radiobutton(
                self.frm_engine,
                text=text,
                variable=self.engine_var,
                value=eng,
                state=state,
            ).pack(anchor=tk.W, padx=8, pady=2)

        if self._engines and self.engine_var.get() not in self._engines:
            self.engine_var.set(self._engines[0])

        self.warn_var = tk.StringVar()
        ttk.Label(self, textvariable=self.warn_var, foreground="#a60").pack(fill=tk.X, padx=10)

        note = (
            "说明：三种算法彼此独立，有损不一定更小。"
            "对比模式会在同级目录生成「原文件夹名_对比」子目录（oxipng / pngquant / pngdeer + 对比结果.csv）。"
        )
        ttk.Label(self, text=note, wraplength=880).pack(fill=tk.X, padx=10)

        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill=tk.X, **pad)
        self.start_btn = ttk.Button(frm_btn, text="开始处理", command=self.start)
        self.start_btn.pack(side=tk.LEFT)
        self.cancel_btn = ttk.Button(frm_btn, text="取消", command=self.cancel, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.open_btn = ttk.Button(
            frm_btn, text="打开对比文件夹", command=self.open_compare_folder, state=tk.DISABLED
        )
        self.open_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(frm_btn, textvariable=self.status_var).pack(side=tk.LEFT, padx=(16, 0))

        cols = ("name", "before", "oxi", "pq", "deer", "best", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        headings = {
            "name": "文件名",
            "before": "原大小",
            "oxi": "oxipng",
            "pq": "pngquant",
            "deer": "pngdeer",
            "best": "最小方案",
            "status": "状态",
        }
        widths = {
            "name": 200,
            "before": 80,
            "oxi": 110,
            "pq": 110,
            "deer": 110,
            "best": 90,
            "status": 120,
        }
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor=tk.W if c in ("name", "best", "status") else tk.E)

        scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=6)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=6)

        self.summary_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.summary_var).pack(fill=tk.X, padx=10, pady=(0, 8))

        self._last_compare_dir: Optional[Path] = None
        self._sync_mode_ui()

    def _sync_mode_ui(self) -> None:
        if self.work_mode_var.get() == WORK_COMPARE:
            self.warn_var.set("对比模式：不会覆盖原图，结果写到「文件夹名_对比」。")
            for child in self.frm_engine.winfo_children():
                # keep radios but grey out selection purpose
                pass
        else:
            self.warn_var.set("原位替换：只会在压缩后更小时覆盖原文件。请先自行备份。")

    def _check_bins(self) -> None:
        if not self._engines:
            messagebox.showerror(
                "缺少组件",
                "bin 目录下找不到 oxipng.exe / pngquant.exe / pngdeer.exe。\n请把官方 Windows 版放到 bin 目录。",
            )
        elif ENGINE_PNGDEER not in self._engines:
            # soft notice in summary area
            self.summary_var.set("提示：pngdeer.exe 暂不可用，对比将只跑 oxipng 与 pngquant。")

    def choose_folder(self) -> None:
        d = filedialog.askdirectory(title="选择要处理的文件夹")
        if d:
            self.folder_var.set(d)

    def open_compare_folder(self) -> None:
        if self._last_compare_dir and self._last_compare_dir.is_dir():
            try:
                if sys.platform == "win32":
                    os.startfile(str(self._last_compare_dir))  # type: ignore[attr-defined]
                else:
                    subprocess.Popen(["xdg-open", str(self._last_compare_dir)])
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning("提示", "请先选择文件夹。")
            return
        p = Path(folder)
        if not p.is_dir():
            messagebox.showerror("错误", "文件夹不存在。")
            return

        work = self.work_mode_var.get()
        engines = available_engines()
        if not engines:
            messagebox.showerror("错误", "没有任何可用引擎。")
            return

        if work == WORK_SINGLE:
            eng = self.engine_var.get()
            if eng not in engines:
                messagebox.showerror("错误", f"{eng} 不可用。")
                return
            ok = messagebox.askokcancel(
                "确认原位替换",
                f"将用【{eng}】单独处理所选文件夹中的 PNG。\n"
                "仅在结果更小时覆盖原文件（不会自动备份）。\n确定开始？",
            )
            if not ok:
                return
            run_engines = [eng]
        else:
            run_engines = engines
            ok = messagebox.askokcancel(
                "确认三方案对比",
                "不会覆盖原图。\n"
                f"将分别用：{', '.join(run_engines)}\n"
                f"结果写到：{compare_folder_name(p)}\n确定开始？",
            )
            if not ok:
                return

        files = collect_pngs(p, self.recursive_var.get())
        if not files:
            messagebox.showinfo("提示", "该文件夹下没有找到 PNG 文件。")
            return

        for i in self.tree.get_children():
            self.tree.delete(i)
        self.summary_var.set("")
        self.cancel_flag.clear()
        self.start_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.open_btn.configure(state=tk.DISABLED)
        self.status_var.set(f"处理中… 共 {len(files)} 张")

        self.worker = threading.Thread(
            target=self._run_batch,
            args=(files, work, run_engines, p),
            daemon=True,
        )
        self.worker.start()

    def cancel(self) -> None:
        self.cancel_flag.set()
        self.status_var.set("正在取消…")

    def _cell(self, before: int, size: Optional[int], ok: bool) -> str:
        if size is None or not ok:
            return "—"
        return f"{format_size(size)} ({pct_saved(before, size):.1f}%)"

    def _run_batch(
        self,
        files: List[Path],
        work: str,
        engines: List[str],
        folder: Path,
    ) -> None:
        cancelled = False
        if work == WORK_COMPARE:
            out_root = compare_folder_name(folder)
            try:
                if out_root.exists():
                    shutil.rmtree(out_root)
                out_root.mkdir(parents=True, exist_ok=True)
                for eng in engines:
                    (out_root / eng).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.after(0, self._finish, f"无法创建对比目录: {e}", None)
                return

            rows_csv: List[Dict[str, str]] = []
            win_counts: Dict[str, int] = {e: 0 for e in engines}
            win_counts["并列/无"] = 0

            for idx, path in enumerate(files, 1):
                if self.cancel_flag.is_set():
                    cancelled = True
                    break
                before = path.stat().st_size
                sizes: Dict[str, Optional[int]] = {e: None for e in [ENGINE_OXIPNG, ENGINE_PNGQUANT, ENGINE_PNGDEER]}
                oks: Dict[str, bool] = {e: False for e in sizes}
                status_parts = []

                for eng in engines:
                    if self.cancel_flag.is_set():
                        cancelled = True
                        break
                    dest = out_root / eng / path.name
                    ok, msg, sz = compress_with_engine(path, dest, eng, self.cancel_flag)
                    oks[eng] = ok
                    sizes[eng] = sz if ok else None
                    if not ok:
                        status_parts.append(f"{eng}:{msg}")

                if cancelled:
                    break

                candidates = [(e, sizes[e]) for e in engines if oks.get(e) and sizes[e] is not None]
                if candidates:
                    best_size = min(s for _, s in candidates if s is not None)
                    winners = [e for e, s in candidates if s == best_size]
                    best_label = "+".join(winners) if len(winners) > 1 else winners[0]
                    if len(winners) == 1:
                        win_counts[winners[0]] = win_counts.get(winners[0], 0) + 1
                    else:
                        win_counts["并列/无"] = win_counts.get("并列/无", 0) + 1
                else:
                    best_label = "失败"
                    win_counts["并列/无"] = win_counts.get("并列/无", 0) + 1

                status = "完成" if not status_parts else "; ".join(status_parts)
                row = {
                    "文件名": path.name,
                    "原大小": str(before),
                    "oxipng大小": str(sizes[ENGINE_OXIPNG] or ""),
                    "oxipng节省%": f"{pct_saved(before, sizes[ENGINE_OXIPNG]):.2f}" if sizes[ENGINE_OXIPNG] else "",
                    "pngquant大小": str(sizes[ENGINE_PNGQUANT] or ""),
                    "pngquant节省%": f"{pct_saved(before, sizes[ENGINE_PNGQUANT]):.2f}" if sizes[ENGINE_PNGQUANT] else "",
                    "pngdeer大小": str(sizes[ENGINE_PNGDEER] or ""),
                    "pngdeer节省%": f"{pct_saved(before, sizes[ENGINE_PNGDEER]):.2f}" if sizes[ENGINE_PNGDEER] else "",
                    "体积最小方案": best_label,
                }
                rows_csv.append(row)

                self.after(
                    0,
                    self._add_compare_row,
                    path.name,
                    format_size(before),
                    self._cell(before, sizes[ENGINE_OXIPNG], oks[ENGINE_OXIPNG]),
                    self._cell(before, sizes[ENGINE_PNGQUANT], oks[ENGINE_PNGQUANT]),
                    self._cell(before, sizes[ENGINE_PNGDEER], oks[ENGINE_PNGDEER]),
                    best_label,
                    status,
                    idx,
                    len(files),
                )

            # write CSV
            csv_path = out_root / "对比结果.csv"
            fieldnames = [
                "文件名",
                "原大小",
                "oxipng大小",
                "oxipng节省%",
                "pngquant大小",
                "pngquant节省%",
                "pngdeer大小",
                "pngdeer节省%",
                "体积最小方案",
            ]
            try:
                with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fieldnames)
                    w.writeheader()
                    w.writerows(rows_csv)
            except Exception as e:
                self.after(0, self._finish, f"CSV 写入失败: {e}", out_root)
                return

            # also a short txt summary
            txt_path = out_root / "对比结果.txt"
            try:
                lines = [
                    f"输入文件夹: {folder}",
                    f"引擎: {', '.join(engines)}",
                    f"文件数: {len(rows_csv)}",
                    "各方案胜出次数: " + ", ".join(f"{k}={v}" for k, v in win_counts.items() if v),
                    "",
                    "详见 对比结果.csv 与各子文件夹中的 PNG。",
                ]
                txt_path.write_text("\n".join(lines), encoding="utf-8")
            except Exception:
                pass

            summary = (
                f"{'已取消。' if cancelled else '对比完成。'}"
                f" 输出：{out_root}  | 胜出： "
                + ", ".join(f"{k} {v}" for k, v in win_counts.items() if v)
            )
            self.after(0, self._finish, summary, out_root)
            return

        # single in-place
        eng = engines[0]
        total_before = 0
        total_after = 0
        replaced = 0
        kept = 0
        failed = 0

        for idx, path in enumerate(files, 1):
            if self.cancel_flag.is_set():
                cancelled = True
                break
            name, before, after, status = process_one_single(path, eng, self.cancel_flag)
            total_before += before
            total_after += after
            if status == "已替换":
                replaced += 1
            elif status.startswith("保持"):
                kept += 1
            elif status == "已取消":
                cancelled = True
                break
            else:
                if "失败" in status or "错误" in status or "不可用" in status:
                    failed += 1
                else:
                    kept += 1

            pct = f"{pct_saved(before, after):.1f}%" if before > 0 and after < before else "0%"
            # reuse compare columns: only fill selected engine
            oxi = pq = deer = "—"
            cell = f"{format_size(after)} ({pct})"
            if eng == ENGINE_OXIPNG:
                oxi = cell
            elif eng == ENGINE_PNGQUANT:
                pq = cell
            else:
                deer = cell
            self.after(
                0,
                self._add_compare_row,
                name,
                format_size(before),
                oxi,
                pq,
                deer,
                eng if status == "已替换" else "—",
                status,
                idx,
                len(files),
            )

        saved = total_before - total_after
        saved_pct = (saved / total_before * 100) if total_before else 0.0
        summary = (
            f"{'已取消。' if cancelled else '完成。'}"
            f"引擎 {eng}：替换 {replaced}，保持 {kept}，失败 {failed}。"
            f" 合计 {format_size(total_before)} → {format_size(total_after)}"
            f"（少 {format_size(max(0, saved))}，约 {saved_pct:.1f}%）"
        )
        self.after(0, self._finish, summary, None)

    def _add_compare_row(
        self,
        name: str,
        before: str,
        oxi: str,
        pq: str,
        deer: str,
        best: str,
        status: str,
        idx: int,
        total: int,
    ) -> None:
        self.tree.insert("", tk.END, values=(name, before, oxi, pq, deer, best, status))
        self.tree.yview_moveto(1.0)
        self.status_var.set(f"处理中… {idx}/{total}")

    def _finish(self, summary: str, compare_dir: Optional[Path]) -> None:
        self.summary_var.set(summary)
        self.status_var.set("就绪")
        self.start_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
        if compare_dir is not None:
            self._last_compare_dir = compare_dir
            self.open_btn.configure(state=tk.NORMAL)
            try:
                if messagebox.askyesno("对比完成", f"结果在：\n{compare_dir}\n\n是否打开该文件夹？"):
                    self.open_compare_folder()
            except Exception:
                pass


def main() -> None:
    try:
        os.chdir(APP_DIR)
    except Exception:
        pass
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
