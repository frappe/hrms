<script setup>
// A request's path, oldest step first: where it has been, where it is now and what is left.
// The rail darkens below a done step, so the walked path reads at a glance.
defineProps({
	// [{ label, sub?, when?, state: "done" | "current" | "todo" }]
	steps: { type: Array, required: true },
});
</script>

<template>
	<ol class="relative">
		<li
			v-for="(step, index) in steps"
			:key="step.label"
			class="relative flex gap-3 pb-5 last:pb-0"
			:aria-current="step.state === 'current' ? 'step' : undefined"
		>
			<span
				v-if="index < steps.length - 1"
				class="absolute -bottom-px left-[0.4375rem] top-[1.375rem] border-l-[1.5px]"
				:class="step.state === 'done' ? 'border-outline-gray-4' : 'border-outline-gray-2'"
				aria-hidden="true"
			/>
			<!-- the step's dot: a dark disc with a check when done, a ring with a core where the
			request is now, a light ring for what is left -->
			<span
				class="relative z-10 mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-surface-base"
				:class="step.state === 'todo' ? 'text-ink-gray-3' : 'text-ink-gray-8'"
			>
				<template v-if="step.state === 'done'">
					<span class="absolute inset-0 rounded-full bg-current" />
					<span class="lucide-check relative size-3 text-ink-gray-1" />
				</template>
				<template v-else-if="step.state === 'current'">
					<span class="absolute inset-0 rounded-full border-[1.5px] border-current" />
					<span class="size-1.5 rounded-full bg-current" />
				</template>
				<span
					v-else
					class="absolute inset-px rounded-full border-[1.5px] border-current"
				/>
			</span>
			<div class="min-w-0 flex-1">
				<div class="flex items-baseline justify-between gap-3">
					<span
						class="text-base"
						:class="
							step.state === 'todo'
								? 'text-ink-gray-5'
								: step.state === 'current'
								  ? 'text-base-medium text-ink-gray-9'
								  : 'text-ink-gray-8'
						"
					>
						{{ step.label }}
					</span>
					<span v-if="step.when" class="shrink-0 text-sm tabular-nums text-ink-gray-5">
						{{ step.when }}
					</span>
				</div>
				<p v-if="step.sub" class="mt-0.5 text-p-sm text-ink-gray-5">{{ step.sub }}</p>
			</div>
		</li>
	</ol>
</template>
