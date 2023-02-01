import click

import frappe


def execute():
	frappe_v = frappe.get_attr("frappe" + ".__version__")
	hrms_v = frappe.get_attr("hrms" + ".__version__")

	WIKI_URL = "https://github.com/frappe/hrms/wiki/Changes-to-branching-and-versioning"

	if "14" in frappe_v and "15" in hrms_v:
		click.secho(
			f"""
			The `develop` branch of Frappe HR is no longer compatible with Frappe & ERPNext's `version-14`.
			Since you are using ERPNext/Frappe `version-14` please switch Frappe HR's branch to `version-14` and then proceed with the update.\n\t
			You can switch the branch by following the steps mentioned here: {WIKI_URL}
			""",
			fg="red",
		)

		# don't skip this patch to enforce switching branches
		raise SystemExit(1)
