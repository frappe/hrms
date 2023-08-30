$(() => {
	show_applied_filters();
	$("input:checkbox").change(function () {
		const filters = $("input").serialize();
		scroll_up_and_update_filters(filters);
	});
	$("#clear-filters").on("click", function () {
		scroll_up_and_update_filters();
	});
	$("#search-box").bind("search", function () {
		const filters = $("input").serialize();
		scroll_up_and_update_filters(filters);
	});
	$("#search-box").keyup(function (e) {
		if (e.keyCode == 13) {
			$(this).trigger("search");
		}
	});
});

function show_applied_filters() {
	const query_params = frappe.utils.get_query_params();
	if ("query" in query_params) {
		$("#search-box").val(query_params["query"]);
		delete query_params["query"];
	} else if ("query=" in query_params) {
		delete query_params["query="];
	}
	for (const filter in query_params) {
		if (typeof query_params[filter] === "string") {
			$("#" + $.escapeSelector(query_params[filter])).prop("checked", true);
		} else {
			for (const d of query_params[filter])
				$("#" + $.escapeSelector(d)).prop("checked", true);
		}
	}
}

function scroll_up_and_update_filters(filters = "") {
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
