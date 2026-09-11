import { createApp } from "vue";
import { Button, FormControl, setConfig, frappeRequest, resourcesPlugin } from "frappe-ui";

import App from "./App.vue";
import router from "./router";
import { session } from "@/data/session";
import { bootstrap } from "@/data/portal";

import "./index.css";

const app = createApp(App);

setConfig("resourceFetcher", frappeRequest);
app.use(resourcesPlugin);
app.use(router);

app.component("Button", Button);
app.component("FormControl", FormControl);

app.provide("$session", session);

router.beforeEach(async (to, _, next) => {
	if (!session.isLoggedIn) {
		// router base is /hrms, so fullPath alone would send login back to a dead path
		window.location.href = `/login?redirect-to=${encodeURIComponent("/hrms" + to.fullPath)}`;
		return;
	}
	if (!bootstrap.data && !bootstrap.loading) {
		try {
			await bootstrap.fetch();
		} catch (e) {
			// the shell renders its own error state
		}
	}
	next();
});

router.isReady().then(async () => {
	if (import.meta.env.DEV) {
		try {
			const values = await frappeRequest({
				url: "/api/method/hrms.www.hrms.get_context_for_dev",
			});
			if (!window.frappe) window.frappe = {};
			window.frappe.boot = values;
		} catch (e) {
			// dev boot is best effort
		}
	}
	app.mount("#app");
});
