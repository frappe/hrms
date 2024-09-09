import dayjs from "@/utils/dayjs"

export const getDates = (shift) => {
	const fromDate = dayjs(shift.from_date).format("D MMM")
	const toDate = shift.to_date ? dayjs(shift.to_date).format("D MMM") : "Ongoing"
	return fromDate == toDate ? fromDate : `${fromDate} - ${toDate}`
}

export const getTotalDays = (shift) => {
	if (!shift.to_date) return null
	const toDate = dayjs(shift.to_date)
	const fromDate = dayjs(shift.from_date)
	return toDate.diff(fromDate, "d") + 1
}

export const getShiftDates = (shift) => {
	const startDate = dayjs(shift.start_date).format("D MMM")
	const endDate = shift.end_date ? dayjs(shift.end_date).format("D MMM") : "Ongoing"
	return startDate == endDate ? startDate : `${startDate} - ${endDate}`
}

export const getTotalShiftDays = (shift) => {
	if (!shift.end_date) return null
	const end_date = dayjs(shift.end_date)
	const start_date = dayjs(shift.start_date)
	return end_date.diff(start_date, "d") + 1
}

export const getShiftTiming = (shift) => {
	return (
		shift.start_time.split(":").slice(0, 2).join(":") +
		" - " +
		shift.end_time.split(":").splice(0, 2).join(":")
	)
}
