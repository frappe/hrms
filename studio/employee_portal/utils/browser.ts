// stand-ins for @vueuse/core, which exported Studio apps can't import
import { onBeforeUnmount, onMounted, ref } from "vue";

export function useMediaQuery(query: string) {
	const matches = ref(false);
	let list: MediaQueryList | null = null;
	const update = () => (matches.value = Boolean(list?.matches));

	onMounted(() => {
		list = window.matchMedia(query);
		update();
		list.addEventListener("change", update);
	});
	onBeforeUnmount(() => list?.removeEventListener("change", update));
	return matches;
}

export function useWindowListener<K extends keyof WindowEventMap>(
	type: K,
	handler: (event: WindowEventMap[K]) => void,
) {
	onMounted(() => window.addEventListener(type, handler));
	onBeforeUnmount(() => window.removeEventListener(type, handler));
}
