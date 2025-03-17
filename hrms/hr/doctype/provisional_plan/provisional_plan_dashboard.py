from frappe import _


def get_data():
	return {
		"fieldname": "provisional_plan",
		"transactions": [
			{"label": _("Reference"), "items": ["Shift Assignment" ]},

		],
	}
