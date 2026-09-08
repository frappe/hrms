import { toast } from "frappe-ui";

export function notifySuccess(message, description) {
	toast.success(join(message, description));
}

export function notifyError(message, description) {
	toast.error(join(message, description));
}

export function notifyInfo(message, description) {
	toast.info(join(message, description));
}

function join(message, description) {
	return description ? `${message}. ${description}` : message;
}

export function errorMessage(e, fallback) {
	return e?.messages?.[0] || e?.message || fallback;
}
