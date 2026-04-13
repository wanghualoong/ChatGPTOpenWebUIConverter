# ChatGPT -> OpenWebUI Migrator

跨平台工具（Windows / macOS）：
1. 将 ChatGPT 导出文件（`.zip` 或 `conversations.json`）转换为 OpenWebUI 可导入 JSON
2. 支持命令行与图形界面
3. 用户在 OpenWebUI 页面手动导入（无需 API key）

适配目标：`OpenWebUI v0.8.12`

## 1) 命令行一键运行（自动建环境 + 自动装依赖）

macOS:

```bash
./run.sh prepare --input /path/to/chatgpt_export.zip --output openwebui_import.json
```

Windows (CMD):

```bat
run.bat prepare --input C:\path\to\chatgpt_export.zip --output openwebui_import.json
```

## 2) 图形界面运行（开发态）

macOS:

```bash
python3 bootstrap.py
```

Windows:

```bat
py -3 bootstrap.py
```

会弹出 GUI，选择输入文件和输出位置后点击 `Convert` 即可。
在应用菜单可查看帮助：
- `Help -> Usage`
- `Help -> About`
- macOS 顶部菜单中的应用 Help 也会跳转到内置帮助内容
支持中英双语：
- 窗口顶部 `语言 / Language` 下拉可切换 `zh-CN` / `en`

## 3) Windows 打包 MSI（安装后图形界面）

在 Windows PowerShell 中执行：

```powershell
cd chatgpt-openwebui-migrator
powershell -ExecutionPolicy Bypass -File .\build_windows_msi.ps1
```

输出位置：`dist\*.msi`

说明：
- 使用 `cx_Freeze` 生成 MSI
- 安装后可从开始菜单启动 `ChatGPT OpenWebUI Converter`


## 3.1) GitHub Actions 自动构建 Windows MSI

已提供工作流文件：`.github/workflows/build-windows-msi.yml`

触发方式：
- 手动触发：GitHub -> `Actions` -> `Build Windows MSI` -> `Run workflow`
- 自动触发：推送/PR 修改 `gui_app.py`、`migrator.py`、`setup_windows.py`、`requirements-build.txt` 等相关文件

产物位置：
- 运行完成后，在该次 workflow 的 `Artifacts` 下载 `windows-msi`
- 解压后得到 `dist/*.msi`

## 4) macOS 打包 DMG（安装后图形界面）

在 macOS 终端执行：

```bash
cd /Users/hw278/chatgpt-openwebui-migrator
./build_macos_dmg.sh
```

输出位置：`dist/ChatGPTOpenWebUIConverter.dmg`

说明：
- 脚本先用 `PyInstaller` 生成 `.app`
- 再用 `hdiutil` 生成 `.dmg`

## 5) OpenWebUI 手动导入

1. 打开 OpenWebUI
2. `Settings`
3. `Data Controls`
4. `Import Chats`
5. 选择生成的 `openwebui_import.json`

## 6) 主要文件

- `migrator.py`: 转换核心逻辑
- `gui_app.py`: 图形界面
- `bootstrap.py`: 自动建 venv、装依赖、启动
- `run.sh` / `run.bat`: 命令行启动器
- `setup_windows.py`: Windows MSI 构建配置
- `build_windows_msi.ps1`: Windows MSI 构建脚本
- `build_macos_dmg.sh`: macOS DMG 构建脚本
- `requirements-build.txt`: 打包依赖

## 7) 注意事项

- ChatGPT 导出需先在 ChatGPT 官网手动触发并下载。
- 本工具不处理 ChatGPT 登录流程。
- 本工具不调用 OpenWebUI API，适合多用户各自导入。
