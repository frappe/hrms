export function __(message, replace = [], context) {
	if (window.__) return window.__(message, replace, context);
	return message.replace(/{(\d+)}/g, (match, index) => replace[index] ?? match);
}
