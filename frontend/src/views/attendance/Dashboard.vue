<template>
	<BaseLayout pageTitle="Attendance">
		<template #body>
			<div class="flex flex-col items-center mt-7 mb-7 py-4">
				<AttendanceCalendar />
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
import AttendanceCalendar from "@/components/AttendanceCalendar.vue"
</script>
