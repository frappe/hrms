import { createRouter, createWebHistory } from "@ionic/vue-router"
import { session } from "@/data/session"
import { userResource } from "@/data/user"

const routes = [
	{
		path: "/",
		name: "Home",
		component: () => import("@/views/Home.vue"),
	},
	{
		path: "/login",
		name: "Login",
		component: () => import("@/views/Login.vue"),
	},
	{
		path: "/status",
		name: "Status",
		component: () => import("@/views/CheckStatus.vue"),
	},
	{
		path: "/leaves",
		name: "Leaves",
		component: () => import("@/views/Leaves.vue")
	}
]

const router = createRouter({
	history: createWebHistory("/hrms"),
	routes,
})

router.beforeEach(async (to, from, next) => {
	let isLoggedIn = session.isLoggedIn
	try {
		await userResource.promise
	} catch (error) {
		isLoggedIn = false
	}

	if (to.name === "Login" && isLoggedIn) {
		next({ name: "Home" })
	} else if (to.name !== "Login" && !isLoggedIn) {
		next({ name: "Login" })
	} else {
		next()
	}
})

export default router
