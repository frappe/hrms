const routes = [
	{
		name: "DeliveryTripListPage",
		path: "/delivery-trips",
		component: () => import("@/views/delivery_trip/List.vue"),
	},
]

export default routes