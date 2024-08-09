<template>
	<BaseLayout pageTitle="Attendance">
		<template #body>
			<div class="flex flex-col mt-7 mb-7 p-4 gap-7">
				<AttendanceCalendar />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"
</script>
