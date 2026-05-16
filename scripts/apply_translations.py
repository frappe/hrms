#!/usr/bin/env python3
import json
from pathlib import Path

in_po = Path('hrms/locale/vi.autofill.po')
map_file = Path('hrms/locale/vi_translations.json')
out_po = Path('hrms/locale/vi.auto_translate.po')

if not in_po.exists():
    print('Missing', in_po)
    raise SystemExit(1)
if not map_file.exists():
    print('Missing', map_file)
    raise SystemExit(1)

mapping = json.loads(map_file.read_text(encoding='utf-8'))
text = in_po.read_text(encoding='utf-8')

# Replace exact msgstr "<orig>" with msgstr "<translated>" for keys in mapping
for orig, trans in mapping.items():
    # escape double quotes
    esc_orig = orig.replace('"', '\\"')
    esc_trans = trans.replace('"', '\\"')
    text = text.replace(f'msgstr "{esc_orig}"', f'msgstr "{esc_trans}"')

out_po.write_text(text, encoding='utf-8')
print('Wrote', out_po)
