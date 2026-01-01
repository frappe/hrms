# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import datetime

import frappe
from frappe import _
from frappe.model.workflow import get_workflow_name
from frappe.query_builder.functions import Max, Min, Sum
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_fullname,
	get_link_to_form,
	getdate,
	nowdate,
)

from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import daterange
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

import hrms
from hrms.api import get_current_employee_info
from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.utils import (
	get_holiday_dates_for_employee,
	get_leave_period,
	set_employee_name,
	share_doc_with_approver,
	validate_active_employee,
)
from hrms.mixins.pwa_notifications import PWANotificationsMixin
from hrms.utils import get_employee_email


class LeaveDayBlockedError(frappe.ValidationError):
	pass


class OverlapError(frappe.ValidationError):
	pass


class AttendanceAlreadyMarkedError(frappe.ValidationError):
	pass


class NotAnOptionalHoliday(frappe.ValidationError):
	pass


class InsufficientLeaveBalanceError(frappe.ValidationError):
	pass


class LeaveAcrossAllocationsError(frappe.ValidationError):
	pass


from frappe.model.document import Document


class LeaveApplication(Document, PWANotificationsMixin):
	def get_feed(self):
		return _("{0}: From {0} of type {1}").format(self.employee_name, self.leave_type)

	def after_insert(self):
		self.notify_approver()

	def validate(self):
		validate_active_employee(self.employee)
		set_employee_name(self)
		self.validate_dates()
		self.validate_balance_leaves()
		self.validate_leave_overlap()
		self.validate_max_days()
		self.show_block_day_warning()
		self.validate_block_days()
		self.validate_salary_processed_days()
		self.validate_attendance()
		self.set_half_day_date()
		if frappe.db.get_value("Leave Type", self.leave_type, "is_optional_leave"):
			self.validate_optional_leave()
		self.validate_applicable_after()

	def on_update(self):
		if self.status == "Open" and self.docstatus < 1:
			# notify leave approver about creation
			if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
				self.notify_leave_approver()

		share_doc_with_approver(self, self.leave_approver)
		self.publish_update()
		self.notify_approval_status()

	def on_submit(self):
		if self.status in ["Open", "Cancelled"]:
			frappe.throw(_("Only Leave Applications with status 'Approved' and 'Rejected' can be submitted"))

		self.validate_back_dated_application()
		self.update_attendance()
		self.validate_for_self_approval()

		# notify leave applier about approval
		if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
			self.notify_employee()

		self.create_leave_ledger_entry()
		self.reload()

	def before_cancel(self):
		self.status = "Cancelled"

	def on_discard(self):
		self.db_set("status", "Cancelled")

	def on_cancel(self):
		self.create_leave_ledger_entry(submit=False)
		# notify leave applier about cancellation
		if frappe.db.get_single_value("HR Settings", "send_leave_notification"):
			self.notify_employee()
		self.cancel_attendance()

		self.publish_update()

	def after_delete(self):
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		hrms.refetch_resource("hrms:my_leaves", employee_user)
		hrms.refetch_resource("hrms:team_leaves")

	def validate_applicable_after(self):
		if self.leave_type:
			leave_type = frappe.get_doc("Leave Type", self.leave_type)
			if leave_type.applicable_after > 0:
				date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
				leave_days = get_approved_leaves_for_period(
					self.employee, False, date_of_joining, self.from_date
				)
				number_of_days = date_diff(getdate(self.from_date), date_of_joining)
				if number_of_days >= 0:
					holidays = 0
					if not frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
						holidays = get_holidays(self.employee, date_of_joining, self.from_date)
					number_of_days = number_of_days - leave_days - holidays
					if number_of_days < leave_type.applicable_after:
						frappe.throw(
							_("{0} applicable after {1} working days").format(
								self.leave_type, leave_type.applicable_after
							)
						)

	def validate_dates(self):
		if frappe.db.get_single_value("HR Settings", "restrict_backdated_leave_application"):
			if self.from_date and getdate(self.from_date) < getdate():
				allowed_role = frappe.db.get_single_value(
					"HR Settings", "role_allowed_to_create_backdated_leave_application"
				)
				user = frappe.get_doc("User", frappe.session.user)
				user_roles = [d.role for d in user.roles]
				if not allowed_role:
					frappe.throw(
						_("Backdated Leave Application is restricted. Please set the {} in {}").format(
							frappe.bold(_("Role Allowed to Create Backdated Leave Application")),
							get_link_to_form("HR Settings", "HR Settings", _("HR Settings")),
						)
					)

				if allowed_role and allowed_role not in user_roles:
					frappe.throw(
						_("Only users with the {0} role can create backdated leave applications").format(
							_(allowed_role)
						)
					)

		if self.from_date and self.to_date and (getdate(self.to_date) < getdate(self.from_date)):
			frappe.throw(_("To date cannot be before from date"))

		if (
			self.half_day
			and self.half_day_date
			and (
				getdate(self.half_day_date) < getdate(self.from_date)
				or getdate(self.half_day_date) > getdate(self.to_date)
			)
		):
			frappe.throw(_("Half Day Date should be between From Date and To Date"))

		if not is_lwp(self.leave_type):
			self.validate_dates_across_allocation()
			self.validate_back_dated_application()

	def validate_dates_across_allocation(self):
		if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
			return

		alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()

		if not (alloc_on_from_date or alloc_on_to_date):
			frappe.throw(_("Application period cannot be outside leave allocation period"))
		elif self.is_separate_ledger_entry_required(alloc_on_from_date, alloc_on_to_date):
			frappe.throw(
				_("Application period cannot be across two allocation records"),
				exc=LeaveAcrossAllocationsError,
			)

	def get_allocation_based_on_application_dates(self) -> tuple[dict, dict]:
		"""Returns allocation name, from and to dates for application dates"""

		def _get_leave_allocation_record(date):
			LeaveAllocation = frappe.qb.DocType("Leave Allocation")
			allocation = (
				frappe.qb.from_(LeaveAllocation)
				.select(LeaveAllocation.name, LeaveAllocation.from_date, LeaveAllocation.to_date)
				.where(
					(LeaveAllocation.employee == self.employee)
					& (LeaveAllocation.leave_type == self.leave_type)
					& (LeaveAllocation.docstatus == 1)
					& ((date >= LeaveAllocation.from_date) & (date <= LeaveAllocation.to_date))
				)
			).run(as_dict=True)

			return allocation and allocation[0]

		allocation_based_on_from_date = _get_leave_allocation_record(self.from_date)
		allocation_based_on_to_date = _get_leave_allocation_record(self.to_date)

		return allocation_based_on_from_date, allocation_based_on_to_date

	def validate_back_dated_application(self):
		future_allocation = frappe.db.sql(
			"""select name, from_date from `tabLeave Allocation`
			where employee=%s and leave_type=%s and docstatus=1 and from_date > %s
			and carry_forward=1""",
			(self.employee, self.leave_type, self.to_date),
			as_dict=1,
		)

		if future_allocation:
			frappe.throw(
				_(
					"Leave cannot be applied/cancelled before {0}, as leave balance has already been carry-forwarded in the future leave allocation record {1}"
				).format(formatdate(future_allocation[0].from_date), future_allocation[0].name)
			)

	def update_attendance(self):
		if self.status != "Approved":
			return

		holiday_dates = []
		if not frappe.db.get_value("Leave Type", self.leave_type, "include_holiday"):
			holiday_dates = get_holiday_dates_for_employee(self.employee, self.from_date, self.to_date)

		for dt in daterange(getdate(self.from_date), getdate(self.to_date)):
			date = dt.strftime("%Y-%m-%d")
			# check for existing attenadnce absent or if half day with half day status absent,
			attendance_name = frappe.db.exists(
				"Attendance",
				dict(
					employee=self.employee,
					attendance_date=date,
					docstatus=("!=", 2),
				),
			)
			# don't mark attendance for holidays
			# if leave type does not include holidays within leaves as leaves
			if date in holiday_dates:
				if attendance_name:
					# cancel and delete existing attendance for holidays
					attendance = frappe.get_doc("Attendance", attendance_name)
					attendance.flags.ignore_permissions = True
					if attendance.docstatus == 1:
						attendance.cancel()
					frappe.delete_doc("Attendance", attendance_name, force=1)
				continue

			self.create_or_update_attendance(attendance_name, date)

	def create_or_update_attendance(self, attendance_name, date):
		status = (
			"Half Day" if self.half_day_date and getdate(date) == getdate(self.half_day_date) else "On Leave"
		)

		if attendance_name:
			# update existing attendance, change absent to on leave or half day
			doc = frappe.get_doc("Attendance", attendance_name)
			half_day_status = None if status == "On Leave" else "Present"
			modify_half_day_status = 1 if doc.status == "Absent" and status == "Half Day" else 0
			doc.db_set(
				{
					"status": status,
					"leave_type": self.leave_type,
					"leave_application": self.name,
					"half_day_status": half_day_status,
					"modify_half_day_status": modify_half_day_status,
				}
			)
		else:
			# make new attendance and submit it
			doc = frappe.new_doc("Attendance")
			doc.employee = self.employee
			doc.employee_name = self.employee_name
			doc.attendance_date = date
			doc.company = self.company
			doc.leave_type = self.leave_type
			doc.leave_application = self.name
			doc.status = status
			doc.half_day_status = "Present" if status == "Half Day" else None
			doc.modify_half_day_status = 1 if status == "Half Day" else 0
			doc.flags.ignore_validate = True  # ignores check leave record validation in attendance
			doc.insert(ignore_permissions=True)
			doc.submit()

	def cancel_attendance(self):
		if self.docstatus == 2:
			attendance = frappe.db.sql(
				"""select name from `tabAttendance` where employee = %s\
				and (attendance_date between %s and %s) and docstatus < 2 and status in ('On Leave', 'Half Day')""",
				(self.employee, self.from_date, self.to_date),
				as_dict=1,
			)
			for name in attendance:
				frappe.db.set_value("Attendance", name, "docstatus", 2)

	def validate_salary_processed_days(self):
		if not frappe.db.get_value("Leave Type", self.leave_type, "is_lwp"):
			return

		last_processed_pay_slip = frappe.db.sql(
			"""
			select start_date, end_date from `tabSalary Slip`
			where docstatus = 1 and employee = %s
			and ((%s between start_date and end_date) or (%s between start_date and end_date))
			order by creation desc limit 1
		""",
			(self.employee, self.to_date, self.from_date),
		)

		if last_processed_pay_slip:
			frappe.throw(
				_(
					"Salary already processed for period between {0} and {1}, Leave application period cannot be between this date range."
				).format(formatdate(last_processed_pay_slip[0][0]), formatdate(last_processed_pay_slip[0][1]))
			)

	def show_block_day_warning(self):
		block_dates = get_applicable_block_dates(
			self.from_date,
			self.to_date,
			self.employee,
			self.company,
			all_lists=True,
			leave_type=self.leave_type,
		)

		if block_dates:
			frappe.msgprint(_("Warning: Leave application contains following block dates") + ":")
			for d in block_dates:
				frappe.msgprint(formatdate(d.block_date) + ": " + d.reason)

	def validate_block_days(self):
		block_dates = get_applicable_block_dates(
			self.from_date, self.to_date, self.employee, self.company, leave_type=self.leave_type
		)

		if block_dates and self.status == "Approved":
			frappe.throw(_("You are not authorized to approve leaves on Block Dates"), LeaveDayBlockedError)

	def validate_balance_leaves(self):
		precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2

		if self.from_date and self.to_date:
			self.total_leave_days = get_number_of_leave_days(
				self.employee,
				self.leave_type,
				self.from_date,
				self.to_date,
				self.half_day,
				self.half_day_date,
			)

			if self.total_leave_days <= 0:
				frappe.throw(
					_(
						"The day(s) on which you are applying for leave are holidays. You need not apply for leave."
					)
				)

			if not is_lwp(self.leave_type):
				leave_balance = get_leave_balance_on(
					self.employee,
					self.leave_type,
					self.from_date,
					self.to_date,
					consider_all_leaves_in_the_allocation_period=True,
					for_consumption=True,
				)
				leave_balance_for_consumption = flt(
					leave_balance.get("leave_balance_for_consumption"), precision
				)
				if self.status != "Rejected" and (
					leave_balance_for_consumption < self.total_leave_days or not leave_balance_for_consumption
				):
					self.show_insufficient_balance_message(leave_balance_for_consumption)

	def show_insufficient_balance_message(self, leave_balance_for_consumption: float) -> None:
		alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()

		if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
			if leave_balance_for_consumption != self.leave_balance:
				msg = _("Warning: Insufficient leave balance for Leave Type {0} in this allocation.").format(
					frappe.bold(self.leave_type)
				)
				msg += "<br><br>"
				msg += _(
					"Actual balances aren't available because the leave application spans over different leave allocations. You can still apply for leaves which would be compensated during the next allocation."
				)
			else:
				msg = _("Warning: Insufficient leave balance for Leave Type {0}.").format(
					frappe.bold(self.leave_type)
				)

			frappe.msgprint(msg, title=_("Warning"), indicator="orange")
		else:
			frappe.throw(
				_("Insufficient leave balance for Leave Type {0}").format(frappe.bold(self.leave_type)),
				exc=InsufficientLeaveBalanceError,
				title=_("Insufficient Balance"),
			)

	def validate_leave_overlap(self):
		if not self.name:
			# hack! if name is null, it could cause problems with !=
			self.name = "New Leave Application"

		for d in frappe.db.sql(
			"""
			select
				name, leave_type, posting_date, from_date, to_date, total_leave_days, half_day_date
			from `tabLeave Application`
			where employee = %(employee)s and docstatus < 2 and status in ('Open', 'Approved')
			and to_date >= %(from_date)s and from_date <= %(to_date)s
			and name != %(name)s""",
			{
				"employee": self.employee,
				"from_date": self.from_date,
				"to_date": self.to_date,
				"name": self.name,
			},
			as_dict=1,
		):
			if (
				cint(self.half_day) == 1
				and getdate(self.half_day_date) == getdate(d.half_day_date)
				and (
					flt(self.total_leave_days) == 0.5
					or getdate(self.from_date) == getdate(d.to_date)
					or getdate(self.to_date) == getdate(d.from_date)
				)
			):
				total_leaves_on_half_day = self.get_total_leaves_on_half_day()
				if total_leaves_on_half_day >= 1:
					self.throw_overlap_error(d)
			else:
				self.throw_overlap_error(d)

	def throw_overlap_error(self, d):
		form_link = get_link_to_form("Leave Application", d.name)
		msg = _("Employee {0} has already applied for {1} between {2} and {3} : {4}").format(
			self.employee, d["leave_type"], formatdate(d["from_date"]), formatdate(d["to_date"]), form_link
		)
		frappe.throw(msg, OverlapError)

	def get_total_leaves_on_half_day(self):
		leave_count_on_half_day_date = frappe.db.sql(
			"""select count(name) from `tabLeave Application`
			where employee = %(employee)s
			and docstatus < 2
			and status in ('Open', 'Approved')
			and half_day = 1
			and half_day_date = %(half_day_date)s
			and name != %(name)s""",
			{"employee": self.employee, "half_day_date": self.half_day_date, "name": self.name},
		)[0][0]

		return leave_count_on_half_day_date * 0.5

	def validate_max_days(self):
		max_days = frappe.db.get_value("Leave Type", self.leave_type, "max_continuous_days_allowed")
		if not max_days:
			return

		details = self.get_consecutive_leave_details()

		if details.total_consecutive_leaves > cint(max_days):
			msg = _("Leave of type {0} cannot be longer than {1}.").format(
				get_link_to_form("Leave Type", self.leave_type), max_days
			)
			if details.leave_applications:
				msg += "<br><br>" + _("Reference: {0}").format(
					", ".join(
						get_link_to_form("Leave Application", name) for name in details.leave_applications
					)
				)

			frappe.throw(msg, title=_("Maximum Consecutive Leaves Exceeded"))

	def get_consecutive_leave_details(self) -> dict:
		leave_applications = set()

		def _get_first_from_date(reference_date):
			"""gets `from_date` of first leave application from previous consecutive leave applications"""
			prev_date = add_days(reference_date, -1)
			application = frappe.db.get_value(
				"Leave Application",
				{
					"employee": self.employee,
					"leave_type": self.leave_type,
					"to_date": prev_date,
					"docstatus": ["!=", 2],
					"status": ["in", ["Open", "Approved"]],
				},
				["name", "from_date"],
				as_dict=True,
			)
			if application:
				leave_applications.add(application.name)
				return _get_first_from_date(application.from_date)
			return reference_date

		def _get_last_to_date(reference_date):
			"""gets `to_date` of last leave application from following consecutive leave applications"""
			next_date = add_days(reference_date, 1)
			application = frappe.db.get_value(
				"Leave Application",
				{
					"employee": self.employee,
					"leave_type": self.leave_type,
					"from_date": next_date,
					"docstatus": ["!=", 2],
					"status": ["in", ["Open", "Approved"]],
				},
				["name", "to_date"],
				as_dict=True,
			)
			if application:
				leave_applications.add(application.name)
				return _get_last_to_date(application.to_date)
			return reference_date

		first_from_date = _get_first_from_date(self.from_date)
		last_to_date = _get_last_to_date(self.to_date)

		total_consecutive_leaves = get_number_of_leave_days(
			self.employee, self.leave_type, first_from_date, last_to_date
		)

		return frappe._dict(
			{
				"total_consecutive_leaves": total_consecutive_leaves,
				"leave_applications": leave_applications,
			}
		)

	def validate_attendance(self):
		attendance_dates = frappe.get_all(
			"Attendance",
			filters=[
				["employee", "=", self.employee],
				["attendance_date", "between", [self.from_date, self.to_date]],
				["status", "in", ["Present", "Work From Home"]],
				["docstatus", "=", 1],
				["half_day_status", "!=", "Absent"],
			],
			fields=["name", "attendance_date"],
			order_by="attendance_date",
		)
		if attendance_dates:
			frappe.throw(
				_("Attendance for employee {0} is already marked for the following dates: {1}").format(
					self.employee,
					(
						"<br><ul><li>"
						+ "</li><li>".join(
							get_link_to_form("Attendance", a.name, label=formatdate(a.attendance_date))
							for a in attendance_dates
						)
						+ "</li></ul>"
					),
				),
				AttendanceAlreadyMarkedError,
			)

	def validate_optional_leave(self):
		leave_period = get_leave_period(self.from_date, self.to_date, self.company)
		if not leave_period:
			frappe.throw(_("Cannot find active Leave Period"))
		optional_holiday_list = frappe.db.get_value(
			"Leave Period", leave_period[0]["name"], "optional_holiday_list"
		)
		if not optional_holiday_list:
			frappe.throw(
				_("Optional Holiday List not set for leave period {0}").format(leave_period[0]["name"])
			)
		day = getdate(self.from_date)
		while day <= getdate(self.to_date):
			if not frappe.db.exists(
				{"doctype": "Holiday", "parent": optional_holiday_list, "holiday_date": day}
			):
				frappe.throw(
					_("{0} is not in Optional Holiday List").format(formatdate(day)), NotAnOptionalHoliday
				)
			day = add_days(day, 1)

	def set_half_day_date(self):
		if self.from_date == self.to_date and self.half_day == 1:
			self.half_day_date = self.from_date

		if self.half_day == 0:
			self.half_day_date = None

	def notify_employee(self):
		employee_email = get_employee_email(self.employee)

		if not employee_email:
			return

		parent_doc = frappe.get_doc("Leave Application", self.name)
		args = parent_doc.as_dict()

		template = frappe.db.get_single_value("HR Settings", "leave_status_notification_template")
		if not template:
			frappe.msgprint(_("Please set default template for Leave Status Notification in HR Settings."))
			return
		email_template = frappe.get_doc("Email Template", template)
		subject = frappe.render_template(email_template.subject, args)
		message = frappe.render_template(email_template.response_, args)

		self.notify(
			{
				# for post in messages
				"message": message,
				"message_to": employee_email,
				# for email
				"subject": subject,
				"notify": "employee",
			}
		)

	def notify_leave_approver(self):
		if self.leave_approver:
			parent_doc = frappe.get_doc("Leave Application", self.name)
			args = parent_doc.as_dict()

			template = frappe.db.get_single_value("HR Settings", "leave_approval_notification_template")
			if not template:
				frappe.msgprint(
					_("Please set default template for Leave Approval Notification in HR Settings.")
				)
				return
			email_template = frappe.get_doc("Email Template", template)
			subject = frappe.render_template(email_template.subject, args)
			message = frappe.render_template(email_template.response_, args)

			self.notify(
				{
					# for post in messages
					"message": message,
					"message_to": self.leave_approver,
					# for email
					"subject": subject,
				}
			)

	def notify(self, args):
		args = frappe._dict(args)
		# args -> message, message_to, subject
		if cint(self.follow_via_email):
			contact = args.message_to
			if not isinstance(contact, list):
				if not args.notify == "employee":
					contact = frappe.get_doc("User", contact).email or contact

			sender = dict()
			sender["email"] = frappe.get_doc("User", frappe.session.user).email
			sender["full_name"] = get_fullname(sender["email"])

			try:
				frappe.sendmail(
					recipients=contact,
					sender=sender["email"],
					subject=args.subject,
					message=args.message,
				)
				frappe.msgprint(_("Email sent to {0}").format(contact))
			except frappe.OutgoingEmailError:
				pass

	def create_leave_ledger_entry(self, submit=True):
		if self.status != "Approved" and submit:
			return

		expiry_date = get_allocation_expiry_for_cf_leaves(
			self.employee, self.leave_type, self.to_date, self.from_date
		)
		lwp = frappe.db.get_value("Leave Type", self.leave_type, "is_lwp")

		if expiry_date:
			self.create_ledger_entry_for_intermediate_allocation_expiry(expiry_date, submit, lwp)
		else:
			alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()
			if self.is_separate_ledger_entry_required(alloc_on_from_date, alloc_on_to_date):
				# required only if negative balance is allowed for leave type
				# else will be stopped in validation itself
				self.create_separate_ledger_entries(alloc_on_from_date, alloc_on_to_date, submit, lwp)
			else:
				raise_exception = False if frappe.flags.in_patch else True
				args = dict(
					leaves=self.total_leave_days * -1,
					from_date=self.from_date,
					to_date=self.to_date,
					is_lwp=lwp,
					holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
					or "",
				)
				create_leave_ledger_entry(self, args, submit)

	def is_separate_ledger_entry_required(
		self, alloc_on_from_date: dict | None = None, alloc_on_to_date: dict | None = None
	) -> bool:
		"""Checks if application dates fall in separate allocations"""
		if (
			(alloc_on_from_date and not alloc_on_to_date)
			or (not alloc_on_from_date and alloc_on_to_date)
			or (alloc_on_from_date and alloc_on_to_date and alloc_on_from_date.name != alloc_on_to_date.name)
		):
			return True
		return False

	def create_separate_ledger_entries(self, alloc_on_from_date, alloc_on_to_date, submit, lwp):
		"""Creates separate ledger entries for application period falling into separate allocations"""
		# for creating separate ledger entries existing allocation periods should be consecutive
		if (
			submit
			and alloc_on_from_date
			and alloc_on_to_date
			and add_days(alloc_on_from_date.to_date, 1) != alloc_on_to_date.from_date
		):
			frappe.throw(
				_(
					"Leave Application period cannot be across two non-consecutive leave allocations {0} and {1}."
				).format(
					get_link_to_form("Leave Allocation", alloc_on_from_date.name),
					get_link_to_form("Leave Allocation", alloc_on_to_date),
				)
			)

		raise_exception = False if frappe.flags.in_patch else True

		if alloc_on_from_date:
			first_alloc_end = alloc_on_from_date.to_date
			second_alloc_start = add_days(alloc_on_from_date.to_date, 1)
		else:
			first_alloc_end = add_days(alloc_on_to_date.from_date, -1)
			second_alloc_start = alloc_on_to_date.from_date

		leaves_in_first_alloc = get_number_of_leave_days(
			self.employee,
			self.leave_type,
			self.from_date,
			first_alloc_end,
			self.half_day,
			self.half_day_date,
		)
		leaves_in_second_alloc = get_number_of_leave_days(
			self.employee,
			self.leave_type,
			second_alloc_start,
			self.to_date,
			self.half_day,
			self.half_day_date,
		)

		args = dict(
			is_lwp=lwp,
			holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception) or "",
		)

		if leaves_in_first_alloc:
			args.update(
				dict(from_date=self.from_date, to_date=first_alloc_end, leaves=leaves_in_first_alloc * -1)
			)
			create_leave_ledger_entry(self, args, submit)

		if leaves_in_second_alloc:
			args.update(
				dict(from_date=second_alloc_start, to_date=self.to_date, leaves=leaves_in_second_alloc * -1)
			)
			create_leave_ledger_entry(self, args, submit)

	def create_ledger_entry_for_intermediate_allocation_expiry(self, expiry_date, submit, lwp):
		"""Splits leave application into two ledger entries to consider expiry of allocation"""
		raise_exception = False if frappe.flags.in_patch else True

		leaves = get_number_of_leave_days(
			self.employee, self.leave_type, self.from_date, expiry_date, self.half_day, self.half_day_date
		)

		if leaves:
			args = dict(
				from_date=self.from_date,
				to_date=expiry_date,
				leaves=leaves * -1,
				is_lwp=lwp,
				holiday_list=get_holiday_list_for_employee(self.employee, raise_exception=raise_exception)
				or "",
			)
			create_leave_ledger_entry(self, args, submit)

		if getdate(expiry_date) != getdate(self.to_date):
			start_date = add_days(expiry_date, 1)
			leaves = get_number_of_leave_days(
				self.employee, self.leave_type, start_date, self.to_date, self.half_day, self.half_day_date
			)

			if leaves:
				args.update(dict(from_date=start_date, to_date=self.to_date, leaves=leaves * -1))
				create_leave_ledger_entry(self, args, submit)

	def validate_for_self_approval(self):
		self_leave_approval_not_allowed = frappe.db.get_single_value(
			"HR Settings", "prevent_self_leave_approval"
		)
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id")
		if (
			self_leave_approval_not_allowed
			and employee_user == frappe.session.user
			and not get_workflow_name("Leave Application")
		):
			frappe.throw(_("Self-approval for leaves is not allowed"))

	def onload(self):
		self.set_onload(
			"self_leave_approval_not_allowed",
			frappe.db.get_single_value("HR Settings", "prevent_self_leave_approval"),
		)


