<template>
	<Dialog v-model:open="open" size="xl" bare>
		<div class="flex flex-col" role="search" :aria-label="__('Search')">
			<div class="p-2">
				<TextInput
					v-model="query"
					size="md"
					:placeholder="__('Search')"
					autofocus
					@keydown.down.prevent="move(1)"
					@keydown.up.prevent="move(-1)"
					@keydown.enter.prevent="select(flat[active])"
					@keydown.esc="open = false"
				>
					<template #prefix>
						<span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
					</template>
				</TextInput>
			</div>

			<div ref="list" class="max-h-[26rem] overflow-y-auto px-2 pb-2" role="listbox">
				<p v-if="!flat.length" class="px-3 py-10 text-center text-base text-ink-gray-5">
					{{ __("No results") }}
				</p>
				<div v-for="group in groups" :key="group.label" class="pt-1">
					<p class="px-3 pt-2 pb-1 text-sm text-ink-gray-5">{{ group.label }}</p>
					<button
						v-for="item in group.items"
						:key="item.id"
						type="button"
						role="option"
						:aria-selected="flat.indexOf(item) === active"
						:data-index="flat.indexOf(item)"
						class="flex h-9 w-full items-center gap-3 rounded-4 px-3 text-left text-base"
						:class="
							flat.indexOf(item) === active
								? 'bg-surface-gray-2 text-ink-gray-9'
								: 'text-ink-gray-7'
						"
						@mousemove="active = flat.indexOf(item)"
						@click="select(item)"
					>
						<span
							:class="[item.icon, 'size-4 shrink-0 text-ink-gray-6']"
							aria-hidden="true"
						/>
						<span class="min-w-0 flex-1 truncate">{{ item.label }}</span>
					</button>
				</div>
			</div>

			<div
				class="flex items-center gap-4 border-t border-outline-elevation-2 px-4 py-2 text-xs text-ink-gray-5"
			>
				<span class="flex items-center gap-1.5">
					<KeyboardShortcut combo="ArrowUp" bg />
					<KeyboardShortcut combo="ArrowDown" bg />
					{{ __("Move") }}
				</span>
				<span class="flex items-center gap-1.5">
					<KeyboardShortcut combo="Enter" bg />
					{{ __("Open") }}
				</span>
				<span class="ml-auto flex items-center gap-1.5">
					<KeyboardShortcut combo="Escape" bg />
					{{ __("Close") }}
				</span>
			</div>
		</div>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useWindowListener } from "@app/utils/browser";
import { Dialog, KeyboardShortcut, TextInput } from "frappe-ui";
import { useNav } from "@app/nav";
import { ROUTES } from "@app/routes";
import { useSession } from "@app/stores/session";
import { __ } from "@app/utils/translation";

type SearchItem = { id: string; label: string; icon: string; route: string };

const open = defineModel<boolean>("open", { default: false });

const router = useRouter();
const { checkinEnabled } = useSession();
const { navItems } = useNav();
const query = ref("");
const active = ref(0);
const list = ref<HTMLElement | null>(null);

// open with Cmd/Ctrl + K
useWindowListener("keydown", (event: KeyboardEvent) => {
	if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
		event.preventDefault();
		open.value = !open.value;
	}
});

const actions = computed<SearchItem[]>(() => [
	...(checkinEnabled.value
		? [
				{
					id: "check-in",
					label: __("Check in"),
					icon: "lucide-log-in",
					route: `${ROUTES.home}?checkin=1`,
				},
		  ]
		: []),
	{
		id: "apply-leave",
		label: __("Apply leave"),
		icon: "lucide-palmtree",
		route: ROUTES.applyLeave,
	},
	{
		id: "new-claim",
		label: __("New expense claim"),
		icon: "lucide-receipt",
		route: ROUTES.newExpenseClaim,
	},
]);

const pages = computed<SearchItem[]>(() => [
	...navItems.value.map((item) => ({
		id: item.route,
		label: item.label,
		icon: item.icon,
		route: item.route,
	})),
	{ id: "profile", label: __("My profile"), icon: "lucide-user", route: ROUTES.profile },
]);

const groups = computed(() => {
	const text = query.value.trim().toLowerCase();
	return [
		{ label: __("Actions"), items: matching(actions.value, text).slice(0, 6) },
		{ label: __("Go to"), items: matching(pages.value, text).slice(0, 8) },
	].filter((group) => group.items.length);
});

const flat = computed(() => groups.value.flatMap((group) => group.items));

watch([query, open], () => (active.value = 0));
watch(open, (isOpen) => {
	if (!isOpen) query.value = "";
});

function move(delta: number) {
	const count = flat.value.length;
	if (!count) return;
	active.value = (active.value + delta + count) % count;
	nextTick(
		() =>
			list.value
				?.querySelector(`[data-index="${active.value}"]`)
				?.scrollIntoView({ block: "nearest" }),
	);
}

function select(item?: SearchItem) {
	if (!item) return;
	open.value = false;
	router.push(item.route);
}

function matching(items: SearchItem[], text: string) {
	return text ? items.filter((item) => item.label.toLowerCase().includes(text)) : items;
}
</script>
