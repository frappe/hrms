import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import get_korea_phase2_custom_fields


def execute():
	"""Create Korea Phase 2 custom fields on already-installed sites.

	`after_install()` already creates these on fresh installs, but `bench migrate`
	does not call `after_install()` on existing sites. Without this patch, sites
	upgraded from a pre-Phase-2 release will be missing the kr_* custom fields
	on Salary Slip, and `import_year_end_settlement_result()` will fail with
	missing-column errors when calling
	`frappe.db.set_value("Salary Slip", ..., {"kr_prepaid_tax": ...})`.

	The patch is idempotent: `create_custom_fields` skips fields that already
	exist, so re-running it is safe.

	Reference: Codex adversarial review b1ux4hqzf [P1].
	"""
	create_custom_fields(get_korea_phase2_custom_fields(), ignore_validate=True)
