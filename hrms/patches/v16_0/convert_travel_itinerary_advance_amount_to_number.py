import re

import frappe
from frappe import _
from frappe.utils import flt


def execute():
	if not frappe.db.has_column("Travel Itinerary", "advance_amount"):
		return

	rows = frappe.db.sql(
		"""select name, parent, advance_amount from `tabTravel Itinerary`
		where ifnull(advance_amount, '') != ''""",
		as_dict=True,
	)

	for row in rows:
		value = row.advance_amount.strip()
		try:
			amount = float(value)
		except ValueError:
			numbers = re.findall(r"\d+(?:\.\d+)?", value.replace(",", ""))
			amount = flt(numbers[0]) if len(numbers) == 1 else 0
			if frappe.db.exists("Travel Request", row.parent):
				frappe.get_doc("Travel Request", row.parent).add_comment(
					"Comment",
					_(
						"Itinerary Advance Amount {0} was converted to {1} when the field became a number."
					).format(frappe.bold(value), frappe.bold(amount)),
				)

		frappe.db.sql(
			"update `tabTravel Itinerary` set advance_amount = %s where name = %s", (str(amount), row.name)
		)
