// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	refresh: function (frm) {
		frm.set_query("payroll_cost_center", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});

		// Call the API to get the attrition risk
		if (frm.doc.name && frm.doc.status === 'Active') {
			frappe.call({
				method: "hrms.api.predict_attrition",
				args: {
					employee: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						let risk_html = "";
						let risk_color = r.message.attrition_risk === "High" ? "red" : "green";
						risk_html = `<span style="color: ${risk_color}; font-weight: bold;">
							${r.message.attrition_risk}</span> (Confidence: ${r.message.confidence_score})`;

						// Add a button to suggest actions if risk is high
						if (r.message.attrition_risk === "High") {
							risk_html += ` <button class="btn btn-xs btn-default" id="suggest-retention-actions">Suggest Actions</button>`;
						}

						// The field was created as 'custom_attrition_risk'
						frm.fields_dict.custom_attrition_risk.$wrapper.html(risk_html);

						// Add click handler for the new button
						$('#suggest-retention-actions').on('click', function() {
							frappe.call({
								method: "hrms.api.get_retention_suggestions",
								args: {
									employee: frm.doc.name
								},
								callback: function(res) {
									if (res.message && res.message.length > 0) {
										let suggestions_html = res.message.map(suggestion => `<li>${suggestion}</li>`).join('');
										frappe.msgprint({
											title: __('Retention Suggestions for ' + frm.doc.employee_name),
											message: `<ul>${suggestions_html}</ul>`,
											indicator: 'blue'
										});
									} else {
										frappe.msgprint(__('No specific suggestions were generated.'));
									}
								}
							});
						});
					}
				}
			});
		}
	},

	date_of_birth(frm) {
		frm.call({
			method: "hrms.overrides.employee_master.get_retirement_date",
			args: {
				date_of_birth: frm.doc.date_of_birth,
			},
		}).then((r) => {
			if (r && r.message) frm.set_value("date_of_retirement", r.message);
		});
	},
});
