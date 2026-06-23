import { toast } from "frappe-ui";

export { default as dayjs } from "./dayjs";

const TOAST_DEDUP_WINDOW_MS = 500;
let lastToast: { type: string; message: string; timestamp: number } | null = null;

export const raiseToast = (type: "success" | "error", message: string) => {
	const now = Date.now();
	if (
		lastToast &&
		lastToast.type === type &&
		lastToast.message === message &&
		now - lastToast.timestamp < TOAST_DEDUP_WINDOW_MS
	) {
		return;
	}

	if (type === "success") {
		const id = toast({
			title: "Success",
			text: message,
			icon: "check-circle",
			position: "bottom-right",
			iconClasses: "text-green-500",
		});
		lastToast = { type, message, timestamp: now };
		return id;
	}

	const div = document.createElement("div");
	div.innerHTML = message;
	// strip html tags
	const text =
		div.textContent || div.innerText || "Failed to perform action. Please try again later.";
	const id = toast({
		title: "Error",
		text: text,
		icon: "alert-circle",
		position: "bottom-right",
		iconClasses: "text-red-500",
		timeout: 7,
	});
	lastToast = { type, message, timestamp: now };
	return id;
};

export const goTo = (path: string) => {
	window.location.href = path;
};
