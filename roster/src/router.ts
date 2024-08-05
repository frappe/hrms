import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{
		path: "/",
		name: "Home",
		component: () => import("./views/Home.vue"),
	},
];

const router = createRouter({
	history: createWebHistory("/hr/roster"),
	routes,
});

export default router;
