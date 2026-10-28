# 第三方开源软件声明

本工具在运行时调用下列第三方程序。算法与实现版权归各原作者所有；下列信息便于合规引用，**不能替代**各项目官方许可证全文。

## oxipng

- 用途：PNG 无损优化 / 重打包  
- 项目：https://github.com/oxipng/oxipng  
- 许可：Apache License 2.0 与 MIT（以官方仓库为准）  
- 本工具调用方式：命令行子进程（如 `-o 4 --strip safe`）

## pngquant / libimagequant

- 用途：PNG 有损量化（减色）压缩  
- 网站：https://pngquant.org/  
- libimagequant：https://github.com/ImageOptim/libimagequant  
- 许可：双许可 — **GPL-3.0 或更高版本**；闭源软件、部分分发方式及商业产品需购买商业授权，详见 https://pngquant.org/licensing.html  
- 本工具调用方式：命令行子进程（如 `--quality=80-95 --nofs`）  
- 注意：将本工具或 libimagequant **嵌入闭源/SaaS 产品**前，请自行评估 GPL 义务或购买商业许可。

## pngdeer

- 用途：基于感知质量（如 SSIMULACRA2 相关思路）的 PNG 压缩 / 调色板搜索  
- 项目：https://github.com/pngdeer/pngdeer  
- 许可：MIT（以官方仓库为准）  
- 本工具调用方式：命令行子进程（`pngdeer <input> -o <output>`）  
- 说明：官方未必提供 Windows 预编译；本仓库 Release 中的 `pngdeer.exe` 若存在，多为交叉编译产物，便于本机使用，版本以 Release 说明为准。

## Python / tkinter / PyInstaller（预编译包）

- GUI：Python 标准库 tkinter  
- Windows 可执行包若由 PyInstaller 打包，还包含 PyInstaller 引导与 Python 运行时；其许可见各对应项目

## 输出文件

经上述工具处理后生成的 PNG 图像文件，**不受**引擎源代码许可证对「衍生作品」规则的自动约束（以各项目 FAQ / 许可页为准，例如 pngquant 说明生成文件不受其许可影响）。仍请尊重图片本身的版权与隐私。
