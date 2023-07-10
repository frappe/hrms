<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<div class="flex flex-col h-screen w-screen">
				<div class="w-full sm:w-96">
					<div class="flex flex-row gap-1 bg-white shadow-sm p-4 items-center">
						<Button appearance="minimal" class="!px-0 !py-0" @click="router.back()">
							<FeatherIcon name="chevron-left" class="h-5 w-5" />
						</Button>
						<h2 class="text-2xl font-semibold text-gray-900">New Leave Application</h2>
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { useRouter } from "vue-router";
import { IonPage, IonContent } from '@ionic/vue';
import { FeatherIcon } from "frappe-ui";

const router = useRouter();
</script>