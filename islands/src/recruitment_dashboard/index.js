import { mountVueIsland } from "@framework/ui/island";

import RecruitmentDashboard from "./RecruitmentDashboard.vue";

export const mount = (el, context) =>
	mountVueIsland(el, { ...context, component: RecruitmentDashboard });
