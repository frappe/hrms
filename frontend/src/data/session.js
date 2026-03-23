import { computed, reactive } from "vue"
import { call } from "frappe-ui"
import { userResource } from "./user"
import { employeeResource } from "./employee"
import { redirectToAmeideLogout } from "@/utils/auth"

export function sessionUser() {
	let cookies = new URLSearchParams(document.cookie.split("; ").join("&"))
	let _sessionUser = cookies.get("user_id")
	if (_sessionUser === "Guest") {
		_sessionUser = null
	}
	return _sessionUser
}

function handleLogin(response) {
	if (response.message === "Logged In") {
		userResource.reload()
		employeeResource.reload()

		session.user = sessionUser()
		router.replace({ path: "/" })
	}
}

export const session = reactive({
	login: async (email, password) => {
		const response = await call("login", { usr: email, pwd: password })
		handleLogin(response)
		return response
	},
	otp: async (tmp_id, otp) => {
		const response = await call("login", { tmp_id, otp })
		handleLogin(response)
		return response
	},
	logout: {
		submit: async () => {
			userResource.reset()
			employeeResource.reset()
			session.user = null
			redirectToAmeideLogout()
		},
	},
	user: sessionUser(),
	isLoggedIn: computed(() => !!session.user),
})
