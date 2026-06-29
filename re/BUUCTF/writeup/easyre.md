# easyre Writeup

打开 IDA 后，加载可执行文件时会看到三个选项，下面按用途说明

## 1 `Portable executable for AMD64 (PE) [pe.dll]`

这是最常用且通常默认的选项（针对 `.exe` / `.dll`）

- 含义：按 Windows PE 标准格式解析文件
- 结果：自动识别文件头（Header）、代码段（`.text`）、数据段（`.data`）、导入表（Imports）、导出表（Exports）
- 优势：可自动标注函数名、库调用（如 `printf`、`MessageBox`）和全局变量，分析效率最高

## 2 `MS-DOS executable (EXE) [dos.dll]`

这是兼容性选项，适用于 16 位 DOS 程序

- 含义：把文件当作早期 DOS 可执行程序处理
- 结果：尝试解析 DOS 头和实模式段地址映射
- 注意：现代 64 位程序（如 `easyre.exe`）选这个通常会导致反汇编结果错误

### 什么时候用 `MS-DOS executable`

仅在非常老的 16 位场景中使用：

- DOS 时代软件分析（例如早期 `.exe` 游戏或工具）
- Bootloader 或引导代码分析（模拟 DOS 加载环境）
- 部分 CTF 怀旧题（考查 `CS` / `DS` / `SS` 等段寄存器概念）

## 3 `Binary file`

这是无格式的底层加载方式

- 含义：不解析文件头，直接把文件视为原始二进制数据
- 结果：没有自动段名、无导入导出信息，需要手动指定基地址和架构

### 什么时候用 `Binary file`

典型场景如下：

1. 分析 Shellcode：没有 PE 头，只能手动指定架构（`x86` / `x64`）
2. 分析固件（Firmware）：如路由器、嵌入式、IoT 固件 dump，通常无标准文件头
3. 分析内存转储（Memory Dump）：头损坏或被改写，自动解析失败时可强制查看指令
4. 恶意代码去壳或脱壳：样本故意破坏 PE 头时，可用 Binary 模式手动修复分析

## Process

1. 打开样本后按 `Shift + F12` 进入字符串窗口
2. 按 `Ctrl + F` 搜索字符串 `flag`
3. 定位到关键字符串并得到答案

## 快速结论

对于 Windows 平台的现代可执行文件（`.exe`、`.dll`、`.sys`）：

- 默认优先选择 `Portable Executable (PE)`
- 只有在老 16 位程序时考虑 `MS-DOS executable`
- 文件头损坏或非标准二进制（如 shellcode、固件）时选择 `Binary file`

## 总结

可以学会根据文件类型选择加载方式，并掌握字符串窗口的基础查询操作