def get_allocation_expiry_for_cf_leaves(
	employee: str, leave_type: str, to_date: datetime.date, from_date: datetime.date
) -> str:
	"""Returns expiry of carry forward allocation in leave ledger entry"""
	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	expiry = (
		frappe.qb.from_(Ledger)
		.select(Ledger.to_date)
		.where(
			(Ledger.employee == employee)
			& (Ledger.leave_type == leave_type)
			& (Ledger.is_carry_forward == 1)
			& (Ledger.transaction_type == "Leave Allocation")
			& (Ledger.to_date.between(from_date, to_date))
			& (Ledger.docstatus == 1)
		)
		.limit(1)
	).run()

	return expiry[0][0] if expiry else ""


@frappe.whitelist()
def get_number_of_leave_days(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	half_day: int | str | None = None,
	half_day_date: datetime.date | str | None = None,
	holiday_list: str | None = None,
) -> float:
	"""Returns number of leave days between 2 dates after considering half day and holidays
	(Based on the include_holiday setting in Leave Type)"""
	number_of_days = 0
	if cint(half_day) == 1:
		if getdate(from_date) == getdate(to_date):
			number_of_days = 0.5
		elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
			number_of_days = date_diff(to_date, from_date) + 0.5
		else:
			number_of_days = date_diff(to_date, from_date) + 1
	else:
		number_of_days = date_diff(to_date, from_date) + 1

	if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
		number_of_days = flt(number_of_days) - flt(
			get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
		)
	return number_of_days


