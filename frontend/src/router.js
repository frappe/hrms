import { createRouter, createWebHistory } from "@ionic/vue-router"

const routes = [
	{
		path: "/",
		name: "Home",
		component: () => import("@/pages/Home.vue"),
	},
]

const router = createRouter({
	history: createWebHistory("/hrms"),
	routes,
})

export default router
