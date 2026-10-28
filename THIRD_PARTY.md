# 第三方开源软件声明 / Third-party open-source notices

本工具在运行时调用下列第三方程序。算法与实现版权归各原作者所有；下列信息便于合规引用，**不能替代**各项目官方许可证全文。

This tool invokes the third-party programs below at runtime. Algorithms and implementations remain copyrighted by their authors. These notes are for attribution only and **do not replace** each project's official license text.

## oxipng

- 用途：PNG 无损优化 / 重打包  
- 项目：https://github.com/oxipng/oxipng  
- 许可：Apache License 2.0 与 MIT（以官方仓库为准）  
- 本工具调用方式：命令行子进程（如 `-o 4 --strip safe`）

Purpose: lossless PNG optimization / repacking. Project: https://github.com/oxipng/oxipng. License: Apache License 2.0 and MIT (follow the official repository). This tool calls it as a command-line subprocess (for example `-o 4 --strip safe`).

## pngquant / libimagequant

- 用途：PNG 有损量化（减色）压缩  
- 网站：https://pngquant.org/  
- libimagequant：https://github.com/ImageOptim/libimagequant  
- 许可：双许可 — **GPL-3.0 或更高版本**；闭源软件、部分分发方式及商业产品需购买商业授权，详见 https://pngquant.org/licensing.html  
- 本工具调用方式：命令行子进程（如 `--quality=80-95 --nofs`）  
- 注意：将本工具或 libimagequant **嵌入闭源/SaaS 产品**前，请自行评估 GPL 义务或购买商业许可。

Purpose: lossy PNG quantization (color reduction). Site: https://pngquant.org/. libimagequant: https://github.com/ImageOptim/libimagequant. License: dual-licensed — **GPL-3.0 or later**; closed-source software, some distribution models, and commercial products need a commercial license, see https://pngquant.org/licensing.html. This tool calls it as a command-line subprocess (for example `--quality=80-95 --nofs`). Before **embedding** this tool or libimagequant in a closed-source or SaaS product, review the GPL obligations or buy a commercial license.

## pngdeer

- 用途：基于感知质量（如 SSIMULACRA2 相关思路）的 PNG 压缩 / 调色板搜索  
- 项目：https://github.com/pngdeer/pngdeer  
- 许可：MIT（以官方仓库为准）  
- 本工具调用方式：命令行子进程（`pngdeer <input> -o <output>`）  
- 说明：官方未必提供 Windows 预编译；本仓库 Release 中的 `pngdeer.exe` 若存在，多为交叉编译产物，便于本机使用，版本以 Release 说明为准。

Purpose: perceptual-quality PNG compression / palette search (related to ideas such as SSIMULACRA2). Project: https://github.com/pngdeer/pngdeer. License: MIT (follow the official repository). This tool calls it as a command-line subprocess (`pngdeer <input> -o <output>`). Upstream may not ship a Windows build; `pngdeer.exe` in this repo's Release, when present, is typically a cross-compiled binary for local use. The version follows the Release notes.

## Python / tkinter / PyInstaller（预编译包 / prebuilt package）

- GUI：Python 标准库 tkinter  
- Windows 可执行包若由 PyInstaller 打包，还包含 PyInstaller 引导与 Python 运行时；其许可见各对应项目

The GUI uses the Python standard-library tkinter. If the Windows executable is packed with PyInstaller, the package also includes the PyInstaller bootloader and the Python runtime. See each of those projects for their licenses.

## 输出文件 / Output files

经上述工具处理后生成的 PNG 图像文件，**不受**引擎源代码许可证对「衍生作品」规则的自动约束（以各项目 FAQ / 许可页为准，例如 pngquant 说明生成文件不受其许可影响）。仍请尊重图片本身的版权与隐私。

PNG image files produced by these tools are **not** automatically subject to the engines' source-license rules on derivative works (follow each project's FAQ or license page; pngquant, for example, states that generated files are not covered by its license). Still respect the copyright and privacy of the images themselves.
