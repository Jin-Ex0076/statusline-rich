#!/usr/bin/env bash
# Rich statusLine for Claude Code.
# Renders one line:
#   📁 <dir> | 🤖 <model> (<ctx>) | 🧠 <pct>% left (<used>/<total>) | 🪙 <tokens> | 💰 $<cost> | ⏱ <api time>
# Claude Code feeds the statusLine JSON payload on stdin. Requires: jq.
# 🪙 token = cumulative full throughput (input+output+cache) summed from the
# session transcript — only ever grows, unaffected by context compaction.

input=$(cat)

# ── Colors ─────────────────────────────────────────────
DIR='\033[36m'    # cyan   – directory
MODEL='\033[35m'  # magenta– model
CTX='\033[32m'    # green  – context remaining
TOK='\033[95m'    # bright magenta – tokens consumed
COST='\033[33m'   # yellow – session cost
TIME='\033[34m'   # blue   – API time
DIM='\033[2m'     # dim    – separators
RST='\033[0m'
SEP="${DIM} | ${RST}"

# ── 📁 Directory ($HOME collapsed to ~) ────────────────
cwd=$(jq -r '.workspace.current_dir // .cwd // empty' <<<"$input")
dir="${cwd/#$HOME/~}"

# ── 🤖 Model (strip any built-in "(… context)" suffix; we add our own) ─
model=$(jq -r '.model.display_name // empty' <<<"$input")
model=$(sed -E 's/[[:space:]]*\([^)]*context\)[[:space:]]*$//' <<<"$model")

# ── Context window ─────────────────────────────────────
size=$(jq -r '.context_window.context_window_size // 0' <<<"$input")
pct=$(jq -r '.context_window.remaining_percentage // 0' <<<"$input")
used=$(jq -r '(.context_window.total_input_tokens // 0) + (.context_window.total_output_tokens // 0)' <<<"$input")

if [ "${size:-0}" -ge 1000000 ]; then
  ctx_label="1M context"
else
  ctx_label="$(( size / 1000 ))k context"
fi
used_k="$(( used / 1000 ))k"
total_k="$(( size / 1000 ))k"
pct_i="${pct%%.*}"

# ── 🪙 Tokens consumed (cumulative full throughput from transcript) ─────
# Sum every request's usage (input + output + cache read + cache creation)
# across the whole session transcript. Stateless: recomputed each refresh,
# so it never falls back when the context window is compacted.
transcript=$(jq -r '.transcript_path // empty' <<<"$input")
if [ -n "$transcript" ] && [ -f "$transcript" ]; then
  tok_total=$(jq -s '[.[] | (.message.usage // .usage) | select(.!=null)
      | ((.input_tokens//0)+(.output_tokens//0)
         +(.cache_read_input_tokens//0)+(.cache_creation_input_tokens//0))] | add // 0' "$transcript")
else
  tok_total=0
fi
tok_total=${tok_total:-0}
if [ "$tok_total" -ge 1000000 ]; then
  tok_fmt=$(awk "BEGIN{printf \"%.1fM\", ${tok_total}/1000000}")
else
  tok_fmt="$(( tok_total / 1000 ))k"
fi

# ── 💰 Session cost (USD, estimated at Anthropic list pricing) ──
cost=$(jq -r '.cost.total_cost_usd // 0' <<<"$input")
cost_fmt=$(printf '%.2f' "$cost")

# ── ⏱ API time (total_api_duration_ms → h/m/s) ─────────
api_ms=$(jq -r '.cost.total_api_duration_ms // 0' <<<"$input")
api_ms="${api_ms%%.*}"
api_s=$(( api_ms / 1000 ))
if [ "$api_s" -ge 3600 ]; then
  dur=$(printf '%dh%02dm' $(( api_s / 3600 )) $(( (api_s % 3600) / 60 )))
elif [ "$api_s" -ge 60 ]; then
  dur="$(( api_s / 60 ))m$(( api_s % 60 ))s"
else
  dur="${api_s}s"
fi

# ── Render ─────────────────────────────────────────────
printf "${DIR}📁 %s${RST}${SEP}${MODEL}🤖 %s (%s)${RST}${SEP}${CTX}🧠 %s%% left (%s/%s)${RST}${SEP}${TOK}🪙 %s tokens${RST}${SEP}${COST}💰 \$%s${RST}${SEP}${TIME}⏱ %s${RST}\n" \
  "$dir" "$model" "$ctx_label" "$pct_i" "$used_k" "$total_k" "$tok_fmt" "$cost_fmt" "$dur"
