# dekapu-osc-clicker

这是一个用于 VRChat OSC 的桌面工具，带图形界面，支持自动点击、读取 VRChat 日志中的 DSM SaveURL、提取 `sp`（Skill Points）并自动发送到 VRChat 聊天框。

## 功能

- 图形界面操作
- `F1` 开始点击
- `F2` 停止点击
- 自动发送 `/input/UseRight`
- 点击频率（ms）可在运行中立即生效
- 点击频率会自动保存并在下次启动时恢复
- 选择 VRChat 日志目录后自动保存
- 发送语言勾选状态会自动保存并在下次启动时恢复
- 程序启动后自动监听最新 `output_log_*.txt`，直到退出程序才停止
- 发现新的 `[DSM SaveURL] Generated URL:` 后自动提取 `sp`（Skill Points）并写入 SQLite 统计库
- 发送 OSC 聊天框消息可单独开关，不影响日志监听和统计记录
- 自动发送聊天框消息，支持中文 / 英语 / 日语按固定顺序轮换
- 聊天框消息按换行显示“当前 Skill Points（当前SP）”和“今日已用 Skill Points（今日已用SP）”
- 今日已用 Skill Points（今日已用SP）按“当天数据库首条 SP 记录”和“当前 SP”推算，重开软件后仍可继续计算
- 可勾选要参与发送的语言：中文 / 英语 / 日语（至少保留一种）
- 英语使用 `K / M / B / T` 单位
- 中文使用 `万 / 亿 / 万亿` 单位
- 日语使用 `万 / 億 / 兆` 单位
- 内置统计网页，固定端口 `45600`
- 第一页显示今日净增 credit 与“每小时 credit 增减”图表
- 第二页显示 `credit / credit_all / sp / sp_use` 的每小时真实数值（取该小时最后一条记录）
- 统计页支持自动刷新
- 统计页支持本机访问或勾选后局域网访问，并可立即无感重绑
- 统计服务在程序启动时自动启动，不需要先点击“统计”按钮
- GitHub Actions Release 打包时可将版本号注入窗口标题
- 支持最小化到系统托盘，并可从托盘恢复窗口
- 仅允许打开一个实例；重复启动时通过 Windows 单实例互斥与窗口激活机制唤醒并显示已打开的窗口（若原窗口已最小化/在托盘中则直接恢复显示）
- 应用图标与桌面图标统一使用“SP 小助手”图标资源

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
2. 在“点击频率（ms）”里输入数值
3. 点击“浏览”选择 VRChat 日志目录
4. 点击“开始”或按 `F1` 开始点击
5. 点击“停止”或按 `F2` 停止点击
6. 程序会自动监听最新 VRChat 日志并记录统计数据
7. 如需发送 OSC 聊天框消息，保持“发送 OSC 聊天框 SP 消息”勾选
8. 在界面中勾选要参与发送的语言：中文 / 英语 / 日语
9. 点击“统计”打开统计页；也可以在程序启动后直接访问 `http://127.0.0.1:45600/`
10. 如需局域网访问，勾选“允许局域网访问统计页面”后用 `http://<本机IP>:45600/` 访问
11. 点击窗口关闭按钮或最小化时，程序会进入系统托盘；可从托盘菜单重新打开或退出

点击频率当前限制范围：

- 最小：`10 ms`
- 最大：`60000 ms`

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
6. 取出 `sp`（Skill Points）
7. 将解析出的数据写入 `stats.db`
8. 按当天数据库首条 `sp` 与当前 `sp` 推算今日已用 SP
9. 若已开启“发送 OSC 聊天框 SP 消息”，则按固定语言顺序（中文 → 英语 → 日语，仅跳过未勾选语言）发送两行聊天框消息

说明：
- 今日已用SP是本工具基于“当天第一次读取到的当前 SP”和“当前 SP”之间的差值推算出来的
- 它不是游戏官方单独提供的“今日消耗统计”字段

中文示例：

```text
当前SP：1234万
今日已用SP：56万
```

