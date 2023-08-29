$(() => {
	select_applied_filters();
	$("input:checkbox").change(function () {
		const filters = $("input:checked").serialize();
		scroll_up_and_update_filters(filters);
	});
	$("#clear-filters").on("click", function () {
		scroll_up_and_update_filters();
	});
});

function select_applied_filters() {
	const query_params = frappe.utils.get_query_params();
	for (const filter in query_params) {
		if (typeof query_params[filter] === "string") {
			$("#" + $.escapeSelector(query_params[filter])).prop("checked", true);
		} else {
			for (const d of query_params[filter])
				$("#" + $.escapeSelector(d)).prop("checked", true);
		}
	}
}

function scroll_up_and_update_filters(filters="") {
	if (window.scrollY === 0) {
		window.location.href = "/jobs?" + filters;
	} else {
		window.scroll({
			top: 0,
			behavior: "smooth",
		});
		window.addEventListener("scroll", function () {
			if (window.scrollY === 0) {
				window.location.href = "/jobs?" + filters;
			}
		});
	}
}
