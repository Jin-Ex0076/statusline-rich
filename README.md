# statusline-rich

一个信息丰富、带图标和颜色的 **Claude Code 状态栏（statusLine）**。一行展示：当前目录、模型（含上下文窗口大小）、上下文剩余百分比、本次会话花费、以及 API 耗时。

```
📁 ~/claude | 🤖 Opus 4.8 (1M context) | 🧠 95% left (45k/1000k) | 💰 $0.42 | ⏱ 2m5s
```

> 终端里各段带颜色：目录=青色，模型=品红，上下文=绿色，花费=黄色，耗时=蓝色，分隔符 `|` 为暗色。

## 展示的内容

| 段 | 图标 | 含义 |
|----|------|------|
| 目录 | 📁 | 当前工作目录（`$HOME` 显示为 `~`） |
| 模型 | 🤖 | 模型名 + 上下文窗口大小（`1M context` / `200k context`），**自动去重**，不会出现两个 `(… context)` |
| 上下文 | 🧠 | 剩余百分比 + `已用k / 总量k` |
| 花费 | 💰 | 本次会话累计花费（美元，按官方定价估算） |
| 耗时 | ⏱ | 本次会话真正等 API 响应的时长（不含思考/打字时间） |

## 依赖

- [`jq`](https://jqlang.github.io/jq/)（解析 Claude Code 传入的 JSON）
  - macOS：`brew install jq`
  - Debian/Ubuntu：`sudo apt install jq`

## 安装

### 方式 A：作为 skill（推荐）

Clone 到 Claude Code 的 skills 目录：

```bash
git clone https://github.com/Jin-Ex0076/statusline-rich.git ~/.claude/skills/statusline-rich
```

然后对 Claude Code 说一句「用 statusline-rich 装状态栏」（或 `/statusline-rich`），它会读 `SKILL.md` 自动完成：检查 `jq` → 拷贝脚本 → 写入 `settings.json` → 验证。

### 方式 B：手动安装

```bash
# 1. 拷贝脚本
cp statusline-command.sh ~/.claude/statusline-command.sh
chmod +x ~/.claude/statusline-command.sh

# 2. 写入 ~/.claude/settings.json 的 statusLine 字段（需要 jq）
tmp=$(mktemp)
jq '.statusLine = {"type":"command","command":"bash ~/.claude/statusline-command.sh"}' \
  ~/.claude/settings.json > "$tmp" && mv "$tmp" ~/.claude/settings.json
```

下次与 Claude Code 交互时即生效。

## 自定义

脚本 `statusline-command.sh` 结构清晰、注释完整，常见改动：

- **只显示目录名**（不显示完整路径）：把 `dir` 改成 `${dir##*/}`
- **删掉某段**：在末尾 `printf` 里去掉对应的占位符与参数即可
- **换颜色**：修改顶部 `C_DIR` / `C_MODEL` / `C_CTX` / `C_COST` / `C_TIME` 的 ANSI 码
- **花费保留 4 位小数**：把 `printf '%.2f'` 改成 `'%.4f'`

## 说明

- 💰 金额按 Anthropic 官方定价估算；若你走第三方中转（自定义 `ANTHROPIC_BASE_URL`），实际扣费可能不同，当参考值看。
- ⏱ 用的是 `total_api_duration_ms`（真正等 API 的时间），不含你阅读/思考/打字的时间。

## License

MIT
