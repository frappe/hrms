const routes = [
	{
		name: "ExpenseClaims",
		path: "/expense-claim/dashboard",
		component: () => import("@/views/expense_claim/Dashboard.vue"),
	},
	{
		name: "ExpenseClaimListView",
		path: "/expense-claim/list",
		component: () => import("@/views/expense_claim/List.vue"),
	},
	{
		name: "ExpenseClaimFormView",
		path: "/expense-claim/new",
		component: () => import("@/views/expense_claim/Form.vue"),
	},
	{
		name: "ExpenseClaimDetailView",
		path: "/expense-claim/:id",
		props: true,
		component: () => import("@/views/expense_claim/Form.vue"),
	},
]

export default routes
