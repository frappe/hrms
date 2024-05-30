<template>
	<div class="h-12 bg-white border-b px-12 flex items-center">
		<a class="text-xl" href="/">Home</a>
		<Dropdown
			class="ml-auto"
			:options="[
				{
					label: 'My Account',
				},
				{
					label: 'Log Out',
				},
				{
					label: 'Switch to Desk',
				},
			]"
		>
			<Avatar size="lg" class="cursor-pointer" />
		</Dropdown>
	</div>
</template>

<script setup lang="ts">
import { Dropdown, Avatar } from "frappe-ui";
</script>
