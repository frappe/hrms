frappe.listview_settings["Expense Claim"] = {
<<<<<<< HEAD
	add_fields: ["total_claimed_amount", "docstatus", "company"],
	get_indicator: function (doc) {
		if (doc.status == "Paid") {
			return [__("Paid"), "green", "status,=,Paid"];
		} else if (doc.status == "Unpaid") {
			return [__("Unpaid"), "orange", "status,=,Unpaid"];
		} else if (doc.status == "Rejected") {
			return [__("Rejected"), "grey", "status,=,Rejected"];
		}
	},
=======
	add_fields: ["company"],
>>>>>>> da17577dc (chore: remove unused import)
};
