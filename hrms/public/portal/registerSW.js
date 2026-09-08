if ("serviceWorker" in navigator) {
	window.addEventListener("load", () => {
		navigator.serviceWorker.register("/assets/hrms/portal/sw.js", {
			scope: "/assets/hrms/portal/",
		});
	});
}
