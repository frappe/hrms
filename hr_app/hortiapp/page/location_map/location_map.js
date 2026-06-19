frappe.pages["location-map"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Employee Location Map"),
		single_column: true,
	});

	// Filters
	const employee_field = page.add_field({
		fieldname: "employee",
		label: __("Employee"),
		fieldtype: "Link",
		options: "Employee",
	});

	const from_field = page.add_field({
		fieldname: "from_time",
		label: __("From"),
		fieldtype: "Datetime",
		default: frappe.datetime.add_days(frappe.datetime.now_datetime(), -1),
	});

	const to_field = page.add_field({
		fieldname: "to_time",
		label: __("To"),
		fieldtype: "Datetime",
		default: frappe.datetime.now_datetime(),
	});

	page.set_primary_action(__("Refresh"), () => render(), "refresh");

	// Map container
	const $map = $('<div style="height: calc(100vh - 180px); width: 100%;"></div>').appendTo(
		page.main
	);

	let map = null;
	let layer = null;

	// Load Leaflet from CDN, then draw.
	frappe.require(
		[
			"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
			"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
		],
		() => {
			map = L.map($map.get(0)).setView([0, 0], 2);
			L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
				attribution: "&copy; OpenStreetMap contributors",
				maxZoom: 19,
			}).addTo(map);
			layer = L.layerGroup().addTo(map);
			render();
		}
	);

	function render() {
		if (!map) return;
		frappe.call({
			method: "hr_app.api.get_recent_locations",
			args: {
				employee: employee_field.get_value() || null,
				from_time: from_field.get_value() || null,
				to_time: to_field.get_value() || null,
				limit: 1000,
			},
			callback: (r) => {
				layer.clearLayers();
				const points = r.message || [];
				if (!points.length) {
					frappe.show_alert({
						message: __("No location data for the selected filters"),
						indicator: "orange",
					});
					return;
				}

				// Keep only the latest ping per employee for the map markers.
				const latest = {};
				const bounds = [];
				points.forEach((p) => {
					if (p.latitude == null || p.longitude == null) return;
					bounds.push([p.latitude, p.longitude]);
					if (!latest[p.employee]) {
						latest[p.employee] = p;
						L.marker([p.latitude, p.longitude])
							.bindPopup(
								`<b>${frappe.utils.escape_html(p.employee_name || p.employee)}</b><br>` +
									`${frappe.datetime.str_to_user(p.timestamp)}`
							)
							.addTo(layer);
					}
				});

				if (bounds.length) {
					map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
				}
			},
		});
	}
};
