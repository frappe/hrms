frappe.provide("hrms.setup");

frappe.setup.on("before_load", function () {
	if (
		frappe.boot.setup_wizard_completed_apps?.length &&
		frappe.boot.setup_wizard_completed_apps.includes("hrms")
	) {
		return;
	}

	if (!frappe.boot.hr_only_setup) return;

	// HR-only site: show the HR persona in place of the ERPNext one
	const persona_index = frappe.setup.slides.findIndex((slide) => slide.name === "persona");
	if (persona_index >= 0) {
		frappe.setup.slides.splice(persona_index, 1, ...hrms.setup.slides_settings);
	} else {
		hrms.setup.slides_settings.map(frappe.setup.add_slide);
	}
});

hrms.setup.slides_settings = [
	{
		// Persona — help us tailor the setup
		name: "hr_persona",
		title: __("A little about you"),
		// subtitle shown under the title
		help: __("A few quick questions so we can set things up the way you work."),
		fields: [
			{
				fieldname: "persona_implementing_for",
				label: __("Who are you setting this up for?"),
				fieldtype: "Select",
				options: [
					"",
					"My own business",
					"A company I work for",
					"A client I'm consulting for",
				].join("\n"),
				reqd: 1,
			},
			{
				fieldname: "persona_company_size",
				label: __("How many employees do you have?"),
				fieldtype: "Select",
				options: ["", "1–10", "11–50", "51–200", "201–1,000", "1,000+"].join("\n"),
				reqd: 1,
			},
			{
				fieldname: "persona_industry",
				label: __("What kind of work do you do?"),
				fieldtype: "Select",
				options: [
					"",
					"Manufacturing",
					"Retail",
					"Wholesale / Distribution",
					"E-commerce",
					"Services / Consulting",
					"Construction / Real Estate",
					"Technology / Software",
					"Healthcare",
					"Education",
					"Agriculture",
					"Food & Beverage",
					"Non Profit",
					"Other",
				].join("\n"),
				reqd: 1,
			},
			{
				fieldname: "persona_current_system",
				label: __("What do you use for HR today?"),
				fieldtype: "Select",
				options: [
					"",
					"Keka",
					"GreytHR",
					"Zoho People",
					"Darwinbox",
					"BambooHR",
					"Workday",
					"SAP SuccessFactors",
					"Excel / Spreadsheets",
					"Nothing yet - starting fresh",
					"Other",
				].join("\n"),
				reqd: 1,
			},
			{
				fieldtype: "Section Break",
				description: __("Select the modules that you plan to implement"),
			},
			{
				fieldname: "module_leave_attendance",
				label: __("Leave & Attendance"),
				fieldtype: "Check",
			},
			{ fieldname: "module_payroll", label: __("Payroll"), fieldtype: "Check" },
			{ fieldtype: "Column Break" },
			{ fieldname: "module_recruitment", label: __("Recruitment"), fieldtype: "Check" },
			{
				fieldname: "module_performance",
				label: __("Performance Management"),
				fieldtype: "Check",
			},
		],

		onload: function (slide) {
			this.bind_company_size_modules(slide);
		},

		bind_company_size_modules: function (slide) {
			let me = this;
			slide.get_input("persona_company_size").on("change", function () {
				me.apply_company_size_modules(slide);
			});
		},

		apply_company_size_modules: function (slide) {
			let company_size = slide.get_field("persona_company_size").get_value();
			let modules = hrms.setup.company_size_modules[company_size] || [
				"leave_attendance",
				"payroll",
			];
			["leave_attendance", "payroll", "recruitment", "performance"].forEach(
				function (module) {
					slide
						.get_field("module_" + module)
						.set_value(modules.includes(module) ? 1 : 0);
				},
			);
		},
	},
];

// Modules pre-selected on the persona slide based on the team size.
// Keys must match the persona_company_size option values. Leave & Attendance and Payroll are always on.
hrms.setup.company_size_modules = {
	"1–10": ["leave_attendance", "payroll"],
	"11–50": ["leave_attendance", "payroll", "recruitment"],
	"51–200": ["leave_attendance", "payroll", "recruitment", "performance"],
	"201–1,000": ["leave_attendance", "payroll", "recruitment", "performance"],
	"1,000+": ["leave_attendance", "payroll", "recruitment", "performance"],
};
