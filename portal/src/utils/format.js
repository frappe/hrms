import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";

dayjs.extend(relativeTime);

export { dayjs };

let currency = "INR";
export function setCurrency(value) {
	if (value) currency = value;
}

/** `currency` overrides the company default, for documents raised in another one. */
export function money(value, { compact = false, currency: override } = {}) {
	if (value === null || value === undefined || value === "") return "—";
	const n = Number(value);
	if (Number.isNaN(n)) return "—";
	const code = override || currency;
	return new Intl.NumberFormat(code === "INR" ? "en-IN" : "en-US", {
		style: "currency",
		currency: code,
		maximumFractionDigits: compact || n % 1 === 0 ? 0 : 2,
	}).format(n);
}

export function date(value, format = "D MMM YYYY") {
	if (!value) return "—";
	return dayjs(value).format(format);
}

export function dateRange(from, to) {
	if (!from) return "—";
	if (!to || from === to) return date(from);
	const a = dayjs(from);
	const b = dayjs(to);
	if (a.year() === b.year() && a.month() === b.month()) {
		return `${a.format("D")} to ${b.format("D MMM YYYY")}`;
	}
	return `${a.format("D MMM")} to ${b.format("D MMM YYYY")}`;
}

export function time(value) {
	if (!value) return "—";
	return dayjs(value).format("HH:mm");
}

/** Seconds since a timestamp, for the running check-in timer. */
export function elapsed(since) {
	if (!since) return "00:00:00";
	const secs = Math.max(0, dayjs().diff(dayjs(since), "second"));
	const h = String(Math.floor(secs / 3600)).padStart(2, "0");
	const m = String(Math.floor((secs % 3600) / 60)).padStart(2, "0");
	const s = String(secs % 60).padStart(2, "0");
	return `${h}:${m}:${s}`;
}

export function shiftTiming(shift) {
	if (!shift || !shift.start_time) return null;
	const fmt = (t) => String(t).slice(0, 5);
	return `${fmt(shift.start_time)} to ${fmt(shift.end_time)}`;
}
