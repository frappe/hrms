$(() => {
	const query_params = frappe.utils.get_query_params();
	update_ui_with_filters();

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

	$("#sort").on("click", function () {
		const filters = $("input").serialize();
		query_params.sort === "asc"
			? scroll_up_and_update_params(filters)
			: scroll_up_and_update_params(filters + "&sort=asc");
	});

	$("[name=card]").on("click", function () {
		window.location.href = this.id;
	});

	$("[name=pagination]").on("click", function () {
		const filters = $("input").serialize();
		scroll_up_and_update_params(filters + "&page=" + this.id);
	});

	$("#previous").on("click", function () {
		const new_page = (Number(query_params?.page) || 1) - 1;
		const filters = $("input").serialize();
		scroll_up_and_update_params(filters + "&page=" + new_page);
	});

	$("#next").on("click", function () {
		const new_page = (Number(query_params?.page) || 1) + 1;
		const filters = $("input").serialize();
		scroll_up_and_update_params(filters + "&page=" + new_page);
	});

	function update_ui_with_filters() {
		const allowed_filters = Object.keys(
			JSON.parse($("#data").data("filters").replace(/'/g, '"'))
		);
		for (const filter in query_params) {
			if (filter === "query") {
				$("#search-box").val(query_params["query"]);
			} else if (filter === "page") {
				disable_inapplicable_pagination_buttons();
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

	function disable_inapplicable_pagination_buttons() {
		const no_of_pages = JSON.parse($("#data").data("no-of-pages"));
		const page_no = Number(query_params["page"]);
		if (page_no === no_of_pages) {
			$("#next").prop("disabled", true);
		} else if (page_no > no_of_pages || page_no <= 1) {
			$("#previous").prop("disabled", true);
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
