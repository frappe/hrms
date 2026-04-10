import { watch } from "vue"

export function useCurrencyConversion(formFields, docRef, fieldsToConvert = []) {
	/**
	 * Accepts a formFields resource, a doc ref and an array of fieldnames which are currency fields and need to have the currency in their label
	 * Watches and updates the labels of the currency fields to include the currency in labels
	 */
	const currencyFields = new Set([...fieldsToConvert])

	const updateLabels = () => {
		formFields.data?.forEach((field) => {
			if (!field?.fieldname) return
			if (!currencyFields.has(field.fieldname)) return

			if (!field._original_label && field.label) {
				field._original_label = field.label.replace(/\([^\)]*\)/g, "").trim()
			}
			if (currencyFields.has(field.fieldname)) {
				field.label = `${field._original_label} (${docRef.value.currency})`
			}
		})
	}

	watch(
		() => docRef.value?.currency,
		() => {
			updateLabels()
		},
		{ immediate: true }
	)

	watch(
		() => formFields.data,
		() => {
			updateLabels()
		},
		{ deep: true, immediate: true }
	)

	return { updateLabels }
}