@frappe.whitelist()
def get_leave_details(employee, date, for_salary_slip=False):
	allocation_records = get_leave_allocation_records(employee, date)
	leave_allocation = {}
	precision = cint(frappe.db.get_single_value("System Settings", "float_precision")) or 2

	for d in allocation_records:
		allocation = allocation_records.get(d, frappe._dict())
		to_date = date if for_salary_slip else allocation.to_date
		remaining_leaves = get_leave_balance_on(
			employee,
			d,
			date,
			to_date=to_date,
			consider_all_leaves_in_the_allocation_period=False if for_salary_slip else True,
		)

		leaves_taken = get_leaves_for_period(employee, d, allocation.from_date, to_date) * -1
		leaves_pending = get_leaves_pending_approval_for_period(employee, d, allocation.from_date, to_date)
		expired_leaves = allocation.total_leaves_allocated - (remaining_leaves + leaves_taken)

		leave_allocation[d] = {
			"total_leaves": flt(allocation.total_leaves_allocated, precision),
			"expired_leaves": flt(expired_leaves, precision) if expired_leaves > 0 else 0,
			"leaves_taken": flt(leaves_taken, precision),
			"leaves_pending_approval": flt(leaves_pending, precision),
			"remaining_leaves": flt(remaining_leaves, precision),
		}

	# is used in set query
	lwp = frappe.get_list("Leave Type", filters={"is_lwp": 1}, pluck="name")

	return {
		"leave_allocation": leave_allocation,
		"leave_approver": get_leave_approver(employee),
		"lwps": lwp,
	}


