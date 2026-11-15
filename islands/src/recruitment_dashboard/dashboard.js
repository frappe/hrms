import { getTargets } from "./drilldown.js";

const __ = (text, args) => window.__(text, args);

export const PERIODS = [
	{ key: "last_30_days", label: "Last 30 days" },
	{ key: "last_90_days", label: "Last 90 days" },
	{ key: "this_quarter", label: "This quarter" },
	{ key: "this_year", label: "This year" },
];

export const STAGES = ["Applied", "Shortlisted", "Interviewing", "Offered", "Hired"];
export const OUTCOMES = ["Applied only", "Interviewed", "Hired"];
// the API sends statuses; these are their names on the donuts
const OFFER_LABELS = {
	Accepted: __("Accepted"),
	Rejected: __("Declined"),
	"Awaiting Response": __("Awaiting reply"),
};
const INTERVIEW_LABELS = {
	Cleared: __("Cleared"),
	Rejected: __("Rejected"),
	Pending: __("Pending"),
	"Under Review": __("Under review"),
	Cancelled: __("Cancelled"),
};

/** The API's numbers in the shape Dashboard.vue draws, with its copy. Empty while loading. */
export function getView(data) {
	if (!data) return getEmptyView();
	const empty = !data.applications;
	return {
		empty,
		targets: empty ? null : getTargets(data),
		...getCards(data, empty),
		chartTitle: getChartTitle(data.openings),
		attention: empty ? undefined : getAttentionLine(data.openings.attention),
		chartRows: empty ? [] : data.openings.rows,
		funnel: empty
			? []
			: data.funnel.map((row) => ({
					stage: __(row.stage),
					key: row.stage,
					count: row.count,
			  })),
		funnelCaption: getFunnelCaption(data.funnel),
		sourceNames: data.weekly.sources,
		weeklySources: empty
			? []
			: data.weekly.rows.map((row) => ({ ...row, week: formatWeek(row.week) })),
		sources: empty ? [] : data.sources,
		offers: empty ? [] : getSlices(data.offers, OFFER_LABELS),
		offersSubtitle: empty ? undefined : getOffersSubtitle(data.offers),
		interviews: empty ? [] : getSlices(data.interviews, INTERVIEW_LABELS),
		interviewsSubtitle: empty ? undefined : getInterviewsSubtitle(data.interviews),
	};
}

function getCards(data, empty) {
	const { positions, time_to_hire: timeToHire, not_reviewed: notReviewed } = data;
	return {
		openRoles: data.open_roles,
		positionsCaption: positions === 1 ? __("1 position") : __("{0} positions", [positions]),
		hired: empty ? null : data.hired,
		hiredCaption: positions === 1 ? __("of 1 position") : __("of {0} positions", [positions]),
		// the caption keeps the real count; the bar stops at full
		hiredPercent: positions ? Math.min(Math.round((data.hired / positions) * 100), 100) : null,
		applications: empty ? null : data.applications,
		applicationsDelta: empty ? null : data.applications_delta,
		applicationsCaption:
			empty || data.applications_delta == null
				? undefined
				: __("vs previous {0} days", [data.days]),
		timeToHire: empty || !timeToHire ? null : timeToHire.days,
		timeToHireCaption: empty || !timeToHire ? undefined : getHiresCaption(timeToHire.hires),
		notReviewed: empty ? null : notReviewed.count,
		notReviewedCaption: empty ? undefined : getOldestCaption(notReviewed.oldest_days),
	};
}

function getEmptyView() {
	return {
		empty: true,
		targets: null,
		chartTitle: __("Openings"),
		chartRows: [],
		funnel: [],
		sourceNames: [],
		weeklySources: [],
		sources: [],
		offers: [],
		interviews: [],
	};
}

function getChartTitle({ rows, total }) {
	if (total > rows.length) return __("Openings · top {0} of {1}", [rows.length, total]);
	return __("Openings");
}

function getAttentionLine(rows) {
	if (!rows.length) return undefined;
	if (rows.length === 1) return __("1 needs attention: {0}", [getReason(rows[0])]);
	if (rows.length === 2) return __("2 need attention: {0}", [rows.map(getReason).join(", ")]);
	return __("{0} need attention, starting with {1}", [rows.length, getReason(rows[0])]);
}

function getReason(row) {
	if (row.reason === "no_applicants") return __("{0} has no applicants", [row.title]);
	if (row.days === 1) return __("{0} is 1 day past closing", [row.title]);
	return __("{0} is {1} days past closing", [row.title, row.days]);
}

function getFunnelCaption(funnel) {
	const count = (stage) => funnel.find((row) => row.stage === stage)?.count;
	return __("{0} of {1} applicants hired", [count("Hired"), count("Applied")]);
}

function getOffersSubtitle(offers) {
	const count = (status) => offers.find((row) => row.status === status)?.count || 0;
	const answered = count("Accepted") + count("Rejected");
	if (!answered) return undefined;
	return __("{0} of {1} answered offers accepted", [count("Accepted"), answered]);
}

function getInterviewsSubtitle(interviews) {
	const count = (status) => interviews.find((row) => row.status === status)?.count || 0;
	const decided = count("Cleared") + count("Rejected");
	if (!decided) return undefined;
	return __("{0} of {1} decided interviews cleared", [count("Cleared"), decided]);
}

function getHiresCaption(hires) {
	return hires === 1 ? __("across 1 hire") : __("across {0} hires", [hires]);
}

function getOldestCaption(days) {
	if (days == null) return undefined;
	if (days === 0) return __("oldest today");
	return days === 1 ? __("oldest 1 day") : __("oldest {0} days", [days]);
}

/** Slices of a donut, or none when every count is 0, so the chart shows its empty state. */
function getSlices(rows, labels) {
	if (!rows.some((row) => row.count > 0)) return [];
	return rows.map((row) => ({ name: labels[row.status], status: row.status, count: row.count }));
}

function formatWeek(week) {
	return window.moment(week).format("D MMM");
}
