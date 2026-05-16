**Auto-translate/process .po**

This repo includes a helper script to auto-fill empty `msgstr` entries in a `.po` file by copying the original `msgid` as a fallback.

Usage:

```bash
python3 scripts/auto_fill_po.py hrms/locale/vi.po hrms/locale/vi.autofill.po
```

- `hrms/locale/vi.autofill.po` will be created with `msgstr` filled where previously empty.
- Review `vi.autofill.po` and, if acceptable, replace the original file or merge changes.

If you want actual Vietnamese translations (not fallback), I can run automated translations for the empty entries and produce a reviewed `vi.auto_translate.po` file next.