export const API = "hrms.hr.page.employee_profile.employee_profile";

// A day as the sketch writes it, 6 Nov, with the year only when it is not this year, in the order
// of the site's date format: 6 Nov for dd-mm-yyyy, Nov 6 for mm-dd-yyyy
export function short_date(value) {
	if (!value) return null;
	const [year, month, day] = String(value).split(" ")[0].split("-").map(Number);
	const month_name = new Date(2000, month - 1, 1).toLocaleDateString(window.frappe?.boot?.lang, {
		month: "short",
	});
	const day_first = !window.frappe?.boot?.sysdefaults?.date_format?.startsWith("mm");
	const text = day_first ? `${day} ${month_name}` : `${month_name} ${day}`;
	return year === new Date().getFullYear() ? text : `${text} ${year}`;
}