@frappe.whitelist()
def get_leave_balance_on(
	employee: str,
	leave_type: str,
	date: datetime.date,
	to_date: datetime.date | None = None,
	consider_all_leaves_in_the_allocation_period: bool = False,
	for_consumption: bool = False,
):
	"""
	Returns leave balance till date
	:param employee: employee name
	:param leave_type: leave type
	:param date: date to check balance on
	:param to_date: future date to check for allocation expiry
	:param consider_all_leaves_in_the_allocation_period: consider all leaves taken till the allocation end date
	:param for_consumption: flag to check if leave balance is required for consumption or display
	        eg: employee has leave balance = 10 but allocation is expiring in 1 day so employee can only consume 1 leave
	        in this case leave_balance = 10 but leave_balance_for_consumption = 1
	        if True, returns a dict eg: {'leave_balance': 10, 'leave_balance_for_consumption': 1}
	        else, returns leave_balance (in this case 10)
	"""

	if not to_date:
		to_date = nowdate()

	allocation_records = get_leave_allocation_records(employee, date, leave_type)
	allocation = allocation_records.get(leave_type, frappe._dict())

	end_date = allocation.to_date if cint(consider_all_leaves_in_the_allocation_period) else date
	cf_expiry = get_allocation_expiry_for_cf_leaves(employee, leave_type, to_date, allocation.from_date)

	leaves_taken = get_leaves_for_period(employee, leave_type, allocation.from_date, end_date)

	manually_expired_leaves = get_manually_expired_leaves(
		employee, leave_type, allocation.from_date, end_date
	)

	remaining_leaves = get_remaining_leaves(
		allocation, leaves_taken, date, cf_expiry, manually_expired_leaves
	)

	if for_consumption:
		return remaining_leaves
	else:
		return remaining_leaves.get("leave_balance")


