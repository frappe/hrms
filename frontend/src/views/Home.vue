<template>
	<ion-menu content-id="main-content">
		<ion-header>
			<ion-toolbar>
				<ion-title>FrappeHR</ion-title>
			</ion-toolbar>
		</ion-header>
		<ion-content class="ion-padding">
			<ion-menu-toggle>
				<Button>Click to close the menu</Button>
			</ion-menu-toggle>
		</ion-content>
	</ion-menu>

	<ion-page id="main-content">
		<ion-content class="ion-no-padding">
			<div class="flex flex-col h-screen w-screen">
				<div class="w-full sm:w-96">
					<div class="flex flex-col bg-white shadow-sm p-4">
						<div class="flex flex-row justify-between items-center">
							<ion-menu-toggle>
								<Button appearance="minimal" class="px-0 py-0">
									<FeatherIcon name="menu" class="h-6 w-6" />
								</Button>
							</ion-menu-toggle>
							<div class="flex flex-row items-center gap-3">
								<Button appearance="minimal" class="px-0 py-0">
									<FeatherIcon name="bell" class="h-6 w-6" />
								</Button>
								<Avatar imageURL="https://placekitten.com/100" label="Whiskers" />
							</div>
						</div>

						<div class="my-5">
							<h2 class="text-3xl font-bold leading-none text-gray-900">
								Hey, Rucha!
							</h2>
						</div>
					</div>

					<!-- quick links -->
					<div class="flex flex-col gap-5 mt-4 p-4">
						<div class="font-medium text-gray-900">Quick Links</div>
						<QuickLinks />
					</div>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>

import { IonContent, IonHeader, IonMenu, IonMenuToggle, IonPage, IonTitle, IonToolbar } from '@ionic/vue';
import { FeatherIcon, Avatar, Card } from "frappe-ui"

import QuickLinks from "@/components/dashboard/QuickLinks.vue"

</script>