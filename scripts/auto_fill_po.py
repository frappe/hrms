#!/usr/bin/env python3
"""
Simple script to fill empty msgstr in a .po file by copying msgid as fallback.
Usage:
    python3 scripts/auto_fill_po.py hrms/locale/vi.po hrms/locale/vi.autofill.po
"""
import sys
from pathlib import Path

def fill_po(in_path: Path, out_path: Path):
    with in_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('msgid'):
            # capture msgid block (could be multi-line)
            msgid_lines = [line]
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                msgid_lines.append(lines[i])
                i += 1
            # next should be msgstr
            if i < len(lines) and lines[i].startswith('msgstr'):
                msgstr_line = lines[i]
                if msgstr_line.strip() == 'msgstr ""':
                    # construct msgid text
                    msgid_text = ''
                    for l in msgid_lines:
                        if l.startswith('msgid'):
                            part = l[len('msgid'):].strip()
                        else:
                            part = l.strip()
                        # strip surrounding quotes
                        if part.startswith('"') and part.endswith('\n'):
                            part = part[:-1]
                        if part.startswith('"') and part.endswith('"'):
                            part = part[1:-1]
                        msgid_text += part
                    # escape quotes in msgid_text
                    escaped = msgid_text.replace('"', '\\"')
                    out_lines.extend(msgid_lines)
                    out_lines.append(f'msgstr "{escaped}"\n')
                    i += 1
                    continue
                else:
                    out_lines.extend(msgid_lines)
                    out_lines.append(msgstr_line)
                    i += 1
                    continue
            else:
                out_lines.extend(msgid_lines)
                continue
        else:
            out_lines.append(line)
            i += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as f:
        f.writelines(out_lines)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 scripts/auto_fill_po.py INPUT_PO OUTPUT_PO')
        sys.exit(1)
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    fill_po(in_path, out_path)
    print(f'Wrote {out_path}')