def get_leave_allocation_records(employee, date, leave_type=None):
	"""Returns the total allocated leaves and carry forwarded leaves based on ledger entries"""
	Ledger = frappe.qb.DocType("Leave Ledger Entry")
	LeaveAllocation = frappe.qb.DocType("Leave Allocation")
	LeaveAdjustment = frappe.qb.DocType("Leave Adjustment")

	cf_leave_case = frappe.qb.terms.Case().when(Ledger.is_carry_forward == "1", Ledger.leaves).else_(0)
	sum_cf_leaves = Sum(cf_leave_case).as_("cf_leaves")

	new_leaves_case = frappe.qb.terms.Case().when(Ledger.is_carry_forward == "0", Ledger.leaves).else_(0)
	sum_new_leaves = Sum(new_leaves_case).as_("new_leaves")

	query = (
		frappe.qb.from_(Ledger)
		.left_join(LeaveAllocation)
		.on(Ledger.transaction_name == LeaveAllocation.name)
		.left_join(LeaveAdjustment)
		.on(Ledger.transaction_name == LeaveAdjustment.name)
		.select(
			sum_cf_leaves,
			sum_new_leaves,
			Min(Ledger.from_date).as_("from_date"),
			Max(Ledger.to_date).as_("to_date"),
			Ledger.leave_type,
			Ledger.employee,
		)
		.where(
			(Ledger.from_date <= date)
			& (Ledger.docstatus == 1)
			& (
				(Ledger.transaction_type == "Leave Allocation")
				| (Ledger.transaction_type == "Leave Adjustment")
			)
			& (Ledger.employee == employee)
			& (Ledger.is_expired == 0)
			& (Ledger.is_lwp == 0)
			& (
				# newly allocated leave's end date is same as the leave allocation's to date
				((Ledger.is_carry_forward == 0) & (Ledger.to_date >= date))
				# carry forwarded leave's end date won't be same as the leave allocation's to date
				# it's between the leave allocation's from and to date
				| (
					(Ledger.is_carry_forward == 1)
					& (
						Ledger.to_date.between(LeaveAllocation.from_date, LeaveAllocation.to_date)
						| (Ledger.to_date.between(LeaveAdjustment.from_date, LeaveAdjustment.to_date))
					)
					# only consider cf leaves from current allocation
					& ((LeaveAllocation.from_date <= date) | (LeaveAdjustment.from_date <= date))
					& ((date <= LeaveAllocation.to_date) | (date <= LeaveAdjustment.to_date))
				)
			)
		)
	)

	if leave_type:
		query = query.where(Ledger.leave_type == leave_type)
	query = query.groupby(Ledger.employee, Ledger.leave_type)

	allocation_details = query.run(as_dict=True)
	allocated_leaves = frappe._dict()
	for d in allocation_details:
		allocated_leaves.setdefault(
			d.leave_type,
			frappe._dict(
				{
					"from_date": d.from_date,
					"to_date": d.to_date,
					"total_leaves_allocated": flt(d.cf_leaves) + flt(d.new_leaves),
					"unused_leaves": d.cf_leaves,
					"new_leaves_allocated": d.new_leaves,
					"leave_type": d.leave_type,
					"employee": d.employee,
				}
			),
		)
	return allocated_leaves


