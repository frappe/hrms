// current user and their nav flags, loaded once for all pages
import { computed, effectScope } from "vue";
import { useCall } from "frappe-ui";
import { __, loadTranslations } from "@app/utils/translation";

type Nav = {
	manages: boolean;
	is_hr: boolean;
	todo_count: number;
	onboarding: string | null;
	resigned: boolean;
};

type PortalContext = {
	user: { name: string; full_name: string; first_name: string; image: string | null };
	employee: {
		name: string;
		employee_name: string;
		first_name: string;
		image: string | null;
		company: string;
	} | null;
	nav: Nav;
	checkin_enabled: boolean;
	checkin_needs_location: boolean;
};

const NO_NAV: Nav = {
	manages: false,
	is_hr: false,
	todo_count: 0,
	onboarding: null,
	resigned: false,
};

const store = effectScope(true).run(createSessionStore)!;

export function useSession() {
	return store;
}

function createSessionStore() {
	loadTranslations();

	const context = useCall<PortalContext>({
		url: "/api/v2/method/hrms.api.portal.get_context",
		cacheKey: "employee-portal-context",
	});

	const user = computed(() => context.data?.user);
	const employee = computed(() => context.data?.employee ?? null);
	const nav = computed(() => context.data?.nav ?? NO_NAV);
	const isNew = computed(() => Boolean(nav.value.onboarding));
	const checkinEnabled = computed(() => Boolean(context.data?.checkin_enabled));
	const checkinNeedsLocation = computed(() => Boolean(context.data?.checkin_needs_location));
	const displayName = computed(
		() => employee.value?.employee_name || user.value?.full_name || "",
	);
	const firstName = computed(() => employee.value?.first_name || user.value?.first_name || "");
	const photo = computed(() => employee.value?.image || user.value?.image || undefined);

	return {
		t: __,
		user,
		employee,
		nav,
		isNew,
		checkinEnabled,
		checkinNeedsLocation,
		displayName,
		firstName,
		photo,
	};
}
