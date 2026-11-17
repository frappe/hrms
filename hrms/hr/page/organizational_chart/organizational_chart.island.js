import { mountVueIsland } from "@framework/ui/island";

import Page from "./organizational_chart.vue";

export const mount = (el, context) => mountVueIsland(el, { ...context, component: Page });