def get_leaves_pending_approval_for_period(
	employee: str, leave_type: str, from_date: datetime.date, to_date: datetime.date
) -> float:
	"""Returns leaves that are pending for approval"""
	leaves = frappe.get_all(
		"Leave Application",
		filters={"employee": employee, "leave_type": leave_type, "status": "Open"},
		or_filters={
			"from_date": ["between", (from_date, to_date)],
			"to_date": ["between", (from_date, to_date)],
		},
		fields=[{"SUM": "total_leave_days", "as": "leaves"}],
	)[0]
	return leaves["leaves"] if leaves["leaves"] else 0.0


def get_remaining_leaves(
	allocation: dict, leaves_taken: float, date: str, cf_expiry: str, manually_expired_leaves: float
) -> dict[str, float]:
	"""Returns a dict of leave_balance and leave_balance_for_consumption
	leave_balance returns the available leave balance
	leave_balance_for_consumption returns the minimum leaves remaining after comparing with remaining days for allocation expiry
	"""

	def _get_remaining_leaves(remaining_leaves, end_date):
		"""Returns minimum leaves remaining after comparing with remaining days for allocation expiry"""
		if remaining_leaves > 0:
			remaining_days = date_diff(end_date, date) + 1
			remaining_leaves = min(remaining_days, remaining_leaves)

		return remaining_leaves

	if cf_expiry and allocation.unused_leaves:
		# allocation contains both carry forwarded and new leaves
		new_leaves_taken, cf_leaves_taken = get_new_and_cf_leaves_taken(allocation, cf_expiry)

		if getdate(date) > getdate(cf_expiry):
			# carry forwarded leaves have expired
			cf_leaves = remaining_cf_leaves = 0
		else:
			cf_leaves = flt(allocation.unused_leaves) + flt(cf_leaves_taken)
			remaining_cf_leaves = _get_remaining_leaves(cf_leaves, cf_expiry)

		# new leaves allocated - new leaves taken + cf leave balance
		# Note: `new_leaves_taken` is added here because its already a -ve number in the ledger
		leave_balance = (
			(flt(allocation.new_leaves_allocated) + flt(new_leaves_taken))
			+ flt(cf_leaves)
			+ flt(manually_expired_leaves)
		)
		leave_balance_for_consumption = (
			(flt(allocation.new_leaves_allocated) + flt(new_leaves_taken))
			+ flt(remaining_cf_leaves)
			+ flt(manually_expired_leaves)
		)
	else:
		# allocation only contains newly allocated leaves
		leave_balance = leave_balance_for_consumption = (
			flt(allocation.total_leaves_allocated) + flt(leaves_taken) + flt(manually_expired_leaves)
		)

	remaining_leaves = _get_remaining_leaves(leave_balance_for_consumption, allocation.to_date)
	return frappe._dict(leave_balance=leave_balance, leave_balance_for_consumption=remaining_leaves)


