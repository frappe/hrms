// Routes inside the page: /desk/organizational-chart and /desk/organizational-chart/directory.
// Desk owns the address bar, so a move is a desk route, and the island reads it back as props.

const frappe = () => (window as any).frappe

export const goChart = () => frappe().set_route('organizational-chart')
export const goDirectory = () => frappe().set_route('organizational-chart', 'directory')

// There is no profile page: a person is their Employee form.
export const openEmployee = (id: string) => frappe().set_route('Form', 'Employee', id)
