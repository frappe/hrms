import { createResource } from "frappe-ui";

const api = (method) => `hrms.api.portal.${method}`;

export const bootstrap = createResource({
	url: api("get_bootstrap"),
	cache: "portal:bootstrap",
});

export const homeData = createResource({ url: api("get_home") });
export const attendanceData = createResource({ url: api("get_attendance") });
export const leaveData = createResource({ url: api("get_leave") });
export const expensesData = createResource({ url: api("get_expenses") });
export const payslipsData = createResource({ url: api("get_payslips") });
export const payslipData = createResource({ url: api("get_payslip") });
export const advancesData = createResource({ url: api("get_advances") });
export const directoryData = createResource({ url: api("get_directory") });
export const colleagueData = createResource({ url: api("get_colleague") });
export const orgChartData = createResource({ url: api("get_org_chart") });
export const holidaysData = createResource({ url: api("get_holidays") });
export const documentsData = createResource({ url: api("get_documents") });
export const profileData = createResource({ url: api("get_profile") });
export const profileFieldOptions = createResource({
	url: api("get_profile_field_options"),
	cache: "portal:field-options",
});

export const updateProfile = createResource({ url: api("update_profile") });
export const markCheckin = createResource({ url: api("mark_checkin") });
