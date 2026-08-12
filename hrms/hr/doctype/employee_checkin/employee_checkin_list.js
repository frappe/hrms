frappe.listview_settings["Employee Checkin"] = {
	add_fields: ["offshift"],
	get_indicator: function (doc) {
		if (doc.offshift) {
			return [__("Off-Shift"), "yellow", "offshift,=,1"];
		}
	},
	onload: function (listview) {
		listview.page.add_action_item(__("Fetch Shifts"), () => {
			const checkins = listview.get_checked_items().map((checkin) => checkin.name);
			frappe.call({
				method: "hrms.hr.doctype.employee_checkin.employee_checkin.bulk_fetch_shift",
				freeze: true,
				args: {
					checkins,
				},
			});
		});

		if (frappe.perm.has_perm("Employee Checkin", 0, "create")) {
			listview.page.add_inner_button(__("Add Checkin for Another Employee"), () =>
				frappe.new_doc("Employee Checkin"),
			);
		}

		setup_checkin_action(listview);
	},
	before_render: function () {
		refresh_checkin_state(cur_list);
	},
	primary_action: function () {
		const listview = cur_list;
		if (listview?.checkin_employee) {
			start_checkin(listview, listview.next_checkin || get_next_checkin());
		}
	},
};

function get_next_checkin(last_log_type) {
	return last_log_type === "IN"
		? { log_type: "OUT", label: __("Check Out"), icon: "circle-arrow-left" }
		: { log_type: "IN", label: __("Check In"), icon: "circle-arrow-right" };
}

async function setup_checkin_action(listview) {
	const employee = await frappe.xcall("hrms.api.get_current_employee_info");
	if (!employee) return;

	listview.checkin_employee = employee;
	listview.set_primary_action = () => {
		const next = listview.next_checkin;
		if (!next) return;

		const button = listview.page.btn_primary;
		if (listview.painted_checkin === next.log_type && !button.hasClass("hide")) return;
		listview.painted_checkin = next.log_type;

		listview.page.set_primary_action(
			next.label,
			() => {
				start_checkin(listview, next);
			},
			next.icon,
		);
	};

	const default_no_result_message = listview.get_no_result_message.bind(listview);
	listview.get_no_result_message = () => {
		if (listview.filter_area?.get()?.length) {
			return default_no_result_message();
		}

		return frappe.ui.empty_state.html({
			icon: "clock",
			title: __("No check-ins yet"),
			description: __("Check in to create your first log."),
			actions: [
				{
					label: __("Check In"),
					icon: "circle-arrow-right",
					css_class: "btn-new-doc",
				},
			],
		});
	};

	await refresh_checkin_state(listview);
}

async function refresh_checkin_state(listview) {
	const employee = listview?.checkin_employee;
	if (!employee) return;

	const [last_log] = await frappe.db.get_list("Employee Checkin", {
		filters: { employee: employee.name },
		fields: ["log_type"],
		order_by: "time desc",
		limit: 1,
	});

	listview.next_checkin = get_next_checkin(last_log?.log_type);
	listview.set_primary_action();
}

async function start_checkin(listview, next) {
	const time = frappe.datetime.now_datetime();

	const track_geolocation = await frappe.db.get_single_value(
		"HR Settings",
		"allow_geolocation_tracking",
	);
	if (!track_geolocation) {
		return submit_checkin(listview, next, time);
	}

	let coordinates;
	frappe.dom.freeze(__("Fetching your geolocation") + "...");
	try {
		coordinates = await hrms.get_current_position();
		await frappe.require(["leaflet.bundle.js", "leaflet.bundle.css"]);
	} catch (error) {
		return;
	} finally {
		frappe.dom.unfreeze();
	}

	confirm_checkin_location(listview, next, time, coordinates);
}

function confirm_checkin_location(listview, next, time, coordinates) {
	const geojson = JSON.stringify({
		type: "FeatureCollection",
		features: [
			{
				type: "Feature",
				properties: {},
				geometry: {
					type: "Point",
					coordinates: [coordinates.longitude, coordinates.latitude],
				},
			},
		],
	});

	const dialog = new frappe.ui.Dialog({
		title: next.label,
		fields: [
			{
				fieldname: "time",
				label: __("Time"),
				fieldtype: "Datetime",
				read_only: 1,
				default: time,
			},
			{ fieldtype: "Section Break", hide_border: 1 },
			{
				fieldname: "latitude",
				label: __("Latitude"),
				fieldtype: "Float",
				precision: "7",
				read_only: 1,
				default: coordinates.latitude,
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "longitude",
				label: __("Longitude"),
				fieldtype: "Float",
				precision: "7",
				read_only: 1,
				default: coordinates.longitude,
			},
			{ fieldtype: "Section Break", hide_border: 1 },
			{
				fieldname: "geolocation",
				fieldtype: "Geolocation",
				default: geojson,
			},
		],
		primary_action_label: __("Confirm {0}", [next.label]),
		primary_action: () => {
			dialog.hide();
			submit_checkin(listview, next, time, coordinates);
		},
	});

	dialog.fields_dict.geolocation.disabled = 1;
	dialog.show();
}

async function submit_checkin(listview, next, time, coordinates) {
	let checkin;
	try {
		checkin = await frappe.db.insert({
			doctype: "Employee Checkin",
			employee: listview.checkin_employee.name,
			log_type: next.log_type,
			time: time,
			...(coordinates || {}),
		});
	} catch (error) {
		return;
	}

	frappe.show_alert({
		message: checkin.offshift
			? __("{0} recorded outside shift hours. It will not be considered for attendance.", [
					next.label,
			  ])
			: __("{0} successful", [next.label]),
		indicator: checkin.offshift ? "orange" : "green",
	});

	await refresh_checkin_state(listview);
	await listview.refresh();
}
