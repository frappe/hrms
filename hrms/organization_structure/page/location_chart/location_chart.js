frappe.pages["location-chart"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Location Chart"),
		single_column: true,
	});

	frappe.breadcrumbs.add("Organization Structure");
	page.main.addClass("frappe-card location-chart-page");

	const $container = $('<div class="loc-chart"></div>').appendTo(page.main);

	page.add_inner_button(__("Refresh"), load);
	page.add_inner_button(__("Expand All"), () => $container.find("ul").show());
	page.add_inner_button(__("Collapse All"), () => {
		$container.find(".loc-tree ul").hide();
	});
	page.add_inner_button(__("Organization Tree"), () => frappe.set_route("Tree", "Organization Unit"));

	const LOCATION_META = {
		"Head Office": {
			abbr: "HO",
			label: __("Head Office"),
			icon: "building",
			theme: "head-office",
		},
		"District Office": {
			abbr: "DIS",
			label: __("District Office"),
			icon: "map",
			theme: "district",
		},
		Branch: {
			abbr: "BR",
			label: __("Branch"),
			icon: "map-pin",
			theme: "branch",
		},
	};

	function location_meta(location_1) {
		return (
			LOCATION_META[location_1] || {
				abbr: "LOC",
				label: location_1 || __("Location"),
				icon: "map",
				theme: "unknown",
			}
		);
	}

	function load() {
		$container.html(`<div class="loc-empty text-muted">${__("Loading chart...")}</div>`);
		frappe
			.call({
				method: "hrms.organization_structure.page.location_chart.location_chart.get_chart_data",
			})
			.then((r) => render(r.message || []));
	}

	function render(roots) {
		if (!roots.length) {
			$container.html(
				`<div class="loc-empty text-muted">${__(
					"No physical sites found. Set Location 1 on organization units to see the chart.",
				)}</div>`,
			);
			return;
		}

		const legend = `
			<div class="loc-hierarchy-legend">
				${Object.values(LOCATION_META)
					.map(
						(meta) =>
							`<span class="loc-legend-item loc-theme-${meta.theme}">
								<span class="loc-legend-dot"></span>${meta.label}
							</span>`,
					)
					.join("")}
			</div>`;

		const html = `${legend}
			<div class="loc-tree-wrap">
				<ul class="loc-tree">${roots.map(node_html).join("")}</ul>
			</div>`;
		$container.html(html);

		$container.find(".loc-node").on("click", function () {
			const id = $(this).data("id");
			if (id) frappe.set_route("Form", "Organization Unit", id);
		});
	}

	function node_html(n) {
		const esc = frappe.utils.escape_html;
		const meta = location_meta(n.location_1);
		const inactive = n.status === "Inactive";

		let stats = "";
		if (n.location_1 === "District Office" && n.branch_count) {
			stats += `<span class="loc-stat-pill">${__("{0} branches", [n.branch_count])}</span>`;
		}
		if (n.location_1 === "Branch" && n.position_count) {
			stats += `<span class="loc-stat-pill">${__("{0} positions", [n.position_count])}</span>`;
		}
		if (inactive) {
			stats += `<span class="loc-stat-pill loc-stat-inactive">${__("Inactive")}</span>`;
		}

		const children =
			n.children && n.children.length
				? `<ul>${n.children.map(node_html).join("")}</ul>`
				: "";

		return `<li>
			<div class="loc-node loc-theme-${meta.theme} ${inactive ? "is-inactive" : ""}" data-id="${esc(n.id)}">
				<div class="loc-head">
					<span class="loc-abbr">${esc(meta.abbr)}</span>
					<span class="loc-name">${esc(n.location || "")}</span>
				</div>
				<div class="loc-body">
					<div class="loc-code">${esc(n.location_code || "—")}</div>
					${n.geography ? `<div class="loc-geo">${esc(n.geography)}</div>` : ""}
					${stats ? `<div class="loc-stats">${stats}</div>` : ""}
				</div>
			</div>
			${children}
		</li>`;
	}

	load();
	$(wrapper).bind("show", load);
};
