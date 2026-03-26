frappe.listview_settings["Employee Benefit Ledger"] = {
	formatters: {
		transaction_type: function (value) {
			if (value === "Accrual") {
				return '<span class="indicator-pill blue">' + __(value) + "</span>";
			} else if (value === "Payout") {
				return '<span class="indicator-pill orange">' + __(value) + "</span>";
			}
			return value;
		},
	},
};
