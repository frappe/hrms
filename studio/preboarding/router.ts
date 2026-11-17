const COMPLETED_PAGE = "Preboarding Completed";
const FORM_PAGE = "Preboarding";

export default {
	setup(router) {
		router.beforeEach((to) => {
			const hasRequest = Boolean(boot?.request);
			if (!hasRequest && to.name !== COMPLETED_PAGE) return { name: COMPLETED_PAGE };
			if (hasRequest && to.name === COMPLETED_PAGE) return { name: FORM_PAGE };
		});
	},
};
