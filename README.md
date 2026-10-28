# PNG 压缩器（pngCompressor）

本地 Windows 小工具：对文件夹里的 PNG 做压缩，可选 **三方案并排对比**（互不串联），方便看出哪种更小、画质是否可接受。

适合游戏素材、UI 切图、批量本地处理；**不上传图片**，全部在本机完成。

**English.** A small local Windows tool that compresses PNGs in a folder. You can run a **side-by-side comparison of three engines** (they are not chained) to see which result is smaller and whether the quality is acceptable. It is meant for game art, UI slices, and local batch jobs. **Images are never uploaded**; everything stays on your machine.

## 功能

1. **三方案对比（推荐）**  
   选择含 PNG 的文件夹后开始处理。**不覆盖原图**。在同级生成 `文件夹名_对比/`：
   - `oxipng/` — 无损重打包
   - `pngquant/` — 有损减色
   - `pngdeer/` — 感知质量自动搜调色板  
   另有 `对比结果.csv` / `对比结果.txt`，界面表格会标出体积最小的方案。

2. **单方案原位替换**  
   只选一个引擎；**仅在压缩后更小时**覆盖原文件。不会自动备份，请先自行备份。

说明：有损不一定比无损更小；不同图片的赢家可能不同，请用对比模式看结果。

**English — Features.**

1. **Compare three engines (recommended).** Pick a folder of PNGs and start. **Originals are not overwritten.** A sibling folder `文件夹名_对比/` is created with `oxipng/` (lossless repack), `pngquant/` (lossy palette reduction), and `pngdeer/` (perceptual quality / automatic palette search), plus `对比结果.csv` and `对比结果.txt`. The table highlights the smallest result.
2. **Single-engine in-place replace.** One engine only. The original file is replaced **only when the compressed file is smaller**. There is no automatic backup; copy your files first.

Lossy is not always smaller than lossless. Different images can prefer different engines, so use compare mode to judge.

## 快速使用（Windows 预编译）

