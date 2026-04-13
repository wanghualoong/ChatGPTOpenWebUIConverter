# ChatGPT -> OpenWebUI Converter

中文 | English

跨平台工具（Windows / macOS）：
- 将 ChatGPT 导出文件（`.zip` 或 `conversations.json`）转换为 OpenWebUI 可导入 JSON
- 支持命令行与图形界面
- 用户在 OpenWebUI 页面手动导入（无需 API key）

Cross-platform tool (Windows / macOS):
- Convert ChatGPT export (`.zip` or `conversations.json`) into OpenWebUI-importable JSON
- Supports both CLI and GUI
- Users import manually in OpenWebUI (no API key required)

目标版本 / Target:
- OpenWebUI `v0.8.12`

## 快速开始 | Quick Start

### 1) 命令行一键运行（自动建环境 + 自动装依赖）
### 1) CLI one-command run (auto venv + dependency install)

macOS:

```bash
./run.sh prepare --input /path/to/chatgpt_export.zip --output openwebui_import.json
```

Windows (CMD):

```bat
run.bat prepare --input C:\path\to\chatgpt_export.zip --output openwebui_import.json
```

### 2) 图形界面运行（开发态）
### 2) Run GUI (dev mode)

macOS:

```bash
python3 bootstrap.py
```

Windows:

```bat
py -3 bootstrap.py
```

## Windows MSI 打包 | Windows MSI Build

本地 PowerShell 构建 / Build locally with PowerShell:

```powershell
cd chatgpt-openwebui-migrator
powershell -ExecutionPolicy Bypass -File .\build_windows_msi.ps1
```

输出 / Output:
- `dist\*.msi`

## GitHub Actions 自动构建 MSI | Build MSI via GitHub Actions

工作流文件 / Workflow:
- `.github/workflows/build-windows-msi.yml`

触发方式 / Trigger:
- 手动：`Actions -> Build Windows MSI -> Run workflow`
- 自动：push/PR 修改核心文件时触发

产物 / Artifact:
- `windows-msi`

## macOS DMG 打包 | macOS DMG Build

```bash
cd /Users/hw278/chatgpt-openwebui-migrator
./build_macos_dmg.sh
```

输出 / Output:
- `dist/ChatGPTOpenWebUIConverter.dmg`

## 在 OpenWebUI 导入 | Import in OpenWebUI

1. 打开 OpenWebUI / Open OpenWebUI
2. `Settings`
3. `Data Controls`
4. `Import Chats`
5. 选择生成的 `openwebui_import.json`

## 发布文件 | Release Files

仓库内路径 / In-repo path:
- `releases/ChatGPTOpenWebUIConverter-1.0.0-win64.msi`
- `releases/ChatGPTOpenWebUIConverter.dmg`
- `releases/SHA256SUMS.txt`

## 说明 | Notes

- ChatGPT 导出需先在官网手动触发并下载。
- 本工具不处理 ChatGPT 登录流程。
- 本工具不调用 OpenWebUI API，适合多用户各自导入。

- ChatGPT export must be requested and downloaded manually from the ChatGPT website.
- This tool does not handle ChatGPT sign-in.
- This tool does not call OpenWebUI API; it is designed for per-user manual import.
