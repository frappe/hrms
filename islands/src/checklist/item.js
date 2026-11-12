export function isFinished(item) {
	return Boolean(item.done || item.skipped);
}

export function hasBody(item, canRemove) {
	return Boolean(
		item.description ||
			item.actions?.length ||
			(item.skippable && !item.done) ||
			(item.removable && canRemove),
	);
}

export function getState(item) {
	if (item.done) return "done";
	if (item.skipped) return "skipped";
	return item.status || "pending";
}
