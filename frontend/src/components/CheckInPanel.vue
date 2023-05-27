<template>
	<div class="flex flex-col">
		<div class="font-medium text-sm text-gray-500" v-if="lastLog">
			{{ `Last ${lastLogType} was at ${lastLogTime}`}}
		</div>
		<Button
			class="mt-2 mb-1 py-2 shadow-sm"
			expand="block"
			id="open-checkin-modal"
			@click="checkinTimestamp = dayjs().format('YYYY-MM-DD HH:mm:ss')"
		>
			{{ nextAction.label }}
		</Button>
	</div>

	<ion-modal ref="modal" trigger="open-checkin-modal" :initial-breakpoint="1" :breakpoints="[0, 1]">
		<div class="h-40 w-full flex flex-col items-center justify-center gap-5 p-4 mb-5">
			<div class="flex flex-col gap-1 items-center justify-center">
				<div class="font-bold text-2xl"> {{ dayjs(checkinTimestamp).format("hh:mm:ss a") }} </div>
				<div class="font-medium text-gray-500 text-sm">
					{{ dayjs().format("D MMM, YYYY") }}
				</div>
			</div>
			<Button
				appearance="primary"
				class="py-2 w-full"
				@click="submitLog(nextAction.action)"
			>
				Confirm {{ nextAction.label }}
			</Button>
		</div>
	</ion-modal>
</template>

<script setup>
	import { createListResource, toast } from "frappe-ui"
	import { computed, inject, ref } from "vue"
	import { IonModal, modalController } from "@ionic/vue"

	import dayjs from "@/utils/dayjs"

	const employee = inject("$employee")
	const checkinTimestamp = ref(null)

	const checkins = createListResource({
		doctype: "Employee Checkin",
		fields: ["name", "employee", "employee_name", "log_type", "time", "device_id"],
		filters: {
			employee: employee.data.name
		},
		orderBy: "time desc",
	})
	checkins.reload()

	const lastLog = computed(() => {
		if (checkins.list.loading || !checkins.data) return {}
		return checkins.data[0]
	})

	const lastLogType = computed(() => {
		return lastLog?.value?.log_type === "IN" ? "check-in" : "check-out"
	})

	const nextAction = computed(() => {
		return (
			lastLog?.value?.log_type === "IN"
			? {"action": "OUT", "label": "Check Out"}
			: {"action": "IN", "label": "Check In"}
		)
	})

	const lastLogTime = computed(() => {
		const timestamp = lastLog?.value?.time
		const formattedTime = dayjs(timestamp).format("hh:mm a")

		if (dayjs(timestamp).isToday())
			return formattedTime

		else if (dayjs(timestamp).isYesterday())
			return `${formattedTime} yesterday`

		else if (dayjs(timestamp).isSame(dayjs(), "year"))
			return `${formattedTime} on ${dayjs(timestamp).format("D MMM")}`

		return `${formattedTime} on ${dayjs(timestamp).format("D MMM, YYYY")}`
	})

	const submitLog = (logType) => {
		const action = logType === "IN" ? "Check-in" : "Check-out"

		checkins.insert.submit(
			{
				employee: employee.data.name,
				log_type: logType,
				time: checkinTimestamp.value,
			},
			{
				onSuccess() {
					modalController.dismiss()
					toast({
						title: "Success",
						text: `${action} successful!`,
						icon: "check-circle",
						position: "bottom-center",
						iconClasses: "text-green-500",
					})
				},
				onError() {
					toast({
						title: "Error",
						text: `${action} failed!`,
						icon: "alert-circle",
						position: "bottom-center",
						iconClasses: "text-red-500",
					})
				}
			}
		)
	}

</script>

<style scoped>
	ion-modal {
		--height: auto;
	}
</style>