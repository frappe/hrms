# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _

from hrms.hrms_setup.demo import setup_demo_data


def get_setup_stages(setup_wizard_values=None):
	setup_wizard_values = setup_wizard_values or {}
	stages = []

	if setup_wizard_values.get("setup_demo"):
		stages.append(
			{
				"status": _("Creating HR Demo Data"),
				"fail_msg": _("Failed to create HR Demo Data"),
				"tasks": [
					{
						"fn": setup_demo_data,
						"args": setup_wizard_values,
						"fail_msg": _("Failed to create HR Demo Data"),
					}
				],
			}
		)

	return stages
