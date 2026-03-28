# dekapu-osc-clicker

这是一个用于 VRChat OSC 的桌面工具，带图形界面，支持自动点击、读取 VRChat 日志中的 DSM SaveURL、提取 `sp` 并自动发送到 VRChat 聊天框。

## 功能

- 图形界面操作
- `F1` 开始点击
- `F2` 停止点击
- 自动发送 `/input/UseRight`
- 点击间隔可在运行中立即生效
- 选择 VRChat 日志目录后自动保存
- 自动监听最新 `output_log_*.txt`
- 发现新的 `[DSM SaveURL] Generated URL:` 后自动提取 `sp`
- 自动发送聊天框消息，支持中文 / 英语 / 日语轮换
- 可勾选要参与发送的语言：中文 / 英语 / 日语
- 英语使用 `K / M / B / T` 单位
- 中文使用 `万 / 亿 / 万亿` 单位
- 日语使用 `万 / 億 / 兆` 单位
- GitHub Actions Release 打包时可将版本号注入窗口标题

## 环境要求

- Python 3.10+
- Windows
- VRChat 本地 OSC 可用

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行方式

兼容旧入口：

```bash
python dekapu_osc_clicker.py
```

包入口：

```bash
python -m dekapu_osc_clicker
```

## 使用说明

1. 启动程序
2. 在“点击间隔（秒）”里输入间隔
3. 点击“浏览”选择 VRChat 日志目录
4. 点击“开始”或按 `F1` 开始点击
5. 点击“停止”或按 `F2` 停止点击
6. 勾选“自动监听最新日志并发送SP”启用自动监听
7. 在界面中勾选要参与发送的语言：中文 / 英语 / 日语

## 日志目录说明

请选择包含以下日志文件的目录：

```text
output_log_*.txt
```

常见路径类似：

```text
C:\Users\你的用户名\AppData\LocalLow\VRChat\VRChat
```

## 自动监听说明

程序会：

1. 找到最新的 `output_log_*.txt`
2. 监听新追加的日志行
3. 匹配 `[DSM SaveURL] Generated URL:`
4. 读取 URL 中的 `data` 参数
5. base64 解码并解析 JSON
6. 取出 `sp`
7. 按当前勾选的语言顺序发送聊天框消息，例如：中文 -> 英语 -> 日语

监听从当前文件末尾开始，不会重复发送旧日志。

## 配置文件

程序会在当前程序同目录生成：

```text
settings.json
```

当前用于保存：

- `log_dir`

## 项目结构

```text
.
├─ README.md
├─ requirements.txt
├─ settings.json
├─ dekapu_osc_clicker.py
└─ dekapu_osc_clicker/
   ├─ __init__.py
   ├─ __main__.py
   ├─ app.py
   ├─ clicker.py
   ├─ constants.py
   ├─ dsm_parser.py
   ├─ log_monitor.py
   ├─ osc_client.py
   ├─ settings.py
   └─ ui.py
```

## 打包与 Release

本地打包：

```powershell
./build.ps1
```

带版本号打包：

```powershell
./build.ps1 -Version v1.0.0
```

打包生成的可执行文件为：

```text
dist/dekapu-osc-clicker.exe
```

当通过 GitHub Actions 的手动 Release 工作流打包时：

- 工作流会使用输入的 `tag` 作为 Release 版本号
- 生成的 Release 附件文件名为 `dekapu-osc-clicker-<tag>-windows.exe`
- 程序窗口标题会自动包含该版本号
- Release 内容会自动附带与上一个版本之间的 diff 日志

## 常见问题

### 1. 监听后没有发送聊天框消息
- 确认 VRChat 已开启 OSC
- 确认日志目录选择正确
- 确认最新日志里确实出现了 `[DSM SaveURL] Generated URL:`

### 2. 热键没反应
- 某些环境下 `keyboard` 可能需要更高权限运行
- 确认没有被其他程序占用 F1/F2

### 3. 找不到日志文件
- 确认选择的是 VRChat 的日志目录，而不是上一级目录

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 说明

当前项目已经按模块拆分，便于后续继续维护、打包和扩展。
