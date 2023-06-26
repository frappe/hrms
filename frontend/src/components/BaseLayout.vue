<template>
	<ion-page>
		<ion-content class="ion-no-padding">
			<div class="flex flex-col h-screen w-screen">
				<div class="w-full sm:w-96">
					<div class="flex flex-col bg-white shadow-sm p-4">
						<div class="flex flex-row justify-between items-center">
							<ion-menu-toggle>
								<Button appearance="minimal" class="!px-0 !py-0">
									<FeatherIcon name="menu" class="h-6 w-6" />
								</Button>
							</ion-menu-toggle>
							<div class="flex flex-row items-center gap-3">
								<Button appearance="minimal" class="!px-0 !py-0">
									<FeatherIcon name="bell" class="h-6 w-6" />
								</Button>
								<router-link :to="{ name: 'Profile' }">
									<Avatar
										:imageURL="user.data.user_image"
										:label="user.data.first_name"
									/>
								</router-link>
							</div>
						</div>

						<div class="mt-5">
							<h2 class="text-2xl font-bold text-gray-900">
								{{ props.pageTitle }}
							</h2>

							<CheckInPanel v-if="props.showCheckInPanel" />
						</div>
					</div>

					<slot name="body"></slot>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonContent, IonMenuToggle, IonPage } from "@ionic/vue"
import { FeatherIcon, Avatar } from "frappe-ui"

import CheckInPanel from "@/components/CheckInPanel.vue"

import { inject } from "vue"

const user = inject("$user")

const props = defineProps({
	pageTitle: {
		type: String,
		required: false,
		default: "Home",
	},
	showCheckInPanel: {
		type: Boolean,
		required: false,
		default: false,
	},
})
</script>
