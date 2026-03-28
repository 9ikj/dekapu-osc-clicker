# Massive Medal Pusher工具

这是一个用于 VRChat OSC 的桌面工具，带图形界面，支持自动左键连点、读取 VRChat 日志中的 DSM SaveURL、提取 `sp` 并自动发送到 VRChat 聊天框。

## 功能

- 图形界面操作
- `F1` 开始连点
- `F2` 停止连点
- 点击间隔可在运行中立即生效
- 选择 VRChat 日志目录后自动保存
- 自动监听最新 `output_log_*.txt`
- 发现新的 `[DSM SaveURL] Generated URL:` 后自动提取 `sp`
- 自动发送聊天框消息，支持中文 / 英语 / 日语轮换
- 英语使用 `K / M / B / T` 单位
- 中文使用 `万 / 亿 / 万亿` 单位
- 日语使用 `万 / 億 / 兆` 单位

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
python vrchat_osc_clicker.py
```

包入口：

```bash
python -m massive_medal_pusher
```

## 使用说明

1. 启动程序
2. 在“点击间隔（秒）”里输入间隔
3. 点击“浏览”选择 VRChat 日志目录
4. 点击“开始”或按 `F1` 开始连点
5. 点击“停止”或按 `F2` 停止连点
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

程序会在项目根目录生成：

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
├─ vrchat_osc_clicker.py
└─ massive_medal_pusher/
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

## 说明

当前项目已经按模块拆分，便于后续继续维护、打包和扩展。
