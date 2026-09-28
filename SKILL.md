---
name: statusline-rich
description: Install the statusline-rich Claude Code status bar (cwd, model + context window, context %, session/today token throughput, session/today API wait time). Use when the user asks to install, restore, or uninstall statusline-rich, or when their status bar vanished after a tool like cc-switch rewrote settings.json.
---

# statusline-rich

一键安装的状态栏。本 skill 目录（加载时给出的 base directory）下有两个文件：

- `statusline.py`：状态栏脚本本体，安装时复制为 `~/.claude/statusline-rich.py`。
- `install.py`：安装器。可重复执行，会先备份 `settings.json`，只写入 `statusLine` 一个字段，其余配置原样保留。

## Steps

1. **安装**：运行 `python3 "<base directory>/install.py"`，找不到 `python3` 时用 `python`。用户要卸载时加 `--uninstall`。
   完成标准：输出最后一行是 `OK`。如果以 `FAIL:` 开头，把原因告诉用户，然后停止。
2. **汇报**：把安装器输出的每一项转述给用户，包括脚本路径、备份文件路径，以及是否替换了用户原有的 `statusLine`（如果替换了，要给出原配置，方便用户找回）。
3. **生效**：告诉用户状态栏会在下一条消息后出现，不用重启。如果以后用 cc-switch 这类工具切换供应商后状态栏消失，再调用一次本 skill 就能恢复，因为这类工具会整个重写 `settings.json`。

## Reference：状态栏各段

```
📁 ~/proj │ 🤖 Opus 5 [1M] │ 🧠 87% (130.5k/1M) │ 🪙 573.9k/2.1M │ ⏱️ 3m12s/1h05m
```

| 段 | 含义 |
|---|---|
| 📁 | 当前工作目录 |
| 🤖 | 模型名 + 上下文窗口大小 |
| 🧠 | 上下文剩余百分比（已用/总量）。剩余 >50% 显示绿色，20% 到 50% 黄色，<20% 红色 |
| 🪙 | Token 全量吞吐：本会话 / 当天所有会话。四项相加：input + cache 写入 + cache 读取 + output，同一条消息只算一次，包括子代理 |
| ⏱️ | 等 API 响应的时间：本会话 / 当天所有会话 |

- 统计数据存在 `~/.claude/statusline-data/`，保留 7 天。
- 当天的数字从安装后开始累计。Token 可以按记录文件里的时间戳补算，API 耗时只有会话运行时才拿得到，所以没法补。
- 颜色在 `statusline.py` 开头的常量里（`TOK_SESS` 等，256 色编号）。用户想改颜色时，改 `~/.claude/statusline-rich.py`；想让改动随 skill 一起分享，就同时改本目录的 `statusline.py`。
- 依赖只有 Python 3.7+，不联网。
