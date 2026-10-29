import { mountVueIsland } from "@framework/ui/island";
import Checklist from "./checklist/Checklist.vue";

export const mount = (el, context) => mountVueIsland(el, { ...context, component: Checklist });
