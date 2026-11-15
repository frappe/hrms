$(() => {
	const form = document.getElementById("careers-filters");
	if (!form) return;

	form.addEventListener("submit", () => {
		for (const field of form.querySelectorAll("input[name], select[name]")) {
			if (field.name !== "sort" && !field.value) field.disabled = true;
		}
	});

	form.querySelectorAll("select").forEach((select) =>
		select.addEventListener("change", () => form.requestSubmit()),
	);

	form.querySelector("#search-box").addEventListener("search", () => form.requestSubmit());

	// phones keep the native picker
	if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
		form.querySelectorAll("select").forEach(show_as_dropdown);
	}

	form.querySelector("#sort").addEventListener("click", () => {
		const sort = form.querySelector("input[name=sort]");
		sort.disabled = !sort.disabled;
		form.requestSubmit();
	});

	set_view(document.documentElement.dataset.careersView || "cards");
	form.querySelectorAll("[data-view]").forEach((button) =>
		button.addEventListener("click", () => {
			set_view(button.dataset.view);
			try {
				localStorage.setItem("careers-view", button.dataset.view);
			} catch (e) {}
		}),
	);

	document
		.querySelectorAll("[name=pagination]")
		.forEach((button) =>
			button.addEventListener("click", () => go_to_page(Number(button.id))),
		);
	const current_page = Number(new URLSearchParams(location.search).get("page")) || 1;
	$("#previous").on("click", () => go_to_page(current_page - 1));
	$("#next").on("click", () => go_to_page(current_page + 1));

	function show_as_dropdown(select) {
		const button = document.createElement("button");
		button.type = "button";
		button.className = "careers-control";
		button.textContent = select.selectedOptions[0].label;
		select.hidden = true;
		select.after(button);

		new frappe.ui.Dropdown({
			trigger: button,
			options: [...select.options].map((option) => ({
				label: option.label,
				selected: option.selected,
				onclick: () => {
					select.value = option.value;
					form.requestSubmit();
				},
			})),
		});
	}

	function set_view(view) {
		document.documentElement.dataset.careersView = view;
		form.querySelectorAll("[data-view]").forEach((button) => {
			const active = button.dataset.view === view;
			button.dataset.state = active ? "active" : "inactive";
			button.setAttribute("aria-checked", active);
		});
	}

	function go_to_page(page) {
		const params = new URLSearchParams(location.search);
		params.set("page", page);
		location.href = "/jobs?" + params.toString();
	}
});
