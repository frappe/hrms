// The island entry for this page. Desk imports this module and calls `mount`.
//
// `mountVueIsland` opens the shadow root, adopts this app's stylesheet, mirrors
// desk's theme and gives frappe-ui's overlays a portal target inside the root.
import { mountVueIsland } from "@framework/ui/island";

import Page from "./employee_profile.vue";

export const mount = (el, context) => {
	// frappe-ui's FileUploader sends window.csrf_token, but Desk keeps the token on frappe.csrf_token
	window.csrf_token ||= window.frappe?.csrf_token;
	return mountVueIsland(el, { ...context, component: Page });
};
