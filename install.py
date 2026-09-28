#!/usr/bin/env python3
"""安装 / 卸载 statusline-rich 状态栏。

安装：把同目录的 statusline.py 复制到 ~/.claude/statusline-rich.py，
并在 ~/.claude/settings.json 写入 statusLine 配置（其余配置原样保留）。
可重复执行；settings.json 被 cc-switch 等工具覆盖后再跑一次即可恢复。

用法：python3 install.py [--uninstall]
"""
import json
import os
import shutil
import sys
import time

CLAUDE_DIR = os.path.join(os.path.expanduser('~'), '.claude')
SETTINGS = os.path.join(CLAUDE_DIR, 'settings.json')
TARGET = os.path.join(CLAUDE_DIR, 'statusline-rich.py')
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'statusline.py')


def backup(path):
    dst = base = f'{path}.bak-{time.strftime("%Y%m%d-%H%M%S")}'
    n = 1
    while os.path.exists(dst):
        dst, n = f'{base}-{n}', n + 1
    shutil.copy2(path, dst)
    return dst


def load_settings():
    if not os.path.exists(SETTINGS):
        return {}
    with open(SETTINGS, encoding='utf-8') as f:
        text = f.read().strip()
    return json.loads(text) if text else {}


def save_settings(settings):
    os.makedirs(CLAUDE_DIR, exist_ok=True)
    tmp = SETTINGS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, SETTINGS)


def python_cmd():
    for name in ('python3', 'python'):
        if shutil.which(name):
            return name
    return sys.executable


def install():
    if sys.version_info < (3, 7):
        sys.exit(f'FAIL: 需要 Python 3.7+，当前 {sys.version.split()[0]}')
    try:
        settings = load_settings()
    except json.JSONDecodeError as e:
        sys.exit(f'FAIL: {SETTINGS} 不是合法 JSON（{e}），未做任何修改')

    os.makedirs(CLAUDE_DIR, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    print(f'脚本已安装: {TARGET}')

    want = {'type': 'command', 'command': f'{python_cmd()} "{TARGET}"', 'padding': 0}
    old = settings.get('statusLine')
    if old == want:
        print('settings.json 已是最新配置，无需修改')
    else:
        if os.path.exists(SETTINGS):
            print(f'settings.json 已备份: {backup(SETTINGS)}')
        if old:
            print(f'替换了原有 statusLine: {json.dumps(old, ensure_ascii=False)}')
        settings['statusLine'] = want
        save_settings(settings)
        print(f'已写入 statusLine: {SETTINGS}')
    print('OK')


def uninstall():
    settings = load_settings()
    old = settings.get('statusLine') or {}
    if TARGET in str(old.get('command', '')):
        print(f'settings.json 已备份: {backup(SETTINGS)}')
        del settings['statusLine']
        save_settings(settings)
        print('已移除 statusLine 配置')
    else:
        print('settings.json 中的 statusLine 不是 statusline-rich，未改动')
    if os.path.exists(TARGET):
        os.remove(TARGET)
        print(f'已删除脚本: {TARGET}')
    print('OK')


if __name__ == '__main__':
    uninstall() if '--uninstall' in sys.argv[1:] else install()
