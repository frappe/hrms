import { mountVueIsland } from "@framework/ui/island";

import Page from "./salary_slip_assignments.vue";

export const mount = (el, context) => mountVueIsland(el, { ...context, component: Page });
