$(() => {
	const query_params = frappe.utils.get_query_params();
	show_applied_filters();

	$("input:checkbox").change(function () {
		scroll_up_and_update_params(get_new_params());
	});

	$("#clear-filters").on("click", function () {
		scroll_up_and_update_params();
	});

	$("#search-box").bind("search", function () {
		scroll_up_and_update_params(get_new_params());
	});

	$("#search-box").keyup(function (e) {
		if (e.keyCode == 13) {
			$(this).trigger("search");
		}
	});

	$("#desc-input").on("click", function () {
		const filters = $("input").serialize();
		if (query_params.sort === "asc") {
			scroll_up_and_update_params(filters);
		}
	});

	$("#asc-input").on("click", function () {
		const filters = $("input").serialize();
		if (query_params.sort != "asc") {
			scroll_up_and_update_params(filters + "&sort=asc");
		}
	});

	$("[name=card]").on("click", function () {
		window.location.href = this.id;
	});

	function show_applied_filters() {
		const allowed_filters = Object.keys(
			JSON.parse($("#data").data("filters").replace(/'/g, '"'))
		);
		$("#desc-input").prop("checked", true);
		for (const filter in query_params) {
			if (filter === "query") {
				$("#search-box").val(query_params["query"]);
			} else if (filter === "sort") {
				if (query_params["sort"] === "asc") {
					$("#asc-input").prop("checked", true);
					$("#desc-input").prop("checked", false);
				}
			} else if (allowed_filters.includes(filter)) {
				if (typeof query_params[filter] === "string") {
					$("#" + $.escapeSelector(query_params[filter])).prop("checked", true);
				} else {
					for (const d of query_params[filter])
						$("#" + $.escapeSelector(d)).prop("checked", true);
				}
			} else {
				continue;
			}
		}
	}

	function get_new_params() {
		return "sort" in query_params
			? $("input").serialize() + "&" + $.param({ sort: query_params["sort"] })
			: $("input").serialize();
	}
});

function scroll_up_and_update_params(params = "") {
	if (window.scrollY === 0) {
		window.location.href = "/jobs?" + params;
	} else {
		window.scroll({
			top: 0,
			behavior: "smooth",
		});
		window.addEventListener("scroll", function () {
			if (window.scrollY === 0) {
				window.location.href = "/jobs?" + params;
			}
		});
	}
}
