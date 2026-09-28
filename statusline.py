#!/usr/bin/env python3
"""Claude Code 状态栏：目录 │ 模型+窗口 │ 上下文剩余 │ Token 吞吐 │ API 耗时

Token 全量吞吐 = input + cache_creation + cache_read + output，按消息 id 去重，
从会话 transcript（含子代理 transcript）增量解析。
当天统计按 ~/.claude/statusline-data/days/<日期>/<session_id>.json 汇总所有会话。
"""
import glob
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime

DATA = os.path.expanduser('~/.claude/statusline-data')
KEEP_DAYS = 7
USAGE_KEYS = ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens')

DIM, RESET = '\033[2m', '\033[0m'
BLUE, CYAN, GREEN, YELLOW, RED, MAGENTA = (f'\033[{c}m' for c in (34, 36, 32, 33, 31, 35))
# Token / 耗时：本会话用亮色加粗突出，当天用同色系的柔和色
TOK_SESS, TOK_DAY = '\033[1;38;5;213m', '\033[38;5;139m'
API_SESS, API_DAY = '\033[1;38;5;221m', '\033[38;5;137m'


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f'{path}.{os.getpid()}.tmp'
    with open(tmp, 'w') as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def local_day(ts):
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone().strftime('%Y-%m-%d')
    except Exception:
        return None


def scan(path, st, today):
    """增量解析 transcript，把每条消息的全量 token 记到其时间戳所在日期。"""
    offset = st.get('offset', 0)
    if offset > os.path.getsize(path):  # 文件被重写，重新统计
        st.clear()
        offset = 0
    with open(path, 'rb') as f:
        f.seek(offset)
        chunk = f.read()
    end = chunk.rfind(b'\n')
    if end < 0:
        return
    st['offset'] = offset + end + 1
    days = st.setdefault('days', {})
    recent = st.setdefault('recent', [])  # 最近的 [msg_id, day, tokens]，流式写入同一消息会有多行
    for line in chunk[:end].split(b'\n'):
        if b'"usage"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get('message')
        if not isinstance(m, dict) or not isinstance(m.get('usage'), dict):
            continue
        n = sum(m['usage'].get(k) or 0 for k in USAGE_KEYS)
        mid = m.get('id')
        prev = next((r for r in recent if mid and r[0] == mid), None)
        if prev:
            days[prev[1]] = days.get(prev[1], 0) - prev[2] + n
            prev[2] = n
        else:
            day = local_day(d.get('timestamp') or '') or today
            days[day] = days.get(day, 0) + n
            recent.append([mid, day, n])
            del recent[:-50]


def cleanup():
    cutoff = time.time() - KEEP_DAYS * 86400
    for p in glob.glob(f'{DATA}/days/*') + glob.glob(f'{DATA}/sessions/*.json'):
        try:
            if os.path.getmtime(p) < cutoff:
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        except OSError:
            pass


def fmt_tokens(n):
    for unit, div in (('B', 1e9), ('M', 1e6), ('k', 1e3)):
        if n >= div:
            v = n / div
            return f'{v:.1f}'.rstrip('0').rstrip('.') + unit
    return str(int(n))


def fmt_ms(ms):
    s = int(ms // 1000)
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    if h:
        return f'{h}h{m:02d}m'
    if m:
        return f'{m}m{s:02d}s'
    return f'{s}s'


def main():
    data = json.load(sys.stdin)
    today = datetime.now().strftime('%Y-%m-%d')
    sid = data.get('session_id') or 'unknown'

    # ---- Token / 耗时统计 ----
    stats_ok = True
    sess_tokens = today_tokens = sess_api_ms = today_api_ms = 0
    try:
        if not os.path.isdir(f'{DATA}/days/{today}'):
            cleanup()
        sess_path = f'{DATA}/sessions/{sid}.json'
        day_path = f'{DATA}/days/{today}/{sid}.json'
        sess = load(sess_path, {'files': {}, 'api_ms': 0})

        tp = data.get('transcript_path') or ''
        files = [tp] if os.path.isfile(tp) else []
        if tp.endswith('.jsonl'):
            files += glob.glob(os.path.join(tp[:-6], '**', '*.jsonl'), recursive=True)
        for p in files:
            scan(p, sess['files'].setdefault(p, {}), today)
        sess_tokens = sum(sum(st.get('days', {}).values()) for st in sess['files'].values())

        # API 耗时只有会话累计值，按增量记入当天；值变小说明计数重置（如 resume）
        sess_api_ms = int((data.get('cost') or {}).get('total_api_duration_ms') or 0)
        last = sess.get('api_ms', 0)
        delta = sess_api_ms - last if sess_api_ms >= last else sess_api_ms
        sess['api_ms'] = sess_api_ms

        day = load(day_path, {'tokens': 0, 'api_ms': 0})
        day['tokens'] = sum(st.get('days', {}).get(today, 0) for st in sess['files'].values())
        day['api_ms'] = day.get('api_ms', 0) + delta
        save(sess_path, sess)
        save(day_path, day)

        for p in glob.glob(f'{DATA}/days/{today}/*.json'):
            rec = load(p, {})
            today_tokens += rec.get('tokens', 0)
            today_api_ms += rec.get('api_ms', 0)
    except Exception:
        stats_ok = False

    # ---- 目录 ----
    cwd = (data.get('workspace') or {}).get('current_dir') or data.get('cwd') or os.getcwd()
    home = os.path.expanduser('~')
    if cwd == home or cwd.startswith(home + os.sep):
        cwd = '~' + cwd[len(home):]

    # ---- 模型 + 窗口 ----
    model = data.get('model') or {}
    name = model.get('display_name') or model.get('id') or '?'
    name = re.sub(r'\s*\([^)]*context[^)]*\)\s*$', '', name, flags=re.I)
    ctx = data.get('context_window') or {}
    size = ctx.get('context_window_size') or 0
    size_s = fmt_tokens(size) if size else '?'

    # ---- 上下文 ----
    used = ctx.get('total_input_tokens') or 0
    remain = ctx.get('remaining_percentage')
    if remain is None:
        remain = max(0.0, 100 - used * 100 / size) if size else 100
    color = GREEN if remain > 50 else YELLOW if remain > 20 else RED

    sep = f' {DIM}│{RESET} '
    parts = [
        f'{BLUE}📁 {cwd}{RESET}',
        f'{CYAN}🤖 {name} [{size_s}]{RESET}',
        f'{color}🧠 {remain:.0f}% ({fmt_tokens(used)}/{size_s}){RESET}',
    ]
    if stats_ok:
        parts += [
            f'🪙 {TOK_SESS}{fmt_tokens(sess_tokens)}{RESET}{DIM}/{RESET}{TOK_DAY}{fmt_tokens(today_tokens)}{RESET}',
            f'⏱️ {API_SESS}{fmt_ms(sess_api_ms)}{RESET}{DIM}/{RESET}{API_DAY}{fmt_ms(today_api_ms)}{RESET}',
        ]
    else:
        parts += ['🪙 --', '⏱️ --']
    print(sep.join(parts))


if __name__ == '__main__':
    main()
