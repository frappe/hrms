<template>
	<div class="h-12 bg-white border-b px-12 flex items-center">
		<a class="text-xl" href="/">Home</a>
		<Dropdown
			class="ml-auto"
			:options="[
				{
					label: 'My Account',
					onClick: () => goTo('/me'),
				},
				{
					label: 'Log Out',
					onClick: () => logout.submit(),
				},
				{
					label: 'Switch to Desk',
					onClick: () => goTo('/app'),
				},
			]"
		>
			<Avatar
				:label="props.user?.full_name"
				:image="props.user?.user_image"
				size="lg"
				class="cursor-pointer"
			/>
		</Dropdown>
	</div>
</template>

<script setup lang="ts">
import { Dropdown, Avatar, createResource } from "frappe-ui";
import router from "../router";

import User from "../views/Home.vue";

const props = defineProps<{
	user: User;
}>();

const goTo = (path: string) => {
	window.location.href = path;
};

// RESOURCES

const logout = createResource({
	url: "logout",
	onSuccess() {
		goTo("/login");
	},
	onError(error: { messages: string[] }) {
		raiseToast("error", error.messages[0]);
	},
});
</script>
