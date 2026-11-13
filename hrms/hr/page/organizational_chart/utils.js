const __ = window.__;
const lang = window.frappe.boot.lang;

// "Back Thu 18" within the next week, "Back 3 Nov" after that
export function leave_label(leave) {
	if (!leave) return "";
	if (leave.half_day) return __("Half day");
	if (!leave.back_on) return __("On leave");

	const back_on = new Date(`${leave.back_on}T00:00:00`);
	const days_away = (back_on - new Date()) / 86_400_000;
	const date =
		days_away < 7
			? `${back_on.toLocaleDateString(lang, { weekday: "short" })} ${back_on.getDate()}`
			: back_on.toLocaleDateString(lang, { day: "numeric", month: "short" });

	return __("Back {0}", [date]);
}
