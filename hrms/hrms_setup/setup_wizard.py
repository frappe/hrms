# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _

from hrms.hrms_setup.demo import setup_demo_data


def get_setup_stages(args=None):
	stages = [
		{
			"status": _("Creating Demo Company and Organization"),
			"fail_msg": _("Failed to create Demo Company and Organization"),
			"tasks": [{"fn": setup_demo_data, "args": args, "fail_msg": _("Failed to create HR Demo Data")}],
		},
	]

	return stages
