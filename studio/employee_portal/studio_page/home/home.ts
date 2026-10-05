import { computed } from "vue";
import { dayjs, toast, useCall } from "frappe-ui";
import { ROUTES, inboxItem } from "@app/routes";
import { useSession } from "@app/stores/session";
import { __ } from "@app/utils/translation";

type Person = { name: string; image: string | null };
type Todo = {
	id: string;
	kind: "leave_approval" | "expense_approval" | "self_appraisal" | "onboarding";
	title: string;
	subtitle?: string;
	icon?: string;
	person?: Person;
	starts?: string;
	sent?: string;
	due?: string;
};
type Upcoming = {
	kind: "leave" | "holiday" | "probation";
	title: string;
	date: string;
	days?: number;
	approved?: boolean;
	months?: number;
};
type CompanyEvent = {
	employee_name: string;
	image: string | null;
	kind: "birthday" | "work_anniversary";
	years?: number;
};
type HomeData = {
	shift: { shift_type: string | null; last_log_type: "IN" | "OUT" | null };
	leave_balance: number;
	absent_count: number;
	first_month: { day: number; of: number } | null;
	todos: Todo[];
	upcoming: Upcoming[];
	out_today: { employee_name: string; image: string | null; back_on: string }[];
	events: CompanyEvent[];
	company: string;
};

const TODO_LIMIT = 5;
// approvals for leave starting within these many days go first
const URGENT_DAYS = 3;

export default function setup(context) {
	const session = useSession();
	const home = useCall<HomeData>({
		url: "/api/v2/method/hrms.api.portal.get_home",
		cacheKey: "employee-portal-home-v3",
	});
	const shift = useShift(home, session);
	const todos = computed(() => sortTodos(home.data?.todos ?? []).map(toTodoRow));

	// from search's Check in; drop the flag first so a refresh doesn't check in again
	if (context.route?.query?.checkin) {
		context.router.replace({ query: {} });
		home.promise.then(shift.checkInFromSearch);
	}

	return {
		...session,
		ROUTES,
		greetingLine: computed(() => `${greeting()}, ${session.firstName.value}`),
		dateLabel: dayjs().format("dddd, D MMMM"),
		outToday: computed(() => (home.data?.out_today ?? []).map(toAwayPerson)),
		outTodayLabel: computed(() => __("{0} out today", [home.data?.out_today?.length ?? 0])),
		stats: computed(() => [shift.stat.value, leaveStat(home.data), thirdStat(home.data)]),
		todoRows: computed(() => todos.value.slice(0, TODO_LIMIT)),
		todoCount: computed(() => todos.value.length),
		hasMoreTodos: computed(() => todos.value.length > TODO_LIMIT),
		upcomingRows: computed(() => (home.data?.upcoming ?? []).map(toUpcomingRow)),
		eventRows: computed(() => (home.data?.events ?? []).map(toEventRow)),
		eventsTitle: computed(() => __("Today at {0}", [home.data?.company ?? ""])),
	};
}

function useShift(home, session) {
	const checkIn = useCall<unknown, { log_type: string; latitude?: number; longitude?: number }>({
		url: "/api/v2/method/hrms.api.portal.check_in",
		method: "POST",
		immediate: false,
	});

	const shift = computed(() => home.data?.shift);
	const state = computed(() => {
		if (!shift.value?.last_log_type) return "out";
		return shift.value.last_log_type === "IN" ? "in" : "done";
	});

	async function submitLog() {
		const logType = state.value === "in" ? "OUT" : "IN";
		const location = session.checkinNeedsLocation.value ? await currentLocation() : {};
		try {
			await checkIn.submit({ log_type: logType, ...location });
		} catch (error) {
			return toast.error(error.message || __("Could not check in"));
		}
		toast.success(logType === "IN" ? __("Checked in") : __("Checked out"));
		home.reload();
	}

	function checkInFromSearch() {
		if (state.value === "in") return toast.info(__("You are already checked in"));
		if (state.value === "done") return toast.info(__("You have checked out for today"));
		return submitLog();
	}

	// no action after checking out for the day
	const stat = computed(() => {
		const label = shift.value?.shift_type || __("Today");
		const action = session.checkinEnabled.value
			? {
					label: state.value === "in" ? __("Check out") : __("Check in"),
					icon: state.value === "in" ? "lucide-log-out" : "lucide-log-in",
					loading: checkIn.loading,
					onClick: submitLog,
			  }
			: undefined;

		if (state.value === "in") {
			return {
				label,
				value: __("Checked in"),
				action: action && { ...action, variant: "subtle" },
			};
		}
		if (state.value === "done") {
			return { label, value: __("Checked out") };
		}
		return {
			label,
			value: __("Not checked in"),
			action: action && { ...action, variant: "solid" },
		};
	});

	return { stat, checkInFromSearch };
}

function leaveStat(data?: HomeData) {
	return {
		label: __("Leave balance"),
		value: days(data?.leave_balance ?? 0),
		action: { label: __("Apply leave"), icon: "lucide-palmtree", route: ROUTES.applyLeave },
	};
}

