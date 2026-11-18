import { onMounted, onUnmounted, shallowRef, watchEffect } from "vue";
import { useHost } from "@framework/ui/island";

/**
 * An element in desk's page head, left of its standard actions, to teleport a control into.
 * The island draws inside a shadow root, so the element gets its own shadow root with the
 * island's stylesheets and theme. Null until mounted, and when the page has no head.
 */
export function usePageHeadTarget(anchor) {
	const host = useHost();
	const target = shallowRef(null);
	let spot = null;

	onMounted(() => {
		const island = anchor.value.getRootNode();
		const actions = island.host
			?.closest(".page-container")
			?.querySelector(".page-head .standard-actions");
		if (!actions) return;

		spot = document.createElement("div");
		spot.className = "frappe-island-head";
		const shadow = spot.attachShadow({ mode: "open" });
		shadow.adoptedStyleSheets = island.adoptedStyleSheets;
		const root = document.createElement("div");
		shadow.append(root);
		actions.before(spot);
		target.value = root;
	});

	watchEffect(() => target.value?.setAttribute("data-theme", host.theme));
	onUnmounted(() => spot?.remove());

	return target;
}
