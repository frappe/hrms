import { computed, reactive } from "vue";
import { createResource } from "frappe-ui";

function cookies() {
	return Object.fromEntries(
		document.cookie
			.split("; ")
			.filter(Boolean)
			.map((c) => {
				const i = c.indexOf("=");
				return [c.slice(0, i), decodeURIComponent(c.slice(i + 1))];
			}),
	);
}

function currentUser() {
	const value = cookies().user_id;
	return value && value !== "Guest" ? value : null;
}

// frappe's logout is declared methods=["POST"], so navigating to it raises a
// permission error instead of logging out. It has to be an actual POST.
const logoutResource = createResource({
	url: "logout",
	onSuccess() {
		session.user = null;
		// full reload rather than a route push: it clears every cached resource
		// and lets the server decide where a signed-out visitor belongs
		window.location.href = "/login";
	},
});

export const session = reactive({
	user: currentUser(),
	isLoggedIn: computed(() => !!session.user),
	logout: logoutResource,
});
