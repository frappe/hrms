import { toast } from "frappe-ui";

export { default as dayjs } from "./dayjs";

export const raiseToast = (type: "success" | "error", message: string) => {
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
