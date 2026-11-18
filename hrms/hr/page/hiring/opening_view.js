hrms.hiring.OpeningView = class OpeningView {
	/** `is_default_stage`: the route named no stage, so the view lands on the first stage with applicants. */
	constructor(desk, name, stage, applicant, is_default_stage = false) {
		this.desk = desk;
		this.page = desk.page;
		this.name = name;
		this.stage = stage;
		this.is_default_stage = is_default_stage;
		this.search = "";
		this.sort = "newest";
		this.source = null;
		this.sources = [];
		this.rows = [];
		this.selected = null;
		this.target = applicant || null;
		// a target from the route shows even when it isn't among the rows; one from an action doesn't
		this.is_link_target = Boolean(applicant);
		this.url_key = get_route_key(name, stage, applicant);
		this.echoes = new Set();
		this.request_id = 0;
		this.is_ready = false;
		this.is_loading_more = false;
		this.media = window.matchMedia(SPLIT_QUERY);
		this.handle_media_change = () => this.is_ready && this.rerender();
		this.media.addEventListener("change", this.handle_media_change);
		this.panel = new hrms.hiring.ApplicantPanel(this);
		this.show_skeleton();
		this.load_first_page();
	}

	/** The view while its first page loads: the split with placeholders, or the boxed list. */
	show_skeleton() {
		if (!this.media.matches) {
			this.$skeleton = skeleton_list(6, { has_avatar: true }).appendTo(this.desk.$body);
			return;
		}
		// the skeleton draws the split, so the sidebar folds with it rather than once rows arrive
		this.desk.$body.attr("data-layout", "split");
		this.panel.show_skeleton();
		this.mount_pane(
			`<div class="hiring__tabs-skeleton"></div>`,
			$(`<div class="hiring__toolbar"></div>`).append(skeleton_bar("100%", "28px")),
		);
		this.pane.set_placeholder(skeleton_list(6, { variant: "flat", has_avatar: true }));
	}

	destroy() {
		// a response or an Undo arriving later must not draw into the page
		this.request_id++;
		this.panel.destroy();
		this.media.removeEventListener("change", this.handle_media_change);
		this.more_observer?.disconnect();
		// empties the page first, so no tooltip stays stuck on screen
		hrms.hiring.clear(this.desk.$body);
		this.pane?.destroy();
	}

	/** Split view: a list on the left, the selected applicant on the right. */
	get is_split() {
		return this.media.matches && this.counts?.[this.stage] > 0;
	}

	get has_filters() {
		return Boolean(this.search || this.source);
	}

	/** Returns true when the route only echoes a selection made on the page. */
	show(stage, applicant) {
		const key = get_route_key(this.name, stage, applicant);
		if (this.echoes.delete(key)) return true;
		this.url_key = key;
		if (stage !== this.stage) {
			this.set_stage(stage, applicant);
		} else if (applicant && applicant !== this.selected && this.has_row(applicant)) {
			this.select(applicant);
		} else {
			this.refresh(applicant, { is_link: true });
		}
		return false;
	}

	set_stage(stage, applicant) {
		this.stage = stage;
		this.selected = null;
		this.target = applicant || null;
		this.is_link_target = Boolean(applicant);
		this.rows = [];
		this.tabs?.set_value(stage, { silent: true });
		this.panel?.reset();
		this.load_first_page();
	}

	step_stage(delta) {
		const stage = STAGES[STAGES.indexOf(this.stage) + delta];
		if (stage) frappe.set_route(hrms.hiring.get_pipeline_route(this.name, stage));
	}

	/** `applicant`: the one that changed, so it is fetched fresh; `is_link`: the route names them. */
	refresh(applicant, { is_link = false } = {}) {
		if (applicant) this.panel.forget(applicant);
		if (!this.desk.is_active(this)) return Promise.resolve();
		this.target = applicant || null;
		this.is_link_target = is_link && Boolean(applicant);
		return this.load_first_page({ silent: true });
	}

	/** Something changed elsewhere: reload the list and the open applicant, keeping the selection and any text being typed. */
	refresh_from_update() {
		if (!this.is_ready || !this.desk.is_active(this)) return;
		return this.load_first_page({ silent: true });
	}

	/** A changed applicant is loaded fresh next time; an interview or offer could be anyone's, so all are. */
	forget_changed({ doctype, name } = {}) {
		if (doctype === "Job Applicant" && name) this.panel.forget(name);
		else if (REALTIME_DOCTYPES.includes(doctype)) this.panel.forget_all();
	}

	/** The first page grows to take in `this.target`, so a linked applicant is in the list. */
	fetch(start, page_length = PAGE_LENGTH) {
		return frappe.call({
			method: `${API}.get_pipeline`,
			type: "GET",
			args: {
				job_opening: this.name,
				stage: this.stage,
				search: this.search || undefined,
				source: this.source || undefined,
				sort: this.sort,
				start,
				page_length,
				applicant: start === 0 ? this.target || undefined : undefined,
			},
		});
	}

	load_first_page({ silent = false } = {}) {
		const request_id = ++this.request_id;
		if (this.is_ready && !silent) this.show_list_skeleton();
		const page_length = silent ? Math.max(PAGE_LENGTH, this.rows.length) : PAGE_LENGTH;
		return this.fetch(0, page_length).then((r) => {
			if (request_id !== this.request_id || !this.desk.is_active(this)) return;
			if (this.land_on_first_stage(r.message.counts)) return;
			const previous_index = Math.max(this.get_index(), 0);
			this.apply(r.message);
			if (!this.is_ready) this.build();
			this.rows = r.message.rows;
			this.rerender(previous_index);
		});
	}

	show_list_skeleton() {
		const $rows = skeleton_list(6, {
			variant: this.is_split ? "flat" : "boxed",
			has_avatar: true,
		});
		if (this.pane) return this.pane.set_placeholder($rows);
		this.$list_area.empty().append($rows);
	}

	/** Returns true when the first load was for an empty "Applied" and the view moved to a stage that has applicants. */
	land_on_first_stage(counts) {
		if (!this.is_default_stage) return false;
		this.is_default_stage = false;
		const stage = STAGES.filter((stage) => stage !== "Rejected").find(
			(stage) => counts[stage] > 0,
		);
		if (!stage || stage === this.stage) return false;
		this.set_stage(stage, this.target);
		this.sync_route();
		return true;
	}

	apply({ opening, counts, total, sources, groups }) {
		this.opening = opening;
		this.counts = counts;
		this.total = total;
		this.sources = sources;
		this.groups = groups;
	}

	build() {
		this.is_ready = true;
		this.$skeleton?.remove();
		this.set_chrome();
		this.count_badges = {};
		this.tabs = new frappe.ui.TabButtons({
			type: "underline",
			label: __("Stage"),
			value: this.stage,
			options: STAGES.map((stage) => ({
				value: stage,
				label: __(stage),
				suffix: () => this.make_count_badge(stage),
			})),
			on_change: (stage) =>
				frappe.set_route(hrms.hiring.get_pipeline_route(this.name, stage)),
		});
		// A clicked tab lets go of focus, so the arrows go back to the list and stages
		// (see bind_shortcuts) instead of moving the tabs. Keyboard users who Tab in keep it.
		this.tabs.$el.on("click", () => document.activeElement?.blur());
		this.$search = $(`<input type="search" class="form-control input-sm hiring__search" />`)
			.attr({ placeholder: __("Search applicants"), "aria-label": __("Search applicants") })
			.on(
				"input",
				frappe.utils.debounce((event) => {
					this.search = event.target.value.trim();
					this.selected = null;
					this.load_first_page();
				}, 300),
			);
		this.$filter = $(`<span class="hiring__filter"></span>`);
		this.$toolbar = $(`<div class="hiring__toolbar"></div>`).append(
			this.$search,
			this.$filter,
		);
		this.$chips = $(`<div class="hiring__chips"></div>`);
		this.tabs.$el.addClass("hiring__tabs");
		this.$list_area = $(`<div class="hiring__list"></div>`);
		this.$list_column = $(`<div class="hiring__list-column"></div>`).append(this.$list_area);
		this.$content = $(`<div class="hiring__content"></div>`).append(this.$list_column);
		if (this.pane) {
			this.pane.$header.empty().append(this.tabs.$el);
			this.pane.$list_header.empty().append(this.$toolbar, this.$chips);
		}
	}

	/** From 1024px: the stage tabs over the list and the applicant, side by side. */
	mount_pane(header = this.tabs.$el, list_header = [this.$toolbar, this.$chips]) {
		this.$content?.detach();
		this.list = null;
		this.pane = new frappe.ui.SplitPane({
			header,
			list_header,
			detail: this.panel.$el,
			on_select: (id, event) => {
				// a row is a link to the applicant's form; a click opens them here instead
				event?.preventDefault();
				this.select(id, { scroll: !event });
			},
			has_more: () => this.rows.length < this.total,
			load_more: () => this.load_more(),
			page: this.page,
			fold_sidebar: true,
			keys: {
				condition: (event, shortcut) => this.desk.can_step(shortcut),
				next_label: __("Next applicant"),
				previous_label: __("Previous applicant"),
			},
		});
		this.desk.$body.append(this.pane.$el);
		this.pane.fit_height();
	}

	/** Below 1024px the boxed list, with actions on its rows, takes the split's place. */
	mount_boxed() {
		if (this.pane) {
			this.pane.destroy();
			this.pane = null;
		}
		if (this.$content[0].isConnected) return;
		this.$list_column.prepend(this.$toolbar, this.$chips);
		this.desk.$body.append(this.tabs.$el, this.$content);
	}

	make_count_badge(stage) {
		this.count_badges[stage] = frappe.ui.badge({
			label: String(this.counts[stage]),
			size: "sm",
		});
		return this.count_badges[stage];
	}

	update_counts() {
		for (const stage of STAGES) {
			this.count_badges[stage].find(".es-badge__label").text(this.counts[stage]);
		}
	}

	set_chrome() {
		const opening = this.opening;
		const is_open = opening.status === "Open";
		this.page.set_breadcrumbs([
			{ label: __("Hiring pipeline"), href: "/desk/hiring" },
			{ label: "" },
		]);
		this.page.set_title(opening.display_title);
		this.make_view_switcher();
		this.page.set_indicator(is_open ? __("Open") : __("Closed"), is_open ? "green" : "gray");
		if (is_open) {
			this.page.set_secondary_action(
				__("Add applicant"),
				() => this.add_applicant(),
				"plus",
			);
		}
		this.page.add_menu_item(__("Edit opening"), () =>
			frappe.set_route("Form", "Job Opening", opening.name),
		);
		if (opening.publish && opening.route) {
			this.page.add_menu_item(__("View job post"), () =>
				window.open(`/${opening.route}`, "_blank"),
			);
		}
		this.page.add_menu_item(is_open ? __("Close opening") : __("Reopen opening"), () =>
			this.set_opening_status(is_open ? "Closed" : "Open"),
		);
		this.page.add_menu_item(__("View as list"), () =>
			frappe.set_route("List", "Job Applicant", { job_title: opening.name }),
		);
	}

	/** The view switcher dropdown list pages have; Kanban is the standard Job Applicant board. */
	make_view_switcher() {
		const icons = frappe.views.view_icon_map;
		const labels = frappe.views.get_view_label_map();
		const $wrapper = $(`<div class="custom-btn-group view-switcher"></div>`);
		const $trigger = frappe.ui.button({ css_class: "ellipsis" });
		frappe.ui.button.dress($trigger, {
			label: labels.Split,
			icon: icons.Split,
			icon_right: "chevrons-up-down",
		});
		$trigger.find(".es-button__label").addClass("hidden-xs custom-btn-group-label");
		$trigger.children("svg").last().addClass("hidden-xs");
		$wrapper.append($trigger);
		new frappe.ui.Dropdown({
			trigger: $trigger,
			options: () => [
				{ label: labels.Split, icon: icons.Split, selected: true },
				{
					label: labels.Kanban,
					icon: icons.Kanban,
					onclick: () => {
						frappe.route_options = { job_title: this.name };
						frappe.set_route("List", "Job Applicant", "Kanban", "Hiring Pipeline");
					},
				},
			],
		});
		const parent = frappe.is_mobile()
			? this.page.custom_mobile_actions
			: this.page.custom_actions;
		parent.removeClass("hide").append($wrapper);
	}

	add_applicant() {
		frappe.new_doc("Job Applicant", {
			job_title: this.opening.name,
			designation: this.opening.designation,
		});
	}

	set_opening_status(status) {
		const change = () =>
			frappe
				.call({
					method: "frappe.client.set_value",
					args: {
						doctype: "Job Opening",
						name: this.name,
						fieldname: "status",
						value: status,
					},
				})
				.then(() => this.reload());
		if (status === "Open") return change();
		frappe.confirm(
			__("Close {0}? It stops taking applications.", [
				frappe.utils.escape_html(this.opening.job_title),
			]),
			change,
		);
	}

	reload() {
		if (!this.desk.is_active(this)) return;
		this.desk.leave_opening();
		this.desk.show();
	}

	get_index(id = this.selected) {
		return this.rows.findIndex((row) => row.name === id);
	}

	has_row(id) {
		return this.get_index(id) !== -1;
	}

	get_position() {
		return { index: this.get_index() + 1, total: this.total };
	}

	rerender(previous_index = 0) {
		if (!this.desk.is_active(this)) return;
		this.render_list();
		this.settle_selection(previous_index);
	}

	render_list() {
		this.update_counts();
		const is_empty_stage = !this.counts[this.stage];
		this.set_layout(is_empty_stage);
		this.render_filter();
		this.render_chips();
		let placeholder = null;
		if (is_empty_stage) placeholder = this.make_empty_stage();
		else if (!this.rows.length && this.has_filters) placeholder = this.make_no_match();
		if (!this.pane) return this.render_boxed(placeholder);
		if (placeholder) return this.pane.set_placeholder(placeholder);
		this.pane.set_items(this.get_items(), this.get_groups());
	}

	/** The split from 1024px, where an empty stage spans its width; the boxed list below that. */
	set_layout(is_empty_stage) {
		const is_wide = this.media.matches;
		this.desk.$body.attr("data-layout", is_wide ? "split" : null);
		if (!is_wide) this.mount_boxed();
		else if (!this.pane) this.mount_pane();
		// an empty stage keeps the pane, and with it the folded sidebar, so stepping through doesn't flicker it
		const frame = this.pane ? this.pane.$el[0] : this.$content[0];
		frame.toggleAttribute("data-empty", is_empty_stage);
		this.pane?.fit_height();
	}

	render_boxed(placeholder) {
		this.list = placeholder ? null : this.make_list();
		this.$list_area.empty().append(placeholder || this.list.$el);
		this.watch_list_end();
	}

	/** In the boxed list the page scrolls, and the next page loads once the list's end scrolls near. */
	watch_list_end() {
		this.more_observer?.disconnect();
		if (!this.list || this.rows.length >= this.total) return;
		const sentinel = $(`<div class="hiring__list-end" aria-hidden="true"></div>`).appendTo(
			this.$list_area,
		)[0];
		this.more_observer = new IntersectionObserver(
			(entries) => entries[0].isIntersecting && this.load_next_page(),
			{ rootMargin: "400px 0px" },
		);
		this.more_observer.observe(sentinel);
	}

	async load_next_page() {
		if (this.is_loading_more || this.rows.length >= this.total) return;
		this.is_loading_more = true;
		try {
			await this.load_more();
		} finally {
			this.is_loading_more = false;
		}
	}

	make_list() {
		return new frappe.ui.List({
			items: this.get_items(),
			groups: this.get_groups(),
			selected: this.selected,
		});
	}

	get_items() {
		return this.rows.map((row) => this.get_item(row));
	}

	is_grouped() {
		return this.stage === "Interviewing" && this.groups.length > 1;
	}

	get_groups() {
		if (!this.is_grouped()) return null;
		return this.groups.map(({ group, label, count }) => ({ id: group, label, count }));
	}

	make_empty_stage() {
		const can_go_to_applied = this.stage !== "Applied" && this.counts.Applied > 0;
		return frappe.ui.empty_state({
			icon: "users",
			title: __("Nobody in {0}", [__(this.stage)]),
			description: get_empty_descriptions()[this.stage],
			css_class: "hiring__empty",
			actions: can_go_to_applied
				? [
						{
							label: __("Go to {0}", [__("Applied")]),
							variant: "subtle",
							onclick: () =>
								frappe.set_route(
									hrms.hiring.get_pipeline_route(this.name, "Applied"),
								),
						},
				  ]
				: [],
		});
	}

	make_no_match() {
		return $(`<div class="hiring__no-match text-p-base"></div>`).append(
			$(`<p></p>`).text(__("No applicants match")),
			frappe.ui.button({ label: __("Clear filters"), onclick: () => this.clear_filters() }),
		);
	}

	clear_filters() {
		this.search = "";
		this.source = null;
		this.$search.val("");
		this.load_first_page();
	}

	render_filter() {
		const labels = get_sort_labels();
		const is_default = this.sort === "newest" && !this.source;
		const dropdown = new frappe.ui.Dropdown({
			button: {
				icon: "list-filter",
				variant: is_default ? "ghost" : "subtle",
				tooltip: __("Sorted by {0}", [labels[this.sort]]),
			},
			align: "end",
			options: () => this.get_filter_options(),
		});
		hrms.hiring.clear(this.$filter).append(dropdown.$trigger);
	}

	get_filter_options() {
		const labels = get_sort_labels();
		const groups = [
			{
				group: __("Sort"),
				options: SORTS.map((sort) => ({
					label: labels[sort],
					selected: sort === this.sort,
					onclick: () => this.set_filter({ sort }),
				})),
			},
		];
		if (this.sources.length) {
			groups.push({
				group: __("Source"),
				options: this.sources.map(({ source, count }) => ({
					label: `${source} · ${count}`,
					selected: source === this.source,
					onclick: () =>
						this.set_filter({ source: source === this.source ? null : source }),
				})),
			});
		}
		return groups;
	}

	set_filter(changes) {
		Object.assign(this, changes);
		this.load_first_page();
	}

	render_chips() {
		this.$chips.empty();
		if (!this.source) return;
		this.$chips.append(
			frappe.ui.button({
				label: this.source,
				icon_right: "x",
				size: "sm",
				attrs: { "aria-label": __("Remove filter: {0}", [this.source]) },
				onclick: () => this.set_filter({ source: null }),
			}),
		);
	}

	load_more() {
		const request_id = this.request_id;
		return this.fetch(this.rows.length).then((r) => {
			if (request_id !== this.request_id || !this.desk.is_active(this)) return;
			this.apply(r.message);
			this.rows = [...this.rows, ...r.message.rows];
			(this.pane || this.list)?.set_items(this.get_items(), this.get_groups());
			this.update_counts();
			if (this.pane) return;
			// observe again, so a list end still in view after this page asks for the next one
			const sentinel = this.$list_area
				.find(".hiring__list-end")
				.appendTo(this.$list_area)[0];
			this.more_observer?.disconnect();
			if (sentinel && this.rows.length < this.total) this.more_observer?.observe(sentinel);
		});
	}

	get_item(row) {
		return {
			id: row.name,
			group: row.group,
			title: row.applicant_name,
			subtitle: this.is_grouped() ? row.group_fact : row.fact,
			meta: ago(row.created),
			avatar: { label: row.applicant_name },
			badge: row.on_hold ? { label: __("On hold") } : null,
			href: get_form_route("Job Applicant", row.name),
			actions: this.is_split ? [] : this.get_actions(row),
		};
	}

	get_actions(row) {
		if (this.stage === "Applied") {
			return [
				{
					label: __("Shortlist"),
					onclick: (item) => this.shortlist(item),
				},
				{
					label: __("Reject"),
					theme: "red",
					onclick: (item) => this.reject(item),
				},
			];
		}
		if (this.stage === "Interviewing" && row.can_make_offer) {
			return [
				{
					label: __("Create offer"),
					onclick: (item) => this.create_offer(item.id, item.title),
				},
			];
		}
		return [];
	}

	create_offer(job_applicant, applicant_name) {
		const { designation, company } = this.opening;
		return hrms.hiring.create_offer({
			name: job_applicant,
			applicant_name,
			designation,
			company,
		});
	}

	/** Shows an applicant; the one already shown is redrawn only once nobody is typing in it. */
	select(id, { scroll = true } = {}) {
		this.selected = id;
		(this.pane || this.list)?.set_selected(id, { scroll });
		this.panel.load(id);
		this.sync_route();
	}

	/**
	 * Picks the applicant to show after rows change; no-op below the split breakpoint. A target from
	 * the route shows even when they are not among the rows, so the URL never moves to someone else;
	 * one that an action moved out of the stage gives way to the row that took their place.
	 */
	settle_selection(previous_index = 0) {
		const { target, is_link_target } = this;
		this.target = null;
		this.is_link_target = false;
		if (!this.media.matches) return;
		const ids = this.rows.map((row) => row.name);
		const is_shown = ids.includes(target) || (is_link_target && ids.length);
		if (target && is_shown) return this.select(target);
		const wanted = ids.includes(this.selected) ? this.selected : null;
		const id = wanted ?? ids[Math.min(previous_index, ids.length - 1)];
		if (id) return this.select(id);
		this.selected = null;
		this.panel.clear();
		this.sync_route();
	}

	/** Writes the selection into the URL, replacing the history entry. */
	sync_route() {
		const key = get_route_key(this.name, this.stage, this.selected);
		if (key === this.url_key || !this.desk.is_active(this)) return;
		this.url_key = key;
		this.echoes.add(key);
		frappe.route_flags.replace_route = true;
		frappe.set_route(hrms.hiring.get_pipeline_route(this.name, this.stage, this.selected));
	}

	step(delta) {
		return this.pane?.step(delta);
	}

	async shortlist(item) {
		const index = this.get_index(item.id);
		const { previous_status } = await frappe.xcall(`${APPLICANT_API}.shortlist_applicant`, {
			job_applicant: item.id,
		});
		this.remove_row(item.id, "Shortlisted", index);
		const toast = frappe.ui.toast({
			message: __("{0} shortlisted", [item.title]),
			action: {
				label: __("Undo"),
				onclick: async () => {
					toast.dismiss();
					await frappe.xcall(`${APPLICANT_API}.undo_shortlist_applicant`, {
						job_applicant: item.id,
						previous_status,
					});
					this.refresh(item.id);
				},
			},
		});
	}

	/** Rejects with a dialog asking for the reason and offering to email the applicant. */
	async reject(item) {
		const { data } = this.panel;
		const rejection = await hrms.hiring.reject({
			name: item.id,
			applicant_name: item.title,
			reject_details: data?.name === item.id ? data : null,
		});
		if (!rejection) return;
		this.remove_row(item.id, "Rejected", this.get_index(item.id));
		hrms.hiring.show_reject_toast({
			applicant: { name: item.id, applicant_name: item.title },
			rejection,
			on_undo: () => this.refresh(item.id),
		});
	}

	/** Takes an applicant out of this stage and moves the selection to the next row. */
	remove_row(id, to_stage, index) {
		const was_selected = this.selected === id;
		this.panel.forget(id);
		this.rows = this.rows.filter((row) => row.name !== id);
		this.total--;
		this.counts[this.stage]--;
		this.counts[to_stage]++;
		if (was_selected) this.selected = null;
		this.rerender(index);
	}

	after_scheduled({ name }) {
		if (this.stage === "Interviewing") return this.refresh(name);
		this.remove_row(name, "Interviewing", this.get_index(name));
	}
};