def get_manually_expired_leaves(
	employee: str, leave_type: str, from_date: datetime.date, end_date: datetime.date
):
	ledger = frappe.qb.DocType("Leave Ledger Entry")

	leaves = (
		frappe.qb.from_(ledger)
		.select(ledger.leaves)
		.where(
			(ledger.docstatus == 1)
			& (ledger.employee == employee)
			& (ledger.leave_type == leave_type)
			& (ledger.from_date >= from_date)
			& (ledger.to_date <= end_date)
			& (ledger.transaction_type == "Leave Allocation")
			& ((ledger.is_expired == 1) & (ledger.is_carry_forward == 0))
		)
	).run()
	return leaves[0][0] if leaves else 0.0


def get_new_and_cf_leaves_taken(allocation: dict, cf_expiry: str) -> tuple[float, float]:
	"""returns new leaves taken and carry forwarded leaves taken within an allocation period based on cf leave expiry"""
	cf_leaves_taken = get_leaves_for_period(
		allocation.employee, allocation.leave_type, allocation.from_date, cf_expiry
	)
	new_leaves_taken = get_leaves_for_period(
		allocation.employee, allocation.leave_type, add_days(cf_expiry, 1), allocation.to_date
	)

	# using abs because leaves taken is a -ve number in the ledger
	if abs(cf_leaves_taken) > allocation.unused_leaves:
		# adjust the excess leaves in new_leaves_taken
		new_leaves_taken += -(abs(cf_leaves_taken) - allocation.unused_leaves)
		cf_leaves_taken = -allocation.unused_leaves

	return new_leaves_taken, cf_leaves_taken


def get_leaves_for_period(
	employee: str,
	leave_type: str,
	from_date: datetime.date,
	to_date: datetime.date,
	skip_expired_leaves: bool = True,
) -> float:
	leave_entries = get_leave_entries(employee, leave_type, from_date, to_date)
	leave_days = 0

	for leave_entry in leave_entries:
		inclusive_period = leave_entry.from_date >= getdate(from_date) and leave_entry.to_date <= getdate(
			to_date
		)

		if inclusive_period and leave_entry.transaction_type == "Leave Encashment":
			leave_days += leave_entry.leaves

		elif (
			inclusive_period
			and leave_entry.transaction_type == "Leave Allocation"
			and leave_entry.is_expired
			and not skip_expired_leaves
		):
			leave_days += leave_entry.leaves

		elif leave_entry.transaction_type == "Leave Application":
			if leave_entry.from_date < getdate(from_date):
				leave_entry.from_date = from_date
			if leave_entry.to_date > getdate(to_date):
				leave_entry.to_date = to_date

			half_day = 0
			half_day_date = None
			# fetch half day date for leaves with half days
			if leave_entry.leaves % 1:
				half_day = 1
				half_day_date = frappe.db.get_value(
					"Leave Application", leave_entry.transaction_name, "half_day_date"
				)

			leave_days += (
				get_number_of_leave_days(
					employee,
					leave_type,
					leave_entry.from_date,
					leave_entry.to_date,
					half_day,
					half_day_date,
					holiday_list=leave_entry.holiday_list,
				)
				* -1
			)

	return leave_days


def get_leave_entries(employee, leave_type, from_date, to_date):
	"""Returns leave entries between from_date and to_date."""
	return frappe.db.sql(
		"""
		SELECT
			employee, leave_type, from_date, to_date, leaves, transaction_name, transaction_type, holiday_list,
			is_carry_forward, is_expired
		FROM `tabLeave Ledger Entry`
		WHERE employee=%(employee)s AND leave_type=%(leave_type)s
			AND docstatus=1
			AND (leaves<0
				OR is_expired=1)
			AND (from_date between %(from_date)s AND %(to_date)s
				OR to_date between %(from_date)s AND %(to_date)s
				OR (from_date < %(from_date)s AND to_date > %(to_date)s))
	""",
		{"from_date": from_date, "to_date": to_date, "employee": employee, "leave_type": leave_type},
		as_dict=1,
	)


