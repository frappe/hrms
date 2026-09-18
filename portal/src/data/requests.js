import { createResource } from "frappe-ui";

const api = (method) => `hrms.api.employee_requests.${method}`;

/** Every document an employee raises goes through these five calls. */
export const requestForm = createResource({ url: api("get_form") });
export const requestData = createResource({ url: api("get_request") });
export const createRequest = createResource({ url: api("create_request") });
export const updateRequest = createResource({ url: api("update_request") });
export const deleteRequest = createResource({ url: api("delete_request") });

/** Slug used in /requests/:type/:name, keyed by the page that lists them. */
export const REQUEST_TYPES = {
	leave: { label: "Leave Application", action: "Apply for Leave" },
	expense: { label: "Expense Claim", action: "New Claim" },
	attendance: { label: "Attendance Request", action: "Regularise" },
	advance: { label: "Employee Advance", action: "Request Advance" },
};

export function requestPath(type, name) {
	return `/requests/${type}/${name}`;
}
