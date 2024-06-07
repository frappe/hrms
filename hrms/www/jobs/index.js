$(() => {
	const query_params = frappe.utils.get_query_params();
	update_ui_with_filters();

	$(".desktop-filters").change(function () {
		update_params(get_new_params(".desktop-filters"));
	});

	$("#apply-filters").on("click", function () {
		update_params(get_new_params(".mobile-filters"));
	});

	$("[name=clear-filters]").on("click", function () {
		update_params();
	});

	$("#filter").click(function () {
		scroll_up_and_execute(() => {
			$("#filters-drawer").css("bottom", 0);
			$("#overlay").show();
			$("html, body").css({
				overflow: "hidden",
				height: "100%",
			});
		});
	});

	$("[name=close-filters-drawer").click(function () {
		$("#filters-drawer").css("bottom", "-80vh");
		$("#overlay").hide();
		$("html, body").css({
			overflow: "auto",
			height: "auto",
		});
	});

	$("#search-box").bind("search", function () {
		update_params(get_new_params(".desktop-filters"));
	});

	$("#search-box").keyup(function (e) {
		if (e.keyCode == 13) {
			$(this).trigger("search");
		}
	});

	$("#sort").on("click", function () {
		const filters = $(".desktop-filters").serialize();
		query_params.sort === "asc"
			? update_params(filters)
			: update_params(filters + "&sort=asc");
	});

	$("[name=card]").on("click", function () {
		window.location.href = this.id;
	});

	$("[name=pagination]").on("click", function () {
		const filters = $(".desktop-filters").serialize();
		update_params(filters + "&page=" + this.id);
	});

	$("#previous").on("click", function () {
		const new_page = (Number(query_params?.page) || 1) - 1;
		const filters = $(".desktop-filters").serialize();
		update_params(filters + "&page=" + new_page);
	});

	$("#next").on("click", function () {
		const new_page = (Number(query_params?.page) || 1) + 1;
		const filters = $(".desktop-filters").serialize();
		update_params(filters + "&page=" + new_page);
	});

	function update_ui_with_filters() {
		const allowed_filters = Object.keys(
			JSON.parse($("#data").data("filters").replace(/'/g, '"')),
		);

		for (const filter in query_params) {
			if (filter === "query") $("#search-box").val(query_params["query"]);
			else if (filter === "page") disable_inapplicable_pagination_buttons();
			else if (allowed_filters.includes(filter)) {
				if (typeof query_params[filter] === "string") {
					$("#desktop-" + $.escapeSelector(query_params[filter])).prop("checked", true);
					$("#mobile-" + $.escapeSelector(query_params[filter])).prop("checked", true);
				} else
					for (const d of query_params[filter]) {
						$("#desktop-" + $.escapeSelector(d)).prop("checked", true);
						$("#mobile-" + $.escapeSelector(d)).prop("checked", true);
					}
			} else continue;
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

	function get_new_params(filter_group) {
		return "sort" in query_params
			? $(filter_group).serialize() + "&" + $.param({ sort: query_params["sort"] })
			: $(filter_group).serialize();
	}
});

function update_params(params = "") {
	if ($("#filters-drawer").css("bottom") != "0px")
		return scroll_up_and_execute(() => (window.location.href = "/jobs?" + params));

	$("#filters-drawer").css("bottom", "-80vh");
	$("#filters-drawer").on("transitionend webkitTransitionEnd oTransitionEnd", () =>
		scroll_up_and_execute(() => (window.location.href = "/jobs?" + params)),
	);
}

function scroll_up_and_execute(callback) {
	if (window.scrollY === 0) return callback();

	function execute_after_scrolling_up() {
		if (window.scrollY === 0) {
			callback();
			window.removeEventListener("scroll", execute_after_scrolling_up);
		}
	}

	window.scroll({
		top: 0,
		behavior: "smooth",
	});
	window.addEventListener("scroll", execute_after_scrolling_up);
}
