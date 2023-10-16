const routes = [
	{
		name: "PersonalInformation",
		path: "/profile/personal-information",
		component: () => import("@/views/profile/PersonalInformation.vue"),
	},
	{
		name: "ContactInformation",
		path: "/profile/contact-information",
		component: () => import("@/views/profile/ContactInformation.vue"),
	},
	{
		name: "MyJourney",
		path: "/profile/my-journey",
		component: () => import("@/views/profile/MyJourney.vue"),
	},
	{
		name: "CompanyInformation",
		path: "/profile/company-information",
		component: () => import("@/views/profile/CompanyInformation.vue"),
	},
	{
		name: "SalaryInformation",
		path: "/profile/salary-information",
		component: () => import("@/views/profile/SalaryInformation.vue"),
	},
]

export default routes
