frappe.provide("hrms.setup");

frappe.setup.on("before_load", function () {
	if (
		frappe.boot.setup_wizard_completed_apps?.length &&
		frappe.boot.setup_wizard_completed_apps.includes("hrms")
	) {
		return;
	}

	hrms.setup.slides_settings.map(frappe.setup.add_slide);
});

hrms.setup.slides_settings = [
	{
		name: "hr_setup",
		title: __("HR Setup"),
		icon: "fa fa-users",
		fields: [
			{
				fieldname: "setup_hr_data",
				label: __("Create HR Data"),
				fieldtype: "Check",
				description: __(
					"Creates demo HR data to explore the system — a demo company (Sparrow Tech Pvt Ltd), departments, designations, leave types, shifts, holiday lists, and salary structure.",
				),
			},
		],
	},
];
