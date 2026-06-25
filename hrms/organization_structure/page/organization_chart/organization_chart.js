frappe.pages["organization-chart"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Organization Chart"),
		single_column: true,
	});

	frappe.breadcrumbs.add("Organization Structure");

	const $container = $('<div class="os-chart"></div>').appendTo(page.body);

	page.add_inner_button(__("Refresh"), load);

	const UNIT_META = {
		Executive: { abbr: "exe", type_class: "os-type-executive" },
		Function: { abbr: "func", type_class: "os-type-function" },
		Process: { abbr: "proc", type_class: "os-type-process" },
		"Sub-Process": { abbr: "subp", type_class: "os-type-sub-process" },
		Department: { abbr: "dept", type_class: "os-type-dept-district" },
		District: { abbr: "dis", type_class: "os-type-dept-district" },
		Team: { abbr: "team", type_class: "os-type-team-branch" },
		Branch: { abbr: "br", type_class: "os-type-team-branch" },
		"Sub-Team": { abbr: "subt", type_class: "os-type-sub-team" },
		Other: { abbr: "oth", type_class: "os-type-other" },
	};

	function unit_meta(unit_type) {
		return UNIT_META[unit_type] || { abbr: "unit", type_class: "os-type-unknown" };
	}

	function load() {
		$container.html(`<div class="os-empty text-muted">${__("Loading...")}</div>`);
		frappe
			.call({
				method: "hrms.organization_structure.page.organization_chart.organization_chart.get_chart_data",
			})
			.then((r) => render(r.message || []));
	}

	function render(roots) {
		if (!roots.length) {
			$container.html(
				`<div class="os-empty text-muted">${__(
					"No organization units found. Create organization units to see the chart.",
				)}</div>`,
			);
			return;
		}

		const html = `<div class="os-tree-wrap"><ul class="os-tree">${roots
			.map(node_html)
			.join("")}</ul></div>`;
		$container.html(html);

		$container.find(".os-node[data-doctype='Organization Unit']").on("click", function () {
			const id = $(this).data("id");
			if (id) frappe.set_route("Form", "Organization Unit", id);
		});

		$container.find(".os-node[data-doctype='Position']").on("click", function () {
			const id = $(this).data("id");
			if (id) frappe.set_route("Form", "Position", id);
		});
	}

	function position_node_html(p) {
		const esc = frappe.utils.escape_html;
		const child_positions =
			p.children && p.children.length
				? `<ul class="os-position-tree">${p.children.map(position_node_html).join("")}</ul>`
				: "";

		let body;
		if (p.occupied) {
			body = `<div class="os-emp">${esc(p.employee || "")}</div>
				<div class="os-pos">${esc(p.title || "")}</div>`;
		} else {
			body = `<div class="os-emp">${esc(p.title || "")}</div>
				<div class="os-pos os-vac">${__("Vacant")}</div>`;
		}

		return `<li>
			<div class="os-node os-node-position ${p.occupied ? "occupied" : "vacant"}"
				data-id="${esc(p.id)}" data-doctype="Position">
				<div class="os-head os-head-position">
					<span class="os-abbr">pos</span>
					<span class="os-unit-name">${esc(p.title || "")}</span>
				</div>
				<div class="os-body">${body}</div>
			</div>
			${child_positions}
		</li>`;
	}

	function node_html(n) {
		const esc = frappe.utils.escape_html;
		const meta = unit_meta(n.unit_type);
		const head = `<span class="os-abbr">${esc(meta.abbr)}</span>
			<span class="os-unit-name">${esc(n.unit || "")}</span>`;

		let body;
		if (!n.has_head) {
			body = `<div class="os-pos">${esc(n.unit_type || __("Organization Unit"))}</div>`;
		} else if (n.occupied) {
			body = `<div class="os-emp">${esc(n.employee || "")}</div>
				<div class="os-pos">${esc(n.title || "")}</div>`;
		} else {
			body = `<div class="os-emp">${esc(n.title || "")}</div>
				<div class="os-pos os-vac">${__("Vacant")}</div>`;
		}

		const org_children =
			n.children && n.children.length
				? `<ul>${n.children.map(node_html).join("")}</ul>`
				: "";

		const position_children =
			n.positions && n.positions.length
				? `<ul class="os-position-tree">${n.positions.map(position_node_html).join("")}</ul>`
				: "";

		return `<li>
			<div class="os-node ${n.occupied ? "occupied" : "vacant"} ${meta.type_class}"
				data-id="${esc(n.id)}" data-doctype="Organization Unit">
				<div class="os-head">${head}</div>
				<div class="os-body">${body}</div>
			</div>
			${org_children}
			${position_children}
		</li>`;
	}

	load();
	$(wrapper).bind("show", load);
};