英文示例：

```text
Current SP: 12M
SP Used Today: 560K
```

日文示例：

```text
現在SP:1234万
本日使用SP:56万
```

监听从当前文件末尾开始，不会重复发送旧日志。
因此启动监听后，只有出现新的 DSM SaveURL 日志时才会发送聊天框消息。

## 配置文件

程序会在当前程序同目录生成：

```text
settings.json
```

当前用于保存：

- `log_dir`
- `click_delay_ms`
- `languages`
- `send_enabled`
- `stats_web_allow_lan`

程序会对配置做基础容错：

- 非法点击频率会自动回退/夹紧到允许范围
- 非法语言列表会自动恢复为默认值

## 项目结构

```text
.
├─ README.md
├─ requirements.txt
├─ settings.json
├─ stats.db
├─ dekapu_osc_clicker.py
├─ build.ps1
├─ tools/
│  └─ generate_icon.py
└─ dekapu_osc_clicker/
   ├─ __init__.py
   ├─ __main__.py
   ├─ app.py
   ├─ assets/
   │  ├─ README.txt
   │  └─ sp_assistant_icon.svg
   ├─ clicker.py
   ├─ constants.py
   ├─ dsm_parser.py
   ├─ log_monitor.py
   ├─ osc_client.py
   ├─ settings.py
   ├─ single_instance.py
   ├─ stats_store.py
   ├─ stats_web.py
   ├─ tray.py
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

说明：
- 若 `dekapu_osc_clicker/assets/sp_assistant_icon.ico` 存在，打包后的 exe 会自动使用该图标
- 程序运行时的窗口图标优先使用内嵌 base64 PNG，不依赖外部资源路径；若需要则再回退到 `assets` 中的图标文件
- 系统托盘图标优先使用内嵌图标，若加载失败则回退到 `assets` 中的 `.png`
- 打包时会一并带上 `dekapu_osc_clicker/assets` 资源目录，供 exe 图标生成与额外回退资源使用

当通过 GitHub Actions 的手动 Release 工作流打包时：

- 工作流会使用输入的 `tag` 作为 Release 版本号
- 工作流会先自动生成 `sp_assistant_icon.png` / `sp_assistant_icon.ico`
- 工作流会先执行编译检查，再校验图标资源是否生成成功
- 生成的 Release 附件文件名为 `dekapu-osc-clicker-<tag>-windows.exe`
- 程序窗口标题会自动包含该版本号
- Release 内容会自动附带与上一个版本之间的 diff 日志

## 常见问题

### 1. 监听后没有发送聊天框消息
- 确认 VRChat 已开启 OSC
- 确认日志目录选择正确
- 确认最新日志里确实出现了 `[DSM SaveURL] Generated URL:`
- 若统计页已有数据但聊天框没有发送，检查“发送 OSC 聊天框 SP 消息”是否被取消勾选

### 2. 热键没反应
- 某些环境下 `keyboard` 可能需要更高权限运行
- 确认没有被其他程序占用 F1/F2

### 3. 找不到日志文件
- 确认选择的是 VRChat 的日志目录，而不是上一级目录

### 4. 今日已用SP为什么是 0
- 当天第一次读取到 Skill Points（SP）时，会把这条记录作为今日起点
- 所以第一条消息里的今日已用SP正常就是 0
- 这表示“今天的起始读数”，不是读取失败

### 5. 为什么手动输入 `http://127.0.0.1:45600/` 现在可以直接打开
- 统计服务会在程序启动时自动启动
- 因此不需要先点击程序里的“统计”按钮
- 若勾选“允许局域网访问统计页面”，也可通过 `http://<本机IP>:45600/` 访问

## 术语说明

- `sp` = `Skill Points`
- 文档中的“当前SP”表示当前剩余的 Skill Points
- 文档中的“今日已用SP”表示今日已使用的 Skill Points（按当天第一次读取到的值开始计算）

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 说明

当前项目已经按模块拆分，便于后续继续维护、打包和扩展。
