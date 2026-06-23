import { toast } from "frappe-ui";

export { default as dayjs } from "./dayjs";

let lastToast: { type: string; message: string; timestamp: number } | null = null;

export const raiseToast = (type: "success" | "error", message: string) => {
	const now = Date.now();
	if (
		lastToast &&
		lastToast.type === type &&
		lastToast.message === message &&
		now - lastToast.timestamp < 500
	) {
		return;
	}
	lastToast = { type, message, timestamp: now };

	if (type === "success")
		return toast({
			title: "Success",
			text: message,
			icon: "check-circle",
			position: "bottom-right",
			iconClasses: "text-green-500",
		});

	const div = document.createElement("div");
	div.innerHTML = message;
	// strip html tags
	const text =
		div.textContent || div.innerText || "Failed to perform action. Please try again later.";
	toast({
		title: "Error",
		text: text,
		icon: "alert-circle",
		position: "bottom-right",
		iconClasses: "text-red-500",
		timeout: 7,
	});
};

export const goTo = (path: string) => {
	window.location.href = path;
};
