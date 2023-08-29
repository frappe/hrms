$(() => {
	const query_params = frappe.utils.get_query_params();
	for (const filter in query_params) {
		if (typeof query_params[filter] === "string") {
			$("#" + $.escapeSelector(query_params[filter])).prop("checked", true);
		} else {
			for (const d of query_params[filter])
				$("#" + $.escapeSelector(d)).prop("checked", true);
		}
	}
	$("input:checkbox").change(function () {
		const filters = $("input:checked").serialize();
		window.location.href = "/jobs?" + filters;
	});
});
