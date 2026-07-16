---
name: statusline-rich
description: Use when installing or setting up a rich Claude Code statusLine that shows current directory, model with context-window size, context remaining percent, session cost, and API time. Copies the bundled script to ~/.claude and wires it into settings.json.
---

# Rich statusLine

## Overview

Installs a ready-made Claude Code statusLine that renders one line:

```
📁 ~/claude | 🤖 Opus 4.8 (1M context) | 🧠 95% left (45k/1000k) | 💰 $0.42 | ⏱ 2m5s
```

| Segment | Icon | Source field |
|---------|------|--------------|
| Directory (`$HOME` → `~`) | 📁 | `.workspace.current_dir` |
| Model + context size | 🤖 | `.model.display_name` + `.context_window.context_window_size` |
| Context remaining | 🧠 | `.context_window.remaining_percentage` + `total_input_tokens`+`total_output_tokens` / `context_window_size` |
| Session cost (USD) | 💰 | `.cost.total_cost_usd` |
| API time | ⏱ | `.cost.total_api_duration_ms` |

## Install

The script lives next to this SKILL.md as `statusline-command.sh`. Run these steps.

1. **Check `jq` is installed** (the script needs it):
   ```bash
   command -v jq || echo "Install jq first: brew install jq  (or)  apt install jq"
   ```

2. **Copy the script into `~/.claude/` and make it executable:**
   ```bash
   mkdir -p ~/.claude
   cp "<this-skill-dir>/statusline-command.sh" ~/.claude/statusline-command.sh
   chmod +x ~/.claude/statusline-command.sh
   ```
   Replace `<this-skill-dir>` with the folder containing this SKILL.md.

3. **Wire it into `~/.claude/settings.json`** — add (or merge) this top-level key:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "bash ~/.claude/statusline-command.sh"
     }
   }
   ```
   If `settings.json` already exists, merge the `statusLine` key in with `jq` rather than overwriting:
   ```bash
   f=~/.claude/settings.json; [ -f "$f" ] || echo '{}' > "$f"
   tmp=$(mktemp)
   jq '.statusLine = {type:"command", command:"bash ~/.claude/statusline-command.sh"}' "$f" > "$tmp" && mv "$tmp" "$f"
   ```

4. **Verify** it renders before relying on it:
   ```bash
   echo '{"workspace":{"current_dir":"'"$HOME"'/claude"},"model":{"display_name":"Opus 4.8"},"context_window":{"context_window_size":1000000,"remaining_percentage":95,"total_input_tokens":40000,"total_output_tokens":5000},"cost":{"total_cost_usd":0.42,"total_api_duration_ms":125000}}' | bash ~/.claude/statusline-command.sh
   ```
   Expected: `📁 ~/claude | 🤖 Opus 4.8 (1M context) | 🧠 95% left (45k/1000k) | 💰 $0.42 | ⏱ 2m5s`

Takes effect on the next interaction with Claude Code — no restart needed.

## Notes

- **Requires `jq`.** Every segment is parsed with it.
- **`(1M context)` is not doubled.** Some Claude Code versions already put `(1M context)` in `display_name`; the script strips any trailing `(… context)` and re-adds one derived from `context_window_size`, so it always shows exactly once (`1M context` at ≥1,000,000, else `<n>k context`).
- **Cost is an estimate** at Anthropic list pricing. Behind a third-party proxy (`ANTHROPIC_BASE_URL`) the real charge may differ — treat 💰 as a relative indicator.
- **⏱ is API time** (`total_api_duration_ms`), i.e. time spent waiting on the API — not wall-clock session time.

## Customize

- **Show only the folder name** instead of the full path: change the directory line to `dir="${cwd##*/}"`.
- **Drop a segment** (e.g. cost or time): remove its `${SEP}...` piece from the final `printf`.
- **Recolor** a segment: edit the ANSI codes in the `Colors` block at the top of the script.
