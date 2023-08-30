$(() => {
	const query_params = frappe.utils.get_query_params();
	show_applied_filters(query_params);
	$("input:checkbox").change(function () {
		const filters = $("input").serialize();
		scroll_up_and_update_params(filters);
	});
	$("#clear-filters").on("click", function () {
		scroll_up_and_update_params();
	});
	$("#search-box").bind("search", function () {
		const filters = $("input").serialize();
		scroll_up_and_update_params(filters);
	});
	$("#search-box").keyup(function (e) {
		if (e.keyCode == 13) {
			$(this).trigger("search");
		}
	});
	$("[name=sort]").on("click", function () {
		const filters = $("input").serialize();
		const sort = $.param({ sort: $(this).text() });
		scroll_up_and_update_params(filters + "&" + sort);
	});
});

function show_applied_filters(query_params) {
	for (const filter in query_params) {
		if (filter === "query") {
			$("#search-box").val(query_params["query"]);
		} else if (filter === "query=") {
			continue;
		}
		if (typeof query_params[filter] === "string") {
			$("#" + $.escapeSelector(query_params[filter])).prop("checked", true);
		} else {
			for (const d of query_params[filter])
				$("#" + $.escapeSelector(d)).prop("checked", true);
		}
	}
}

function scroll_up_and_update_params(filters = "") {
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
