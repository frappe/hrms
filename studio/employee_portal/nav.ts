// nav groups, shared by the sidebar and search
import { computed } from "vue";
import { ROUTES } from "@app/routes";
import { useSession } from "@app/stores/session";
import { __ } from "@app/utils/translation";

export type NavItem = { label: string; icon: string; route: string; badge?: number };
export type NavGroup = { label?: string; items: NavItem[] };

const present = <T>(items: (T | false | undefined)[]) => items.filter(Boolean) as T[];

export function useNav() {
	const { nav, isNew } = useSession();

	const navGroups = computed<NavGroup[]>(() =>
		present<NavGroup>([
			{
				items: present<NavItem>([
					isNew.value && {
						label: __("Your first month"),
						icon: "lucide-flag",
						route: ROUTES.firstMonth,
					},
					{ label: __("Home"), icon: "lucide-house", route: ROUTES.home },
					{
						label: __("Inbox"),
						icon: "lucide-inbox",
						route: ROUTES.inbox,
						badge: nav.value.todo_count || undefined,
					},
				]),
			},
			{
				label: __("Company"),
				items: [
					{ label: __("News"), icon: "lucide-newspaper", route: ROUTES.news },
					{ label: __("People"), icon: "lucide-users", route: ROUTES.people },
					{ label: __("Policies"), icon: "lucide-book-open", route: ROUTES.policies },
				],
			},
			{
				label: __("Personal"),
				items: present<NavItem>([
					{
						label: __("Attendance"),
						icon: "lucide-calendar-days",
						route: ROUTES.attendance,
					},
					{ label: __("Pay"), icon: "lucide-wallet", route: ROUTES.pay },
					{ label: __("Expenses"), icon: "lucide-receipt", route: ROUTES.expenses },
					{ label: __("Performance"), icon: "lucide-target", route: ROUTES.performance },
					nav.value.resigned && {
						label: __("Offboarding"),
						icon: "lucide-door-open",
						route: ROUTES.offboarding,
					},
				]),
			},
			(nav.value.manages || nav.value.is_hr) && {
				label: __("Manage"),
				items: [
					{
						label: __("Onboarding"),
						icon: "lucide-user-round-plus",
						route: ROUTES.joiners,
					},
				],
			},
		]),
	);

	const navItems = computed(() => navGroups.value.flatMap((group) => group.items));

	return { navGroups, navItems };
}
