#!/usr/bin/env python3
import json
from pathlib import Path

p = Path('hrms/locale/vi.po')
if not p.exists():
    print('Input file not found:', p)
    raise SystemExit(1)

text = p.read_text(encoding='utf-8')
lines = text.splitlines()

items = []
for i, line in enumerate(lines):
    if line.startswith('msgstr ""'):
        # walk backwards to find msgid block
        j = i-1
        msgid_parts = []
        while j >= 0:
            l = lines[j]
            if l.startswith('msgid'):
                msgid_parts.insert(0, l)
                break
            elif l.startswith('"'):
                msgid_parts.insert(0, l)
            else:
                break
            j -= 1
        # assemble msgid text
        msgid_text = ''
        for part in msgid_parts:
            if part.startswith('msgid'):
                s = part[len('msgid'):].strip()
            else:
                s = part.strip()
            if s.startswith('"') and s.endswith('"'):
                s = s[1:-1]
            msgid_text += s
        items.append(msgid_text)

out = Path('hrms/locale/vi_to_translate.json')
out.write_text(json.dumps(sorted(list(dict.fromkeys(items))), ensure_ascii=False, indent=2), encoding='utf-8')
print('Wrote', out)
