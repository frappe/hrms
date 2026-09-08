frappe.provide("hrms.telemetry");

// HR workspaces shown on the desk sidebar (see hrms/hr/workspace + payroll/workspace).
const HR_WORKSPACES = new Set([
	"HR",
	"HR Setup",
	"Leaves",
	"Shift & Attendance",
	"Expenses",
	"Performance",
	"Recruitment",
	"Tenure",
	"Payroll",
]);

// Key HR doctypes worth tracking navigation into. Kept explicit so we only ever
// emit HR-relevant events and never generic desk traffic.
const HR_DOCTYPES = new Set([
	"Employee",
	"Employee Checkin",
	"Attendance",
	"Attendance Request",
	"Leave Application",
	"Leave Allocation",
	"Leave Type",
	"Leave Policy",
	"Shift Type",
	"Shift Assignment",
	"Shift Request",
	"Expense Claim",
	"Salary Structure",
	"Salary Structure Assignment",
	"Salary Slip",
	"Payroll Entry",
	"Payroll Period",
	"Job Opening",
	"Job Applicant",
	"Job Offer",
	"Interview",
	"Appraisal",
	"Appraisal Cycle",
	"Appraisal Template",
	"Employee Onboarding",
	"Employee Separation",
]);

// HR + Payroll reports (query/script reports). Scoped explicitly so we learn which
// HR reports get used frequently, without capturing unrelated desk report traffic.
const HR_REPORTS = new Set([
	"Monthly Attendance Sheet",
	"Shift Attendance",
	"Employees working on a holiday",
	"Employee Leave Balance",
	"Employee Leave Balance Summary",
	"Leave Ledger",
	"Employee Analytics",
	"Employee Information",
	"Employee Birthday",
	"Employee Exits",
	"Employee Advance Summary",
	"Employee Hours Utilization Based On Timesheet",
	"Recruitment Analytics",
	"Appraisal Overview",
	"Unpaid Expense Claim",
	"Vehicle Expenses",
	"Project Profitability",
	"Salary Register",
	"Salary Payments Based On Payment Mode",
	"Salary Payments via ECS",
	"Bank Remittance",
	"Employee CTC Break-up",
	"Accrued Earnings Report",
	"Income Tax Computation",
	"Income Tax Deductions",
	"Professional Tax Deductions",
	"Provident Fund Deductions",
	"Daily Work Summary Replies",
]);

function hr_capture(event, props) {
	if (!frappe.telemetry?.enabled) return;
	try {
		frappe.telemetry.capture(event, "hrms", props || {});
	} catch (e) {
		// telemetry must never break navigation
	}
}

// Turn the current route into a semantic HR event, or null if it's not HR.
function classify(route) {
	if (!route || !route.length) return null;
	const head = route[0];

	if (head === "Workspaces") {
		// ["Workspaces", Name] or ["Workspaces", "private", Name]
		const name = route[route.length - 1];
		if (HR_WORKSPACES.has(name)) {
			return { event: "viewed_workspace", props: { workspace: name } };
		}
		return null;
	}

	if (head === "List" && HR_DOCTYPES.has(route[1])) {
		return {
			event: "viewed_list",
			props: { doctype: route[1], view: route[2] || "List" },
		};
	}

	if (head === "Form" && HR_DOCTYPES.has(route[1])) {
		const name = route[2];
		const is_new = typeof name === "string" && name.startsWith("new-");
		return {
			event: is_new ? "started_creating" : "viewed_form",
			props: { doctype: route[1] },
		};
	}

	if ((head === "query-report" || head === "report") && HR_REPORTS.has(route[1])) {
		return { event: "viewed_report", props: { report: route[1] } };
	}

	return null;
}

// The draft the user is currently sitting on, if it is an unsaved HR document.
let pending_draft = null;

// How far into the form the user got, as a count. Values themselves are never
// read — only whether each field holds something.
function count_filled_fields(doctype, draft) {
	try {
		const meta = frappe.get_meta(doctype);
		if (!meta) return null;
		return meta.fields.filter((df) => {
			if (frappe.model.no_value_type.includes(df.fieldtype)) return false;
			const value = draft[df.fieldname];
			return value !== undefined && value !== null && value !== "";
		}).length;
	} catch (e) {
		return null;
	}
}

// A saved document is renamed away from its `new-…` key, so a draft still
// sitting in `locals` when we leave the route was abandoned rather than saved.
function resolve_pending_draft(route) {
	if (!pending_draft) return;

	const { doctype, name } = pending_draft;
	if (route[0] === "Form" && route[1] === doctype && route[2] === name) return;

	const draft = locals?.[doctype]?.[name];
	if (draft) {
		hr_capture("creation_abandoned", {
			doctype,
			fields_filled: count_filled_fields(doctype, draft),
		});
	}
	pending_draft = null;
}

function remember_pending_draft(route) {
	const name = route[2];
	const is_new =
		route[0] === "Form" &&
		HR_DOCTYPES.has(route[1]) &&
		typeof name === "string" &&
		name.startsWith("new-");

	pending_draft = is_new ? { doctype: route[1], name } : null;
}

function track_route() {
	const route = frappe.get_route() || [];
	resolve_pending_draft(route);

	const hit = classify(route);
	if (hit) hr_capture(hit.event, hit.props);

	remember_pending_draft(route);
}

function track_landing() {
	try {
		if (sessionStorage.getItem("hrms_landing_tracked")) return;
		sessionStorage.setItem("hrms_landing_tracked", "1");
	} catch (e) {
		// private mode / storage disabled — fall through and still capture once
	}

	const route = frappe.get_route() || [];
	const hit = classify(route);
	hr_capture("landed_on_desk", {
		route_type: route[0] || "",
		landed_in_hr: Boolean(hit),
		...(hit ? hit.props : {}),
	});
}

$(document).on("app_ready", function () {
	if (!frappe.telemetry?.enabled) return;

	// Defer to the next tick so the first route is fully resolved.
	frappe.after_ajax(() => {
		track_landing();
		track_route();
		frappe.router.on("change", track_route);
	});

	// Closing the tab on a half-filled form is abandonment too. Best effort —
	// the event is dropped if the provider has not flushed by the time the page
	// goes away, so treat this as a floor on the real count.
	window.addEventListener("pagehide", () => resolve_pending_draft([]), { capture: true });
});
