const routes = [
	{
		name: "ExpenseClaimListView",
		path: "/expense-claims",
		component: () => import("@/views/expense_claim/List.vue"),
	},
	{
		name: "ExpenseClaimFormView",
		path: "/expense-claims/new",
		component: () => import("@/views/expense_claim/Form.vue"),
	},
	{
		name: "ExpenseClaimDetailView",
		path: "/expense-claims/:id",
		props: true,
		component: () => import("@/views/expense_claim/Form.vue"),
	},
]

export default routes
