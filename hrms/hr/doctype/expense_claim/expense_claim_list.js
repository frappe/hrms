<<<<<<< HEAD
frappe.listview_settings['Expense Claim'] = {
	add_fields: ["total_claimed_amount", "docstatus", "company"],
	get_indicator: function(doc) {
		if(doc.status == "Paid") {
			return [__("Paid"), "green", "status,=,Paid"];
		}else if(doc.status == "Unpaid") {
			return [__("Unpaid"), "orange", "status,=,Unpaid"];
		} else if(doc.status == "Rejected") {
			return [__("Rejected"), "grey", "status,=,Rejected"];
		}
	}
};
=======
frappe.listview_settings["Expense Claim"] = {
	add_fields: ["company"]
}
>>>>>>> f7c8f64e2 (fix(Expense Claim): Pass company to properly pick currency for each record (#1335))