@frappe.whitelist()
def get_holidays(employee, from_date, to_date, holiday_list=None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)

	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s""",
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays


def is_lwp(leave_type):
	lwp = frappe.db.sql("select is_lwp from `tabLeave Type` where name = %s", leave_type)
	return lwp and cint(lwp[0][0]) or 0


@frappe.whitelist()
def get_events(start, end, filters=None):
	import json

	filters = json.loads(filters)
	for idx, filter in enumerate(filters):
		# taking relevant fields from the list [doctype, fieldname, condition, value, hidden]
		filters[idx] = filter[1:-1]

	events = []

	employee = frappe.db.get_value(
		"Employee", filters={"user_id": frappe.session.user}, fieldname=["name", "company"], as_dict=True
	)

	if employee:
		employee, company = employee.name, employee.company
	else:
		employee = ""
		company = frappe.db.get_single_value("Global Defaults", "default_company")

	# show department leaves for employee
	if "Employee" in frappe.get_roles():
		add_department_leaves(events, start, end, employee, company)

	add_leaves(events, start, end, filters)
	add_block_dates(events, start, end, employee, company)
	add_holidays(events, start, end, employee, company)

	return events


def add_department_leaves(events, start, end, employee, company):
	if department := frappe.db.get_value("Employee", employee, "department"):
		department_employees = frappe.get_list(
			"Employee", filters={"department": department, "company": company}, pluck="name"
		)
		filters = [["employee", "in", department_employees]]
		add_leaves(events, start, end, filters=filters)


def add_leaves(events, start, end, filters=None):
	if not filters:
		filters = []
	filters.extend(
		[
			["from_date", "<=", getdate(end)],
			["to_date", ">=", getdate(start)],
			["status", "in", ["Approved", "Open"]],
			["docstatus", "<", 2],
		]
	)

	fields = [
		"name",
		"from_date",
		"to_date",
		"color",
		"docstatus",
		"employee_name",
		"leave_type",
	]

	show_leaves_of_all_members = frappe.db.get_single_value(
		"HR Settings", "show_leaves_of_all_department_members_in_calendar"
	)
	if cint(show_leaves_of_all_members):
		leave_applications = frappe.get_all("Leave Application", filters=filters, fields=fields)
	else:
		leave_applications = frappe.get_list("Leave Application", filters=filters, fields=fields)
	for d in leave_applications:
		d["title"] = f"{d['employee_name']} ({d['leave_type']})"
		d["allDay"] = 1
		d["doctype"] = "Leave Application"
		del d["employee_name"]
		del d["leave_type"]
		if d not in events:
			events.append(d)


def add_block_dates(events, start, end, employee, company):
	cnt = 0
	block_dates = get_applicable_block_dates(start, end, employee, company, all_lists=True)

	for block_date in block_dates:
		events.append(
			{
				"doctype": "Leave Block List Date",
				"from_date": block_date.block_date,
				"to_date": block_date.block_date,
				"title": _("Leave Blocked") + ": " + block_date.reason,
				"name": "_" + str(cnt),
				"allDay": 1,
			}
		)
		cnt += 1


def add_holidays(events, start, end, employee, company):
	applicable_holiday_list = get_holiday_list_for_employee(employee, company)
	if not applicable_holiday_list:
		return

	for holiday in frappe.db.sql(
		"""select name, holiday_date, description
		from `tabHoliday` where parent=%s and holiday_date between %s and %s""",
		(applicable_holiday_list, start, end),
		as_dict=True,
	):
		events.append(
			{
				"doctype": "Holiday",
				"from_date": holiday.holiday_date,
				"to_date": holiday.holiday_date,
				"title": _("Holiday") + ": " + cstr(holiday.description),
				"name": holiday.name,
				"allDay": 1,
			}
		)


@frappe.whitelist()
def get_mandatory_approval(doctype):
	mandatory = ""
	if doctype == "Leave Application":
		mandatory = frappe.db.get_single_value("HR Settings", "leave_approver_mandatory_in_leave_application")
	else:
		mandatory = frappe.db.get_single_value("HR Settings", "expense_approver_mandatory_in_expense_claim")

	return mandatory


def get_approved_leaves_for_period(employee, leave_type, from_date, to_date):
	LeaveApplication = frappe.qb.DocType("Leave Application")
	query = (
		frappe.qb.from_(LeaveApplication)
		.select(
			LeaveApplication.employee,
			LeaveApplication.leave_type,
			LeaveApplication.from_date,
			LeaveApplication.to_date,
			LeaveApplication.total_leave_days,
		)
		.where(
			(LeaveApplication.employee == employee)
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (
				(LeaveApplication.from_date.between(from_date, to_date))
				| (LeaveApplication.to_date.between(from_date, to_date))
				| ((LeaveApplication.from_date < from_date) & (LeaveApplication.to_date > to_date))
			)
		)
	)

	if leave_type:
		query = query.where(LeaveApplication.leave_type == leave_type)

	leave_applications = query.run(as_dict=True)

	leave_days = 0
	for leave_app in leave_applications:
		if leave_app.from_date >= getdate(from_date) and leave_app.to_date <= getdate(to_date):
			leave_days += leave_app.total_leave_days
		else:
			if leave_app.from_date < getdate(from_date):
				leave_app.from_date = from_date
			if leave_app.to_date > getdate(to_date):
				leave_app.to_date = to_date

			leave_days += get_number_of_leave_days(
				employee, leave_type, leave_app.from_date, leave_app.to_date
			)

	return leave_days


@frappe.whitelist()
def get_leave_approver(employee):
	leave_approver, department = frappe.db.get_value("Employee", employee, ["leave_approver", "department"])

	if not leave_approver and department:
		leave_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	return leave_approver


def on_doctype_update():
	frappe.db.add_index("Leave Application", ["employee", "from_date", "to_date"])
