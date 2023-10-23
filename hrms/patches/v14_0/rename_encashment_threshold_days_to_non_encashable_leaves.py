from frappe.model.utils.rename_field import rename_field


def execute():
	try:
		rename_field("Leave Type", "encashment_threshold_days", "non_encashable_leaves")

	except Exception as e:
		if e.args[0] != 1054:
			raise
