frappe.ui.form.on("Employee Attendance Tool", {
	refresh(frm) {
		frm.disable_save();
	},

	onload(frm) {
		frm.set_value("date", frappe.datetime.get_today());
		frm.trigger("load_employees");
		frm.trigger("set_primary_action");
	},

	date(frm) {
		frm.trigger("load_employees");
	},

	department(frm) {
		frm.trigger("load_employees");
	},

	branch(frm) {
		frm.trigger("load_employees");
	},

	company(frm) {
		frm.trigger("load_employees");
	},

	status(frm) {
		frm.trigger("set_primary_action");
	},

	load_employees(frm) {
		if (!frm.doc.date)
			return;

		frappe.call({
			method: "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.get_employees",
			args: {
				date: frm.doc.date,
				department: frm.doc.department,
				branch: frm.doc.branch,
				company: frm.doc.company
			}
		}).then((r) => {
			if (r.message["unmarked"].length > 0) {
				unhide_field("unmarked_attendance_section");
				frm.employees = r.message["unmarked"];
				frm.events.show_unmarked_employees(frm, r.message["unmarked"]);
			} else {
				hide_field("unmarked_attendance_section");
			}

			if (r.message["marked"].length > 0) {
				unhide_field("marked_attendance_section");
				frm.events.show_marked_employees(frm, r.message["marked"]);
			} else {
				hide_field('marked_attendance_section')
			}
		});
	},

	show_unmarked_employees(frm, unmarked_employees) {
		let $wrapper = frm.get_field("employees_html").$wrapper;

		if (!frm.employee_area) {
			frm.employee_area = $(`<div>`).appendTo($wrapper);
		}

		$($wrapper).empty();
		let employee_toolbar = $(
			`<div class="col-sm-12 top-toolbar">
				<button class="btn btn-xs btn-default btn-add">${__("Check all")}</button>
				<button class="btn btn-xs btn-default btn-remove">${__("Uncheck all")}</button>
			</div>`
		).appendTo($wrapper);

		employee_toolbar.find(".btn-add")
			.html(__('Check all'))
			.on("click", function() {
				$wrapper.find('input[type="checkbox"]').each(function(i, check) {
					if(!$(check).is(":checked")) {
						check.checked = true;
					}
				});
			});

		employee_toolbar.find(".btn-remove")
			.html(__('Uncheck all'))
			.on("click", function() {
				$wrapper.find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						check.checked = false;
					}
				});
			});

		let row;
		$.each(unmarked_employees, function(i, m) {
			if (i===0 || (i % 4) === 0) {
				row = $('<div class="row"></div>').appendTo($wrapper);
			}

			$(repl('<div class="col-sm-3 unmarked-employee-checkbox">\
				<div class="checkbox">\
				<label><input type="checkbox" class="employee-check" employee="%(employee)s"/>\
				%(employee)s</label>\
				</div></div>', {employee: m.employee +' : '+ m.employee_name})).appendTo(row);
		});

	},

	show_marked_employees(frm, marked_employees) {
		let $wrapper = frm.get_field("marked_attendance_html").$wrapper;

		if (!frm.marked_employee_area) {
			frm.marked_employee_area = $(`<div>`).appendTo($wrapper);
		}

		$wrapper.empty();

		let row;
		$.each(marked_employees, function(i, m) {
			var attendance_icon = "fa fa-check";
			var color_class = "";
			if(m.status == "Absent") {
				attendance_icon = "fa fa-check-empty"
				color_class = "text-muted";
			}
			else if(m.status == "Half Day") {
				attendance_icon = "fa fa-check-minus"
			}

			if (i===0 || i % 4===0) {
				row = $('<div class="row"></div>').appendTo($wrapper);
			}

			$(repl('<div class="col-sm-3 %(color_class)s">\
				<label class="marked-employee-label"><span class="%(icon)s"></span>\
				%(employee)s</label>\
				</div>', {
					employee: m.employee +' : '+ m.employee_name,
					icon: attendance_icon,
					color_class: color_class
				})).appendTo(row);
		});
	},

	set_primary_action(frm) {
		frm.disable_save();

		if (frm.doc.status)
			frm.page.set_primary_action(__("Mark Attendance"), () => frm.trigger("mark_attendance"));
	},

	mark_attendance(frm) {
		const marked_employees = [];

		frm.get_field("employees_html").$wrapper
			.find('input[type="checkbox"]')
			.each(function(i, check) {
				if($(check).is(":checked")) {
					marked_employees.push(frm.employees[i]);
				}
		});

		frappe.call({
			method: "hrms.hr.doctype.employee_attendance_tool.employee_attendance_tool.mark_employee_attendance",
			args: {
				"employee_list": marked_employees,
				"status": frm.doc.status,
				"date": frm.doc.date,
				"company": frm.doc.company
			},
			freeze: true,
			callback: function(r) {
				if (!r.exc) {
					frappe.show_alert({message: __("Attendance marked successfully"), indicator: "green"});
					frm.trigger("load_employees");
				}
			}
		});
	}
});