// new joiners see their onboarding day instead of absences
function thirdStat(data?: HomeData) {
	if (data?.first_month) {
		return {
			label: __("First month"),
			value: __("Day {0} of {1}", [data.first_month.day, data.first_month.of]),
			action: {
				label: __("View plan"),
				icon: "lucide-list-checks",
				route: ROUTES.firstMonth,
			},
		};
	}
	return {
		label: __("Absent this month"),
		value: data?.absent_count ?? 0,
		action: {
			label: __("View calendar"),
			icon: "lucide-calendar-days",
			route: ROUTES.attendance,
		},
	};
}

function sortTodos(todos: Todo[]) {
	return [...todos].sort((a, b) => todoClock(a).sort - todoClock(b).sort);
}

function todoClock(todo: Todo) {
	if (todo.kind === "leave_approval" || todo.kind === "expense_approval") {
		const startsIn = todo.starts ? daysFromToday(todo.starts) : Infinity;
		if (startsIn <= URGENT_DAYS)
			return { label: startsLabel(startsIn), urgent: true, sort: -1000 + startsIn };
		const waited = -daysFromToday(todo.sent);
		return { label: relative(todo.sent), urgent: false, sort: 50 - waited / 1000 };
	}
	if (!todo.due) return { label: "", urgent: false, sort: 99 };
	const dueIn = daysFromToday(todo.due);
	return {
		label: dueIn < 0 ? __("Overdue") : relative(todo.due),
		urgent: dueIn <= 1,
		sort: dueIn,
	};
}

function toTodoRow(todo: Todo) {
	const clockLabel = todoClock(todo);
	return {
		key: todo.id,
		lead: todo.person
			? { kind: "person", name: todo.person.name, image: todo.person.image }
			: { kind: "icon", icon: todo.icon ?? "lucide-circle" },
		title: todo.title,
		subtitle: todo.person ? todo.person.name : todo.subtitle,
		trailing: clockLabel.label,
		urgent: clockLabel.urgent,
		route: inboxItem(todo.id),
	};
}

function toUpcomingRow(row: Upcoming) {
	const date = dayjs(row.date);
	const subtitles = {
		leave: row.approved
			? __("{0}, approved", [days(row.days ?? 0)])
			: __("{0}, waiting for approval", [days(row.days ?? 0)]),
		holiday: __("Holiday"),
		probation: __("{0} months since you joined", [row.months ?? 0]),
	};
	return {
		key: `${row.kind}:${row.date}:${row.title}`,
		lead: {
			kind: "date",
			month: date.format("MMM"),
			day: date.format("D"),
			muted: row.kind === "leave" && !row.approved,
		},
		title: row.title,
		subtitle: subtitles[row.kind],
		trailing: inDays(daysFromToday(row.date)),
	};
}

function toEventRow(event: CompanyEvent) {
	const reasons = {
		birthday: { trailing: __("Birthday"), trailingIcon: "lucide-cake" },
		work_anniversary: {
			trailing:
				event.years === 1 ? __("1 year today") : __("{0} years today", [event.years]),
			trailingIcon: "lucide-party-popper",
		},
	};
	return {
		key: `${event.kind}:${event.employee_name}`,
		lead: { kind: "person", name: event.employee_name, image: event.image },
		title: event.employee_name,
		...reasons[event.kind],
	};
}

function toAwayPerson(person: HomeData["out_today"][number]) {
	return {
		name: person.employee_name,
		image: person.image,
		sub: __("Back {0}", [dayjs(person.back_on).format("ddd D MMM")]),
	};
}

function greeting() {
	const hour = dayjs().hour();
	if (hour < 12) return __("Good morning");
	if (hour < 17) return __("Good afternoon");
	return __("Good evening");
}

function daysFromToday(date?: string) {
	return dayjs(date).startOf("day").diff(dayjs().startOf("day"), "day");
}

function relative(date?: string) {
	const diff = daysFromToday(date);
	if (diff === 0) return __("Today");
	if (diff === 1) return __("Tomorrow");
	if (diff === -1) return __("Yesterday");
	if (diff < 0 && diff > -7) return __("{0} days ago", [-diff]);
	if (diff > 1 && diff < 7) return dayjs(date).format("ddd");
	return dayjs(date).format("D MMM");
}

function startsLabel(startsIn: number) {
	if (startsIn <= 0) return __("Starts today");
	if (startsIn === 1) return __("Starts tomorrow");
	return __("Starts in {0} days", [startsIn]);
}

function inDays(diff: number) {
	if (diff === 0) return __("Today");
	if (diff === 1) return __("Tomorrow");
	return __("in {0} days", [diff]);
}

function days(count: number) {
	const rounded = Number(count.toFixed(1));
	return rounded === 1 ? __("1 day") : __("{0} days", [rounded]);
}

function currentLocation(): Promise<{ latitude?: number; longitude?: number }> {
	return new Promise((resolve) => {
		if (!navigator.geolocation) return resolve({});
		navigator.geolocation.getCurrentPosition(
			(position) =>
				resolve({
					latitude: position.coords.latitude,
					longitude: position.coords.longitude,
				}),
			() => resolve({}),
		);
	});
}