1. 从 [Releases](https://github.com/sTarrr13/pngCompressor/releases) 下载 `PNG压缩工具.zip`（若已发布）
2. 解压后双击 `PNG压缩器.exe`（保持 `_internal`、`bin` 与 EXE 同目录）
3. 选模式 → 选文件夹 → 开始处理

也可直接运行源码（需本机 Python 3，并将引擎放到 `bin/`）：

```bash
python png_compressor.py
```

命令行对比样例见 `compare_cli.py`。

**English — Quick start.** Download `PNG压缩工具.zip` from [Releases](https://github.com/sTarrr13/pngCompressor/releases), unzip it, and run `PNG压缩器.exe`. Keep `_internal` and `bin` next to the EXE. Choose a mode, choose a folder, then start. To run from source you need Python 3 and the engines in `bin/`: `python png_compressor.py`. See `compare_cli.py` for a command-line compare example.

## 引擎说明

| 方案 | 类型 | 默认参数思路 |
|------|------|----------------|
| [oxipng](https://github.com/oxipng/oxipng) | 无损 | `-o 4 --strip safe` |
| [pngquant](https://pngquant.org/) | 有损减色 | `--quality=80-95 --nofs`（失败再试 65-90） |
| [pngdeer](https://github.com/pngdeer/pngdeer) | 感知质量 / 自动调色板 | `pngdeer in.png -o out.png` |

可执行文件放在 `bin/`：`oxipng.exe`、`pngquant.exe`、`pngdeer.exe`（pngdeer 可选；没有则对比只跑前两个）。

**English — Engines.**

| Engine | Kind | Default idea |
|--------|------|----------------|
| [oxipng](https://github.com/oxipng/oxipng) | Lossless | `-o 4 --strip safe` |
| [pngquant](https://pngquant.org/) | Lossy color reduction | `--quality=80-95 --nofs` (retry `65-90` on failure) |
| [pngdeer](https://github.com/pngdeer/pngdeer) | Perceptual quality / automatic palette | `pngdeer in.png -o out.png` |

Put `oxipng.exe`, `pngquant.exe`, and `pngdeer.exe` in `bin/`. pngdeer is optional; without it, compare runs only the first two.

## 开源与第三方引用

本仓库中的 GUI / 脚本（如 `png_compressor.py`）以 **MIT License** 授权，见 [LICENSE](LICENSE)。

压缩能力来自下列独立项目（**本工具只是调用它们，算法版权归原作者**）：

| 组件 | 协议概要 | 项目 |
|------|----------|------|
| oxipng | Apache-2.0 / MIT | https://github.com/oxipng/oxipng |
| pngquant / libimagequant | **GPL-3.0+**，闭源/商用产品需另购[商业授权](https://pngquant.org/licensing.html) | https://pngquant.org/ · https://github.com/ImageOptim/libimagequant |
| pngdeer | MIT | https://github.com/pngdeer/pngdeer |

- **用本工具压出来的 PNG 文件本身**，不受上述引擎协议约束。  
- **再分发本工具（含预编译包）时**：请保留本 README / `THIRD_PARTY.md` 中的归属说明；若你的产品是闭源或 SaaS 且内置 pngquant/libimagequant，请自行确认并遵守其 GPL 或购买商业许可。  
- 预编译包中的 `bin/*.exe` 为各上游项目的构建产物，仅便于本机使用；版本与完整许可证文本以各上游仓库为准。

更细的归属与免责见 [THIRD_PARTY.md](THIRD_PARTY.md)。

**English — Third-party licenses.** The GUI and scripts in this repo (such as `png_compressor.py`) are **MIT**, see [LICENSE](LICENSE). Compression comes from separate projects; **this tool only invokes them, and the algorithms remain the authors'**:

| Component | License (summary) | Project |
|-----------|-------------------|---------|
| oxipng | Apache-2.0 / MIT | https://github.com/oxipng/oxipng |
| pngquant / libimagequant | **GPL-3.0+**; closed-source or commercial products need a separate [commercial license](https://pngquant.org/licensing.html) | https://pngquant.org/ · https://github.com/ImageOptim/libimagequant |
| pngdeer | MIT | https://github.com/pngdeer/pngdeer |

PNG files produced by this tool are not themselves bound by those engine licenses. If you redistribute this tool (including the prebuilt package), keep the attribution in this README and `THIRD_PARTY.md`. If a closed-source or SaaS product embeds pngquant/libimagequant, check the GPL terms or buy a commercial license yourself. The `bin/*.exe` files in the prebuilt package are upstream build artifacts for local use; versions and full license texts follow each upstream repo. Details: [THIRD_PARTY.md](THIRD_PARTY.md).

## 仓库内容

| 路径 | 说明 |
|------|------|
| `png_compressor.py` | 主程序（tkinter GUI） |
| `compare_cli.py` | 命令行对比辅助 |
| `使用说明.txt` | 中文简要说明 |
| `LICENSE` | 本仓库脚本的 MIT 许可 |
| `THIRD_PARTY.md` | 第三方开源引用 |

预编译 Windows 包（含 `_internal` 与 `bin`）通过 **GitHub Release** 提供，不放入源码树，以免仓库过大。

**English — Repository layout.** `png_compressor.py` is the tkinter GUI, `compare_cli.py` is the command-line compare helper, `使用说明.txt` is a short Chinese guide, `LICENSE` is the MIT license for these scripts, and `THIRD_PARTY.md` is the third-party attribution. The Windows prebuilt package (`_internal` and `bin` included) is published as a **GitHub Release**, not in the source tree.

## 免责声明

按「原样」提供，作者不对压缩结果、数据丢失或第三方引擎许可合规承担保证责任。正式商用前请自行备份原图并核对各引擎许可。

**English — Disclaimer.** Provided as is. The author does not guarantee compression results, against data loss, or that your use of the third-party engines is license-compliant. Back up originals and check each engine's license before commercial use.
