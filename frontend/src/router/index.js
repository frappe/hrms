import { createRouter, createWebHistory } from "@ionic/vue-router"

import leaveRoutes from "./leaves"
import claimRoutes from "./claims"
import employeeAdvanceRoutes from "./advances"
import salarySlipRoutes from "./salary_slips"

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
		path: "/profile",
		name: "Profile",
		component: () => import("@/views/Profile.vue"),
	},
	...leaveRoutes,
	...claimRoutes,
	...employeeAdvanceRoutes,
	...salarySlipRoutes,
]

const router = createRouter({
	history: createWebHistory("/hrms"),
	routes,
})

export default router
