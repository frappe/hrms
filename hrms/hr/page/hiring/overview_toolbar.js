const OVERVIEW_SORTS = ["attention", "closing", "newest", "role"];

function get_overview_sort_labels() {
	return {
		attention: __("Needs attention"),
		closing: __("Closing soonest"),
		newest: __("Newest"),
		role: __("Role A–Z"),
	};
}

/** Search, Department and Location dropdowns and sort over the openings on the overview; the state lives on the page so it survives opening one. */
hrms.hiring.OverviewToolbar = class OverviewToolbar {
	constructor(openings, state, on_change) {
		this.state = state;
		this.on_change = on_change;
		this.groups = [
			{ key: "department", label: __("Department"), all: __("All departments") },
			{ key: "location", label: __("Location"), all: __("All locations") },
		]
			.map((group) => ({ ...group, values: this.get_values(openings, group.key) }))
			.filter((group) => group.values.length > 1);
		for (const key of ["department", "location"]) {
			const group = this.groups.find((group) => group.key === key);
			if (!group?.values.includes(state[key])) state[key] = null;
		}
		this.make();
	}

	get_values(openings, key) {
		const values = openings.map((opening) => opening[key]).filter(Boolean);
		return [...new Set(values)].sort((a, b) => a.localeCompare(b));
	}

	get has_filters() {
		return Boolean(this.state.search || this.state.department || this.state.location);
	}

	matches(opening) {
		const { search, department, location } = this.state;
		if (department && opening.department !== department) return false;
		if (location && opening.location !== location) return false;
		if (!search) return true;
		const haystack = [opening.job_title, opening.department, opening.location].join("\n");
		return haystack.toLowerCase().includes(search.toLowerCase());
	}

	/** A sorted copy; "Needs attention" keeps the order the server returned. */
	sort(openings) {
		const compare = {
			closing: (a, b) => (a.closes_on || "9999").localeCompare(b.closes_on || "9999"),
			newest: (a, b) => b.creation.localeCompare(a.creation),
			role: (a, b) => a.job_title.localeCompare(b.job_title),
		}[this.state.sort];
		return compare ? [...openings].sort(compare) : openings;
	}

	make() {
		this.$search = $(`<input type="search" class="form-control input-sm hiring__search" />`)
			.attr({ placeholder: __("Search openings"), "aria-label": __("Search openings") })
			.val(this.state.search)
			.on("input", (event) => {
				this.state.search = event.target.value.trim();
				this.on_change();
			});
		this.$filters = $(`<span class="hiring__filters"></span>`);
		this.$sort = $(`<span class="hiring__sort"></span>`);
		this.$el = $(`<div class="hiring__toolbar" data-view="overview"></div>`).append(
			this.$search,
			this.$filters,
			this.$sort,
		);
		this.render_controls();
	}

	render_controls() {
		hrms.hiring
			.clear(this.$filters)
			.append(...this.groups.map((group) => this.make_filter_dropdown(group).$trigger));
		hrms.hiring.clear(this.$sort).append(this.make_sort_dropdown().$trigger);
	}

	make_filter_dropdown({ key, label, all, values }) {
		const current = this.state[key];
		const make_option = (text, value) => ({
			label: text,
			icon_right: value === current ? "check" : null,
			onclick: () => this.set_filter(key, value),
		});
		const dropdown = new frappe.ui.Dropdown({
			button: {
				label: current || label,
				icon_right: "chevron-down",
				variant: "subtle",
				tooltip: current,
				attrs: { "aria-label": label },
			},
			align: "start",
			options: [
				{ group: label, hide_label: true, options: [make_option(all, null)] },
				{
					group: label,
					hide_label: true,
					options: values.map((value) => make_option(value, value)),
				},
			],
		});
		dropdown.$trigger.addClass("hiring__select");
		return dropdown;
	}

	make_sort_dropdown() {
		const labels = get_overview_sort_labels();
		return new frappe.ui.Dropdown({
			button: {
				icon: "arrow-up-down",
				variant: "subtle",
				tooltip: __("Sorted by {0}", [labels[this.state.sort]]),
			},
			align: "end",
			options: OVERVIEW_SORTS.map((sort) => ({
				label: labels[sort],
				icon_right: sort === this.state.sort ? "check" : null,
				onclick: () => this.set_sort(sort),
			})),
		});
	}

	set_filter(key, value) {
		this.state[key] = value;
		this.render_controls();
		this.on_change();
	}

	set_sort(sort) {
		this.state.sort = sort;
		this.render_controls();
		this.on_change();
	}

	clear_filters() {
		Object.assign(this.state, { search: "", department: null, location: null });
		this.$search.val("");
		this.render_controls();
		this.on_change();
	}
};
