/**
 * The list behind each number, filtered to exactly the records it counts. Null where no list
 * filter can find those records, such as a stage reached through interview or offer records.
 */
export function getTargets(data) {
	const applied = { creation: ["Between", [data.period.from, data.period.to]] };
	const applicants = (filters) => ({
		doctype: "Job Applicant",
		filters: { ...applied, ...filters },
	});
	const source = (name) => data.source_filters[name];
	const between = [data.period.from, data.period.to];

	return {
		openRoles: { doctype: "Job Opening", filters: { status: "Open" } },
		hired: applicants({ stage: "Hired" }),
		applications: applicants({}),
		notReviewed: applicants({ stage: "Applied", status: ["!=", "Hold"] }),
		funnel: (stage) => {
			if (stage === "Applied") return applicants({});
			return stage === "Hired" ? applicants({ stage: "Hired" }) : null;
		},
		opening: (row, stage) => applicants({ job_title: row.opening, stage }),
		week: (row, name) =>
			source(name)
				? {
						doctype: "Job Applicant",
						filters: {
							creation: ["Between", [row.from, row.to]],
							source: source(name),
						},
				  }
				: null,
		hiresBySource: (row, outcome) =>
			outcome === "Hired" && source(row.source)
				? applicants({ source: source(row.source), stage: "Hired" })
				: null,
		offer: (status) => ({
			doctype: "Job Offer",
			filters: { status, docstatus: 1, offer_date: ["Between", between] },
		}),
		interview: (status) => ({
			doctype: "Interview",
			filters: { status, docstatus: ["!=", 2], scheduled_on: ["Between", between] },
		}),
	};
}

/** The plain list view's route, with the target's filters as its only filters. */
export function getListRoute({ doctype, filters }) {
	const slug = doctype.toLowerCase().replaceAll(" ", "-");
	const query = new URLSearchParams(
		Object.entries(filters).map(([field, value]) => [
			field,
			typeof value === "object" ? JSON.stringify(value) : String(value),
		]),
	);
	return `/desk/${slug}/view/list?${query}`;
}
