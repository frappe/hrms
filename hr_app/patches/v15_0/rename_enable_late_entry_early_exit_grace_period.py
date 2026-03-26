from frappe.model.utils.rename_field import rename_field


def execute():
	try:
		rename_field("Shift Type", "enable_entry_grace_period", "enable_late_entry_marking")
		rename_field("Shift Type", "enable_exit_grace_period", "enable_early_exit_marking")

	except Exception as e:
		if e.args[0] != 1054:
			raise
