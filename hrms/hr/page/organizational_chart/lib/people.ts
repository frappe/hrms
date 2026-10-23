// People: one store for the directory and the org chart, from `get_people` (every Active
// employee the user can read, with who is on leave today and each person's report count).
import { computed, ref } from "vue";
import { dayjs } from "frappe-ui";

declare const __: (text: string, args?: unknown[]) => string;

export interface Staff {
	id: string;
	name: string;
	role: string;
	office: string;
	manager: string | null;
	email: string;
	joined: string;
	photo?: string;
	dob?: string;
	dept: string;
	userId: string;
	out?: boolean;
	away?: string;
}

export type Moment = {
	kind: "out" | "birthday" | "new" | "anniversary";
	label: string;
	icon?: string;
};

const ISO = "YYYY-MM-DD";
export const today = () => dayjs().startOf("day");

// ---- load -------------------------------------------------------------------------------
export const staff = ref<Staff[]>([]);
export const ready = ref(false);
export const failed = ref(false);
let loading: Promise<void> | null = null;

// Loads once; `refresh` loads again without blanking the page.
export function loadPeople(refresh = false) {
	if (!loading || refresh) {
		loading = fetchStaff()
			.then(() => (failed.value = false))
			.catch(() => (failed.value = true))
			.finally(() => (ready.value = true));
	}
	return loading;
}

async function fetchStaff() {
	const response = await fetch(
		"/api/method/hrms.hr.page.organizational_chart.organizational_chart.get_people",
		{
			credentials: "same-origin",
			headers: { Accept: "application/json" },
		},
	);
	if (!response.ok) throw new Error(`get_people ${response.status}`);
	const rows: any[] = (await response.json()).message;
	const now = today().format(ISO);
	const list: Staff[] = rows
		// someone who has not started yet is not on the chart
		.filter((r) => !r.date_of_joining || r.date_of_joining <= now)
		.map((r) => ({
			id: r.name,
			name: r.employee_name,
			role: r.designation || "",
			office: r.branch || "",
			manager: r.reports_to || null,
			email: r.company_email || "",
			joined: r.date_of_joining || now,
			photo: r.image || undefined,
			dob: r.date_of_birth || undefined,
			dept: r.department_name || "",
			userId: r.user_id || "",
			out: !!r.on_leave_today,
			away: r.on_leave_today ? awayLabel(r) : undefined,
		}));
	// A manager who is not on the chart hangs their reports from nobody.
	const ids = new Set(list.map((p) => p.id));
	for (const p of list) if (p.manager && !ids.has(p.manager)) p.manager = null;
	staff.value = list;
	deriveDepartments();
}

// The server works out the back date from the employee's own holiday list.
function awayLabel(leave: any) {
	if (leave.leave_half_day) return __("Half day");
	return __("Back {0}", [dayjs(leave.leave_back_date).format("ddd D")]);
}

// A person with no department takes their manager's.
function deriveDepartments() {
	const map = byId.value;
	for (const p of staff.value) {
		const own = (d: string) => (d && d !== "All Departments" ? d : "");
		let cur: Staff | undefined = p;
		let dept = own(p.dept);
		for (let hops = 0; !dept && cur?.manager && hops < 8; hops++) {
			cur = map[cur.manager];
			dept = own(cur?.dept || "");
		}
		p.dept = dept || __("Other");
	}
}

// ---- lookups ----------------------------------------------------------------------------
export const byId = computed<Record<string, Staff>>(() =>
	Object.fromEntries(staff.value.map((p) => [p.id, p])),
);
const reportsCount = (id: string) => staff.value.filter((p) => p.manager === id).length;
export const reportsOf = (id: string) =>
	staff.value
		.filter((p) => p.manager === id)
		.sort((a, b) => reportsCount(b.id) - reportsCount(a.id) || a.name.localeCompare(b.name));

// Managers from the nearest up to the top. A loop in reports_to stops where it comes back round.
export function chainOf(id: string) {
	const out: string[] = [];
	const seen = new Set([id]);
	let cur = byId.value[id];
	while (cur?.manager && !seen.has(cur.manager)) {
		out.push(cur.manager);
		seen.add(cur.manager);
		cur = byId.value[cur.manager];
	}
	return out;
}

export const deptOf = (id: string) => byId.value[id]?.dept || "";
export const isHead = (id: string) => {
	const p = byId.value[id];
	return !!p && (!p.manager || deptOf(p.manager) !== p.dept);
};
export const DEPT_ORDER = computed(() => {
	const present = [...new Set(staff.value.map((p) => p.dept))];
	const other = __("Other");
	return [
		...present.filter((d) => d !== other).sort(),
		...(present.includes(other) ? [other] : []),
	];
});
export const OFFICES = computed(() =>
	[...new Set(staff.value.map((p) => p.office).filter(Boolean))].sort(),
);

const subtree = (id: string): number => reportsOf(id).reduce((n, p) => n + 1 + subtree(p.id), 0);
// Everyone without a manager tops a tree of their own; the biggest tree comes first.
export const rootIds = computed(() =>
	staff.value
		.filter((p) => !p.manager)
		.map((p) => ({ id: p.id, name: p.name, size: subtree(p.id) }))
		.sort((a, b) => b.size - a.size || a.name.localeCompare(b.name))
		.map((p) => p.id),
);

// ---- who is looking ---------------------------------------------------------------------
// The session's employee. Administrator and anyone without an employee record have none.
export const meId = computed(() => {
	const user = (window as any).frappe?.session?.user;
	return staff.value.find((p) => p.userId && p.userId === user)?.id || "";
});

// ---- moments ----------------------------------------------------------------------------
// The next (or latest) time a month and day came round, as a signed number of days from today.
function daysFromToday(date: string) {
	const t = today();
	const d = dayjs(date);
	return [-1, 0, 1]
		.map((k) =>
			d
				.year(t.year() + k)
				.startOf("day")
				.diff(t, "day"),
		)
		.sort((a, b) => Math.abs(a) - Math.abs(b))[0];
}

const WINDOW = 7;
const near = (days: number) => Math.abs(days) <= WINDOW;
const onDay = (date: string) => dayjs(date).format("D MMM");

export function celebration(p?: Staff | null): Moment | null {
	if (!p) return null;
	if (p.dob) {
		const days = daysFromToday(p.dob);
		if (near(days))
			return {
				kind: "birthday",
				label: days === 0 ? __("Birthday today") : __("Birthday {0}", [onDay(p.dob)]),
				icon: "lucide-cake",
			};
	}
	const anniversary = daysFromToday(p.joined);
	const turning = today().add(anniversary, "day").year() - dayjs(p.joined).year();
	if (turning > 0 && near(anniversary))
		return {
			kind: "anniversary",
			label:
				anniversary === 0
					? __("{0} years today", [turning])
					: __("{0} years {1}", [turning, onDay(p.joined)]),
			icon: "lucide-party-popper",
		};
	return null;
}

// The one thing about a person that is true now: out, a birthday or anniversary this week, new.
export function momentOf(p?: Staff | null): Moment | null {
	if (!p) return null;
	if (p.out) return { kind: "out", label: p.away || __("On leave") };
	const c = celebration(p);
	if (c) return c;
	if (today().diff(dayjs(p.joined), "day") < 30)
		return { kind: "new", label: __("New hire"), icon: "lucide-sparkle" };
	return null;
}
